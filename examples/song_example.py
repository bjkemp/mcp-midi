#!/usr/bin/env python3
"""
Example demonstrating the song functionality of MCP-MIDI
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_midi.song.song import Song
from mcp_midi.song.manager import SongManager
import mido

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('song_example')

def midi_callback(message_type, params):
    """Send MIDI messages to the output port"""
    try:
        if message_type == "note_on":
            msg = mido.Message('note_on', 
                              note=params.get("note", 60), 
                              velocity=params.get("velocity", 64), 
                              channel=params.get("channel", 0))
        elif message_type == "note_off":
            msg = mido.Message('note_off', 
                              note=params.get("note", 60), 
                              velocity=0, 
                              channel=params.get("channel", 0))
        elif message_type == "program_change":
            msg = mido.Message('program_change', 
                              program=params.get("program", 0), 
                              channel=params.get("channel", 0))
        elif message_type == "control_change":
            msg = mido.Message('control_change', 
                              control=params.get("control", 0),
                              value=params.get("value", 0),
                              channel=params.get("channel", 0))
        else:
            logger.warning(f"Unknown message type: {message_type}")
            return False
        
        midi_out.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending MIDI message: {e}")
        return False

async def create_and_play_song():
    """Create and play a simple song demonstration"""
    # Create a song manager
    manager = SongManager()
    manager.set_midi_callback(midi_callback)
    
    # Create a simple C major scale
    scale_song = manager.create_scale_song(
        name="C Major Scale",
        root_note=60,  # Middle C
        scale_type="major",
        octaves=1,
        duration=0.3  # 300ms per note
    )
    
    # Create a simple chord progression (C, F, G, C)
    chord_song = manager.create_chord_progression_song(
        name="Simple Progression",
        root_note=60,  # Middle C
        chord_progression=[
            [0, 4, 7],    # C major (C, E, G)
            [5, 9, 12],   # F major (F, A, C)
            [7, 11, 14],  # G major (G, B, D)
            [0, 4, 7]     # C major (C, E, G)
        ],
        durations=[1.0, 1.0, 1.0, 1.5]  # Longer last chord
    )
    
    # Create a custom melody
    melody = Song(name="Custom Melody", tempo=100)
    
    # Add a program change to a piano sound
    melody.add_program_change(program=0, time=0, channel=0)
    
    # Add some notes to create a melody
    notes = [60, 62, 64, 65, 67, 65, 64, 62, 60, 64, 67, 72]
    durations = [0.25, 0.25, 0.25, 0.25, 0.5, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.75]
    
    current_time = 0.0
    for note, duration in zip(notes, durations):
        melody.add_note(
            pitch=note,
            time=current_time,
            duration=duration,
            velocity=70 if current_time % 1 < 0.5 else 50,  # Alternate emphasis
            channel=0
        )
        current_time += duration
    
    # Add the melody to the song manager
    manager.add_song(melody)
    
    # List all songs
    songs = manager.get_all_songs()
    logger.info(f"Available songs: {', '.join(songs.keys())}")
    
    # Play each song
    logger.info("Playing scale song...")
    manager.play_song("C Major Scale")
    await asyncio.sleep(scale_song.duration + 1)  # Wait for the song to finish
    
    logger.info("Playing chord progression...")
    manager.play_song("Simple Progression")
    await asyncio.sleep(chord_song.duration + 1)  # Wait for the song to finish
    
    logger.info("Playing custom melody...")
    manager.play_song("Custom Melody")
    await asyncio.sleep(melody.duration + 1)  # Wait for the song to finish

async def main():
    """Main entry point"""
    logger.info("Starting song example")
    
    # Open a MIDI output port
    global midi_out
    try:
        midi_out = mido.open_output()
        logger.info(f"Connected to MIDI output: {midi_out}")
    except Exception as e:
        logger.error(f"Failed to open MIDI output: {e}")
        return
    
    try:
        await create_and_play_song()
    finally:
        # Clean up
        midi_out.close()
        logger.info("Example finished")

if __name__ == "__main__":
    asyncio.run(main())
