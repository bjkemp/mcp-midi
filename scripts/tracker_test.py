#!/usr/bin/env python3
"""
Test script for playing a tracker format song
"""
import time
import rtmidi
from mcp_midi.tracker_parser import parse_tracker_content, tracker_to_midi_commands

# Create tracker content for a simple melody
tracker_content = """
TITLE: Simple Melody
TEMPO: 120
SPEED: 4
INSTRUMENT0: Synth Lead
INSTRUMENT1: Bass

|   CH1   |   CH2   |
|--------|--------|
| Row 0  |        |
| C-4 00 64 | ... |
| ... | ... |
| ... | ... |
| ... | ... |
| Row 4  |        |
| E-4 00 64 | G-2 01 64 |
| ... | ... |
| ... | ... |
| ... | ... |
| Row 8  |        |
| G-4 00 64 | ... |
| ... | ... |
| ... | G-2 01 64 |
| ... | ... |
| Row 12 |        |
| F-4 00 64 | ... |
| ... | ... |
| E-4 00 64 | ... |
| ... | ... |
| Row 16 |        |
| C-4 00 64 | C-3 01 64 |
"""

def play_tracker_content(tracker_content, midi_port):
    """
    Parse and play tracker content using a MIDI port
    """
    # Parse the tracker content
    print("Parsing tracker content...")
    tracker_data = parse_tracker_content(tracker_content)
    
    # Convert to MIDI commands
    print("Converting to MIDI commands...")
    midi_commands = tracker_to_midi_commands(tracker_data)
    
    # Set up a timer for playback
    start_time = time.time()
    end_time = start_time + max([cmd["time"] + cmd.get("duration", 0) for cmd in midi_commands])
    
    # Sort commands by time
    midi_commands.sort(key=lambda cmd: cmd["time"])
    
    # Play the commands
    print(f"Playing song: {tracker_data['title']} (tempo: {tracker_data['tempo']})")
    next_cmd_index = 0
    
    try:
        while time.time() < end_time and next_cmd_index < len(midi_commands):
            current_time = time.time() - start_time
            
            # Process all commands that should play now
            while (next_cmd_index < len(midi_commands) and 
                   midi_commands[next_cmd_index]["time"] <= current_time):
                cmd = midi_commands[next_cmd_index]
                
                if cmd["command"] == "program_change":
                    # Program change: channel, program
                    midi_message = [0xC0 | cmd["channel"], cmd["program"]]
                    midi_port.send_message(midi_message)
                    print(f"Program change: {cmd['program']} on channel {cmd['channel']+1}")
                
                elif cmd["command"] == "note":
                    # Note on: channel, note, velocity
                    midi_message = [0x90 | cmd["channel"], cmd["pitch"], cmd["velocity"]]
                    midi_port.send_message(midi_message)
                    print(f"Note on: {cmd['pitch']} on channel {cmd['channel']+1}")
                    
                    # Schedule note off
                    note_off_time = cmd["time"] + cmd["duration"]
                    # Store the note off information for later
                    cmd["note_off_time"] = note_off_time
                
                next_cmd_index += 1
            
            # Check for any notes that need to be turned off
            for i in range(next_cmd_index):
                cmd = midi_commands[i]
                if cmd["command"] == "note" and "note_off_time" in cmd:
                    if cmd["note_off_time"] <= current_time:
                        # Note off: channel, note, velocity 0
                        midi_message = [0x80 | cmd["channel"], cmd["pitch"], 0]
                        midi_port.send_message(midi_message)
                        print(f"Note off: {cmd['pitch']} on channel {cmd['channel']+1}")
                        # Remove the note_off_time to avoid sending it again
                        del cmd["note_off_time"]
            
            # Small sleep to prevent CPU usage
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\nPlayback interrupted.")
    
    # Make sure all notes are off
    for channel in range(16):
        # All notes off on this channel
        midi_port.send_message([0xB0 | channel, 123, 0])
    
    print("Playback complete!")

# Main function
def main():
    # Create a MIDI output object
    midi_out = rtmidi.MidiOut()
    
    # Print available ports
    ports = midi_out.get_ports()
    print("Available MIDI ports:", ports)
    
    if not ports:
        print("No MIDI ports available.")
        return
    
    # Open the first available port
    midi_out.open_port(0)
    print(f"Connected to: {ports[0]}")
    
    try:
        # Play the tracker content
        play_tracker_content(tracker_content, midi_out)
    
    finally:
        # Close the port
        midi_out.close_port()
        print("MIDI port closed.")

if __name__ == "__main__":
    main()
