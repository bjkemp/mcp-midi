import os
import sys
import logging
from contextlib import closing
from pathlib import Path
import mido
import rtmidi
from typing import Dict, List, Optional, Any, Union
from pydantic import AnyUrl

from mcp_midi.song.song import Song
from mcp_midi.song.manager import SongManager
from mcp_midi.tracker_parser import create_midi_song

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# reconfigure UnicodeEncodeError prone default (i.e. windows-1252) to utf-8
if sys.platform == "win32" and os.environ.get('PYTHONIOENCODING') is None:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger('mcp_midi_server')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Starting MCP MIDI Server")

PROMPT_TEMPLATE = """
You now have access to a MIDI synthesizer through the MCP MIDI server. You can use the following tools to interact with MIDI devices:

<tools>
- discover_ports: List all available MIDI output ports
- connect_port: Connect to a specific MIDI output port
- note_on: Play a note (parameters: note, velocity, channel)
- note_off: Stop a note (parameters: note, channel)
- program_change: Change the instrument sound (parameters: program, channel)
- control_change: Change a controller value (parameters: control, value, channel)

Song Creation and Management:
- create_song: Create a new empty song with a name and tempo
- create_scale: Create a new song with a musical scale (major, minor, pentatonic, blues, chromatic)
- add_note: Add a note to the current song
- add_chord: Add a chord to the current song
- add_program_change: Add a program change to the current song
- play_song: Play a song by name
- stop_song: Stop the currently playing song
- list_songs: List all available songs
</tools>

Here are some common MIDI notes:
- C4 (middle C): 60
- D4: 62
- E4: 64
- F4: 65
- G4: 67
- A4: 69
- B4: 71
- C5: 72

Common General MIDI instruments (program numbers):
- Piano: 0
- Acoustic Guitar: 24
- Electric Guitar: 30
- Violin: 40
- Flute: 73
- Trumpet: 56
- Synth Lead: 80

You can play individual notes or create and play more complex songs with multiple notes, chords, and instrument changes.

You can also load and play tracker files, which are text-based music files that organize notes into a grid pattern. Tracker files provide a visual representation of music composition, separating different instrument tracks into columns and time positions into rows.

Tracker tools:
- load_tracker_content: Load a tracker file from a text string
- play_song: Play the created song
"""

class MidiManager:
    def __init__(self):
        self.ports = {}
        self.active_port = None
        self.current_port_id = None
        self.song_manager = SongManager()
        self.discover_ports()
        
        # Set up the song manager with the MIDI sending callback
        self.song_manager.set_midi_callback(self._handle_midi_message)
        
    def discover_ports(self) -> Dict[int, Dict]:
        """Discover available MIDI output ports"""
        try:
            midi_out = rtmidi.MidiOut()
            available_ports = midi_out.get_ports()
            
            self.ports = {}
            for i, port in enumerate(available_ports):
                self.ports[i] = {
                    "id": i,
                    "name": port,
                    "type": "output",
                }
            
            logger.info(f"Discovered {len(self.ports)} MIDI ports")
            return self.ports
        except Exception as e:
            logger.error(f"Error discovering MIDI ports: {e}")
            return {}
    
    def connect_port(self, port_id: int) -> bool:
        """Connect to a MIDI output port"""
        try:
            if port_id in self.ports:
                if self.active_port is not None:
                    self.active_port.close()
                
                self.active_port = mido.open_output(self.ports[port_id]["name"])
                self.current_port_id = port_id
                logger.info(f"Connected to MIDI port {port_id}: {self.ports[port_id]['name']}")
                return True
            else:
                logger.error(f"MIDI port {port_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error connecting to MIDI port {port_id}: {e}")
            return False
    
    def send_note_on(self, note: int, velocity: int = 64, channel: int = 0) -> bool:
        """Send a note_on message"""
        try:
            if self.active_port is None:
                if len(self.ports) > 0:
                    self.connect_port(next(iter(self.ports)))
                else:
                    logger.error("No MIDI ports available")
                    return False
            
            msg = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
            self.active_port.send(msg)
            logger.info(f"Sent note_on: note={note}, velocity={velocity}, channel={channel}")
            return True
        except Exception as e:
            logger.error(f"Error sending note_on: {e}")
            return False
    
    def send_note_off(self, note: int, channel: int = 0) -> bool:
        """Send a note_off message"""
        try:
            if self.active_port is None:
                logger.error("No active MIDI port")
                return False
            
            msg = mido.Message('note_off', note=note, velocity=0, channel=channel)
            self.active_port.send(msg)
            logger.info(f"Sent note_off: note={note}, channel={channel}")
            return True
        except Exception as e:
            logger.error(f"Error sending note_off: {e}")
            return False
    
    def send_program_change(self, program: int, channel: int = 0) -> bool:
        """Send a program_change message"""
        try:
            if self.active_port is None:
                if len(self.ports) > 0:
                    self.connect_port(next(iter(self.ports)))
                else:
                    logger.error("No MIDI ports available")
                    return False
            
            msg = mido.Message('program_change', program=program, channel=channel)
            self.active_port.send(msg)
            logger.info(f"Sent program_change: program={program}, channel={channel}")
            return True
        except Exception as e:
            logger.error(f"Error sending program_change: {e}")
            return False
    
    def send_control_change(self, control: int, value: int, channel: int = 0) -> bool:
        """Send a control_change message"""
        try:
            if self.active_port is None:
                if len(self.ports) > 0:
                    self.connect_port(next(iter(self.ports)))
                else:
                    logger.error("No MIDI ports available")
                    return False
            
            msg = mido.Message('control_change', control=control, value=value, channel=channel)
            self.active_port.send(msg)
            logger.info(f"Sent control_change: control={control}, value={value}, channel={channel}")
            return True
        except Exception as e:
            logger.error(f"Error sending control_change: {e}")
            return False
    
    def _handle_midi_message(self, message_type: str, params: Dict[str, Any]) -> bool:
        """Callback for sending MIDI messages from the song system"""
        try:
            if message_type == "note_on":
                return self.send_note_on(
                    params.get("note", 60),
                    params.get("velocity", 64),
                    params.get("channel", 0)
                )
            elif message_type == "note_off":
                return self.send_note_off(
                    params.get("note", 60),
                    params.get("channel", 0)
                )
            elif message_type == "program_change":
                return self.send_program_change(
                    params.get("program", 0),
                    params.get("channel", 0)
                )
            elif message_type == "control_change":
                return self.send_control_change(
                    params.get("control", 0),
                    params.get("value", 0),
                    params.get("channel", 0)
                )
            else:
                logger.warning(f"Unknown MIDI message type: {message_type}")
                return False
        except Exception as e:
            logger.error(f"Error handling MIDI message: {e}")
            return False
    
    def close(self):
        """Close all connections"""
        # Stop any playing songs
        self.song_manager.stop_current_song()
        
        if self.active_port is not None:
            self.active_port.close()
            self.active_port = None
            self.current_port_id = None
            logger.info("Closed MIDI connections")

async def main():
    """Main entry point for the MCP MIDI server"""
    logger.info("Starting MCP MIDI server")
    
    midi_manager = MidiManager()
    server = Server("midi-manager")
    
    # Register handlers
    logger.debug("Registering handlers")
    
    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        """List available resources"""
        logger.debug("Handling list_resources request")
        return []  # No resources for MIDI server
    
    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        """List available prompts"""
        logger.debug("Handling list_prompts request")
        return [
            types.Prompt(
                name="midi-intro",
                description="Introduction to controlling MIDI devices",
                arguments=[],
            )
        ]
    
    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        """Get a prompt by name"""
        logger.debug(f"Handling get_prompt request for {name}")
        if name != "midi-intro":
            logger.error(f"Unknown prompt: {name}")
            raise ValueError(f"Unknown prompt: {name}")
        
        prompt = PROMPT_TEMPLATE.strip()
        
        return types.GetPromptResult(
            description="Introduction to controlling MIDI devices",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt),
                )
            ],
        )
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        logger.debug("Handling list_tools request")
        return [
            types.Tool(
                name="discover_ports",
                description="List all available MIDI output ports",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="connect_port",
                description="Connect to a specific MIDI output port",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "port_id": {"type": "integer", "description": "ID of the MIDI port to connect to"},
                    },
                    "required": ["port_id"],
                },
            ),
            types.Tool(
                name="note_on",
                description="Play a note on the MIDI device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note": {"type": "integer", "description": "MIDI note number (0-127)"},
                        "velocity": {"type": "integer", "description": "Velocity (0-127)"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["note"],
                },
            ),
            types.Tool(
                name="note_off",
                description="Stop a note on the MIDI device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note": {"type": "integer", "description": "MIDI note number (0-127)"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["note"],
                },
            ),
            types.Tool(
                name="program_change",
                description="Change the instrument sound on the MIDI device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "program": {"type": "integer", "description": "Program/instrument number (0-127)"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["program"],
                },
            ),
            types.Tool(
                name="control_change",
                description="Change a controller value on the MIDI device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "control": {"type": "integer", "description": "Controller number (0-127)"},
                        "value": {"type": "integer", "description": "Control value (0-127)"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["control", "value"],
                },
            ),
            # Song-related tools
            types.Tool(
                name="create_song",
                description="Create a new empty song",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the song"},
                        "tempo": {"type": "integer", "description": "Tempo in BPM (beats per minute)"},
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="create_scale",
                description="Create a new song with a musical scale",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the song"},
                        "root_note": {"type": "integer", "description": "Root note of the scale (0-127)"},
                        "scale_type": {"type": "string", "description": "Type of scale (major, minor, pentatonic, blues, chromatic)"},
                        "octaves": {"type": "integer", "description": "Number of octaves"},
                        "duration": {"type": "number", "description": "Duration of each note in seconds"},
                    },
                    "required": ["name", "root_note", "scale_type"],
                },
            ),
            types.Tool(
                name="add_note",
                description="Add a note to the current song",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pitch": {"type": "integer", "description": "MIDI note number (0-127)"},
                        "time": {"type": "number", "description": "Time in seconds when the note should start"},
                        "duration": {"type": "number", "description": "Duration of the note in seconds"},
                        "velocity": {"type": "integer", "description": "Velocity (0-127)"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["pitch", "time", "duration"],
                },
            ),
            types.Tool(
                name="add_chord",
                description="Add a chord to the current song",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "notes": {"type": "array", "items": {"type": "integer"}, "description": "List of MIDI note numbers"},
                        "time": {"type": "number", "description": "Time in seconds when the chord should start"},
                        "duration": {"type": "number", "description": "Duration of the chord in seconds"},
                        "velocity": {"type": "integer", "description": "Velocity (0-127)"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["notes", "time", "duration"],
                },
            ),
            types.Tool(
                name="add_program_change",
                description="Add a program change to the current song",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "program": {"type": "integer", "description": "Program/instrument number (0-127)"},
                        "time": {"type": "number", "description": "Time in seconds when the program change should occur"},
                        "channel": {"type": "integer", "description": "MIDI channel (0-15)"},
                    },
                    "required": ["program", "time"],
                },
            ),
            types.Tool(
                name="play_song",
                description="Play a song by name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the song to play"},
                    },
                    "required": ["name"],
                },
            ),
            types.Tool(
                name="stop_song",
                description="Stop the currently playing song",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="list_songs",
                description="List all available songs",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            # Tracker tools
            types.Tool(
                name="load_tracker_content",
                description="Load a tracker file from a text string",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Tracker file content as text"},
                        "name": {"type": "string", "description": "Name for the tracker song"},
                    },
                    "required": ["content", "name"],
                },
            ),
        ]
    
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        logger.debug(f"Handling call_tool request for {name} with args {arguments}")
        try:
            # Standard MIDI tools
            if name == "discover_ports":
                ports = midi_manager.discover_ports()
                return [types.TextContent(type="text", text=str(ports))]
            
            elif name == "connect_port":
                if not arguments or "port_id" not in arguments:
                    raise ValueError("Missing port_id argument")
                
                success = midi_manager.connect_port(arguments["port_id"])
                if success:
                    return [types.TextContent(type="text", text=f"Connected to MIDI port {arguments['port_id']}: {midi_manager.ports[arguments['port_id']]['name']}")]
                else:
                    return [types.TextContent(type="text", text=f"Failed to connect to MIDI port {arguments['port_id']}")]
            
            elif name == "note_on":
                if not arguments or "note" not in arguments:
                    raise ValueError("Missing note argument")
                
                velocity = arguments.get("velocity", 64)
                channel = arguments.get("channel", 0)
                
                success = midi_manager.send_note_on(arguments["note"], velocity, channel)
                if success:
                    return [types.TextContent(type="text", text=f"Played note {arguments['note']} with velocity {velocity} on channel {channel}")]
                else:
                    return [types.TextContent(type="text", text=f"Failed to play note {arguments['note']}")]
            
            elif name == "note_off":
                if not arguments or "note" not in arguments:
                    raise ValueError("Missing note argument")
                
                channel = arguments.get("channel", 0)
                
                success = midi_manager.send_note_off(arguments["note"], channel)
                if success:
                    return [types.TextContent(type="text", text=f"Stopped note {arguments['note']} on channel {channel}")]
                else:
                    return [types.TextContent(type="text", text=f"Failed to stop note {arguments['note']}")]
            
            elif name == "program_change":
                if not arguments or "program" not in arguments:
                    raise ValueError("Missing program argument")
                
                channel = arguments.get("channel", 0)
                
                success = midi_manager.send_program_change(arguments["program"], channel)
                if success:
                    return [types.TextContent(type="text", text=f"Changed to program/instrument {arguments['program']} on channel {channel}")]
                else:
                    return [types.TextContent(type="text", text=f"Failed to change to program/instrument {arguments['program']}")]
            
            elif name == "control_change":
                if not arguments or "control" not in arguments or "value" not in arguments:
                    raise ValueError("Missing control or value argument")
                
                channel = arguments.get("channel", 0)
                
                success = midi_manager.send_control_change(arguments["control"], arguments["value"], channel)
                if success:
                    return [types.TextContent(type="text", text=f"Changed controller {arguments['control']} to value {arguments['value']} on channel {channel}")]
                else:
                    return [types.TextContent(type="text", text=f"Failed to change controller {arguments['control']}")]
            
            # Song-related tools
            elif name == "create_song":
                if not arguments or "name" not in arguments:
                    raise ValueError("Missing name argument")
                
                tempo = arguments.get("tempo", 120)
                song = Song(name=arguments["name"], tempo=tempo)
                midi_manager.song_manager.add_song(song)
                midi_manager.song_manager.set_current_song(arguments["name"])
                
                return [types.TextContent(type="text", text=f"Created new song '{arguments['name']}' with tempo {tempo} BPM")]
            
            elif name == "create_scale":
                if not arguments or "name" not in arguments or "root_note" not in arguments or "scale_type" not in arguments:
                    raise ValueError("Missing required arguments")
                
                octaves = arguments.get("octaves", 1)
                duration = arguments.get("duration", 0.5)
                
                song = midi_manager.song_manager.create_scale_song(
                    name=arguments["name"],
                    root_note=arguments["root_note"],
                    scale_type=arguments["scale_type"],
                    octaves=octaves,
                    duration=duration
                )
                
                midi_manager.song_manager.set_current_song(arguments["name"])
                
                return [types.TextContent(type="text", text=f"Created scale song '{arguments['name']}' with root note {arguments['root_note']} ({arguments['scale_type']} scale), {octaves} octaves, and note duration {duration}s")]
            
            elif name == "add_note":
                if not arguments or "pitch" not in arguments or "time" not in arguments or "duration" not in arguments:
                    raise ValueError("Missing required arguments")
                
                if not midi_manager.song_manager.current_song:
                    return [types.TextContent(type="text", text="No current song selected. Please create a song first.")]
                
                velocity = arguments.get("velocity", 64)
                channel = arguments.get("channel", 0)
                
                midi_manager.song_manager.current_song.add_note(
                    pitch=arguments["pitch"],
                    time=arguments["time"],
                    duration=arguments["duration"],
                    velocity=velocity,
                    channel=channel
                )
                
                return [types.TextContent(type="text", text=f"Added note {arguments['pitch']} at time {arguments['time']}s with duration {arguments['duration']}s to song '{midi_manager.song_manager.current_song.name}'")]
            
            elif name == "add_chord":
                if not arguments or "notes" not in arguments or "time" not in arguments or "duration" not in arguments:
                    raise ValueError("Missing required arguments")
                
                if not midi_manager.song_manager.current_song:
                    return [types.TextContent(type="text", text="No current song selected. Please create a song first.")]
                
                velocity = arguments.get("velocity", 64)
                channel = arguments.get("channel", 0)
                
                midi_manager.song_manager.current_song.add_chord(
                    notes=arguments["notes"],
                    time=arguments["time"],
                    duration=arguments["duration"],
                    velocity=velocity,
                    channel=channel
                )
                
                return [types.TextContent(type="text", text=f"Added chord {arguments['notes']} at time {arguments['time']}s with duration {arguments['duration']}s to song '{midi_manager.song_manager.current_song.name}'")]
            
            elif name == "add_program_change":
                if not arguments or "program" not in arguments or "time" not in arguments:
                    raise ValueError("Missing required arguments")
                
                if not midi_manager.song_manager.current_song:
                    return [types.TextContent(type="text", text="No current song selected. Please create a song first.")]
                
                channel = arguments.get("channel", 0)
                
                midi_manager.song_manager.current_song.add_program_change(
                    program=arguments["program"],
                    time=arguments["time"],
                    channel=channel
                )
                
                return [types.TextContent(type="text", text=f"Added program change to {arguments['program']} at time {arguments['time']}s to song '{midi_manager.song_manager.current_song.name}'")]
            
            elif name == "play_song":
                if not arguments or "name" not in arguments:
                    raise ValueError("Missing name argument")
                
                success = midi_manager.song_manager.play_song(arguments["name"])
                if success:
                    return [types.TextContent(type="text", text=f"Playing song '{arguments['name']}'")]
                else:
                    return [types.TextContent(type="text", text=f"Failed to play song '{arguments['name']}'. Make sure it exists.")]
            
            elif name == "stop_song":
                success = midi_manager.song_manager.stop_current_song()
                if success:
                    return [types.TextContent(type="text", text="Stopped the current song")]
                else:
                    return [types.TextContent(type="text", text="No song is currently playing")]
            
            elif name == "list_songs":
                songs = midi_manager.song_manager.get_all_songs()
                if not songs:
                    return [types.TextContent(type="text", text="No songs available. Use create_song to create a new song.")]
                
                song_list = []
                for name, song in songs.items():
                    song_list.append(f"- {name} (duration: {song.duration:.2f}s, tempo: {song.tempo} BPM)")
                
                return [types.TextContent(type="text", text="Available songs:\n" + "\n".join(song_list))]
            
            # Tracker tools
            elif name == "load_tracker_content":
                if not arguments or "content" not in arguments or "name" not in arguments:
                    raise ValueError("Missing content or name argument")
                
                content = arguments["content"]
                song_name = arguments["name"]
                
                result = create_midi_song(midi_manager.song_manager, song_name, content)
                
                if result["status"] == "success":
                    return [types.TextContent(type="text", text=f"{result['message']}\nSong: {result['song_data']['name']}\nTempo: {result['song_data']['tempo']} BPM\nNotes: {result['song_data']['notes']}\n\nUse play_song name=\"{song_name}\" to play it")]
                else:
                    return [types.TextContent(type="text", text=f"Error: {result['message']}")]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        except Exception as e:
            logger.error(f"Error in tool {name}: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server running with stdio transport")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="midi",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        midi_manager.close()
        logger.info("MIDI MCP server shut down")
