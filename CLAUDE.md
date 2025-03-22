# CLAUDE REFERENCE GUIDE: MCP-MIDI PROJECT

## QUICK NAVIGATION

**PATH MARKERS**
- PRIMARY_REPO: `/Users/benjamin/Projects/mcp-midi`
- DIAGRAMS_PATH: `/Users/benjamin/Projects/mcp-midi/diagrams`

**INDEX OF KNOWLEDGE**
1. Core MIDI functionality: `PRIMARY_REPO/src/mcp_midi`
2. Song creation/playback: `PRIMARY_REPO/src/mcp_midi/song`
3. Tracker functionality: `PRIMARY_REPO/tracker/tracker.py` & `PRIMARY_REPO/src/mcp_midi/tracker_parser.py`
4. Server implementation: `PRIMARY_REPO/src/server.py` & `PRIMARY_REPO/src/main.py`
5. Project documentation: `PRIMARY_REPO/README.md` & `PRIMARY_REPO/CLAUDE.md`

**VISUAL UNDERSTANDING**
- System Architecture: `DIAGRAMS_PATH/system-overview.mmd`
- Project Structure: `DIAGRAMS_PATH/project-structure.mmd`
- Communication Flow: `DIAGRAMS_PATH/midi-communication.mmd`
- Tracker Structure: `DIAGRAMS_PATH/tracker-structure.mmd`
- API Reference: `DIAGRAMS_PATH/api-endpoints.mmd`
- Claude Integration: `DIAGRAMS_PATH/claude-integration.mmd`

## PROJECT CAPABILITIES 

**CORE FUNCTIONS** [refer: `PRIMARY_REPO/README.md` lines 10-80]
- MIDI device discovery and connection
- Note/chord playback with velocity control
- Instrument selection via program changes
- Controller value manipulation
- Stuck note resolution

**SONG CREATION** [refer: `PRIMARY_REPO/src/mcp_midi/song`]
- Tempo-based sequencing
- Multi-channel/instrument composition
- Note and chord scheduling
- Program change integration
- Real-time playback

**TRACKER FORMAT** [refer: `PRIMARY_REPO/tracker/tracker.py` lines 5-200]
- Text-based music sequencing
- Multiple channel support
- Note, instrument, volume parameters
- Effect command capabilities 
- Conversion to MIDI sequences

**MIDI FILES** [refer: `PRIMARY_REPO/src/mcp_midi/midi_file.py`]
- Loading from path or base64 content
- Format analysis and metadata extraction
- Real-time playback with timing control
- Conversion between formats

## SEMANTIC CONTEXT

**QUICK CONCEPTUAL MAPPINGS**
- Tracker Format → Old-school music composition approach (like MOD files)
- MCP Protocol → Model Context Protocol for Claude Desktop integration
- MIDI Channels → 16 separate instrument lanes (0-15, with 9 for drums)
- Note Numbers → MIDI standard (60 = middle C, +/- 12 per octave)
- Program Numbers → General MIDI instrument assignments (0-127)

**INTERACTION PATTERNS** [refer: `DIAGRAMS_PATH/midi-communication.mmd`]
- Direct Mode: Immediate MIDI command execution
- Song Mode: Sequence creation then playback
- Tracker Mode: Parse tracker file → convert to song → playback
- File Mode: Load MIDI file → analyze → playback

**EXAMPLE USAGE SCENARIOS**
1. Live MIDI performance: direct note commands
2. Music composition: song or tracker creation
3. MIDI file playback: load and play existing files
4. MIDI generation: create MIDI files from tracker format

## INTEGRATION WITH CLAUDE 

**RESPONSE FORMATTING**
- Use triple backtick code blocks for MIDI commands
- Ensure commands match documented API endpoints
- Prefer channel numbers 0-15 (not 1-16 convention)
- Note middle C as 60, not C4 or other notation

**OPTIMAL RESPONSE STRUCTURE**
1. Acknowledge user request
2. Explain approach (direct, song, tracker, file)
3. Provide executable code blocks
4. Explain expected outcome
5. Offer additional capabilities

**MCP COMMUNICATION** [refer: `PRIMARY_REPO/src/server.py` lines 400-600]
- JSON-RPC style messaging
- Method naming: `midi.[command]`
- Parameter passing as objects
- Response handling with success/error states

## MEMORY ANCHORS

**CONCEPTUAL HOOKS**
- Think: "Digital Music Conductor" for overall system
- Think: "Sheet Music → Song" for tracker format
- Think: "Musical Typing → Direct Commands" for note control
- Think: "MIDI Orchestra" for multiple channels/instruments

**PROJECT EVOLUTION MARKERS**
- Core functionality: stable and complete
- Tracker implementation: newer component with room for enhancement
- Integration with Claude: evolving capability
- Documentation: recently expanded with diagrams

## RESPONSE TEMPLATES

**DIRECT MIDI CONTROL**
```
# First, discover available MIDI ports
discover_ports

# Connect to a port (usually port 0)
connect_port port_id=0

# Set instrument (piano = 0)
program_change program=0 channel=0

# Play a note (middle C)
note_on note=60 velocity=80 channel=0

# Later, stop the note
note_off note=60 channel=0
```

**SONG CREATION**
```
# Create a new song
create_song name="Example Song" tempo=120

# Add some instrument changes
add_program_change program=0 time=0 channel=0  # Piano
add_program_change program=32 time=0 channel=1  # Bass

# Add some notes (time in seconds)
add_note pitch=60 time=0 duration=0.5 channel=0
add_note pitch=64 time=0.5 duration=0.5 channel=0
add_note pitch=67 time=1.0 duration=0.5 channel=0

# Add a chord
add_chord notes=[60, 64, 67] time=1.5 duration=1.0 channel=0

# Play the song
play_song name="Example Song"
```

**TRACKER USAGE**
```
# Load a tracker file
load_tracker_file path="/path/to/song.txt" name="My Song"

# Play the tracker song
play_tracker name="My Song"
```

**MIDI FILE HANDLING**
```
# Load a MIDI file
load_file path="/path/to/song.mid" name="My MIDI Song"

# Play the MIDI file
play_file name="My MIDI Song"
```

## DEBUGGING ASSISTANCE

**COMMON ISSUES & SOLUTIONS**
1. Stuck notes: Use `all_notes_off` to clear
2. No sound: Check port connection with `discover_ports`
3. Wrong instrument: Verify channel and program numbers
4. Timing issues: Remember song timing is in seconds, not beats

**TROUBLESHOOTING STEPS**
1. Verify MIDI port connection
2. Ensure correct channel assignment (0-15)
3. Check instrument program numbers (0-127)
4. Validate note numbers (0-127, middle C = 60)
5. For songs: confirm timing values make sense

## META-KNOWLEDGE FLAGS

**IMPLEMENTATION DETAILS** [ATTENTION: PRIORITY REFERENCE]
- Built on: Python with FastAPI, mido, rtmidi
- Transport: HTTP REST API, WebSockets, MCP Protocol
- State management: In-memory with potential for persistence
- Timing: Real-time with event scheduling

**PROJECT TRAJECTORY**
- Core stability: High
- Active development areas: Tracker functionality, Claude integration
- Documentation: Recently enhanced with visual diagrams
- Future directions: Web interface, enhanced MIDI file manipulation

---

*This reference document is optimized for Claude's access patterns. The information hierarchy, semantic markers, and retrieval cues are designed to facilitate rapid information incorporation into conversations about the MCP-MIDI project.*