"""
Integration script for tracker functionality.
This adds the tracker functionality to the MCP-MIDI interface.
"""

import os
import sys
import mcp.midi.core as midi
from tracker import parse_tracker_file, tracker_to_midi, create_demo_tracker

# Add functions to the global scope to expose them to the MCP interface

def load_tracker_file(path, name=None):
    """
    Load a tracker file from path
    
    Args:
        path (str): Path to the tracker file
        name (str, optional): Name to identify the tracker file
    
    Returns:
        Information about the loaded tracker file
    """
    if not os.path.exists(path):
        return f"Error: File {path} does not exist"
    
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        song = parse_tracker_file(content)
        
        if name is None:
            name = os.path.basename(path).replace('.', '_')
        
        tracker_to_midi(song, name)
        
        return f"Loaded tracker file '{path}' as '{name}'"
    except Exception as e:
        return f"Error loading tracker file: {str(e)}"


def create_tracker_demo(path):
    """
    Create a demo tracker file for Happy Birthday
    
    Args:
        path (str): Path where to save the demo file
    
    Returns:
        Information about the created file
    """
    try:
        return create_demo_tracker(path)
    except Exception as e:
        return f"Error creating demo tracker file: {str(e)}"


def play_tracker(name):
    """
    Play a previously loaded tracker file
    
    Args:
        name (str): Name of the tracker song to play
    
    Returns:
        Confirmation of playback start
    """
    try:
        # The tracker has already been converted to a MIDI song with the given name
        return midi.play_song(name=name)
    except Exception as e:
        return f"Error playing tracker: {str(e)}"


# Add the tracker functions to the MCP-MIDI module
setattr(midi, 'load_tracker_file', load_tracker_file)
setattr(midi, 'create_tracker_demo', create_tracker_demo)
setattr(midi, 'play_tracker', play_tracker)

# Print confirmation for debugging
print("Tracker integration loaded successfully")
