"""
A minimal tracker parser that converts tracker notation directly to MIDI events.
"""

import re
from typing import Dict, List, Optional, Any, Tuple, Union


def parse_note(note_str: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Parse a note string in tracker format (e.g., 'C-4 01 40')
    Returns (midi_note, instrument, volume) or None for empty cells
    """
    if not note_str or note_str.strip() == '.....' or note_str.strip() == '---':
        return None, None, None
    
    parts = note_str.strip().split()
    
    # Parse the note (e.g., C-4)
    midi_note = None
    if len(parts) > 0 and parts[0] not in ('...', '---'):
        note_pattern = r'([A-G][#b]?)[\-_]?(\d+)'
        match = re.match(note_pattern, parts[0])
        if match:
            note_name, octave = match.groups()
            # Convert note name to MIDI number
            note_values = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 
                          'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 
                          'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
            
            if note_name in note_values:
                midi_note = (int(octave) + 1) * 12 + note_values[note_name]
    
    # Parse instrument
    instrument = None
    if len(parts) > 1 and parts[1] not in ('..', '--'):
        try:
            instrument = int(parts[1])
        except ValueError:
            pass
    
    # Parse volume
    volume = None
    if len(parts) > 2 and parts[2] not in ('..', '--'):
        try:
            volume = int(parts[2])
        except ValueError:
            pass
    
    return midi_note, instrument, volume


def parse_tracker_content(content: str) -> Dict[str, Any]:
    """
    Parse tracker content into a structured format.
    Returns a dictionary with song metadata and note events.
    """
    lines = content.strip().split('\n')
    
    # Extract header information
    title = "Untitled"
    tempo = 120
    speed = 4
    instruments = {}
    
    line_index = 0
    
    # Parse header
    while line_index < len(lines) and not lines[line_index].startswith('|'):
        line = lines[line_index].strip()
        if line.startswith('TITLE:'):
            title = line[6:].strip()
        elif line.startswith('TEMPO:'):
            try:
                tempo = int(line[6:].strip())
            except ValueError:
                pass
        elif line.startswith('SPEED:'):
            try:
                speed = int(line[6:].strip())
            except ValueError:
                pass
        elif line.startswith('INSTRUMENT') and ':' in line:
            parts = line.split(':', 1)
            instr_def = parts[0].strip()
            instr_name = parts[1].strip()
            try:
                instr_num = int(instr_def.replace('INSTRUMENT', '').strip())
                instruments[instr_num] = instr_name
            except ValueError:
                pass
        line_index += 1
    
    # Skip any blank lines before pattern
    while line_index < len(lines) and not lines[line_index].startswith('|'):
        line_index += 1
    
    if line_index >= len(lines):
        return {
            "title": title,
            "tempo": tempo,
            "speed": speed,
            "instruments": instruments,
            "notes": []
        }
    
    # Parse the channel headers to determine number of channels
    header_line = lines[line_index]
    channel_headers = [h.strip() for h in header_line.split('|')[1:-1]]
    num_channels = len(channel_headers)
    
    # Skip separator line if present
    line_index += 1
    if line_index < len(lines) and lines[line_index].startswith('|---'):
        line_index += 1
    
    # Parse pattern data into notes
    notes = []  # List of (row, channel, midi_note, instrument, volume)
    
    current_row = 0
    while line_index < len(lines) and lines[line_index].startswith('|'):
        line = lines[line_index]
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        
        # Skip row indicator lines
        if len(cells) > 0 and 'Row' in line:
            # Extract row number if it exists
            row_match = re.search(r'Row\s+(\d+)', line)
            if row_match:
                current_row = int(row_match.group(1))
            line_index += 1
            continue
        
        # Process each cell in the row
        for channel_index, cell in enumerate(cells):
            if channel_index < num_channels and cell and cell.strip() != '.....':
                midi_note, instrument, volume = parse_note(cell)
                if midi_note is not None:
                    notes.append({
                        "row": current_row,
                        "channel": channel_index,
                        "note": midi_note,
                        "instrument": instrument,
                        "volume": volume if volume is not None else 64
                    })
        
        current_row += 1
        line_index += 1
    
    return {
        "title": title,
        "tempo": tempo,
        "speed": speed,
        "instruments": instruments,
        "notes": notes
    }


def tracker_to_midi_commands(tracker_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert tracker data to a sequence of MIDI commands.
    """
    tempo = tracker_data["tempo"]
    speed = tracker_data["speed"]
    instruments = tracker_data["instruments"]
    notes = tracker_data["notes"]
    
    # Calculate timing constants
    seconds_per_beat = 60 / tempo
    rows_per_beat = speed
    seconds_per_row = seconds_per_beat / rows_per_beat
    
    # Sort notes by row and channel
    notes = sorted(notes, key=lambda n: (n["row"], n["channel"]))
    
    midi_commands = []
    
    # Add program changes for all instruments
    for channel, instrument in instruments.items():
        # Convert instrument name to program number if needed
        program = channel
        if isinstance(instrument, str):
            # If it's a string, try to extract a number from it
            match = re.search(r'(\d+)', instrument)
            if match:
                program = int(match.group(1))
        else:
            program = instrument
        
        midi_commands.append({
            "command": "program_change",
            "program": program,
            "time": 0.0,
            "channel": channel
        })
    
    # Add note events
    for note in notes:
        row = note["row"]
        time = row * seconds_per_row
        
        # Calculate note duration (default to one row)
        duration = seconds_per_row
        
        # Convert tracker volume (0-64) to MIDI velocity (0-127)
        velocity = min(127, note["volume"] * 2) if note["volume"] is not None else 64
        
        midi_commands.append({
            "command": "note",
            "pitch": note["note"],
            "time": time,
            "duration": duration,
            "velocity": velocity,
            "channel": note["channel"]
        })
    
    return midi_commands


def create_midi_song(song_manager, name: str, tracker_content: str) -> Dict[str, Any]:
    """
    Parse tracker content and create a MIDI song.
    
    Args:
        song_manager: The MIDI song manager instance
        name: Name for the created MIDI song
        tracker_content: String containing tracker notation
        
    Returns:
        Dict with status and message
    """
    try:
        # Parse the tracker content
        tracker_data = parse_tracker_content(tracker_content)
        
        # Create a new song
        song = song_manager.create_song(name=name, tempo=tracker_data["tempo"])
        
        # Convert tracker data to MIDI commands
        midi_commands = tracker_to_midi_commands(tracker_data)
        
        # Add all commands to the song
        for cmd in midi_commands:
            if cmd["command"] == "program_change":
                song.add_program_change(
                    program=cmd["program"],
                    time=cmd["time"],
                    channel=cmd["channel"]
                )
            elif cmd["command"] == "note":
                song.add_note(
                    pitch=cmd["pitch"],
                    time=cmd["time"],
                    duration=cmd["duration"],
                    velocity=cmd["velocity"],
                    channel=cmd["channel"]
                )
        
        return {
            "status": "success",
            "message": f"Created MIDI song '{name}' from tracker content",
            "song_data": {
                "name": name,
                "title": tracker_data["title"],
                "tempo": tracker_data["tempo"],
                "channels": len(set(cmd["channel"] for cmd in midi_commands if "channel" in cmd)),
                "notes": len([cmd for cmd in midi_commands if cmd["command"] == "note"])
            }
        }
        
        return {
            "status": "success",
            "message": f"Created MIDI song '{name}' from tracker content",
            "song_data": {
                "name": name,
                "title": tracker_data["title"],
                "tempo": tracker_data["tempo"],
                "channels": len(set(cmd["channel"] for cmd in midi_commands if "channel" in cmd)),
                "notes": len([cmd for cmd in midi_commands if cmd["command"] == "note"])
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating MIDI song from tracker content: {str(e)}"
        }
