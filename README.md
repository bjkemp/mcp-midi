# MIDI MCP Server

## Overview
A Model Context Protocol (MCP) server implementation that provides MIDI device interaction capabilities. This server enables sending MIDI messages to control synthesizers, play notes and chords, change instruments, and manipulate controller parameters using natural language.

## Components

### Prompts
The server provides an introduction prompt:
- `midi-intro`: A prompt that introduces MIDI capabilities and provides guidance
  - No arguments required
  - Explains available MIDI commands and note/instrument reference information
  - Guides users through interacting with MIDI devices

### Tools
The server offers six core tools:

#### Device Tools
- `discover_ports`
   - List all available MIDI output ports
   - No input required
   - Returns: Array of detected MIDI ports with IDs and names

- `connect_port`
   - Connect to a specific MIDI output port
   - Input:
     - `port_id` (integer): The ID of the MIDI port to connect to
   - Returns: Confirmation of connection

#### Note Tools
- `note_on`
   - Play a note on the MIDI device
   - Input:
     - `note` (integer): MIDI note number (0-127)
     - `velocity` (integer, optional): Velocity/loudness (0-127, default: 64)
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of note played

- `note_off`
   - Stop a note on the MIDI device
   - Input:
     - `note` (integer): MIDI note number (0-127)
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of note stopped

#### Control Tools
- `program_change`
   - Change the instrument sound on the MIDI device
   - Input:
     - `program` (integer): Program/instrument number (0-127)
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of instrument change

- `control_change`
   - Change a controller value on the MIDI device
   - Input:
     - `control` (integer): Controller number (0-127)
     - `value` (integer): Control value (0-127)
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of controller change

## Usage with Claude Desktop

### uv

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "midi": {
    "command": "uv",
    "args": [
      "--directory",
      "/Users/benjamin/Projects/mcp-midi",
      "run",
      "mcp-midi"
    ]
  }
}
```

### Docker

```json
# Add the server to your claude_desktop_config.json
"mcpServers": {
  "midi": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "-i",
      "--device",
      "/dev/snd",
      "mcp/midi"
    ]
  }
}
```

## Building

Docker:

```bash
docker build -t mcp/midi .
```

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.