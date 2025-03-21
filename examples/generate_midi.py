
import mido
import base64
import io

# Create a new MIDI file with one track
mid = mido.MidiFile()
track = mido.MidiTrack()
mid.tracks.append(track)

# Add program change (instrument selection - trumpet)
track.append(mido.Message('program_change', program=56, time=0))

# Create a simple melody (Happy Birthday)
# Note: time is in ticks, 480 ticks = quarter note at default tempo

# Happy
track.append(mido.Message('note_on', note=67, velocity=100, time=0))
track.append(mido.Message('note_off', note=67, velocity=64, time=240))

# Birth-
track.append(mido.Message('note_on', note=67, velocity=100, time=0))
track.append(mido.Message('note_off', note=67, velocity=64, time=240))

# -day
track.append(mido.Message('note_on', note=69, velocity=100, time=0))
track.append(mido.Message('note_off', note=69, velocity=64, time=480))

# to
track.append(mido.Message('note_on', note=67, velocity=100, time=0))
track.append(mido.Message('note_off', note=67, velocity=64, time=480))

# you
track.append(mido.Message('note_on', note=72, velocity=100, time=0))
track.append(mido.Message('note_off', note=72, velocity=64, time=480))

# Happy
track.append(mido.Message('note_on', note=71, velocity=100, time=0))
track.append(mido.Message('note_off', note=71, velocity=64, time=960))

# Add a drum track
drum_track = mido.MidiTrack()
mid.tracks.append(drum_track)

# Set drums (channel 9)
for i in range(4):
    # Bass drum
    drum_track.append(mido.Message('note_on', note=36, velocity=100, time=0 if i == 0 else 480, channel=9))
    drum_track.append(mido.Message('note_off', note=36, velocity=0, time=10, channel=9))
    
    # Hi-hat
    drum_track.append(mido.Message('note_on', note=42, velocity=80, time=230, channel=9))
    drum_track.append(mido.Message('note_off', note=42, velocity=0, time=10, channel=9))
    
    # Snare (on beats 2 and 4)
    if i % 2 == 1:
        drum_track.append(mido.Message('note_on', note=38, velocity=100, time=230, channel=9))
        drum_track.append(mido.Message('note_off', note=38, velocity=0, time=10, channel=9))
    else:
        drum_track.append(mido.Message('note_on', note=42, velocity=60, time=230, channel=9))
        drum_track.append(mido.Message('note_off', note=42, velocity=0, time=10, channel=9))

# End of track
track.append(mido.MetaMessage('end_of_track', time=0))
drum_track.append(mido.MetaMessage('end_of_track', time=0))

# Convert to bytes
buffer = io.BytesIO()
mid.save(file=buffer)
midi_data = buffer.getvalue()

# Convert to base64
base64_data = base64.b64encode(midi_data).decode('utf-8')

print(base64_data)
