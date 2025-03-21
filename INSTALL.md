# Installation Guide

This guide walks you through setting up the MCP MIDI Bridge for Claude Desktop.

## Prerequisites

- Python 3.10 or higher
- Node.js and npm (for Claude Desktop)
- A USB MIDI device (synthesizer, keyboard, etc.)
- Claude Desktop application

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mcp-midi.git
cd mcp-midi
```

### 2. Install Dependencies using uv

Run the setup script which will install uv and all dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
- Check for and install `uv` if necessary
- Install all required dependencies
- Set up the package for development

### 3. Manual Installation

If you prefer to install manually:

```bash
# Install uv if not already installed
curl -sSf https://astral.sh/uv/install.sh | sh

# Install the package
uv pip install -e .
```

### 4. Test the Server

Run the MCP MIDI server:

```bash
mcp-midi
```

### 5. Configure Claude Desktop

To add the MCP MIDI server to Claude Desktop:

1. Locate your Claude Desktop configuration file:
   - Windows: `%APPDATA%\claude-desktop\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/claude-desktop/claude_desktop_config.json`
   - Linux: `~/.config/claude-desktop/claude_desktop_config.json`

2. Add the MIDI server configuration to the `mcpServers` section:

```json
"midi": {
  "command": "mcp-midi",
  "args": [],
  "cwd": "/path/to/mcp-midi"
}
```

Make sure to replace `/path/to/mcp-midi` with the actual path to your installation.

3. Save the configuration file and restart Claude Desktop.

### 6. Test Claude Integration

Once Claude Desktop is running with the updated configuration, you can test the integration by asking Claude to use the MIDI tools. For example:

> Claude, can you check what MIDI ports are available?

Claude should respond by using the `discover_ports` tool.

## Troubleshooting

### No MIDI Devices Found

If the server doesn't detect your MIDI device:

1. Make sure your device is properly connected and powered on
2. Check if your operating system recognizes the device
3. Restart the server

### Claude Can't Connect to the Server

If Claude reports it can't connect to the MCP MIDI server:

1. Make sure the server is running (`mcp-midi`)
2. Verify the path in the `cwd` parameter is correct
3. Check Claude Desktop logs for any error messages

### Permission Issues

If you encounter permission issues:

1. Make sure the setup script has execute permissions (`chmod +x setup.sh`)
2. On some systems, you may need to run the server with elevated privileges to access MIDI devices

## Additional Resources

- See the `README.md` for more detailed information about the project
