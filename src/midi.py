from settings import SETTINGS
import adafruit_midi
import usb_midi
import busio
import board
from collections import OrderedDict
from debug import debug, DEBUG_MODE
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from display import display_notification,display_text_middle

# PINS / SETUP
NUM_PADS = 16
MIDI_AUX_TX_PIN = board.GP16
MIDI_AUX_RX_PIN = board.GP17 # not used, but so we can use library

uart = busio.UART(MIDI_AUX_TX_PIN, MIDI_AUX_RX_PIN, baudrate=31250,timeout=0.001)
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=SETTINGS['MIDI_CHANNEL'])
aux_midi = adafruit_midi.MIDI(
    midi_in=uart,
    midi_out=uart,
    in_channel=(1),
    out_channel=(SETTINGS['MIDI_CHANNEL']),
    debug=False,
)

# MIDI 1: SET UP NOTES / BANKS
current_midi_notes = SETTINGS['MIDI_NOTES_DEFAULT']
midi_banks_chromatic = [[0 + i for i in range(16)],
              [4 + i for i in range(16)],
              [20 + i for i in range(16)],
              [36 + i for i in range(16)],
              [52 + i for i in range(16)],
              [68 + i for i in range(16)],
              [84 + i for i in range(16)],
              [100 + i for i in range(16)],
              [111 + i for i in range(16)]
              ]
current_midibank_set = midi_banks_chromatic
midi_bank_idx = SETTINGS['DEFAULT_MIDIBANK_IDX']
scale_bank_idx = 0
current_scale_dict = []
midi_velocities = [SETTINGS['DEFAULT_VELOCITY']] * 16 
midi_velocities_singlenote = SETTINGS['DEFAULT_SINGLENOTE_MODE_VELOCITIES'] 
midi_mode = "all"   # "usb" "aux" or "all"
play_mode = "standard" # 'standard' 'encoder'
current_assignment_velocity = 120

midi_to_note = {
    0: 'C0', 1: 'C#0', 2: 'D0', 3: 'D#0', 4: 'E0', 5: 'F0', 6: 'F#0', 7: 'G0', 8: 'G#0', 9: 'A0', 10: 'A#0', 11: 'B0',
    12: 'C1', 13: 'C#1', 14: 'D1', 15: 'D#1', 16: 'E1', 17: 'F1', 18: 'F#1', 19: 'G1', 20: 'G#1', 21: 'A1', 22: 'A#1', 23: 'B1',
    24: 'C2', 25: 'C#2', 26: 'D2', 27: 'D#2', 28: 'E2', 29: 'F2', 30: 'F#2', 31: 'G2', 32: 'G#2', 33: 'A2', 34: 'A#2', 35: 'B2',
    36: 'C3', 37: 'C#3', 38: 'D3', 39: 'D#3', 40: 'E3', 41: 'F3', 42: 'F#3', 43: 'G3', 44: 'G#3', 45: 'A3', 46: 'A#3', 47: 'B3',
    48: 'C4', 49: 'C#4', 50: 'D4', 51: 'D#4', 52: 'E4', 53: 'F4', 54: 'F#4', 55: 'G4', 56: 'G#4', 57: 'A4', 58: 'A#4', 59: 'B4',
    60: 'C5', 61: 'C#5', 62: 'D5', 63: 'D#5', 64: 'E5', 65: 'F5', 66: 'F#5', 67: 'G5', 68: 'G#5', 69: 'A5', 70: 'A#5', 71: 'B5',
    72: 'C6', 73: 'C#6', 74: 'D6', 75: 'D#6', 76: 'E6', 77: 'F6', 78: 'F#6', 79: 'G6', 80: 'G#6', 81: 'A6', 82: 'A#6', 83: 'B6',
    84: 'C7', 85: 'C#7', 86: 'D7', 87: 'D#7', 88: 'E7', 89: 'F7', 90: 'F#7', 91: 'G7', 92: 'G#7', 93: 'A7', 94: 'A#7', 95: 'B7',
    96: 'C8', 97: 'C#8', 98: 'D8', 99: 'D#8', 100: 'E8', 101: 'F8', 102: 'F#8', 103: 'G8', 104: 'G#8', 105: 'A8', 106: 'A#8', 107: 'B8',
    108: 'C9', 109: 'C#9', 110: 'D9', 111: 'D#9', 112: 'E9', 113: 'F9', 114: 'F#9', 115: 'G9', 116: 'G#9', 117: 'A9', 118: 'A#9', 119: 'B9',
    120: 'C10', 121: 'C#10', 122: 'D10', 123: 'D#10', 124: 'E10', 125: 'F10', 126: 'F#10', 127: 'G10',
}

# MIDI 2: SCALES 
scale_root_note_dict = {
    'C': 0,
    'C#': 1,
    'Db': 1,
    'D': 2,
    'D#': 3,
    'Eb': 3,
    'E': 4,
    'F': 5,
    'F#': 6,
    'Gb': 6,
    'G': 7,
    'G#': 8,
    'Ab': 8,
    'A': 9,
    'A#': 10,
    'Bb': 10,
    'B': 11
}

all_scales_midi_dicts = []

# Dictionary of common major scales (key: root note, value: scale intervals)
major_scales_intervals = OrderedDict({
    'C': [0, 2, 4, 5, 7, 9, 11],   # C major
    'G': [7, 9, 11, 0, 2, 4, 5],   # G major
    'D': [2, 4, 5, 7, 9, 11, 0],   # D major
    'A': [9, 11, 0, 2, 4, 5, 7],   # A major
    'E': [4, 5, 7, 9, 11, 0, 2],   # E major
    'B': [11, 0, 2, 4, 5, 7, 9],   # B major
    'F#': [6, 7, 9, 11, 1, 2, 4],  # F# major
    'Db': [1, 2, 4, 6, 7, 9, 11],  # Db major
    'Ab': [8, 10, 0, 1, 3, 4, 6],  # Ab major
    'Eb': [3, 5, 6, 8, 10, 11, 1], # Eb major
    'Bb': [10, 0, 1, 3, 5, 6, 8],  # Bb major
    'F': [5, 7, 8, 10, 0, 1, 3]    # F major
})

# Dictionary of common minor scales (key: root note, value: scale intervals)
minor_scales_intervals = OrderedDict({
    'A': [9, 11, 0, 2, 4, 5, 7],   # A minor
    'E': [4, 5, 7, 9, 11, 0, 2],   # E minor
    'B': [11, 0, 2, 4, 5, 7, 9],   # B minor
    'F#': [6, 7, 9, 11, 1, 2, 4],  # F# minor
    'C#': [1, 2, 4, 6, 7, 9, 11],  # C# minor
    'Ab': [8, 10, 0, 1, 3, 4, 6],  # Ab minor
    'Eb': [3, 5, 6, 8, 10, 11, 1], # Eb minor
    'Bb': [10, 11, 1, 3, 5, 6, 8], # Bb minor
    'F': [5, 7, 8, 10, 0, 1, 3],   # F minor
    'C': [0, 1, 3, 5, 7, 8, 10],   # C minor
    'D': [2, 4, 5, 7, 9, 11, 1]    # D minor
})

def get_midi_notes_in_scale(root, scale_intervals): # Helper function to generate scale midi

    # Number of octaves to generate notes for (C0 to C10)
    num_octaves = 11

    # List to store MIDI notes
    midi_notes = []

    for octave in range(num_octaves):
        for interval in scale_intervals:
            midi_note = octave * 12 + ((root + interval) % 12)

            # Account invalid midi, and when interval order is wonky
            if len(midi_notes) > 0 and midi_note < midi_notes[-1]: 
                midi_note = midi_note + 12
            while midi_note > 127:
                midi_note = midi_note - 12
            while midi_note < 0:
                midi_note = midi_note + 12
            
            midi_notes.append(midi_note)

    # Now split into 16 pad sets 
    midi_notes_pad_mapped = []
    numarys = round(len(midi_notes) / NUM_PADS)  # how many 16 pad banks do we need
    for i in range(numarys):
        if i == 0:
            padset = midi_notes[ : NUM_PADS-1]
        else:
            st = i * NUM_PADS
            end = st + NUM_PADS
            padset = midi_notes[st:end]

            # Need arrays to be exaclty 16. Fix if needed.
            pads_short = 16 - len(padset)
            if pads_short > 0:
                lastnote = padset[-1]
                for i in range(pads_short):
                    padset.append(lastnote)

        midi_notes_pad_mapped.append(padset)

    return midi_notes_pad_mapped

# Generate arrays for all scales
chromatic_dict = {
    'root_note': 'ALL',
    'type': "Chromatic",
    'midi_arrays':midi_banks_chromatic
}
all_scales_midi_dicts.append(chromatic_dict)

for root_note, intervals in major_scales_intervals.items(): # Major
    major_scale_array = get_midi_notes_in_scale(scale_root_note_dict[root_note], intervals)
    scale_dict = {
        'root_note': root_note,
        'type': "Major",
        'midi_arrays':major_scale_array
    }
    all_scales_midi_dicts.append(scale_dict)

for root_note, intervals in minor_scales_intervals.items(): # Minor
    minor_scale_array = get_midi_notes_in_scale(scale_root_note_dict[root_note], intervals)
    scale_dict = {
        'root_note': root_note,
        'type': "Minor",
        'midi_arrays':minor_scale_array
    }
    all_scales_midi_dicts.append(scale_dict)

def create_chord(root_note, chord_type, scale_type='major'):
    """
    Get the MIDI note values of a specific chord based on the given root note and chord type.

    Args:
        root_note (str): The root note of the chord (e.g., 'C', 'G#', 'F').
        chord_type (str): The type of chord (e.g., 'maj', 'min', '7', 'maj7', 'm7').
        scale_type (str): The type of scale to use (e.g., 'major', 'minor', 'other').
                         Default is 'major'.

    Returns:
        list: A list of MIDI note values representing the chord.
    """
    if scale_type == 'major':
        scale_dict = major_scales_intervals
    elif scale_type == 'minor':
        scale_dict = minor_scales_intervals
    # elif scale_type == 'other':
    #     scale_dict = other_scales_intervals
    else:
        raise ValueError("Invalid scale type. Please use 'major', 'minor', or 'other'.")

    if root_note not in scale_dict:
        raise ValueError(f"Root note '{root_note}' not found in the scale dictionary.")

    intervals = scale_dict[root_note]
    root_midi = 60  # MIDI note number of 'C' (assuming MIDI Note 60 is middle C)

    # Convert root note to MIDI note number
    root_midi += intervals[0]

    # Calculate the MIDI note values of the chord based on the intervals
    chord_notes_midi = [(root_midi + interval) % 12 for interval in intervals]

    # Apply chord type to the notes
    if chord_type == 'maj':
        pass
    elif chord_type == 'min':
        chord_notes_midi[2] -= 1
    elif chord_type == '7':
        chord_notes_midi.append((root_midi + intervals[4] + 10) % 12)
    elif chord_type == 'maj7':
        chord_notes_midi.append((root_midi + intervals[4] + 11) % 12)
    elif chord_type == 'm7':
        chord_notes_midi[2] -= 1
        chord_notes_midi.append((root_midi + intervals[4] + 10) % 12)
    # Add more chord types here...

    # Convert MIDI note numbers back to MIDI values (0 to 127)
    chord_notes_midi = [root_midi + note for note in chord_notes_midi]

    return chord_notes_midi

# Display Text = whehter to print new info to screen.
def chg_scale(upOrDown=True,display_text = True):
    global scale_bank_idx
    global midi_bank_idx
    global current_scale_dict
    global current_midi_notes
    """
    Get the next or previous scale array from 'all_scales_midi_dicts'.

    Args:
        scale_array (list): The current scale array.
        upOrDown (bool): Set to True to go up (next) the scale, and False to go down (previous).
                         Default is True (go up).

    Returns:
        list: The next or previous scale array.
    """
    total_scales = len(all_scales_midi_dicts)

    if upOrDown:
        scale_bank_idx = (scale_bank_idx + 1) % total_scales
    else:
        scale_bank_idx = (scale_bank_idx - 1) % total_scales

    current_scale_dict = all_scales_midi_dicts[scale_bank_idx]

    midi_bank_idx = 2
    current_midi_notes = current_scale_dict['midi_arrays'][midi_bank_idx]
    if DEBUG_MODE:
        print(f"current midi notes: {current_midi_notes}")
    if DEBUG_MODE:
        debug.add_debug_line("Current Scale",get_scale_display_text())
    if display_text:
        display_text_middle(get_scale_display_text())
    #display_scale()

# External use - by Menu object to print to screen
def get_scale_display_text():
    num_scales = len(all_scales_midi_dicts)
    disp_text = [f"Scale: {current_scale_dict['root_note']} {current_scale_dict['type']}",
                 "",
                 f"               {scale_bank_idx+1}/{num_scales}"]
    return disp_text

# display = should it print to display
def chg_midi_bank(upOrDown = True, display_text=True):
    global midi_bank_idx
    global current_midi_notes

    current_midibank_set = current_scale_dict['midi_arrays']
    if upOrDown is True and midi_bank_idx < (len(current_midibank_set) - 1):
        clear_all_notes()
        midi_bank_idx = midi_bank_idx + 1

    if upOrDown is False and midi_bank_idx > 0:
        clear_all_notes()
        midi_bank_idx = midi_bank_idx - 1

    current_midi_notes = current_midibank_set[midi_bank_idx]
     # Dont let notes get stuck on
    for note in current_midi_notes:
         midi.send(NoteOff(note, 0))

    if DEBUG_MODE:
        debug.add_debug_line("Midi Bank Vals",get_midi_bank_display_text())
    if display_text:
        display_text_middle(get_midi_bank_display_text())

    return

# Get the MIDI note name as text based on the MIDI value
def get_midi_note_name_text(midi_val):
    """
    Returns the MIDI note name as text based on the provided MIDI value.
    
    Args:
        midi_val (int): MIDI value (0-127) to get the note name for.
        
    Returns:
        str: The MIDI note name as text, e.g., "C4" or "OUT OF RANGE" if out of MIDI range.
    """
    if midi_val < 0 or midi_val > 127:
        return "OUT OF RANGE"
    else:
        return midi_to_note[midi_val]

# Get a string of text displaying the current MIDI bank information
def get_midi_bank_display_text():
    """
    Returns a string displaying the current MIDI bank information.
    
    Returns:
        str: A string containing the MIDI bank index and the note range, e.g., "Bank: 0 (C1 - G1)".
    """
    disp_text = f"Bank: {midi_bank_idx}  ({get_currentbank_noterange()})"
    return disp_text

# Get a string of text corresponding to the note range of the current MIDI bank
def get_currentbank_noterange():
    """
    Returns a string of text representing the note range of the current MIDI bank.
    
    Returns:
        str: A string describing the note range, e.g., "C#1 - G1".
    """
    first = midi_to_note[current_midi_notes[0]]
    last = midi_to_note[current_midi_notes[-1]]
    text = f"{first} - {last}"
    return text

# Get MIDI velocity for a given index (used by external modules)
def get_midi_velocity_by_idx(idx):
    """
    Returns the MIDI velocity for a given index.
    
    Args:
        idx (int): Index of the MIDI velocity to retrieve.
        
    Returns:
        int: The MIDI velocity value.
    """
    return midi_velocities[idx]

# Set the MIDI velocity for a given index (used by external modules)
def set_midi_velocity_by_idx(idx, val):
    """
    Sets the MIDI velocity for a given index.
    
    Args:
        idx (int): Index of the MIDI velocity to set.
        val (int): The new MIDI velocity value.
    """
    midi_velocities[idx] = val
    if DEBUG_MODE: 
        print(f"Setting MIDI velocity: {val}")

# Get MIDI note by index (used by external modules)
def get_midi_note_by_idx(idx):
    """
    Returns the MIDI note for a given index.
    
    Args:
        idx (int): Index of the MIDI note to retrieve.
        
    Returns:
        int: The MIDI note value.
    """
    if DEBUG_MODE: 
        print(f"Getting MIDI note for pad index: {idx}")

    if idx > len(current_midi_notes) - 1:
        idx = len(current_midi_notes) - 1
        
    return current_midi_notes[idx]

# Set MIDI note by index (used by external modules)
def set_midi_note_by_idx(idx, val):
    """
    Sets the MIDI note for a given index.
    
    Args:
        idx (int): Index of the MIDI note to set.
        val (int): The new MIDI note value.
    """
    current_midi_notes[idx] = val

# Get MIDI note velocity for a specific pad
def get_midi_velocity_singlenote_by_idx(idx):
    """
    Returns the MIDI note velocity for a specific pad index.
    
    Args:
        idx (int): Index of the pad.
        
    Returns:
        int: The MIDI velocity value.
    """
    return midi_velocities_singlenote[idx]

# Wrapper for sending a MIDI note-on message (handles USB and AUX MIDI)
def send_midi_note_on(note, velocity):
    """
    Sends a MIDI note-on message with the given note and velocity.
    
    Args:
        note (int): MIDI note value (0-127).
        velocity (int): MIDI velocity value (0-127).
    """
    if midi_mode == "usb" or midi_mode == "all":
        midi.send(NoteOn(note, velocity))
    
    if midi_mode == "aux" or midi_mode == "all":
        aux_midi.send(NoteOn(note, velocity))

# Wrapper for sending a MIDI note-off message (handles USB and AUX MIDI)
def send_midi_note_off(note):
    """
    Sends a MIDI note-off message for the given note.
    
    Args:
        note (int): MIDI note value (0-127).
    """
    if midi_mode == "usb" or midi_mode == "all":
        midi.send(NoteOff(note, 0))

    if midi_mode == "aux" or midi_mode == "all":
        aux_midi.send(NoteOff(note, 0))

# Send an off message to ALL notes. Use for panic, or to make sure nothing is stuck on.
def clear_all_notes():
    for i in range(127):
        midi.send(NoteOff(i,0))

# Change MIDI mode to the next or previous mode
def chg_midi_mode(nextOrPrev=1):
    """
    Changes the MIDI mode to the next or previous mode.
    
    Args:
        nextOrPrev (bool): True for the next mode, False for the previous mode.
    """
    global midi_mode

    if nextOrPrev:
        if midi_mode == "usb":
            midi_mode = "aux"
        elif midi_mode == "aux":
            midi_mode = "all"
        elif midi_mode == "all":
            midi_mode = "usb"
    
    if not nextOrPrev:
        if midi_mode == "usb":
            midi_mode = "all"
        elif midi_mode == "aux":
            midi_mode = "usb"
        elif midi_mode == "all":
            midi_mode = "aux"

# Double-click function for MIDI bank, changes velocity to encoder roll mode
def double_click_func_btn():
    global play_mode

    if play_mode == "standard":
        play_mode = "encoder"
    elif play_mode == "encoder":
        play_mode = "standard"
    
    display_notification(f"Note mode: {play_mode}")

# Called when on the play screen and an encoder btn is held.
# Params: 
#   int - encoder steps recorded.
#   bool - True if this is the first hold of this hold session (resets when all released)
# Returns: 
#   bool - if encoder count was used in this function, return true
def pad_held_function(pad_idx,encoder_delta,first_pad_held):

    global current_assignment_velocity
    delta_used = False

    # No pads were held before this one in this session
    if first_pad_held is True:
        current_assignment_velocity = get_midi_velocity_by_idx(pad_idx)

    if abs(encoder_delta) > 0:
        current_assignment_velocity = current_assignment_velocity + encoder_delta
        current_assignment_velocity = min(current_assignment_velocity,127) # Make sure its valid midi (0 - 127)
        current_assignment_velocity = max(current_assignment_velocity,0)
        delta_used = True

        if play_mode == "standard":
            set_midi_velocity_by_idx(pad_idx,current_assignment_velocity)
            display_notification(f"velocity: {current_assignment_velocity}")

    return delta_used

def setup_midi():
    global current_scale_dict
    current_scale_dict = all_scales_midi_dicts[scale_bank_idx]