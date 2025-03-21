# Claude Desktop Integration Guide

This guide explains how to integrate the MCP MIDI server with Claude Desktop to enable direct MIDI control using natural language.

## Prerequisites

- Claude Desktop installed and configured
- MCP MIDI server installed (follow the steps in `INSTALL.md`)
- A connected MIDI device (synthesizer, keyboard, etc.)

## Configuration Steps

### 1. Locate Your Claude Desktop Configuration File

Depending on your operating system, the configuration file will be in:

- **Windows**: `%APPDATA%\claude-desktop\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/claude-desktop/claude_desktop_config.json`
- **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`

If the file doesn't exist, create it with the following structure:

```json
{
  "mcpServers": {}
}
```

### 2. Add the MIDI Server Configuration

Edit the configuration file to add the MIDI server to the `mcpServers` section:

```json
{
  "mcpServers": {
    "midi": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "src.main",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
        "--mcp-mode"
      ],
      "cwd": "/path/to/mcp-midi"
    }
  }
}
```

Replace `/path/to/mcp-midi` with the actual path to your MCP MIDI installation.

If you already have other MCP servers configured, add the MIDI server alongside them:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/benjamin/Desktop",
        "/Users/benjamin/Projects",
        "/Users/benjamin/Downloads"
      ]
    },
    "midi": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "src.main",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
        "--mcp-mode"
      ],
      "cwd": "/path/to/mcp-midi"
    }
  }
}
```

### 3. Restart Claude Desktop

After updating the configuration file, restart Claude Desktop for the changes to take effect.

### 4. Verify the Integration

When Claude Desktop starts, it should automatically launch the MCP MIDI server. You can verify this by:

1. Looking for the server process in your task manager or activity monitor
2. Checking the Claude Desktop logs for any errors
3. Asking Claude to interact with your MIDI device

## Using Claude with MIDI

Once configured, you can ask Claude to interact with your MIDI devices using natural language. Here are some examples:

### Playing Notes

> Claude, can you play middle C on my MIDI synthesizer?

Claude will send the appropriate MIDI command to play middle C.

### Playing Chords

> Claude, play a C major chord.

Claude will send commands to play the C, E, and G notes simultaneously.

### Changing Instruments

> Claude, switch to a piano sound.

Claude will send a Program Change message to select a piano sound.

### Playing Melodies

> Claude, play a simple melody using a violin sound.

Claude will change the instrument to violin and play a melody.

## Troubleshooting

### Claude Can't Find MIDI Devices

If Claude reports it can't find any MIDI devices:

1. Make sure your MIDI device is properly connected and powered on
2. Restart the MCP MIDI server
3. Restart Claude Desktop

### MIDI Commands Not Working

If Claude sends MIDI commands but nothing happens:

1. Check that your MIDI device is properly configured to receive on the correct channel
2. Verify that your synthesizer's volume is up
3. Try a different MIDI port if available

### Server Crashes

If the MCP MIDI server crashes:

1. Check the server logs for error messages
2. Make sure you have the required dependencies installed
3. Update to the latest version of the MCP MIDI server

## Advanced Configuration

### Custom Port

To use a different port for the MCP MIDI server, update the `args` in the configuration:

```json
"args": [
  "run",
  "python",
  "-m",
  "src.main",
  "--host",
  "127.0.0.1",
  "--port",
  "8090",  // Changed from 8080 to 8090
  "--mcp-mode"
]
```

### Debug Mode

To enable debug mode for troubleshooting:

```json
"args": [
  "run",
  "python",
  "-m",
  "src.main",
  "--host",
  "127.0.0.1",
  "--port",
  "8080",
  "--mcp-mode",
  "--debug"  // Added debug flag
]
```

## Resources

- See `examples/claude_interaction.md` for more examples of MIDI commands
- Check the project README for API documentation
- Visit the MCP specification website for more information about MCP: https://mcp.ai/
