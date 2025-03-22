#!/usr/bin/env python3
"""
Simple test script to send MIDI notes to Deluge
"""
import time
import rtmidi

def play_note(midi_out, note, velocity=80, duration=0.5, channel=1):
    # Channel in MIDI is 0-15, but users often think of channels as 1-16
    channel_byte = max(0, min(15, channel - 1))  # Ensure channel is in 0-15 range
    
    # Note On message: [Status byte, Note number, Velocity]
    # Status byte: 0x90 for Note On on channel 1, add channel_byte for other channels
    note_on = [0x90 | channel_byte, note, velocity]
    midi_out.send_message(note_on)
    print(f"Note On: {note} on channel {channel} with velocity {velocity}")
    
    # Wait for duration
    time.sleep(duration)
    
    # Note Off message: [Status byte, Note number, 0]
    # Status byte: 0x80 for Note Off on channel 1, add channel_byte for other channels
    note_off = [0x80 | channel_byte, note, 0]
    midi_out.send_message(note_off)
    print(f"Note Off: {note} on channel {channel}")

def set_program(midi_out, program, channel=1):
    channel_byte = max(0, min(15, channel - 1))
    
    # Program Change message: [Status byte, Program number]
    # Status byte: 0xC0 for Program Change on channel 1, add channel_byte for other channels
    program_change = [0xC0 | channel_byte, program]
    midi_out.send_message(program_change)
    print(f"Program Change: {program} on channel {channel}")

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
        # Set to a synth lead sound
        set_program(midi_out, 80, channel=1)
        
        # Wait a moment for the program change to take effect
        time.sleep(0.1)
        
        # Play a simple scale on channel 1
        print("Playing C major scale...")
        for note in [60, 62, 64, 65, 67, 69, 71, 72]:  # C4 to C5
            play_note(midi_out, note, velocity=80, duration=0.3, channel=1)
            time.sleep(0.1)  # Small gap between notes
        
        # Play a chord
        print("Playing C major chord...")
        play_note(midi_out, 60, velocity=80, duration=0.0, channel=1)  # No duration - don't wait
        play_note(midi_out, 64, velocity=80, duration=0.0, channel=1)  # No duration - don't wait
        play_note(midi_out, 67, velocity=80, duration=1.0, channel=1)  # Wait on the last note
        
    finally:
        # Close the port
        midi_out.close_port()
        print("MIDI port closed.")

if __name__ == "__main__":
    main()
