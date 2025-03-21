#!/bin/bash
# Setup script for MCP MIDI

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -sSf https://astral.sh/uv/install.sh | sh
fi

# Install the package in development mode
echo "Installing dependencies with uv..."
uv pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
uv pip install pytest

echo "Setup complete! You can now run the server with:"
echo "mcp-midi"
