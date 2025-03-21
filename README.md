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

#### Song Creation and Playback Tools
- `create_song`
   - Create a new empty song
   - Input:
     - `name` (string): Name of the song
     - `tempo` (integer, optional): Tempo in BPM (beats per minute, default: 120)
   - Returns: Confirmation of song creation

- `create_scale`
   - Create a new song with a musical scale
   - Input:
     - `name` (string): Name of the song
     - `root_note` (integer): Root note of the scale (0-127)
     - `scale_type` (string): Type of scale (major, minor, pentatonic, blues, chromatic)
     - `octaves` (integer, optional): Number of octaves (default: 1)
     - `duration` (number, optional): Duration of each note in seconds (default: 0.5)
   - Returns: Confirmation of scale song creation

- `add_note`
   - Add a note to the current song
   - Input:
     - `pitch` (integer): MIDI note number (0-127)
     - `time` (number): Time in seconds when the note should start
     - `duration` (number): Duration of the note in seconds
     - `velocity` (integer, optional): Velocity (0-127, default: 64)
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of note addition

- `add_chord`
   - Add a chord to the current song
   - Input:
     - `notes` (array of integers): List of MIDI note numbers
     - `time` (number): Time in seconds when the chord should start
     - `duration` (number): Duration of the chord in seconds
     - `velocity` (integer, optional): Velocity (0-127, default: 64)
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of chord addition

- `add_program_change`
   - Add a program change to the current song
   - Input:
     - `program` (integer): Program/instrument number (0-127)
     - `time` (number): Time in seconds when the program change should occur
     - `channel` (integer, optional): MIDI channel (0-15, default: 0)
   - Returns: Confirmation of program change addition

- `play_song`
   - Play a song by name
   - Input:
     - `name` (string): Name of the song to play
   - Returns: Confirmation of song playback

- `stop_song`
   - Stop the currently playing song
   - No input required
   - Returns: Confirmation of song stopped

- `list_songs`
   - List all available songs
   - No input required
   - Returns: List of available songs with their durations and tempos

## Example Usage

### Simple Note Playing
```
# Discover MIDI ports
discover_ports

# Connect to a port (usually port 0)
connect_port port_id=0

# Change to piano instrument
program_change program=0

# Play a middle C note
note_on note=60 velocity=80

# Stop the note after a while
note_off note=60
```

### Song Creation and Playback
```
# Create a C major scale
create_scale name="C Major Scale" root_note=60 scale_type="major" octaves=1 duration=0.3

# Create a chord progression
create_song name="Chord Progression" tempo=100

# Add some chords (C, Am, F, G)
add_chord notes=[60, 64, 67] time=0.0 duration=1.0
add_chord notes=[57, 60, 64] time=1.0 duration=1.0
add_chord notes=[53, 57, 60, 65] time=2.0 duration=1.0
add_chord notes=[55, 59, 62, 67] time=3.0 duration=1.0

# Play the songs
play_song name="C Major Scale"
play_song name="Chord Progression"

# Stop the currently playing song
stop_song
```

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