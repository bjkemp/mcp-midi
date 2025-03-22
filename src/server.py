#!/usr/bin/env python3
"""
MCP MIDI Server - Bridge between Claude and USB MIDI devices
"""
import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Any, Tuple, Union

import mido
import rtmidi
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from mcp_midi.all_notes_off import register_note_on, register_note_off, all_notes_off

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_midi")

# Create FastAPI app
app = FastAPI(title="MCP MIDI Server")

# Helper function to create a MIDI callback
def create_midi_callback():
    """Create a callback function for sending MIDI messages
    This is a workaround for the async issue in the Song class
    """
    def send_midi_callback(cmd_type, params, port_id=0):
        try:
            port = connect_to_port(port_id)
            
            if cmd_type == "note_on":
                msg = mido.Message('note_on', note=params["note"], velocity=params["velocity"], channel=params["channel"])
            elif cmd_type == "note_off":
                msg = mido.Message('note_off', note=params["note"], velocity=params.get("velocity", 0), channel=params["channel"])
            elif cmd_type == "control_change":
                msg = mido.Message('control_change', control=params["control"], value=params["value"], channel=params["channel"])
            elif cmd_type == "program_change":
                msg = mido.Message('program_change', program=params["program"], channel=params["channel"])
            else:
                return
            
            port.send(msg)
        except Exception as e:
            logger.error(f"Error in MIDI callback: {e}")
    
    return send_midi_callback

# Global state for MIDI connections
midi_ports = {}
active_ports = {}
current_instrument = 0  # Default General MIDI instrument

# Import song functionality
from mcp_midi.song.manager import SongManager
from mcp_midi.song.song import Song

# Initialize song manager
song_manager = SongManager()

class MidiCommand(BaseModel):
    """Model for MIDI commands from Claude"""
    command: str
    params: Dict[str, Any] = Field(default_factory=dict)


class MidiNoteOn(BaseModel):
    """Model for note_on events"""
    note: int
    velocity: int = 64
    channel: int = 0


class MidiNoteOff(BaseModel):
    """Model for note_off events"""
    note: int
    velocity: int = 0
    channel: int = 0


class MidiControlChange(BaseModel):
    """Model for control_change events"""
    control: int
    value: int
    channel: int = 0


class MidiProgramChange(BaseModel):
    """Model for program_change events"""
    program: int
    channel: int = 0


def discover_midi_ports():
    """Discover available MIDI output ports"""
    try:
        midi_out = rtmidi.MidiOut()
        available_ports = midi_out.get_ports()
        
        midi_ports.clear()
        for i, port in enumerate(available_ports):
            midi_ports[i] = {
                "id": i,
                "name": port,
                "type": "output",
            }
        
        return midi_ports
    except Exception as e:
        logger.error(f"Error in discover_midi_ports: {e}")
        return {}


def connect_to_port(port_id: int):
    """Connect to a MIDI output port"""
    if port_id in active_ports:
        return active_ports[port_id]
    
    if port_id not in midi_ports:
        discover_midi_ports()
        if port_id not in midi_ports:
            raise ValueError(f"MIDI port {port_id} not found")
    
    midi_out = mido.open_output(midi_ports[port_id]["name"])
    active_ports[port_id] = midi_out
    return midi_out


def close_all_connections():
    """Close all active MIDI connections"""
    for port_id, port in active_ports.items():
        port.close()
    active_ports.clear()


@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup"""
    try:
        # Discover MIDI ports
        ports = discover_midi_ports()
        if ports:
            logger.info(f"Discovered MIDI ports: {ports}")
        else:
            logger.warning("No MIDI ports were discovered. Please connect a MIDI device and restart the server.")
        
        # Initialize song manager with MIDI callback
        midi_callback = create_midi_callback()
        song_manager.set_midi_callback(midi_callback)
        logger.info("Song manager initialized with MIDI callback")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        logger.warning("The server will continue running, but MIDI functionality may not work properly.")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on server shutdown"""
    close_all_connections()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MCP MIDI Server"}


@app.get("/midi/ports")
async def get_midi_ports():
    """Get available MIDI ports"""
    ports = discover_midi_ports()
    return {"ports": list(ports.values())}


@app.post("/midi/connect/{port_id}")
async def connect_midi_port(port_id: int):
    """Connect to a specific MIDI port"""
    try:
        port = connect_to_port(port_id)
        return {"message": f"Connected to MIDI port {port_id}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/midi/instrument/{instrument_id}")
async def set_instrument(instrument_id: int, port_id: int = 0):
    """Set the active instrument"""
    global current_instrument
    
    try:
        port = connect_to_port(port_id)
        current_instrument = instrument_id
        
        # Send program change message
        msg = mido.Message('program_change', program=instrument_id, channel=0)
        port.send(msg)
        
        return {
            "message": f"Set instrument to {instrument_id}",
            "port_id": port_id
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/midi/note_on")
async def send_note_on(note_data: MidiNoteOn, port_id: int = 0):
    """Send a note_on message"""
    try:
        port = connect_to_port(port_id)
        msg = mido.Message(
            'note_on',
            note=note_data.note,
            velocity=note_data.velocity,
            channel=note_data.channel
        )
        port.send(msg)
        
        # Register the note as active
        register_note_on(note_data.note, note_data.channel)
        
        return {"message": f"Sent note_on: {note_data}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/midi/note_off")
async def send_note_off(note_data: MidiNoteOff, port_id: int = 0):
    """Send a note_off message"""
    try:
        port = connect_to_port(port_id)
        msg = mido.Message(
            'note_off',
            note=note_data.note,
            velocity=note_data.velocity,
            channel=note_data.channel
        )
        port.send(msg)
        
        # Unregister the note
        register_note_off(note_data.note, note_data.channel)
        
        return {"message": f"Sent note_off: {note_data}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/midi/control_change")
async def send_control_change(cc_data: MidiControlChange, port_id: int = 0):
    """Send a control_change message"""
    try:
        port = connect_to_port(port_id)
        msg = mido.Message(
            'control_change',
            control=cc_data.control,
            value=cc_data.value,
            channel=cc_data.channel
        )
        port.send(msg)
        return {"message": f"Sent control_change: {cc_data}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/midi/program_change")
async def send_program_change(pc_data: MidiProgramChange, port_id: int = 0):
    """Send a program_change message"""
    try:
        port = connect_to_port(port_id)
        msg = mido.Message(
            'program_change',
            program=pc_data.program,
            channel=pc_data.channel
        )
        port.send(msg)
        return {"message": f"Sent program_change: {pc_data}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


class AllNotesOffRequest(BaseModel):
    """Model for all_notes_off request"""
    channels: Optional[List[int]] = None  # None = all channels


@app.post("/midi/all_notes_off")
async def send_all_notes_off(request: AllNotesOffRequest = None, port_id: int = 0):
    """Send all_notes_off messages for the specified channels"""
    try:
        port = connect_to_port(port_id)
        
        # Use default if no request body was provided
        if request is None:
            request = AllNotesOffRequest()
        
        # Send all notes off
        all_notes_off(port, None, request.channels)
        
        return {"message": f"Sent all_notes_off for channels: {request.channels or 'all'}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )

# Song-related endpoints

class CreateSongRequest(BaseModel):
    """Model for creating a new song"""
    name: str
    tempo: int = 120


class CreateScaleRequest(BaseModel):
    """Model for creating a scale"""
    name: str
    root_note: int
    scale_type: str
    octaves: int = 1
    duration: float = 0.5


class AddNoteRequest(BaseModel):
    """Model for adding a note to a song"""
    pitch: int
    time: float
    duration: float
    velocity: int = 64
    channel: int = 0


class AddChordRequest(BaseModel):
    """Model for adding a chord to a song"""
    notes: List[int]
    time: float
    duration: float
    velocity: int = 64
    channel: int = 0


class AddProgramChangeRequest(BaseModel):
    """Model for adding a program change to a song"""
    program: int
    time: float
    channel: int = 0


class PlaySongRequest(BaseModel):
    """Model for playing a song by name"""
    name: str


@app.post("/song/create")
async def create_song(request: CreateSongRequest):
    """Create a new empty song"""
    try:
        song = Song(name=request.name, tempo=request.tempo)
        
        # Set MIDI callback for the song
        midi_callback = create_midi_callback()
        
        song.set_midi_callback(send_midi_callback)
        song_manager.add_song(song)
        
        return {"message": f"Created song: {request.name}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/song/create_scale")
async def create_scale(request: CreateScaleRequest):
    """Create a new song with a musical scale"""
    try:
        # Set MIDI callback for the song manager if not already set
        if not song_manager.send_midi_callback:
            midi_callback = create_midi_callback()
            song_manager.set_midi_callback(midi_callback)
        
        song = song_manager.create_scale_song(
            name=request.name,
            root_note=request.root_note,
            scale_type=request.scale_type,
            octaves=request.octaves,
            duration=request.duration
        )
        
        return {
            "message": f"Created scale song: {request.name}",
            "song": {
                "name": song.name,
                "duration": song.duration
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/song/add_note")
async def add_note_to_song(request: AddNoteRequest, song_name: str):
    """Add a note to a song"""
    try:
        song = song_manager.get_song(song_name)
        if not song:
            return JSONResponse(
                status_code=404,
                content={"error": f"Song not found: {song_name}"}
            )
        
        song.add_note(
            pitch=request.pitch,
            time=request.time,
            duration=request.duration,
            velocity=request.velocity,
            channel=request.channel
        )
        
        return {"message": f"Added note to song: {song_name}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/song/add_chord")
async def add_chord_to_song(request: AddChordRequest, song_name: str):
    """Add a chord to a song"""
    try:
        song = song_manager.get_song(song_name)
        if not song:
            return JSONResponse(
                status_code=404,
                content={"error": f"Song not found: {song_name}"}
            )
        
        song.add_chord(
            notes=request.notes,
            time=request.time,
            duration=request.duration,
            velocity=request.velocity,
            channel=request.channel
        )
        
        return {"message": f"Added chord to song: {song_name}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/song/add_program_change")
async def add_program_change_to_song(request: AddProgramChangeRequest, song_name: str):
    """Add a program change to a song"""
    try:
        song = song_manager.get_song(song_name)
        if not song:
            return JSONResponse(
                status_code=404,
                content={"error": f"Song not found: {song_name}"}
            )
        
        song.add_program_change(
            program=request.program,
            time=request.time,
            channel=request.channel
        )
        
        return {"message": f"Added program change to song: {song_name}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/song/play")
async def play_song(request: PlaySongRequest):
    """Play a song by name"""
    try:
        success = song_manager.play_song(request.name)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": f"Song not found or could not be played: {request.name}"}
            )
        
        return {"message": f"Playing song: {request.name}"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.post("/song/stop")
async def stop_song():
    """Stop the currently playing song"""
    try:
        success = song_manager.stop_current_song()
        if not success:
            return JSONResponse(
                status_code=400,
                content={"error": "No song is currently playing"}
            )
        
        return {"message": "Stopped current song"}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.get("/song/list")
async def list_songs():
    """List all available songs"""
    try:
        songs = song_manager.get_all_songs()
        song_list = [
            {
                "name": name,
                "duration": song.duration,
                "tempo": song.tempo
            }
            for name, song in songs.items()
        ]
        
        return {"songs": song_list}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


# MCP Protocol implementation
class MCPRequest(BaseModel):
    """MCP Request Model"""
    jsonrpc: str
    id: Optional[str] = None
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """MCP Response Model"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP requests"""
    try:
        data = await request.json()
        mcp_request = MCPRequest(**data)
        
        # Handle different MCP methods
        if mcp_request.method == "midi.discover":
            ports = discover_midi_ports()
            return MCPResponse(
                id=mcp_request.id,
                result={"ports": list(ports.values())}
            )
        
        elif mcp_request.method == "midi.connect":
            port_id = mcp_request.params.get("port_id", 0)
            connect_to_port(port_id)
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Connected to port {port_id}"}
            )
        
        elif mcp_request.method == "midi.note_on":
            port_id = mcp_request.params.get("port_id", 0)
            note = mcp_request.params.get("note")
            velocity = mcp_request.params.get("velocity", 64)
            channel = mcp_request.params.get("channel", 0)
            
            port = connect_to_port(port_id)
            msg = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
            port.send(msg)
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Note on: {note}, velocity: {velocity}"}
            )
        
        elif mcp_request.method == "midi.note_off":
            port_id = mcp_request.params.get("port_id", 0)
            note = mcp_request.params.get("note")
            velocity = mcp_request.params.get("velocity", 0)
            channel = mcp_request.params.get("channel", 0)
            
            port = connect_to_port(port_id)
            msg = mido.Message('note_off', note=note, velocity=velocity, channel=channel)
            port.send(msg)
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Note off: {note}"}
            )
        
        elif mcp_request.method == "midi.program_change":
            port_id = mcp_request.params.get("port_id", 0)
            program = mcp_request.params.get("program", 0)
            channel = mcp_request.params.get("channel", 0)
            
            port = connect_to_port(port_id)
            msg = mido.Message('program_change', program=program, channel=channel)
            port.send(msg)
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Program change: {program}"}
            )
        
        elif mcp_request.method == "midi.control_change":
            port_id = mcp_request.params.get("port_id", 0)
            control = mcp_request.params.get("control")
            value = mcp_request.params.get("value")
            channel = mcp_request.params.get("channel", 0)
            
            port = connect_to_port(port_id)
            msg = mido.Message('control_change', control=control, value=value, channel=channel)
            port.send(msg)
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Control change: {control}, value: {value}"}
            )
            
        elif mcp_request.method == "midi.all_notes_off":
            port_id = mcp_request.params.get("port_id", 0)
            channels = mcp_request.params.get("channels")
            
            port = connect_to_port(port_id)
            all_notes_off(port, None, channels)
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"All notes off sent for channels: {channels or 'all'}"}
            )
        
        # Song-related MCP methods
        elif mcp_request.method == "create_song":
            name = mcp_request.params.get("name", "Untitled")
            tempo = mcp_request.params.get("tempo", 120)
            
            song = Song(name=name, tempo=tempo)
            
            # Set MIDI callback for the song
            midi_callback = create_midi_callback()
            song.set_midi_callback(midi_callback)
            song_manager.add_song(song)
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Created song: {name}"}
            )
        
        elif mcp_request.method == "create_scale":
            name = mcp_request.params.get("name", "Scale")
            root_note = mcp_request.params.get("root_note", 60)  # Middle C
            scale_type = mcp_request.params.get("scale_type", "major")
            octaves = mcp_request.params.get("octaves", 1)
            duration = mcp_request.params.get("duration", 0.5)
            
            # Set MIDI callback for the song manager if not already set
            if not song_manager.send_midi_callback:
                async def send_midi_callback(cmd_type, params, port_id=0):
                    port = connect_to_port(port_id)
                    
                    if cmd_type == "note_on":
                        msg = mido.Message('note_on', note=params["note"], velocity=params["velocity"], channel=params["channel"])
                    elif cmd_type == "note_off":
                        msg = mido.Message('note_off', note=params["note"], velocity=params.get("velocity", 0), channel=params["channel"])
                    elif cmd_type == "control_change":
                        msg = mido.Message('control_change', control=params["control"], value=params["value"], channel=params["channel"])
                    elif cmd_type == "program_change":
                        msg = mido.Message('program_change', program=params["program"], channel=params["channel"])
                    else:
                        return
                    
                    port.send(msg)
                
                song_manager.set_midi_callback(send_midi_callback)
            
            song = song_manager.create_scale_song(
                name=name,
                root_note=root_note,
                scale_type=scale_type,
                octaves=octaves,
                duration=duration
            )
            
            return MCPResponse(
                id=mcp_request.id,
                result={
                    "message": f"Created scale song: {name}",
                    "song": {
                        "name": song.name,
                        "duration": song.duration
                    }
                }
            )
        
        elif mcp_request.method == "add_note":
            song_name = mcp_request.params.get("name")
            pitch = mcp_request.params.get("pitch")
            time = mcp_request.params.get("time")
            duration = mcp_request.params.get("duration")
            velocity = mcp_request.params.get("velocity", 64)
            channel = mcp_request.params.get("channel", 0)
            
            if not song_name:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": "Required parameter 'name' missing"
                    }
                )
            
            song = song_manager.get_song(song_name)
            if not song:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": f"Song not found: {song_name}"
                    }
                )
            
            song.add_note(
                pitch=pitch,
                time=time,
                duration=duration,
                velocity=velocity,
                channel=channel
            )
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Added note to song: {song_name}"}
            )
        
        elif mcp_request.method == "add_chord":
            song_name = mcp_request.params.get("name")
            notes = mcp_request.params.get("notes")
            time = mcp_request.params.get("time")
            duration = mcp_request.params.get("duration")
            velocity = mcp_request.params.get("velocity", 64)
            channel = mcp_request.params.get("channel", 0)
            
            if not song_name:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": "Required parameter 'name' missing"
                    }
                )
            
            song = song_manager.get_song(song_name)
            if not song:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": f"Song not found: {song_name}"
                    }
                )
            
            song.add_chord(
                notes=notes,
                time=time,
                duration=duration,
                velocity=velocity,
                channel=channel
            )
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Added chord to song: {song_name}"}
            )
        
        elif mcp_request.method == "add_program_change":
            song_name = mcp_request.params.get("name")
            program = mcp_request.params.get("program")
            time = mcp_request.params.get("time")
            channel = mcp_request.params.get("channel", 0)
            
            if not song_name:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": "Required parameter 'name' missing"
                    }
                )
            
            song = song_manager.get_song(song_name)
            if not song:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": f"Song not found: {song_name}"
                    }
                )
            
            song.add_program_change(
                program=program,
                time=time,
                channel=channel
            )
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Added program change to song: {song_name}"}
            )
        
        elif mcp_request.method == "play_song":
            song_name = mcp_request.params.get("name")
            
            if not song_name:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": "Required parameter 'name' missing"
                    }
                )
            
            success = song_manager.play_song(song_name)
            if not success:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": f"Song not found or could not be played: {song_name}"
                    }
                )
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": f"Playing song: {song_name}"}
            )
        
        elif mcp_request.method == "stop_song":
            success = song_manager.stop_current_song()
            if not success:
                return MCPResponse(
                    id=mcp_request.id,
                    error={
                        "code": -32602,
                        "message": "No song is currently playing"
                    }
                )
            
            return MCPResponse(
                id=mcp_request.id,
                result={"message": "Stopped current song"}
            )
        
        elif mcp_request.method == "list_songs":
            songs = song_manager.get_all_songs()
            song_list = [
                {
                    "name": name,
                    "duration": song.duration,
                    "tempo": song.tempo
                }
                for name, song in songs.items()
            ]
            
            return MCPResponse(
                id=mcp_request.id,
                result={"songs": song_list}
            )
        
        else:
            return MCPResponse(
                id=mcp_request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {mcp_request.method}"
                }
            )
    
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return MCPResponse(
            id=getattr(mcp_request, 'id', None),
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )


# WebSocket implementation for real-time MIDI control
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                
                if command["type"] == "midi":
                    midi_data = command["data"]
                    cmd_type = midi_data.get("command")
                    
                    if cmd_type == "note_on":
                        await send_note_on(
                            MidiNoteOn(**midi_data["params"]),
                            midi_data.get("port_id", 0)
                        )
                    
                    elif cmd_type == "note_off":
                        await send_note_off(
                            MidiNoteOff(**midi_data["params"]),
                            midi_data.get("port_id", 0)
                        )
                    
                    elif cmd_type == "control_change":
                        await send_control_change(
                            MidiControlChange(**midi_data["params"]),
                            midi_data.get("port_id", 0)
                        )
                    
                    elif cmd_type == "program_change":
                        await send_program_change(
                            MidiProgramChange(**midi_data["params"]),
                            midi_data.get("port_id", 0)
                        )
                    
                    await websocket.send_json({
                        "type": "response",
                        "status": "success",
                        "message": f"Processed {cmd_type}"
                    })
                
                else:
                    await websocket.send_json({
                        "type": "response",
                        "status": "error",
                        "message": f"Unknown command type: {command['type']}"
                    })
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "response",
                    "status": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP MIDI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
