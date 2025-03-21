# Claude MIDI Interaction Examples

This document shows examples of how Claude can interact with the MCP MIDI server to control MIDI devices.

## Prerequisites

1. The MCP MIDI server is running:
   ```bash
   python -m src.main
   ```

2. Claude is connected to the MCP MIDI server via an MCP integration.

## Example 1: Playing a Single Note

You can ask Claude to play a single note with a prompt like:

> Claude, can you play middle C on my MIDI synthesizer?

Claude might respond:

```
I'd be happy to play middle C on your MIDI synthesizer! I'll send a MIDI note_on command followed by a note_off command to create a clean note.

```midi
{
  "type": "note_on",
  "note": 60,
  "velocity": 100,
  "channel": 0
}
```

This will play middle C (MIDI note 60) at a strong velocity. Let me know if you'd like me to stop the note:

```midi
{
  "type": "note_off",
  "note": 60,
  "channel": 0
}
```

The note has now been turned off. Is there anything else you'd like me to play?
```

## Example 2: Playing a Chord

You can ask Claude to play a chord:

> Claude, please play a C major chord.

Claude might respond:

```
I'll play a C major chord for you. This chord consists of the notes C, E, and G.

```midi
{
  "type": "note_on",
  "note": 60,
  "velocity": 90,
  "channel": 0
}
```

```midi
{
  "type": "note_on",
  "note": 64,
  "velocity": 90,
  "channel": 0
}
```

```midi
{
  "type": "note_on",
  "note": 67,
  "velocity": 90,
  "channel": 0
}
```

I'm now playing all three notes of the C major chord (C, E, and G). Let me know when you'd like me to stop the chord.

To stop playing the chord, I'll need to turn off each note:

```midi
{
  "type": "note_off",
  "note": 60,
  "channel": 0
}
```

```midi
{
  "type": "note_off",
  "note": 64,
  "channel": 0
}
```

```midi
{
  "type": "note_off",
  "note": 67,
  "channel": 0
}
```

The chord has now stopped. Would you like me to play another chord or explain what I did?
```

## Example 3: Changing Instruments

You can ask Claude to change the instrument:

> Claude, please change to a violin sound.

Claude might respond:

```
I'll change the instrument to a violin sound for you. In the General MIDI standard, violin is instrument number 40.

```midi
{
  "type": "program_change",
  "program": 40,
  "channel": 0
}
```

I've changed to violin (program 40). Would you like me to play something with this instrument?
```

## Example 4: Playing a Melody

You can ask Claude to play a simple melody:

> Claude, can you play "Mary Had a Little Lamb" on the piano?

Claude might respond:

```
I'd be happy to play "Mary Had a Little Lamb" on the piano! First, let me set the instrument to a piano sound (General MIDI program 0).

```midi
{
  "type": "program_change",
  "program": 0,
  "channel": 0
}
```

Now I'll play the melody note by note. The traditional tune goes like this:

E D C D E E E (rest) D D D (rest) E G G (rest) E D C D E E E E D D E D C

Here's the performance:

```midi
{
  "type": "note_on",
  "note": 64,  // E
  "velocity": 80,
  "channel": 0
}
```

[Wait for 500ms]

```midi
{
  "type": "note_off",
  "note": 64,
  "channel": 0
}
```

```midi
{
  "type": "note_on",
  "note": 62,  // D
  "velocity": 80,
  "channel": 0
}
```

[Continue with the rest of the melody...]
```

## Example 5: Controlling Expression

You can ask Claude to add expressive control:

> Claude, can you make the synthesizer's sound brighter?

Claude might respond:

```
I'll make the synthesizer sound brighter by sending a MIDI Control Change message. For most synthesizers, Controller #74 controls brightness/filter cutoff.

```midi
{
  "type": "control_change",
  "control": 74,
  "value": 100,
  "channel": 0
}
```

I've increased the brightness/filter cutoff to a high value (100 out of 127). The sound should now be noticeably brighter. Would you like me to play something so you can hear the difference?
```

## Notes for Developers

- Claude can send multiple MIDI commands in a single response
- Each MIDI command should be wrapped in a ```midi {...}``` code block
- Claude will automatically extract and process these commands when the response is displayed
- The MCP server handles the actual communication with the MIDI device
