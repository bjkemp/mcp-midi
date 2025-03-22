"""
A simple module to parse and play tracker files with MCP-MIDI.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Union, Any
import re


@dataclass
class TrackerNote:
    """Represents a single note in a tracker pattern."""
    note: Optional[str] = None  # Note in format C-4, D#5, etc. or '...' for empty
    instrument: Optional[int] = None  # Instrument number or None
    volume: Optional[int] = None  # Volume (0-64) or None
    effect: Optional[str] = None  # Effect command (like Fxx for tempo)
    effect_value: Optional[int] = None  # Effect value


@dataclass
class TrackerPattern:
    """Represents a tracker pattern with multiple channels and rows."""
    rows: int  # Number of rows in pattern
    channels: int  # Number of channels
    notes: List[List[TrackerNote]]  # [row][channel]


@dataclass
class TrackerSong:
    """Represents a complete tracker song."""
    title: str
    initial_tempo: int = 125  # Default BPM
    initial_speed: int = 6  # Default speed (ticks per row)
    patterns: List[TrackerPattern] = None
    pattern_order: List[int] = None
    instruments: Dict[int, str] = None

    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []
        if self.pattern_order is None:
            self.pattern_order = []
        if self.instruments is None:
            self.instruments = {}


def parse_note(note_str: str) -> Tuple[Optional[str], Optional[int]]:
    """Parse a note string like 'C-4' or 'F#5' to note name and octave."""
    if not note_str or note_str.strip() == '...' or note_str.strip() == '---':
        return None, None
    
    note_pattern = r'([A-G][#b]?)[\-_]?(\d)'
    match = re.match(note_pattern, note_str)
    if match:
        note_name, octave = match.groups()
        return note_name, int(octave)
    return None, None


def note_to_midi(note: str, octave: int) -> int:
    """Convert a note name and octave to MIDI note number."""
    if note is None or octave is None:
        return None
    
    # Base values for notes in an octave
    note_values = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 
                  'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 
                  'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    
    # Calculate MIDI note number: (octave+1)*12 + note_value
    # MIDI uses octave -1 to 9, where middle C (C4) is note number 60
    if note in note_values:
        return (octave + 1) * 12 + note_values[note]
    return None


def parse_tracker_file(file_content: str) -> TrackerSong:
    """Parse a simple tracker file format."""
    lines = file_content.strip().split('\n')
    
    # Extract header information
    title = "Untitled"
    tempo = 125
    speed = 6
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
        return TrackerSong(title=title, initial_tempo=tempo, initial_speed=speed, instruments=instruments)
    
    # Parse the channel headers to determine number of channels
    header_line = lines[line_index]
    channel_headers = [h.strip() for h in header_line.split('|')[1:-1]]
    num_channels = len(channel_headers)
    
    # Skip separator line if present
    line_index += 1
    if line_index < len(lines) and lines[line_index].startswith('|---'):
        line_index += 1
    
    # Parse pattern data
    pattern_data = []
    row_index = 0
    
    while line_index < len(lines) and lines[line_index].startswith('|'):
        line = lines[line_index]
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        
        # If this is a row indicator line
        if len(cells) > 0 and all(c.strip() == '' for c in cells):
            line_index += 1
            continue
        
        # Create a new row of notes if needed
        while row_index >= len(pattern_data):
            pattern_data.append([TrackerNote() for _ in range(num_channels)])
        
        # Process each cell in the row
        for channel_index, cell in enumerate(cells):
            if channel_index < num_channels:
                parts = cell.split()
                
                # Default empty note
                note = TrackerNote()
                
                # Parse the parts based on typical tracker format
                if len(parts) >= 1 and parts[0] not in ('...', '---'):
                    note_name, octave = parse_note(parts[0])
                    note.note = parts[0] if (note_name and octave) else None
                
                if len(parts) >= 2 and parts[1] not in ('..', '--'):
                    try:
                        note.instrument = int(parts[1])
                    except ValueError:
                        note.instrument = None
                
                if len(parts) >= 3 and parts[2] not in ('..', '--'):
                    try:
                        note.volume = int(parts[2])
                    except ValueError:
                        note.volume = None
                
                if len(parts) >= 4 and parts[3] not in ('...', '---'):
                    effect_match = re.match(r'([A-Z])([0-9A-F]{2})', parts[3])
                    if effect_match:
                        note.effect = effect_match.group(1)
                        note.effect_value = int(effect_match.group(2), 16)
                
                pattern_data[row_index][channel_index] = note
        
        row_index += 1
        line_index += 1
    
    # Create the pattern
    pattern = TrackerPattern(rows=len(pattern_data), channels=num_channels, notes=pattern_data)
    
    # Create and return the song
    song = TrackerSong(
        title=title,
        initial_tempo=tempo,
        initial_speed=speed,
        patterns=[pattern],
        pattern_order=[0],
        instruments=instruments
    )
    
    return song


def tracker_to_midi(song: TrackerSong, midi_song_name: str) -> None:
    """Convert a tracker song to MIDI commands for MCP-MIDI."""
    import mcp.midi.core as midi
    
    # Create a new MIDI song
    midi.create_song(name=midi_song_name, tempo=song.initial_tempo)
    
    # Calculate timing constants
    seconds_per_beat = 60 / song.initial_tempo
    beats_per_row = 1 / song.initial_speed  # This is an approximation
    seconds_per_row = seconds_per_beat * beats_per_row
    
    # Set up instruments
    for channel, instrument in song.instruments.items():
        # Convert instrument name to program number if needed
        program = channel if isinstance(instrument, int) else int(instrument)
        midi.add_program_change(program=program, time=0, channel=channel)
    
    # Process each pattern in order
    for pattern_index in song.pattern_order:
        pattern = song.patterns[pattern_index]
        
        # Process each row
        for row_index in range(pattern.rows):
            row_time = row_index * seconds_per_row
            
            # Process each channel in the row
            for channel_index, note_data in enumerate(pattern.notes[row_index]):
                if not note_data or not note_data.note:
                    continue
                
                # Convert note to MIDI note number
                note_name, octave = parse_note(note_data.note)
                midi_note = note_to_midi(note_name, octave)
                
                if midi_note is not None:
                    # Set default duration if not specified
                    duration = seconds_per_row
                    
                    # Get volume (convert from 0-64 to 0-127)
                    velocity = 64
                    if note_data.volume is not None:
                        velocity = min(127, note_data.volume * 2)
                    
                    # Add the note to the MIDI song
                    midi.add_note(
                        pitch=midi_note,
                        time=row_time,
                        duration=duration,
                        velocity=velocity,
                        channel=channel_index
                    )
                
                # Process effects
                if note_data.effect and note_data.effect_value is not None:
                    # Handle tempo change
                    if note_data.effect == 'F':
                        # Set new tempo - this is simplified
                        new_tempo = note_data.effect_value
                        # In a real implementation, we would need to adjust timing
    
    # End of conversion
    return midi_song_name


def play_tracker_file(file_path: str) -> str:
    """Load and play a tracker file."""
    import mcp.midi.core as midi
    import os
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the tracker file
    song = parse_tracker_file(content)
    
    # Convert to MIDI
    midi_song_name = os.path.basename(file_path).replace('.', '_')
    tracker_to_midi(song, midi_song_name)
    
    # Play the song
    midi.play_song(name=midi_song_name)
    
    return f"Playing tracker song '{song.title}' as MIDI"


# Helper function to create a simple tracker file
def create_demo_tracker(output_path: str) -> None:
    """Create a simple demo tracker file for Happy Birthday."""
    content = """TITLE: Happy Birthday
TEMPO: 125
SPEED: 4
INSTRUMENT 0: Acoustic Grand Piano
INSTRUMENT 1: String Ensemble
INSTRUMENT 2: Acoustic Bass

|Ch1   |Ch2   |Ch3   |
|------|------|------|
|C-4 00|..... |..... | Row 00
|..... |..... |..... | Row 01
|C-4 00|..... |..... | Row 02
|..... |..... |..... | Row 03
|D-4 00|..... |..... | Row 04
|..... |..... |..... | Row 05
|..... |..... |..... | Row 06
|..... |..... |..... | Row 07
|C-4 00|..... |..... | Row 08
|..... |..... |..... | Row 09
|..... |..... |..... | Row 10
|..... |..... |..... | Row 11
|F-4 00|..... |C-3 02| Row 12
|..... |..... |..... | Row 13
|..... |..... |..... | Row 14
|..... |..... |..... | Row 15
|E-4 00|C-4 01|G-2 02| Row 16
|..... |..... |..... | Row 17
|..... |..... |..... | Row 18
|..... |..... |..... | Row 19
|..... |..... |..... | Row 20
|..... |..... |..... | Row 21
|..... |..... |..... | Row 22
|..... |..... |..... | Row 23
|C-4 00|..... |C-3 02| Row 24
|..... |..... |..... | Row 25
|C-4 00|..... |..... | Row 26
|..... |..... |..... | Row 27
|D-4 00|..... |..... | Row 28
|..... |..... |..... | Row 29
|..... |..... |..... | Row 30
|..... |..... |..... | Row 31
|C-4 00|..... |..... | Row 32
|..... |..... |..... | Row 33
|..... |..... |..... | Row 34
|..... |..... |..... | Row 35
|G-4 00|E-4 01|E-3 02| Row 36
|..... |..... |..... | Row 37
|..... |..... |..... | Row 38
|..... |..... |..... | Row 39
|F-4 00|..... |C-3 02| Row 40
|..... |..... |..... | Row 41
|..... |..... |..... | Row 42
|..... |..... |..... | Row 43
|..... |..... |..... | Row 44
|..... |..... |..... | Row 45
|..... |..... |..... | Row 46
|..... |..... |..... | Row 47
"""
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    return f"Created demo tracker file at {output_path}"


if __name__ == "__main__":
    # If run directly, create a demo tracker file
    import sys
    if len(sys.argv) > 1:
        create_demo_tracker(sys.argv[1])
    else:
        print("Usage: python tracker.py output_filename.txt")
