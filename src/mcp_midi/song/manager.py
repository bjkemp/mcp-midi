"""
Song Manager for MCP-MIDI
Handles loading, saving, and playback of multiple songs
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable

from .song import Song

logger = logging.getLogger("mcp_midi.song.manager")

class SongManager:
    """Manages multiple songs for MCP-MIDI"""
    def __init__(self):
        self.songs: Dict[str, Song] = {}
        self.current_song: Optional[Song] = None
        self.send_midi_callback: Optional[Callable] = None
    
    def set_midi_callback(self, callback: Callable) -> None:
        """Set the callback function for sending MIDI messages"""
        self.send_midi_callback = callback
        # Update all songs with this callback
        for song in self.songs.values():
            song.set_midi_callback(callback)
    
    def add_song(self, song: Song) -> None:
        """Add a song to the manager"""
        if song.name in self.songs:
            # Append a suffix to make the name unique
            i = 1
            while f"{song.name}_{i}" in self.songs:
                i += 1
            song.name = f"{song.name}_{i}"
        
        self.songs[song.name] = song
        
        # Set the MIDI callback if it exists
        if self.send_midi_callback:
            song.set_midi_callback(self.send_midi_callback)
    
    def remove_song(self, name: str) -> bool:
        """Remove a song from the manager"""
        if name in self.songs:
            # Stop the song if it's playing
            if self.current_song and self.current_song.name == name:
                self.stop_current_song()
                self.current_song = None
            
            del self.songs[name]
            return True
        return False
    
    def get_song(self, name: str) -> Optional[Song]:
        """Get a song by name"""
        return self.songs.get(name)
    
    def get_all_songs(self) -> Dict[str, Song]:
        """Get all songs"""
        return self.songs
    
    def set_current_song(self, name: str) -> bool:
        """Set the current song by name"""
        if name in self.songs:
            # Stop current song if it's playing
            if self.current_song and self.current_song._is_playing:
                self.stop_current_song()
            
            self.current_song = self.songs[name]
            return True
        return False
    
    def play_song(self, name: str) -> bool:
        """Play a song by name"""
        if not self.send_midi_callback:
            logger.error("No MIDI callback set for playback")
            return False
        
        if name in self.songs:
            # Stop current song if it's different and playing
            if self.current_song and self.current_song.name != name and self.current_song._is_playing:
                self.stop_current_song()
            
            self.current_song = self.songs[name]
            self.current_song.start_playback()
            return True
        
        return False
    
    def play_current_song(self) -> bool:
        """Play the current song"""
        if not self.current_song:
            logger.warning("No current song selected")
            return False
        
        if not self.send_midi_callback:
            logger.error("No MIDI callback set for playback")
            return False
        
        self.current_song.start_playback()
        return True
    
    def stop_current_song(self) -> bool:
        """Stop the current song"""
        if not self.current_song:
            return False
        
        self.current_song.stop_playback()
        return True
    
    def save_song(self, name: str, path: str) -> bool:
        """Save a song to a file"""
        if name not in self.songs:
            logger.warning(f"Song not found: {name}")
            return False
        
        song = self.songs[name]
        json_data = song.to_json()
        
        try:
            with open(path, 'w') as f:
                f.write(json_data)
            logger.info(f"Saved song '{name}' to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving song '{name}' to {path}: {e}")
            return False
    
    def load_song(self, path: str) -> Optional[Song]:
        """Load a song from a file"""
        try:
            with open(path, 'r') as f:
                json_data = f.read()
            
            song = Song.from_json(json_data)
            self.add_song(song)
            logger.info(f"Loaded song '{song.name}' from {path}")
            return song
        except Exception as e:
            logger.error(f"Error loading song from {path}: {e}")
            return None
    
    def save_all_songs(self, directory: str) -> Dict[str, bool]:
        """Save all songs to a directory"""
        results = {}
        os.makedirs(directory, exist_ok=True)
        
        for name, song in self.songs.items():
            path = os.path.join(directory, f"{name}.json")
            results[name] = self.save_song(name, path)
        
        return results
    
    def load_all_songs(self, directory: str) -> Dict[str, bool]:
        """Load all songs from a directory"""
        results = {}
        
        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.error(f"Directory not found: {directory}")
            return results
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                path = os.path.join(directory, filename)
                song = self.load_song(path)
                results[filename] = song is not None
        
        return results
    
    def create_simple_song(
        self, name: str, notes: List[int], 
        durations: List[float], tempo: int = 120
    ) -> Song:
        """Create a simple song with sequential notes"""
        song = Song(name=name, tempo=tempo)
        
        current_time = 0.0
        for i, (note, duration) in enumerate(zip(notes, durations)):
            song.add_note(
                pitch=note,
                time=current_time,
                duration=duration,
                velocity=64,
                channel=0
            )
            current_time += duration
        
        song.duration = current_time
        self.add_song(song)
        return song
    
    def create_scale_song(
        self, name: str, root_note: int, scale_type: str, 
        octaves: int = 1, duration: float = 0.5
    ) -> Song:
        """Create a song with a musical scale"""
        # Define scale intervals (semitones)
        scale_intervals = {
            "major": [0, 2, 4, 5, 7, 9, 11, 12],  # Major scale intervals
            "minor": [0, 2, 3, 5, 7, 8, 10, 12],  # Natural minor scale intervals
            "pentatonic": [0, 2, 4, 7, 9, 12],    # Pentatonic scale intervals
            "blues": [0, 3, 5, 6, 7, 10, 12],     # Blues scale intervals
            "chromatic": list(range(13))          # Chromatic scale intervals
        }
        
        if scale_type not in scale_intervals:
            logger.warning(f"Unknown scale type: {scale_type}")
            scale_type = "major"  # Default to major scale
        
        intervals = scale_intervals[scale_type]
        song = Song(name=name, tempo=120)
        
        # Create ascending and descending scale
        current_time = 0.0
        
        # Ascending scale
        for octave in range(octaves):
            for interval in intervals[:-1] if octave < octaves - 1 else intervals:
                note = root_note + octave * 12 + interval
                song.add_note(
                    pitch=note,
                    time=current_time,
                    duration=duration,
                    velocity=64,
                    channel=0
                )
                current_time += duration
        
        # Descending scale (excluding the last note which is the same as the first note of the descent)
        for octave in range(octaves-1, -1, -1):
            for interval in reversed(intervals):
                if octave == octaves-1 and interval == intervals[-1]:
                    continue  # Skip the highest note (already played)
                
                note = root_note + octave * 12 + interval
                song.add_note(
                    pitch=note,
                    time=current_time,
                    duration=duration,
                    velocity=64,
                    channel=0
                )
                current_time += duration
        
        song.duration = current_time
        self.add_song(song)
        return song
    
    def create_chord_progression_song(
        self, name: str, root_note: int, chord_progression: List[List[int]], 
        durations: List[float]
    ) -> Song:
        """Create a song with a chord progression"""
        song = Song(name=name, tempo=120)
        
        current_time = 0.0
        for chord_intervals, duration in zip(chord_progression, durations):
            # Create a chord from the intervals
            chord_notes = [root_note + interval for interval in chord_intervals]
            
            song.add_chord(
                notes=chord_notes,
                time=current_time,
                duration=duration,
                velocity=64,
                channel=0
            )
            current_time += duration
        
        song.duration = current_time
        self.add_song(song)
        return song
