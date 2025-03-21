import os
import sys
import logging
from contextlib import closing
from pathlib import Path
import mido
import rtmidi
from typing import Dict, List, Optional, Any, Union
from pydantic import AnyUrl

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

You can play notes, chords, and melodies on the connected MIDI device. Feel free to ask me to play specific notes, chords, or change instruments.
"""

class MidiManager:
    def __init__(self):
        self.ports = {}
        self.active_port = None
        self.current_port_id = None
        self.discover_ports()
        
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
    
    def close(self):
        """Close all connections"""
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
        ]
    
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        logger.debug(f"Handling call_tool request for {name} with args {arguments}")
        try:
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
