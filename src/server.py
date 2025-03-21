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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_midi")

# Create FastAPI app
app = FastAPI(title="MCP MIDI Server")

# Global state for MIDI connections
midi_ports = {}
active_ports = {}
current_instrument = 0  # Default General MIDI instrument

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
        ports = discover_midi_ports()
        if ports:
            logger.info(f"Discovered MIDI ports: {ports}")
        else:
            logger.warning("No MIDI ports were discovered. Please connect a MIDI device and restart the server.")
    except Exception as e:
        logger.error(f"Error discovering MIDI ports: {e}")
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
