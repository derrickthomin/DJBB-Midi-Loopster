import board
import digitalio
import rotaryio
import midi
from debug import DEBUG_MODE
from midi import (get_midi_velocity_by_idx,
                       set_midi_velocity_by_idx,
                       get_midi_note_by_idx,
                       get_midi_velocity_singlenote_by_idx,
                       get_midi_note_name_text)
#from display import Menu
from menus import Menu
from time import monotonic
from display import display_notification


# Constants djt - move this to some file
BUTTON_HOLD_THRESH_S = 0.100       # If held for this long, it counts as "holding" or a long hold.
DBL_PRESS_THRESH_S = 0.4
ENCODER_MODE_DURATION_S = 0.25     # Wait this long before sending off msg.
encoder_pos_now = 0
encoder_delta = 0                  # Track change in encoder. Reset to 0 at end of loop (after processing)
current_assignment_velocity = 0    # use when setting velocity for notess

# State Tracking
note_states = [False] * 16         # Keep track of if we are sending a midi note or not
button_states = [False] * 16       # Keep track of the state of the button - may not want to send MIDI on a press
button_press_start_times = [None] * 16
button_held = [False] * 16
new_press = [False] * 16           # Track when a new btn press.
new_release = [False] * 16         # and release
button_holdtimes_s = [0] * 16
encoder_mode_ontimes = []
select_button_starttime = 0
select_button_holdtime_s = 0
select_button_held = False
select_button_dbl_press = False
select_button_dbl_press_time = 0
select_button_state = False
encoder_button_state = False
encoder_button_starttime = 0
encoder_button_holdtime = 0
encoder_button_held = False
new_notes_on = []               # Set when new midi note should send. Clear after sending. tuple: (note, velocity)
new_notes_off = []              # Set when a new note off message should go. int: midi note val
singlehit_velocity_btn_midi = None       # In this mode, 1 midi note is mapped to 16 diff velocities
any_pad_held = False

# Pin Setup
DRUMPAD_BTN_PINS = [board.GP12, board.GP13, board.GP14, board.GP15,
                    board.GP8, board.GP9, board.GP10, board.GP11, board.GP4,
                    board.GP5, board.GP6, board.GP7, board.GP0, board.GP1, board.GP2, board.GP3]

SELECT_BTN_PIN = board.GP22
ENCODER_BTN_PIN = board.GP28
ENCODER_CLK_PIN = board.GP27
ENCODER_DT_PIN = board.GP26

select_button = digitalio.DigitalInOut(SELECT_BTN_PIN)
encoder_button = digitalio.DigitalInOut(ENCODER_BTN_PIN)
encoder = rotaryio.IncrementalEncoder(ENCODER_DT_PIN, ENCODER_CLK_PIN)

select_button.direction = digitalio.Direction.INPUT
select_button.pull = digitalio.Pull.DOWN
encoder_button.direction = digitalio.Direction.INPUT
encoder_button.pull = digitalio.Pull.UP

note_buttons = []

# Populate note_button array 
for pin in DRUMPAD_BTN_PINS:
    note_pin = digitalio.DigitalInOut(pin)
    note_pin.direction = digitalio.Direction.INPUT
    note_pin.pull = digitalio.Pull.DOWN
    note_buttons.append(note_pin)

def update_nav_controls():
    """
    Update the navigation control states and trigger corresponding actions based on button presses and holds.
    This function manages the state and behavior of the select button and encoder button.

    Globals Used:
    - select_button_state: Indicates if the select button is currently pressed.
    - select_button_starttime: Timestamp when the select button is pressed.
    - select_button_holdtime_s: Threshold for considering the button press as a long hold.
    - select_button_held: Flag to indicate if the select button is being held down.
    - select_button_dbl_press: Flag to indicate if the select button is double-pressed.
    - select_button_dbl_press_time: Timestamp for the last double-press event.
    - encoder_button_state: Indicates if the encoder button is currently pressed.
    - encoder_button_starttime: Timestamp when the encoder button is pressed.
    - encoder_button_holdtime: Threshold for considering the encoder button press as a long hold.
    - encoder_button_held: Flag to indicate if the encoder button is being held down.

    Actions:
    - Handles single presses, double presses, and long holds for the select button.
    - Toggles the navigation mode when the encoder button is pressed.

    Usage:
    Call this function in a loop to continuously monitor and react to button presses and holds.

    Example:
    update_nav_controls()
    """
    global select_button_state
    global select_button_starttime
    global select_button_holdtime_s
    global select_button_held
    global select_button_dbl_press
    global select_button_dbl_press_time
    global encoder_button_state
    global encoder_button_starttime
    global encoder_button_holdtime
    global encoder_button_held

    # 1.2 - Check the select button
    if select_button.value and not select_button_state:

        select_button_state = True
        select_button_starttime = monotonic()
        select_button_dbl_press = False  # Reset double press flag

        # Check for a double press
        if (select_button_starttime - select_button_dbl_press_time < DBL_PRESS_THRESH_S) and not select_button_dbl_press:
            select_button_dbl_press = True
            select_button_dbl_press_time = 0
            Menu.current_menu.fn_button_dbl_press_function()
        else:
            select_button_dbl_press = False
            select_button_dbl_press_time = 0
            if DEBUG_MODE:
                print("New Sel Btn Press!!!")
            Menu.current_menu.fn_button_press_function()

    if select_button_state and (monotonic() - select_button_starttime) > BUTTON_HOLD_THRESH_S and not select_button_held:
        select_button_held = True
        select_button_dbl_press = False  # Reset double press flag

        # Display updates
        Menu.toggle_select_button_icon(True)
        Menu.current_menu.fn_button_held_function()
        if DEBUG_MODE:
            print("Select Button Held")

    if not select_button.value and select_button_state:
        select_button_held = False
        select_button_state = False
        select_button_dbl_press_time = monotonic()  # Reference for next press to check for a double press
        select_button_starttime = 0

        # Display
        Menu.toggle_select_button_icon(False)

    # 1.3 - Check the encoder button
    if not encoder_button.value and not encoder_button_state:
        encoder_button_state = True
        Menu.toggle_nav_mode()
        encoder_button_starttime = monotonic()
        if DEBUG_MODE:
            print("New encoder Btn Press!!!")

    if encoder_button_state and (monotonic() - encoder_button_starttime) > BUTTON_HOLD_THRESH_S and not encoder_button_held:
        # Handle long encoder button press
        encoder_button_held = True
        if DEBUG_MODE:
            print("encoder Button Held")

    if encoder_button.value and encoder_button_state:
        encoder_button_state = False
        encoder_button_starttime = 0
        encoder_button_held = False

# - Checks and processes drumpad btn holds
# - Updates states / hold status of select and encoder buttons 
def check_inputs_slow():

    global button_states 
    global button_press_start_times 
    global button_held 
    global button_holdtimes_s 
    global encoder_button_holdtime
    global encoder_pos_now
    global any_pad_held
    global encoder_delta
    global current_assignment_velocity

    hold_count = 0

    # 1.1 - Check each drumpad button

    # Get encoder delta. Only need once per loop? Save off chg and reset.
    encoder_delta = encoder.position
    encoder.position = 0

    for i in range(16):

        delta_used = False
        # Update whether or not button is being held
        if button_states[i] is True:
            button_holdtimes_s[i] = monotonic() - button_press_start_times[i]
            if button_holdtimes_s[i] > BUTTON_HOLD_THRESH_S and button_held[i] is False:
                button_held[i] = True
                if DEBUG_MODE is True : print(f"holding {i}")

        elif button_states[i] is False:
            button_held[i] = False
            button_holdtimes_s[i] = 0
        
        # Process holds here so we don't have to do it in fast loop
        # djt - need to move this logic
        if button_held[i] is True:
            hold_count = hold_count + 1
            if any_pad_held is False:
                any_pad_held = True
                current_assignment_velocity = get_midi_velocity_by_idx(i)
            
            #print(f"encoder delta: {encoder_delta} --------- abs encoder delta: {abs(encoder_delta)}")
            if abs(encoder_delta) > 0:
                current_assignment_velocity = current_assignment_velocity + encoder_delta
                current_assignment_velocity = min(current_assignment_velocity,127) # Make sure its valid midi (0 - 127)
                current_assignment_velocity = max(current_assignment_velocity,0)
                delta_used = True

                if midi.play_mode == "standard" and Menu.current_menu_idx == 0:
                    set_midi_velocity_by_idx(i,current_assignment_velocity)
                    display_notification(f"velocity: {current_assignment_velocity}")

    if delta_used is True:
        encoder_delta = 0 # **djt mayyybbe use a "did you use the delta" check and not chg this so often. maybe.

    # No pads held, reset global flag
    if hold_count == 0 and any_pad_held is True:
        any_pad_held = False
        encoder_delta = 0

    update_nav_controls() # select button, encoder 

    # Update encoder if not in drumpad mode w held btn
    if any_pad_held is True:
        return

    enc_direction = None 
    if encoder_delta > 0:
        enc_direction = True
    elif encoder_delta < 0:
        enc_direction = False

    if enc_direction is None: # no change, bail
        return
    
    # 1. We are in nav mode, do nav stuff
    if Menu.menu_nav_mode is True:
        Menu.change_menu(enc_direction)
        return

    # 2. Not in nav mode, do stuff depending on setting
    else:
        Menu.current_menu.encoder_change_function(enc_direction)

# - Checks for new presses and releases
def check_inputs_fast():
    global note_states 
    global button_states 
    global new_press
    global new_release
    global button_press_start_times 

    for i in range(16):
        button = note_buttons[i]
        new_press[i] = False
        new_release[i] = False

        #  Register New Press
        if button.value and button_states[i] is False:
            button_states[i] = True
            new_press[i] = True
            button_press_start_times[i] = monotonic()

        #  Register New Release
        if not button.value:
            if button_states[i] is True:
                new_release[i] = True
                button_states[i] = False
                button_press_start_times[i] = 0
    return

# - Processes new presses and releases of drumpad buttons
# - Populates new notes and new releases array if needed.
def process_inputs_fast():
    global new_press
    global new_release
    global new_notes_on
    global new_notes_off
    global singlehit_velocity_btn_midi
    global encoder_mode_ontimes
    global any_pad_held
    global encoder_delta

    new_notes_on = []                 
    new_notes_off = []

    # so domething special if select button is held - no midi sent
    if select_button_held:
        for i in range(16):
            if new_press[i]:
                if singlehit_velocity_btn_midi is not None: 
                    singlehit_velocity_btn_midi = None
                    Menu.display_notification(f"Single Note Mode: OFF")
                else:
                    singlehit_velocity_btn_midi = get_midi_note_by_idx(i)
                    Menu.display_notification(f"Pads mapped to: {get_midi_note_name_text(singlehit_velocity_btn_midi)}")
        return

    # Do something spcial if encoder button is held ** DJT commnet below to delete encoder hold
    if encoder_button_held:
        return

    # In this mode, add directly to note queue with new encoder turns
    if midi.play_mode is "encoder" and any_pad_held is True:

        for i in range(16):
            if button_held[i] is True:
                if encoder_delta < 0:
                    note = get_midi_note_by_idx(i)

                    if singlehit_velocity_btn_midi:
                        note = singlehit_velocity_btn_midi

                    for note in midi.current_midi_notes:
                        new_notes_off.append((note, 0))

                if encoder_delta > 0:
                    note = get_midi_note_by_idx(i)
                    if singlehit_velocity_btn_midi:
                        note = singlehit_velocity_btn_midi
                    velocity = get_midi_velocity_by_idx(i)
                    new_notes_off.append((note, 0))  # Clear previous before starting new. 
                    new_notes_on.append((note, velocity))

    # else: # normal mode 
    for i in range(16):

        if not (new_press[i] or new_release[i]):
            continue

        note = None
        velocity = None

        # Set up midi note and vel based on mode
        if singlehit_velocity_btn_midi is not None:
            note = singlehit_velocity_btn_midi
            velocity = get_midi_velocity_singlenote_by_idx(i)
        else:
            note = get_midi_note_by_idx(i)
            velocity = get_midi_velocity_by_idx(i)

        if new_press[i]:
            new_notes_on.append((note, velocity))
            if DEBUG_MODE is True : print(f"new press on {i}")
        
        if new_release[i]:
            new_notes_off.append((note, 127))