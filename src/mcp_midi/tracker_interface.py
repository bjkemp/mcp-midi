"""
Tracker interface for MCP-MIDI.
This module provides functions to load and play tracker files.
"""

import os
import sys
from typing import Dict, Any, Optional, List, Union

# Add the tracker module to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tracker'))

# Import the tracker module
from tracker import parse_tracker_file, tracker_to_midi, create_demo_tracker, play_tracker_file

# Import core MIDI functionality
from mcp_midi.song import song_manager


def load_tracker_file(path: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a tracker file from path
    
    Args:
        path (str): Path to the tracker file
        name (str, optional): Name to identify the tracker file
    
    Returns:
        Dict: Information about the loaded tracker file
    """
    if not os.path.exists(path):
        return {"status": "error", "message": f"File {path} does not exist"}
    
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        song = parse_tracker_file(content)
        
        if name is None:
            name = os.path.basename(path).replace('.', '_')
        
        tracker_to_midi(song, name)
        
        return {
            "status": "success",
            "message": f"Loaded tracker file '{path}' as '{name}'",
            "song_name": name,
            "title": song.title,
            "tempo": song.initial_tempo,
            "patterns": len(song.patterns),
            "channels": song.patterns[0].channels if song.patterns else 0,
            "rows": song.patterns[0].rows if song.patterns else 0,
        }
    except Exception as e:
        return {"status": "error", "message": f"Error loading tracker file: {str(e)}"}


def load_tracker_content(content: str, name: str) -> Dict[str, Any]:
    """
    Load a tracker file from content string
    
    Args:
        content (str): Tracker file content
        name (str): Name to identify the tracker file
    
    Returns:
        Dict: Information about the loaded tracker file
    """
    try:
        song = parse_tracker_file(content)
        tracker_to_midi(song, name)
        
        return {
            "status": "success",
            "message": f"Loaded tracker content as '{name}'",
            "song_name": name,
            "title": song.title,
            "tempo": song.initial_tempo,
            "patterns": len(song.patterns),
            "channels": song.patterns[0].channels if song.patterns else 0,
            "rows": song.patterns[0].rows if song.patterns else 0,
        }
    except Exception as e:
        return {"status": "error", "message": f"Error loading tracker content: {str(e)}"}


def create_tracker_demo(path: str) -> Dict[str, Any]:
    """
    Create a demo tracker file for Happy Birthday
    
    Args:
        path (str): Path where to save the demo file
    
    Returns:
        Dict: Information about the created file
    """
    try:
        message = create_demo_tracker(path)
        return {"status": "success", "message": message}
    except Exception as e:
        return {"status": "error", "message": f"Error creating demo tracker file: {str(e)}"}


def play_tracker(name: str) -> Dict[str, Any]:
    """
    Play a previously loaded tracker file
    
    Args:
        name (str): Name of the tracker song to play
    
    Returns:
        Dict: Confirmation of playback start
    """
    try:
        # The tracker has already been converted to a MIDI song with the given name
        result = song_manager.play_song(name)
        return {"status": "success", "message": f"Playing tracker song '{name}'"}
    except Exception as e:
        return {"status": "error", "message": f"Error playing tracker: {str(e)}"}


def stop_tracker() -> Dict[str, Any]:
    """
    Stop the currently playing tracker song
    
    Returns:
        Dict: Confirmation of playback stop
    """
    try:
        result = song_manager.stop_song()
        return {"status": "success", "message": "Stopped tracker playback"}
    except Exception as e:
        return {"status": "error", "message": f"Error stopping tracker: {str(e)}"}
