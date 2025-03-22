#!/usr/bin/env python3
"""
Emergency script to turn off all MIDI notes
"""
import rtmidi

# Create a MIDI output object
midi_out = rtmidi.MidiOut()

# Print available ports
ports = midi_out.get_ports()
print("Available MIDI ports:", ports)

if ports:
    # Open the first available port
    midi_out.open_port(0)
    print(f"Connected to: {ports[0]}")
    
    # Send "All Notes Off" message on all 16 MIDI channels
    for channel in range(16):
        midi_out.send_message([0xB0 | channel, 123, 0])
        print(f"Sent All Notes Off to channel {channel+1}")
    
    # Also send All Sound Off for good measure
    for channel in range(16):
        midi_out.send_message([0xB0 | channel, 120, 0])
        print(f"Sent All Sound Off to channel {channel+1}")
    
    # Close the port
    midi_out.close_port()
    print("MIDI port closed.")
else:
    print("No MIDI ports available.")
