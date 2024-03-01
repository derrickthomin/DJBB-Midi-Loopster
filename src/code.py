import time
import inputs
from settings import SETTINGS
from looper import setup_midi_loops, MidiLoop
import chordmaker
from menus import Menu
from debug import debug, DEBUG_MODE
from midi import (
    setup_midi,
    get_midi_note_name_text,
    send_midi_note_on,
    send_midi_note_off,
)
from display import check_show_display

# Initialize MIDI and other components
setup_midi()
setup_midi_loops()
Menu.initialize()

# Initialize time variables
polling_time_prev = time.monotonic()
if DEBUG_MODE:
    debug_time_prev = time.monotonic()

# Main loop
while True:
    timenow = time.monotonic()

    # Polling for navigation buttons
    if (timenow - polling_time_prev) > SETTINGS['NAV_BUTTONS_POLL_S']:
        inputs.check_inputs_slow()  # Update screen, button holds
        Menu.display_clear_notifications()
        check_show_display()
        if DEBUG_MODE:
            debug.check_display_debug()

    # Fast input processing
    inputs.check_inputs_fast()
    inputs.process_inputs_fast()

    # Send MIDI notes off 
    for note in inputs.new_notes_off:
        note_val, velocity = note
        if DEBUG_MODE:
            print(
                f"sending MIDI OFF val: {get_midi_note_name_text(note_val)} ({note_val}) vel: {velocity}"
            )
        send_midi_note_off(note_val)

        # Add note to current loop or chord if recording
        if MidiLoop.current_loop_obj.loop_record_state:
            MidiLoop.current_loop_obj.add_loop_note(note_val, velocity, False)
        if chordmaker.recording:
            chordmaker.current_chord_notes[chordmaker.recording_pad_idx].add_loop_note(note_val, velocity, False)

    # Send MIDI notes on
    for note in inputs.new_notes_on:
        note_val, velocity = note
        if DEBUG_MODE:
            print(
                f"sending MIDI ON val: {get_midi_note_name_text(note_val)} ({note_val}) vel: {velocity}"
            )
        send_midi_note_on(note_val, velocity)

        # Add note to current loop or chord if recording
        if MidiLoop.current_loop_obj.loop_record_state:
            MidiLoop.current_loop_obj.add_loop_note(note_val, velocity, True)
        if chordmaker.recording:
            chordmaker.current_chord_notes[chordmaker.recording_pad_idx].add_loop_note(note_val, velocity, True)

    # Handle loop notes if playing
    if MidiLoop.current_loop_obj.loop_playstate:
        new_notes = MidiLoop.current_loop_obj.get_new_notes()
        if new_notes:
            loop_notes_on, loop_notes_off = new_notes
            for note in loop_notes_on:
                send_midi_note_on(note[0], note[1])
            for note in loop_notes_off:
                send_midi_note_off(note[0])
 
    # Chord Mode loops
    for chord in chordmaker.current_chord_notes:
        if chord == "":
            continue
        new_notes = chord.get_new_notes() # chord is a loop object
        if new_notes:
            loop_notes_on, loop_notes_off = new_notes
            for note_val,velocity in loop_notes_on:
                send_midi_note_on(note_val, velocity)
                if MidiLoop.current_loop_obj.loop_record_state:
                    MidiLoop.current_loop_obj.add_loop_note(note_val, velocity, True)
            for note_val,velocity in loop_notes_off:
                send_midi_note_off(note_val) 
                if MidiLoop.current_loop_obj.loop_record_state:
                    MidiLoop.current_loop_obj.add_loop_note(note_val, velocity, False)