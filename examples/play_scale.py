#!/usr/bin/env python3
# Run with: uv run python examples/play_scale.py
"""
Example script to play a C major scale using the MCP MIDI server
"""
import json
import requests
import time

# Server configuration
SERVER_URL = "http://127.0.0.1:8080"
MCP_ENDPOINT = f"{SERVER_URL}/mcp"

# C major scale notes (MIDI numbers)
C_MAJOR_SCALE = [60, 62, 64, 65, 67, 69, 71, 72]


def send_mcp_request(method: str, params: dict):
    """Send an MCP request to the server"""
    payload = {
        "jsonrpc": "2.0",
        "id": "example-1",
        "method": method,
        "params": params
    }
    
    response = requests.post(MCP_ENDPOINT, json=payload)
    return response.json()


def play_note(note, duration=0.5, velocity=80, channel=0):
    """Play a note for a specific duration"""
    # Send note_on
    send_mcp_request("midi.note_on", {
        "note": note,
        "velocity": velocity,
        "channel": channel
    })
    
    # Wait for the specified duration
    time.sleep(duration)
    
    # Send note_off
    send_mcp_request("midi.note_off", {
        "note": note,
        "channel": channel
    })


def main():
    """Main function"""
    # List available MIDI ports
    response = send_mcp_request("midi.discover", {})
    print("Available MIDI ports:")
    for port in response.get("result", {}).get("ports", []):
        print(f"- [{port['id']}] {port['name']}")
    
    # Connect to the first port (default)
    port_id = 0
    print(f"\nConnecting to port {port_id}...")
    send_mcp_request("midi.connect", {"port_id": port_id})
    
    # Set instrument to Acoustic Grand Piano (program 0)
    print("Setting instrument to Acoustic Grand Piano...")
    send_mcp_request("midi.program_change", {"program": 0, "channel": 0})
    
    # Play the C major scale ascending
    print("\nPlaying C major scale ascending...")
    for note in C_MAJOR_SCALE:
        print(f"Playing note {note}")
        play_note(note)
    
    # Play the C major scale descending
    print("\nPlaying C major scale descending...")
    for note in reversed(C_MAJOR_SCALE):
        print(f"Playing note {note}")
        play_note(note)
    
    # Play a C major chord
    print("\nPlaying C major chord...")
    send_mcp_request("midi.note_on", {"note": 60, "velocity": 80, "channel": 0})
    send_mcp_request("midi.note_on", {"note": 64, "velocity": 80, "channel": 0})
    send_mcp_request("midi.note_on", {"note": 67, "velocity": 80, "channel": 0})
    
    time.sleep(1.0)
    
    send_mcp_request("midi.note_off", {"note": 60, "channel": 0})
    send_mcp_request("midi.note_off", {"note": 64, "channel": 0})
    send_mcp_request("midi.note_off", {"note": 67, "channel": 0})
    
    print("\nDone!")


if __name__ == "__main__":
    main()
