"""
MIDI File Handler
Reads and plays standard MIDI files
"""
import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union, Callable

import mido

from .song.song import Song
from .all_notes_off import all_notes_off

logger = logging.getLogger("mcp_midi.midi_file")

class MidiFilePlayer:
    """Class for handling MIDI file loading and playback"""
    
    def __init__(self):
        self.midi_files = {}  # Dictionary of loaded MIDI files
        self.current_file = None
        self.playback_task = None
        self.stop_event = asyncio.Event()
        self.send_midi_callback = None
        self.midi_port = None
    
    def set_midi_callback(self, callback: Callable) -> None:
        """Set the callback for sending MIDI messages"""
        self.send_midi_callback = callback
    
    def set_midi_port(self, port) -> None:
        """Set the MIDI output port"""
        self.midi_port = port
    
    def load_file(self, path: str, name: Optional[str] = None) -> bool:
        """Load a MIDI file from path"""
        try:
            # If name isn't provided, use the filename
            if name is None:
                name = os.path.basename(path)
                # Remove extension if present
                if name.lower().endswith('.mid') or name.lower().endswith('.midi'):
                    name = os.path.splitext(name)[0]
            
            # Load the MIDI file
            midi_file = mido.MidiFile(path)
            
            self.midi_files[name] = {
                'path': path,
                'midi': midi_file,
                'ticks_per_beat': midi_file.ticks_per_beat,
                'type': midi_file.type,
                'tracks': len(midi_file.tracks),
                'length': midi_file.length  # Length in seconds
            }
            
            logger.info(f"Loaded MIDI file '{name}' from {path}")
            logger.info(f"File details: Type {midi_file.type}, {len(midi_file.tracks)} tracks, " 
                       f"{midi_file.length:.2f} seconds")
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading MIDI file from {path}: {e}")
            return False
    
    def get_file_info(self, name: str) -> Optional[Dict]:
        """Get information about a loaded MIDI file"""
        return self.midi_files.get(name)
    
    def list_files(self) -> Dict:
        """List all loaded MIDI files"""
        return {name: info for name, info in self.midi_files.items()}
    
    def convert_to_song(self, name: str) -> Optional[Song]:
        """Convert a MIDI file to a Song object"""
        if name not in self.midi_files:
            logger.warning(f"MIDI file '{name}' not found")
            return None
        
        try:
            midi_file = self.midi_files[name]['midi']
            song = Song(name=name, tempo=120)  # Default tempo, will be updated
            
            # Track the current time position in seconds for each track
            track_time = 0.0
            
            # Process each message in the file
            for track_idx, track in enumerate(midi_file.tracks):
                absolute_time = 0.0  # Current time in seconds for this track
                
                for msg in track:
                    # Update the time
                    if msg.time > 0:
                        # Convert MIDI ticks to seconds
                        delta_time = mido.tick2second(
                            msg.time, 
                            midi_file.ticks_per_beat, 
                            tempo=500000  # Default tempo = 120 BPM (500000 microseconds per beat)
                        )
                        absolute_time += delta_time
                    
                    # Process different message types
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Add note_on at the current time
                        song.add_note(
                            pitch=msg.note,
                            time=absolute_time,
                            duration=0.1,  # Temporary duration, will be updated when note_off is found
                            velocity=msg.velocity,
                            channel=msg.channel
                        )
                    
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        # Find the corresponding note_on event and update its duration
                        # This is a simplified approach and would need more complexity for a real implementation
                        for event in song.events:
                            if (hasattr(event, 'pitch') and event.pitch == msg.note and 
                                event.channel == msg.channel and 
                                event.time + event.duration > absolute_time - 0.001):
                                # Update the duration
                                event.duration = absolute_time - event.time
                                break
                    
                    elif msg.type == 'program_change':
                        # Add program change at the current time
                        song.add_program_change(
                            program=msg.program,
                            time=absolute_time,
                            channel=msg.channel
                        )
                    
                    elif msg.type == 'control_change':
                        # Add control change at the current time
                        song.add_control_change(
                            control=msg.control,
                            value=msg.value,
                            time=absolute_time,
                            channel=msg.channel
                        )
                    
                    elif msg.type == 'set_tempo':
                        # TODO: Handle tempo changes
                        # This would involve more complex time calculations
                        pass
            
            # Update the song's total duration
            song.duration = max([event.time + event.duration for event in song.events if hasattr(event, 'duration')])
            
            # Sort the events by time
            song.sort_events()
            
            return song
        
        except Exception as e:
            logger.error(f"Error converting MIDI file '{name}' to Song: {e}")
            return None
    
    async def play_file(self, name: str) -> bool:
        """Play a MIDI file directly"""
        if name not in self.midi_files:
            logger.warning(f"MIDI file '{name}' not found")
            return False
        
        if not self.send_midi_callback and not self.midi_port:
            logger.error("No MIDI output method available")
            return False
        
        try:
            midi_file = self.midi_files[name]['midi']
            self.current_file = name
            self.stop_event.clear()
            
            logger.info(f"Starting playback of MIDI file '{name}'")
            
            # Play through each message
            for message in midi_file.play():
                # Check if we should stop
                if self.stop_event.is_set():
                    logger.info(f"Playback of MIDI file '{name}' stopped")
                    break
                
                # Skip meta messages
                if not hasattr(message, 'type') or message.is_meta:
                    continue
                
                # Send the message
                if self.midi_port:
                    self.midi_port.send(message)
                
                if self.send_midi_callback:
                    msg_dict = {'channel': getattr(message, 'channel', 0)}
                    
                    if message.type == 'note_on':
                        msg_dict.update({
                            'note': message.note,
                            'velocity': message.velocity
                        })
                        self.send_midi_callback('note_on', msg_dict)
                    
                    elif message.type == 'note_off':
                        msg_dict.update({
                            'note': message.note,
                            'velocity': 0
                        })
                        self.send_midi_callback('note_off', msg_dict)
                    
                    elif message.type == 'program_change':
                        msg_dict.update({
                            'program': message.program
                        })
                        self.send_midi_callback('program_change', msg_dict)
                    
                    elif message.type == 'control_change':
                        msg_dict.update({
                            'control': message.control,
                            'value': message.value
                        })
                        self.send_midi_callback('control_change', msg_dict)
            
            # Make sure all notes are off at the end
            if self.midi_port:
                all_notes_off(self.midi_port)
            
            if self.send_midi_callback:
                all_notes_off(None, self.send_midi_callback)
            
            logger.info(f"Playback of MIDI file '{name}' completed")
            self.current_file = None
            return True
        
        except Exception as e:
            logger.error(f"Error playing MIDI file '{name}': {e}")
            
            # Clean up
            if self.midi_port:
                all_notes_off(self.midi_port)
            
            if self.send_midi_callback:
                all_notes_off(None, self.send_midi_callback)
            
            self.current_file = None
            return False
    
    def start_playback(self, name: str) -> bool:
        """Start playback of a MIDI file as a background task"""
        if self.playback_task is not None and not self.playback_task.done():
            logger.warning("Already playing a MIDI file")
            return False
        
        self.playback_task = asyncio.create_task(self.play_file(name))
        return True
    
    def stop_playback(self) -> bool:
        """Stop current MIDI file playback"""
        if self.current_file is None:
            return False
        
        self.stop_event.set()
        
        # Clean up
        if self.midi_port:
            all_notes_off(self.midi_port)
        
        if self.send_midi_callback:
            all_notes_off(None, self.send_midi_callback)
        
        return True
