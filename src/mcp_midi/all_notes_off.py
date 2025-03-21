"""
MIDI All Notes Off Utility
Provides functionality to ensure no notes are left hanging
"""
import logging
from typing import Optional, Callable, List, Dict

import mido

logger = logging.getLogger("mcp_midi.all_notes_off")

# Track active notes per channel
active_notes: Dict[int, List[int]] = {}
for channel in range(16):
    active_notes[channel] = []

def register_note_on(note: int, channel: int = 0):
    """Register a note as active to track it"""
    if note not in active_notes[channel]:
        active_notes[channel].append(note)
        logger.debug(f"Registered note {note} on channel {channel}")

def register_note_off(note: int, channel: int = 0):
    """Unregister a note when it's turned off"""
    if note in active_notes[channel]:
        active_notes[channel].remove(note)
        logger.debug(f"Unregistered note {note} on channel {channel}")

def all_notes_off(midi_port: Optional[mido.ports.BaseOutput] = None, 
                 send_midi_callback: Optional[Callable] = None,
                 channels: List[int] = None):
    """Send note_off messages for all active notes
    
    Args:
        midi_port: The MIDI port to send messages to (direct)
        send_midi_callback: Function to send MIDI messages (API-based)
        channels: List of channels to clear (default: all channels)
    """
    if channels is None:
        channels = list(range(16))  # Default to all 16 MIDI channels
    
    logger.info(f"Sending all notes off for channels: {channels}")
    
    for channel in channels:
        # Method 1: Send note_off for each active note we're tracking
        notes_to_turn_off = active_notes[channel].copy()
        for note in notes_to_turn_off:
            if midi_port:
                msg = mido.Message('note_off', note=note, velocity=0, channel=channel)
                midi_port.send(msg)
            
            if send_midi_callback:
                send_midi_callback("note_off", {
                    "note": note,
                    "velocity": 0,
                    "channel": channel
                })
            
            active_notes[channel].remove(note)
        
        # Method 2: Send All Notes Off controller message (CC 123)
        if midi_port:
            msg = mido.Message('control_change', control=123, value=0, channel=channel)
            midi_port.send(msg)
        
        if send_midi_callback:
            send_midi_callback("control_change", {
                "control": 123,  # All Notes Off
                "value": 0,
                "channel": channel
            })
        
        logger.info(f"All notes off sent for channel {channel}")
    
    # Clear our tracking
    for channel in channels:
        active_notes[channel] = []
