#!/usr/bin/env python3
"""
Very simple test script for MIDI output
"""
import time
import rtmidi

# Create a MIDI output object
midi_out = rtmidi.MidiOut()

# Print available ports
ports = midi_out.get_ports()
print("Available MIDI ports:", ports)

if ports:
    # Open the first available port (assuming Deluge is port 0)
    midi_out.open_port(0)
    print(f"Connected to: {ports[0]}")
    
    try:
        # Set to a synth sound (program change: channel 1, program 80)
        midi_out.send_message([0xC0, 80])
        print("Sent program change to synth lead (80) on channel 1")
        time.sleep(0.1)
        
        # Play a simple C note (channel 1, note C4, velocity 100)
        print("Playing C4 note...")
        midi_out.send_message([0x90, 60, 100])  # Note On: channel 1, C4 (60), velocity 100
        time.sleep(1.0)  # Play for 1 second
        midi_out.send_message([0x80, 60, 0])    # Note Off: channel 1, C4 (60)
        print("Note off.")
        
    finally:
        # Close the port
        midi_out.close_port()
        print("MIDI port closed.")
else:
    print("No MIDI ports available.")
