# Claude's Guide to MCP-MIDI

This document provides helpful information for interacting with the MCP-MIDI system through Claude.

## Important MIDI Concepts

### MIDI Channels
- MIDI supports 16 channels (0-15, sometimes referenced as 1-16)
- Channel 9 (or 10 in 1-indexed systems) is traditionally reserved for drum kits
- Each channel can have its own instrument

### Note Numbers and Musical Notes
The MIDI standard uses note numbers 0-127. Here's a reference for common notes:

| Note Number | Musical Note |
|-------------|--------------|
| 60          | Middle C     |
| 62          | D            |
| 64          | E            |
| 65          | F            |
| 67          | G            |
| 69          | A            |
| 71          | B            |
| 72          | C (octave up)|

Add or subtract 12 to change octaves.

### Drum Mapping (Channel 9/10)
When using the drum channel, each note number corresponds to a different percussion sound:

| Note Number | Drum Sound        |
|-------------|-------------------|
| 36          | Bass/Kick Drum    |
| 38          | Snare Drum        |
| 40          | Snare Drum (Alt)  |
| 42          | Closed Hi-hat     |
| 46          | Open Hi-hat       |
| 49          | Crash Cymbal      |
| 51          | Ride Cymbal       |

## Common Issues and Solutions

### Stuck Notes
MIDI notes can sometimes get "stuck" if a note_off message isn't received. This can happen when:
- A program crashes
- Communication is interrupted
- Timing issues occur

To resolve stuck notes, use the `all_notes_off` function:
```
all_notes_off  # Clear all notes on all channels
all_notes_off channels=[0]  # Clear specific channel
```

### Working with Songs
- Remember that songs operate on a time-based system (seconds)
- Add notes sequentially with proper timing
- Always include program_change messages at the beginning
- Include all_notes_off calls when stopping playback

## Working with MIDI Files

### MIDI File Formats
- Standard MIDI files (.mid or .midi) are supported
- Type 0 (single track) and Type 1 (multi-track) files are supported
- Files contain notes, program changes, controller messages, and more

### Loading and Playing MIDI Files
1. Load a file from path: `load_file path="/path/to/song.mid" name="My Song"`
2. OR load from base64-encoded binary data: `load_content data="TVRoZAAAAAYAAQABA..." name="My Song"`
3. Verify loading: `list_files`
4. Play the file: `play_file name="My Song"`
5. Stop playback: `stop_file`

### Generating MIDI Content with Claude
As Claude, you can generate MIDI content directly by:
1. Creating the binary structure of a MIDI file
2. Base64-encoding the binary data
3. Sending it to mcp-midi via the `load_content` function

This allows for dynamic MIDI generation without needing to save to the filesystem first.

#### MIDI File Structure
MIDI files consist of a header chunk and one or more track chunks:
- Header: `MThd` + length (4 bytes) + format (2 bytes) + tracks (2 bytes) + division (2 bytes)
- Track: `MTrk` + length (4 bytes) + events...

For simple MIDI generation, you can create a basic template and modify it as needed.

#### Example: Generating a Simple MIDI Melody
Here's an example of generating a simple MIDI file with Python code and then base64-encoding it:

```python
import mido
import base64
import io

# Create a new MIDI file with one track
mid = mido.MidiFile()
track = mido.MidiTrack()
mid.tracks.append(track)

# Add program change (instrument selection)
track.append(mido.Message('program_change', program=0, time=0))  # Piano

# Add some notes
track.append(mido.Message('note_on', note=60, velocity=100, time=0))   # C4
track.append(mido.Message('note_off', note=60, velocity=64, time=480)) # After 1 beat

track.append(mido.Message('note_on', note=62, velocity=100, time=0))   # D4
track.append(mido.Message('note_off', note=62, velocity=64, time=480)) # After 1 beat

track.append(mido.Message('note_on', note=64, velocity=100, time=0))   # E4
track.append(mido.Message('note_off', note=64, velocity=64, time=480)) # After 1 beat

# End of track
track.append(mido.MetaMessage('end_of_track', time=0))

# Convert to bytes
buffer = io.BytesIO()
mid.save(file=buffer)
midi_data = buffer.getvalue()

# Convert to base64
base64_data = base64.b64encode(midi_data).decode('utf-8')

print(base64_data)
```

This generates a base64-encoded string that you can send directly to the `load_content` function.

When Claude generates a MIDI file, it should:
1. Understand the MIDI file format structure
2. Generate the appropriate binary data
3. Base64-encode it for transmission
4. Send it to the `load_content` endpoint

This allows for completely dynamic MIDI generation without requiring access to the filesystem.

#### Claude's MIDI Workflow

As an AI assistant, Claude can:

1. **Generate MIDI data** directly in response to user requests
2. **Base64-encode** this data for transmission
3. **Send** the encoded data to the MCP-MIDI server
4. **Play** the musical content through connected MIDI devices

Example interaction:

```
Human: Can you create a happy tune for my birthday?

Claude: I'd love to create a birthday tune for you! Let me compose something cheerful.

[Claude internally generates appropriate MIDI data]

I've composed a happy birthday tune! Let me send it to your MIDI device:

load_content data="TVRoZAAAAAYAAQACAeBNVHJrAAAAPQDAOACQQ2SBcIBDQACQQ2SBcIBDQA..." name="Happy Birthday"

play_file name="Happy Birthday"

How does that sound? Would you like me to adjust anything about the melody or instrumentation?
```

This workflow enables completely dynamic music generation directly from conversation, without needing to save files to disk first.

### Converting MIDI Files to Songs
You can convert a MIDI file to a Song object for more control:
1. Load the file: `load_file path="/path/to/song.mid"`
2. Convert to song: `convert_to_song name="My Song"`
3. The song is now available: `play_song name="My Song"`

This allows you to:
- Modify the song structure
- Add or remove notes
- Change tempo or instruments
- Save the song for later use

## Workflow Patterns

### Simple Demo Workflow
1. Discover ports: `discover_ports`
2. Connect to port: `connect_port port_id=0`
3. Set instrument: `program_change program=0`
4. Play notes: `note_on note=60`
5. Stop notes: `note_off note=60`
6. Clean up: `all_notes_off`

### Song Creation Workflow
1. Create song: `create_song name="My Song" tempo=120`
2. Add instrument change: `add_program_change program=0 time=0`
3. Add notes and chords sequentially
4. Play song: `play_song name="My Song"`
5. If necessary, stop: `stop_song`

## Advanced Tips

### Multi-Instrument Songs
When creating songs with multiple instruments, make sure to:
1. Use different channels for different instruments
2. Add program_change events for each channel
3. Make sure to route notes to the correct channel

Example:
```
# Piano on channel 0
add_program_change program=0 time=0 channel=0
add_note pitch=60 time=0 duration=1 channel=0

# Violin on channel 1
add_program_change program=40 time=0 channel=1
add_note pitch=72 time=0 duration=1 channel=1
```

### Timed Sequences
Remember that song timing is in seconds, not beats. To convert from beats to seconds:
- Seconds per beat = 60 / BPM
- Time in seconds = beat number × (60 / BPM)

For a song at 120 BPM:
- Beat 1 = 0.0 seconds
- Beat 2 = 0.5 seconds
- Beat 3 = 1.0 seconds
- Beat 4 = 1.5 seconds

### MIDI Controller Values
Common controller numbers:
- 1: Modulation Wheel
- 7: Volume
- 10: Pan
- 11: Expression
- 64: Sustain Pedal
- 123: All Notes Off

## Troubleshooting

If you encounter issues:

1. **Stuck notes**: Always use `all_notes_off` when finished with a MIDI session
2. **No sound**: Check port connection and make sure synth is receiving MIDI
3. **Wrong sounds**: Verify channel and program numbers
4. **Song playback issues**: Check timing and duration values
5. **All notes off doesn't work**: Try sending note_off messages for specific notes

## Useful MIDI Resources

- General MIDI Instrument List: [Link to GM instrument list]
- MIDI Note Number Reference: [Link to MIDI note chart]
- Standard MIDI Controllers: [Link to MIDI CC reference]
