"""
Song module for MCP-MIDI
Provides functionality for sequencing and playing back MIDI notes
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable

import mido

logger = logging.getLogger("mcp_midi.song")

class NoteType(Enum):
    """Types of MIDI events in a song"""
    NOTE = "note"  # Note with duration (combines note_on and note_off)
    CHORD = "chord"  # Multiple notes played simultaneously
    REST = "rest"  # Silent period
    PROGRAM_CHANGE = "program_change"  # Change instrument
    CONTROL_CHANGE = "control_change"  # Change controller value


@dataclass
class MidiEvent:
    """Base class for MIDI events in a song"""
    event_type: NoteType
    time: float = 0.0  # Time in seconds (when to play this event)
    duration: float = 0.0  # Duration in seconds (for NOTE and CHORD types)
    channel: int = 0


@dataclass
class Note(MidiEvent):
    """A single note with pitch, velocity, and duration"""
    pitch: int = 60  # MIDI note number (0-127)
    velocity: int = 64  # Velocity (0-127)
    
    def __post_init__(self):
        self.event_type = NoteType.NOTE


@dataclass
class Chord(MidiEvent):
    """Multiple notes played simultaneously"""
    notes: List[int] = None  # List of MIDI note numbers
    velocity: int = 64  # Velocity for all notes in the chord
    
    def __post_init__(self):
        self.event_type = NoteType.CHORD
        if self.notes is None:
            self.notes = []


@dataclass
class Rest(MidiEvent):
    """A period of silence"""
    def __post_init__(self):
        self.event_type = NoteType.REST
        self.duration = max(0.0, self.duration)


@dataclass
class ProgramChange(MidiEvent):
    """Change the instrument sound"""
    program: int = 0  # Program/instrument number (0-127)
    
    def __post_init__(self):
        self.event_type = NoteType.PROGRAM_CHANGE


@dataclass
class ControlChange(MidiEvent):
    """Change a controller value"""
    control: int = 0  # Controller number (0-127)
    value: int = 0  # Control value (0-127)
    
    def __post_init__(self):
        self.event_type = NoteType.CONTROL_CHANGE


class Song:
    """Represents a MIDI song sequence"""
    def __init__(self, name: str = "Untitled", tempo: int = 120):
        self.name = name
        self.tempo = tempo  # BPM (beats per minute)
        self.events: List[MidiEvent] = []
        self.sorted_events: List[MidiEvent] = []  # Events sorted by time
        self.is_sorted = False
        self.duration = 0.0  # Total duration in seconds
        self._task = None  # asyncio task for playback
        self._stop_event = asyncio.Event()  # To signal playback to stop
        self._is_playing = False
        self.send_midi_callback: Optional[Callable] = None
    
    def add_event(self, event: MidiEvent) -> None:
        """Add an event to the song"""
        self.events.append(event)
        self.is_sorted = False
        # Update duration if this event extends beyond current duration
        potential_duration = event.time + event.duration
        if potential_duration > self.duration:
            self.duration = potential_duration
    
    def add_note(
        self, pitch: int, time: float, duration: float, 
        velocity: int = 64, channel: int = 0
    ) -> None:
        """Add a note to the song"""
        note = Note(
            event_type=NoteType.NOTE,
            pitch=pitch,
            time=time,
            duration=duration,
            velocity=velocity,
            channel=channel
        )
        self.add_event(note)
    
    def add_chord(
        self, notes: List[int], time: float, duration: float, 
        velocity: int = 64, channel: int = 0
    ) -> None:
        """Add a chord to the song"""
        chord = Chord(
            event_type=NoteType.CHORD,
            notes=notes,
            time=time,
            duration=duration,
            velocity=velocity,
            channel=channel
        )
        self.add_event(chord)
    
    def add_rest(self, time: float, duration: float) -> None:
        """Add a rest to the song"""
        rest = Rest(
            event_type=NoteType.REST,
            time=time,
            duration=duration
        )
        self.add_event(rest)
    
    def add_program_change(
        self, program: int, time: float, channel: int = 0
    ) -> None:
        """Add a program change to the song"""
        program_change = ProgramChange(
            event_type=NoteType.PROGRAM_CHANGE,
            program=program,
            time=time,
            channel=channel
        )
        self.add_event(program_change)
    
    def add_control_change(
        self, control: int, value: int, time: float, channel: int = 0
    ) -> None:
        """Add a control change to the song"""
        control_change = ControlChange(
            event_type=NoteType.CONTROL_CHANGE,
            control=control,
            value=value,
            time=time,
            channel=channel
        )
        self.add_event(control_change)
    
    def sort_events(self) -> None:
        """Sort events by time"""
        self.sorted_events = sorted(self.events, key=lambda e: e.time)
        self.is_sorted = True
    
    def clear(self) -> None:
        """Clear all events from the song"""
        self.events = []
        self.sorted_events = []
        self.is_sorted = True
        self.duration = 0.0
    
    def to_json(self) -> str:
        """Convert the song to JSON format"""
        song_dict = {
            "name": self.name,
            "tempo": self.tempo,
            "duration": self.duration,
            "events": []
        }
        
        for event in self.events:
            event_dict = {
                "type": event.event_type.value,
                "time": event.time,
                "duration": event.duration,
                "channel": event.channel,
            }
            
            if event.event_type == NoteType.NOTE:
                event_dict["pitch"] = event.pitch
                event_dict["velocity"] = event.velocity
            
            elif event.event_type == NoteType.CHORD:
                event_dict["notes"] = event.notes
                event_dict["velocity"] = event.velocity
            
            elif event.event_type == NoteType.PROGRAM_CHANGE:
                event_dict["program"] = event.program
            
            elif event.event_type == NoteType.CONTROL_CHANGE:
                event_dict["control"] = event.control
                event_dict["value"] = event.value
            
            song_dict["events"].append(event_dict)
        
        return json.dumps(song_dict)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Song':
        """Create a song from JSON format"""
        data = json.loads(json_str)
        song = cls(name=data.get("name", "Untitled"), tempo=data.get("tempo", 120))
        
        for event_data in data.get("events", []):
            event_type = event_data.get("type")
            time = event_data.get("time", 0.0)
            duration = event_data.get("duration", 0.0)
            channel = event_data.get("channel", 0)
            
            if event_type == NoteType.NOTE.value:
                song.add_note(
                    pitch=event_data.get("pitch", 60),
                    time=time,
                    duration=duration,
                    velocity=event_data.get("velocity", 64),
                    channel=channel
                )
            
            elif event_type == NoteType.CHORD.value:
                song.add_chord(
                    notes=event_data.get("notes", []),
                    time=time,
                    duration=duration,
                    velocity=event_data.get("velocity", 64),
                    channel=channel
                )
            
            elif event_type == NoteType.REST.value:
                song.add_rest(time=time, duration=duration)
            
            elif event_type == NoteType.PROGRAM_CHANGE.value:
                song.add_program_change(
                    program=event_data.get("program", 0),
                    time=time,
                    channel=channel
                )
            
            elif event_type == NoteType.CONTROL_CHANGE.value:
                song.add_control_change(
                    control=event_data.get("control", 0),
                    value=event_data.get("value", 0),
                    time=time,
                    channel=channel
                )
        
        return song
    
    def set_midi_callback(self, callback: Callable) -> None:
        """Set the callback function for sending MIDI messages"""
        self.send_midi_callback = callback
    
    async def play(self) -> None:
        """Play the song asynchronously"""
        if self._is_playing:
            logger.warning("Song is already playing")
            return
        
        if not self.send_midi_callback:
            logger.error("No MIDI callback set for playback")
            return
        
        if not self.is_sorted:
            self.sort_events()
        
        self._is_playing = True
        self._stop_event.clear()
        
        logger.info(f"Playing song: {self.name} (duration: {self.duration:.2f}s)")
        
        # Track active notes to ensure they're turned off if playback is stopped
        active_notes = {}  # Dict of {(pitch, channel): stop_time}
        
        start_time = time.time()
        last_event_time = 0.0
        
        for i, event in enumerate(self.sorted_events):
            # Calculate how long to wait until this event
            wait_time = event.time - last_event_time
            
            if wait_time > 0:
                # Wait until it's time to play this event
                try:
                    # Use asyncio.wait_for to allow cancellation
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=wait_time
                    )
                    # If we get here, stop was requested
                    break
                except asyncio.TimeoutError:
                    # Timeout is expected, continue with playback
                    pass
            
            last_event_time = event.time
            
            # Process the event based on its type
            if event.event_type == NoteType.NOTE:
                note: Note = event
                # Send note_on message
                self.send_midi_callback("note_on", {
                    "note": note.pitch,
                    "velocity": note.velocity,
                    "channel": note.channel
                })
                
                # Schedule note_off after duration
                # Store the note in active_notes to turn it off if playback is stopped
                active_notes[(note.pitch, note.channel)] = event.time + note.duration
                
                # Schedule task to turn off the note
                asyncio.create_task(self._schedule_note_off(
                    note.pitch, note.channel, note.duration
                ))
            
            elif event.event_type == NoteType.CHORD:
                chord: Chord = event
                # Send note_on messages for all notes in the chord
                for pitch in chord.notes:
                    self.send_midi_callback("note_on", {
                        "note": pitch,
                        "velocity": chord.velocity,
                        "channel": chord.channel
                    })
                    
                    # Store the note in active_notes
                    active_notes[(pitch, chord.channel)] = event.time + chord.duration
                    
                    # Schedule task to turn off the note
                    asyncio.create_task(self._schedule_note_off(
                        pitch, chord.channel, chord.duration
                    ))
            
            elif event.event_type == NoteType.PROGRAM_CHANGE:
                program_change: ProgramChange = event
                self.send_midi_callback("program_change", {
                    "program": program_change.program,
                    "channel": program_change.channel
                })
            
            elif event.event_type == NoteType.CONTROL_CHANGE:
                control_change: ControlChange = event
                self.send_midi_callback("control_change", {
                    "control": control_change.control,
                    "value": control_change.value,
                    "channel": control_change.channel
                })
            
            # Check if we should stop
            if self._stop_event.is_set():
                break
        
        # If we get here, either all events played or playback was stopped
        # Turn off any active notes
        current_time = time.time() - start_time
        for (pitch, channel), stop_time in active_notes.items():
            if stop_time > current_time:
                # This note is still playing, turn it off
                self.send_midi_callback("note_off", {
                    "note": pitch,
                    "channel": channel
                })
        
        self._is_playing = False
        logger.info(f"Song playback completed: {self.name}")
    
    async def _schedule_note_off(self, pitch: int, channel: int, duration: float) -> None:
        """Schedule a note_off message after the specified duration"""
        try:
            # Wait for the note duration or until stop is requested
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=duration
            )
        except asyncio.TimeoutError:
            # Timeout is expected, send note_off
            pass
        
        # If we haven't been stopped or the stop happened at exactly the note duration,
        # send the note_off message
        if not self._stop_event.is_set() or duration <= 0:
            self.send_midi_callback("note_off", {
                "note": pitch,
                "channel": channel
            })
    
    def start_playback(self) -> None:
        """Start song playback"""
        if self._is_playing:
            logger.warning("Song is already playing")
            return
        
        # Cancel any existing task
        if self._task is not None and not self._task.done():
            self._task.cancel()
        
        # Start new playback task
        self._task = asyncio.create_task(self.play())
    
    def stop_playback(self) -> None:
        """Stop song playback"""
        if not self._is_playing:
            logger.debug("Song is not playing")
            return
        
        # Signal the playback to stop
        self._stop_event.set()
        logger.info(f"Stopping song playback: {self.name}")
