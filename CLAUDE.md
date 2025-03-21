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
