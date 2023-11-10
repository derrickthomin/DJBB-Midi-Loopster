from settings import SETTINGS
import time
from debug import debug,DEBUG_MODE
import display
from midi import clear_all_notes

class MidiLoop:
    """
    A class representing a MIDI loop.

    Attributes:
        current_loop_idx (int): Index of the currently playing loop.
        loops (list): List to store all MidiLoop instances.
        current_loop_obj (MidiLoop): Reference to the current MidiLoop instance.
        loop_start_timestamp (float): Time in seconds when the loop started playing.
        total_loop_time (float): Total duration of the loop in seconds.
        current_loop_time (float): Current time position within the loop in seconds.
        loop_notes_ontime_ary (list): List to store tuples of (note, velocity, time) for notes played ON.
        loop_notes_offtime_ary (list): List to store tuples of (note, velocity, time) for notes played OFF.
        loop_notes_on_queue (list): Temporary list for notes to be played ON each loop.
        loop_notes_off_queue (list): Temporary list for notes to be played OFF each loop.
        loop_playstate (bool): Flag to indicate if the loop is currently playing.
        loop_record_state (bool): Flag to indicate if the loop is currently recording.

    Methods:
        reset_loop(): Resets the loop to start from the beginning.
        clear_loop(): Clears all recorded notes and resets loop attributes.
        loop_toggle_playstate(on_or_off=None): Toggles loop play state on or off.
        toggle_record_state(on_or_off=None): Toggles loop recording state on or off.
        add_loop_note(midi, velocity, add_or_remove): Adds a note to the loop record.
        check_new_notes(): Checks for new notes to be played based on loop position.

    """

    current_loop_idx = 0
    loops = []
    current_loop_obj = None

    def __init__(self):
        """
        Initializes a new MidiLoop instance.
        """
        MidiLoop.loops.append(self)
        self.loop_start_timestamp = 0
        self.loop_encoder_mode_timestamp = 0
        self.total_loop_time = 0
        self.current_loop_time = 0
        self.loop_notes_ontime_ary = []
        self.loop_notes_offtime_ary = []
        self.loop_notes_on_queue = []
        self.loop_notes_off_queue = []
        self.loop_playstate = False
        self.loop_record_state = False
        self.has_loop =  False   

    def reset_loop(self):
        """
        Resets the loop to start from the beginning.
        """
        self.loop_start_timestamp = time.monotonic()
        self.loop_encoder_mode_timestamp = 0
        self.loop_notes_on_queue = []
        self.loop_notes_off_queue = []

        for note in (self.loop_notes_ontime_ary):
            self.loop_notes_on_queue.append(note)
        for note in (self.loop_notes_offtime_ary):
            self.loop_notes_off_queue.append(note)

    def clear_loop(self):
        """
        Clears all recorded notes and resets loop attributes.
        """

        self.loop_notes_ontime_ary = []
        self.loop_notes_offtime_ary = []
        self.loop_notes_on_queue = []
        self.loop_notes_off_queue = []
        self.total_loop_time = 0
        self.loop_start_timestamp = 0
        self.loop_toggle_playstate(False)
        self.toggle_record_state(False)
        self.current_loop_time = 0
        self.has_loop = False

        clear_all_notes()   # Make sure nothing is caught in an on state

        display.display_notification("Loop Cleared")

    def loop_toggle_playstate(self, on_or_off=None):
        """
        Toggles loop play state on or off.

        Args:
            on_or_off (bool, optional): True to turn on, False to turn off. Default is None.

        """

        if on_or_off is True:
            self.loop_playstate = True

        elif on_or_off is False:
            self.loop_playstate = False

        else:
            self.loop_playstate = not self.loop_playstate

        self.current_loop_time = 0

        if self.loop_playstate:
            self.reset_loop()

        else:
            self.loop_start_timestamp = 0
        
        display.toggle_play_icon(self.loop_playstate)
        
        if DEBUG_MODE:
            debug.add_debug_line("Loop Playstate", self.loop_playstate)

    def toggle_record_state(self, on_or_off=None):
        """
        Toggles loop recording state on or off.

        Args:
            on_or_off (bool, optional): True to turn on, False to turn off. Default is None.
            record mode options: "Off","Play","Overdub","Extend"
        """
        if on_or_off is True:
            self.loop_record_state = True

        elif on_or_off is False:
            self.loop_record_state = False

        else:
            self.loop_record_state = not self.loop_record_state

        display.toggle_recording_icon(self.loop_record_state)

        # No existing loop. Start new timer. 
        if self.loop_record_state and not self.has_loop:
            self.loop_start_timestamp = time.monotonic()
            self.loop_toggle_playstate(True)              # Auto play only on first loop rec

        elif not self.loop_record_state and self.has_loop is False:
            self.total_loop_time = time.monotonic() - self.loop_start_timestamp
            self.has_loop = True
        

        if DEBUG_MODE: 
            debug.add_debug_line("Loop Record State", self.loop_record_state,True)

    def add_loop_note(self, midi, velocity, add_or_remove):
        """
        Adds a note to the loop record.

        About ~80 midi notes is the max until memory fails.
        ** djt maybe set a limit??

        Args:
            midi (int): MIDI note number.
            velocity (int): Velocity of the note.
            add_or_remove (bool): True to add note to the ON queue, False to add note to the OFF queue.

        """
        if not self.loop_record_state:
            if DEBUG_MODE is True: print("Not in record mode.. can't add new notes")
            return
        
        if self.loop_start_timestamp == 0:
            if DEBUG_MODE is True: print("loop not playing, cannot add")
            display.display_notification(f"Play loop to record")
            self.toggle_record_state(False)
            return

        note_time_offset = time.monotonic() - self.loop_start_timestamp
        note_data = (midi, velocity, note_time_offset)

        # Prevent memory related crashes
        if len(self.loop_notes_ontime_ary) > SETTINGS['MIDI_NOTES_LIMIT']:
            display.display_notification(f"MAX NOTES REACHED")
            self.toggle_record_state(False)
            return

        if add_or_remove:
            self.loop_notes_ontime_ary.append(note_data)
            if DEBUG_MODE:
                debug.add_debug_line(f"Num Midi notes in looper",len(self.loop_notes_ontime_ary))
        else:
            self.loop_notes_offtime_ary.append(note_data)

    def get_new_notes(self):
        """
        Checks for new notes to be played based on loop position.

        Returns:
            tuple: Tuple in the form (on_array, off_array) containing new notes to play ON and OFF.

        """
        new_notes = ([], [])
        if not self.total_loop_time > 0 or self.loop_start_timestamp == 0:
            return None

        now_time = time.monotonic()
        if now_time - self.loop_start_timestamp > self.total_loop_time:
            if DEBUG_MODE:
                print(f"self.total_loop_time: {self.total_loop_time}")
            self.reset_loop()
            return

        self.current_loop_time = time.monotonic() - self.loop_start_timestamp

        new_on_notes = []
        new_off_notes = []

        for idx, (note, vel, hit_time) in enumerate(self.loop_notes_on_queue):
            if hit_time < self.current_loop_time:
                new_on_notes.append((note, vel))
                self.loop_notes_on_queue.pop(idx)

        for idx, (note, vel, hit_time) in enumerate(self.loop_notes_off_queue):
            if hit_time < self.current_loop_time:
                new_off_notes.append((note, vel))
                self.loop_notes_off_queue.pop(idx)

        if len(new_on_notes) > 0 or len(new_off_notes) > 0:
            new_notes = (new_on_notes,new_off_notes)
            if DEBUG_MODE:
                debug.add_debug_line("New Notes Arry",new_notes)
            if DEBUG_MODE:
                debug.check_display_debug()
            return new_notes

def get_loopermode_display_text():
    disp_text = ["<- click = record ",
                 "   dbl  = st/stop",
                 "   hold = clear loop"]
    return disp_text

def update_play_rec_icons(): # Used as setup function in menu module
    display.toggle_play_icon(MidiLoop.current_loop_obj.loop_playstate)
    display.toggle_recording_icon(MidiLoop.current_loop_obj.loop_record_state)

def process_select_btn_press(): # Used in Menu setup. does what it says.
    MidiLoop.current_loop_obj.toggle_record_state()
    return

def clear_all_loops():       # Clears all playing loops
    MidiLoop.current_loop_obj.clear_loop()

def toggle_loops_playstate(): # Stop all playing loops. Also turn off recording.
    MidiLoop.current_loop_obj.loop_toggle_playstate()
    MidiLoop.current_loop_obj.toggle_record_state(False)

# DJT for now just make one...
def setup_midi_loops():
    """
    Initializes a MIDI loop and sets it as the current loop object.
    """
    _ = MidiLoop()
    MidiLoop.current_loop_obj = MidiLoop.loops[MidiLoop.current_loop_idx]