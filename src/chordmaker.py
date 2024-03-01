import looper
import display

# Track chord notes. Only 16 for now. Will store loop objects.
current_chord_notes = [""] * 16

# Index of the pad currently being recorded
recording_pad_idx = ""

# Boolean flag to indicate if recording is in progress
recording = False


# Function to arm a pad for recording a chord
def assign_chord_mode_pad(pad_idx):
    """
    This function assigns a MidiLoop object of type "chord" to the pad at the given index.
    
    Args:
        pad_idx (int): The index of the pad to be armed for recording.
    """
    current_chord_notes[pad_idx] = looper.MidiLoop(loop_type="chord")
    return


# Function to assign a chord loop object to a pad, or remove it
def add_remove_chord(pad_idx):
    """
    This function either starts recording a chord if there is no chord on the pad at the given index,
    or deletes the chord if one exists.
    
    Args:
        pad_idx (int): The index of the pad to add or remove a chord from.
    """
    global current_chord_notes
    global recording_pad_idx
    global recording

    # No chord - start recording
    if current_chord_notes[pad_idx] == "":
        display.display_notification(f"Recording Chord")
        current_chord_notes[pad_idx] = looper.MidiLoop(loop_type="chord")
        current_chord_notes[pad_idx].toggle_record_state()
        recording_pad_idx = pad_idx
        recording = True

    # Chord exists - delete it
    else:
        current_chord_notes[pad_idx] = ""
        recording = False
        display.display_notification(f"Chrd Deleted on pd {pad_idx}")


# Function to stop recording loop if there is one recording.
def chordmode_fn_press_function():
    """
    This function stops the recording of a chord if one is currently being recorded.
    """
    global recording
        
    if recording:
        current_chord_notes[recording_pad_idx].toggle_record_state(False)
        current_chord_notes[recording_pad_idx].trim_silence()
        recording = False