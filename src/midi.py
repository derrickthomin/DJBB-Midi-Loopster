from settings import SETTINGS
import adafruit_midi
import time
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
current_midi_notes = SETTINGS['MIDI_NOTES_DEFAULT']                   # Track chord notes. Only 16 for now. Will store loop objects.
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
current_scale_list = []
scale_bank_idx = 0 # maj, minor, etc. separate from root
rootnote_idx = 0 # C,Db,D..
midi_velocities = [SETTINGS['DEFAULT_VELOCITY']] * 16 
midi_velocities_singlenote = SETTINGS['DEFAULT_SINGLENOTE_MODE_VELOCITIES'] 
midi_mode = "all"   # "usb" "aux" or "all"
play_mode = "standard" # 'standard' 'encoder' 'chord'
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

scale_root_notes_list = [('C', 0),
                        ('Db', 1), 
                        ('D', 2), 
                        ('Eb', 3), 
                        ('E', 4), 
                        ('F', 5), 
                        ('Gb', 6), 
                        ('G', 7),
                        ('Ab', 8), 
                        ('A', 9), 
                        ('Bb', 10), 
                        ('B', 11)]




scale_intervals = OrderedDict({
    "maj": [2, 2, 1, 2, 2, 2, 1],
    "min": [2, 1, 2, 2, 1,  2,2],
    "harm_min": [2, 1, 2, 2, 1, 3, 1],
    "mel_min": [2, 1, 2, 2, 2, 2, 1],
    "dorian": [2, 1, 2, 2, 2, 1, 2],
    "phrygian": [1, 2, 2, 2, 1, 2, 2],
    "lydian": [2, 2, 2, 1, 2, 2, 1]
    #"mixolydian": [2, 2, 1, 2, 2, 1, 2],
    #"aeolian": [2, 1, 2, 2, 1, 2, 2],
    #"locrian": [1, 2, 2, 1, 2, 2, 2],
    #"lyd_dom": [2, 2, 2, 1, 2, 1, 2],
    #"super_loc": [1, 2, 1, 2, 2, 2, 2],
    #"min_penta": [3, 2, 2, 3, 2],
    #"maj_penta": [2, 2, 3, 2, 3],
    #"min_blues": [3, 2, 1, 1, 3, 2],
    #"maj_blues": [2, 1, 1, 3, 2, 3],
    #"wh_half_dim": [2, 1, 2, 1, 2, 1, 2, 1],
    #"half_wh_dim": [1, 2, 1, 2, 1, 2, 1, 2]
})


def get_midi_notes_in_scale(root, scale_intervals): # Helper function to generate scale midi
    oct =1  # octave
    midi_notes = []
    cur_note = root 

    for interval in scale_intervals:
        cur_note = cur_note + interval
        midi_notes.append(cur_note)

    base_notes = midi_notes
    while cur_note < 127:
        for note in base_notes:
            cur_note = note + (12 * oct)
            if cur_note > 127:
                break
            midi_notes.append(cur_note)
        oct = oct + 1

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

# Houses ALL scales. Sorted by type - maj/min/etc
# Lists of tuples (name, notes ary)
# Structure: all_scales list [("major", [("C", 01234...),
#                                       ("D", 01234...),..]
all_scales_list = []
chromatic_ary = ('chromatic',[('chromatic',midi_banks_chromatic)])
all_scales_list.append(chromatic_ary)

for scale_name, interval in scale_intervals.items():
    interval_ary = []
    for root_name, root in scale_root_notes_list:
        interval_ary.append((root_name,get_midi_notes_in_scale(root,interval)))
        #interval_dict[root_name] = get_midi_notes_in_scale(root,interval)
    #all_scales_dicts[scale_name] = interval_dict
    all_scales_list.append((scale_name,interval_ary))

NUM_SCALES = len(all_scales_list)
NUM_ROOTS = len(scale_root_notes_list)
# Display Text = whehter to print new info to screen.
def chg_scale(upOrDown=True,display_text = True):
    global scale_bank_idx
    global rootnote_idx
    global midi_bank_idx
    global current_scale_list
    global current_midi_notes

    total_scales = len(all_scales_list)

    if upOrDown:
        scale_bank_idx = (scale_bank_idx + 1) % total_scales
    else:
        scale_bank_idx = (scale_bank_idx - 1) % total_scales

    midi_bank_idx = 2
    current_scale_list = all_scales_list[scale_bank_idx][1] # maj, min, etc. item 0 is the name.
    if scale_bank_idx == 0: #special handling for chromatic.
        current_midi_notes = current_scale_list[0][1][midi_bank_idx]
    else:
        current_midi_notes = current_scale_list[rootnote_idx][1][midi_bank_idx] # item 0 is c,d,etc.
    if DEBUG_MODE:
        print(f"current midi notes: {current_midi_notes}")
    if DEBUG_MODE:
        debug.add_debug_line("Current Scale",get_scale_display_text())
    if display_text:
        display_text_middle(get_scale_display_text())

def chg_root(upOrDown=True,display_text = True):
    global scale_bank_idx
    global rootnote_idx
    global midi_bank_idx
    global current_midi_notes

    if scale_bank_idx == 0: #doesnt make sense for chromatic.
        return

    if upOrDown:
        rootnote_idx = (rootnote_idx + 1) % NUM_ROOTS
    else:
        rootnote_idx = (rootnote_idx - 1) % NUM_ROOTS

    current_midi_notes = current_scale_list[rootnote_idx][1][midi_bank_idx] # item 0 is c,d,etc.
    if DEBUG_MODE:
        print(f"current midi notes: {current_midi_notes}")
    if DEBUG_MODE:
        debug.add_debug_line("Current Scale",get_scale_display_text())
    if display_text:
        display_text_middle(get_scale_display_text())

# External use - by Menu object to print to screen
def get_scale_display_text():

    if scale_bank_idx == 0: #special handling for chromatic
        disp_text = "Scale: Chromatic"
    else:
        scale_name = all_scales_list[scale_bank_idx][0]
        root_name = current_scale_list[rootnote_idx][0]
        disp_text = [f"Scale: {root_name} {scale_name}",
                    "",
                    f"       {rootnote_idx+1}/{NUM_ROOTS}     {scale_bank_idx+1}/{NUM_SCALES}",]
    return disp_text

# display = should it print to display
def chg_midi_bank(upOrDown = True, display_text=True):
    global midi_bank_idx
    global current_midi_notes

    if scale_bank_idx == 0:
        current_midibank_set = current_scale_list[0][1] # chromatic is special
    else:
        current_midibank_set = current_scale_list[rootnote_idx][1]

    if upOrDown is True and midi_bank_idx < (len(current_midibank_set) - 1):
        clear_all_notes()
        midi_bank_idx = midi_bank_idx + 1

    if upOrDown is False and midi_bank_idx > 0:
        clear_all_notes()
        midi_bank_idx = midi_bank_idx - 1

    current_midi_notes = current_midibank_set[midi_bank_idx] # Dont let notes get stuck on

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
    disp_text = f"Bank: {midi_bank_idx}"
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
        midi.send(NoteOff(note, 1))

    if midi_mode == "aux" or midi_mode == "all":
        aux_midi.send(NoteOff(note, 1))

# Send an off message to ALL notes. Use for panic, or to make sure nothing is stuck on.
def clear_all_notes():
    for i in range(127):
        send_midi_note_off(i)

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
# Play Modes: standard, encoder (turn to play notes), chord (create chords and play)
def double_click_func_btn():
    global play_mode

    if play_mode == "standard":
        play_mode = "encoder"
    elif play_mode == "encoder":
        play_mode = "chord"
    elif play_mode == "chord":
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
    global current_scale_list
    current_scale_list = all_scales_list[scale_bank_idx][1]