import json

FILENAME = "\loopster_settings.json"
DEFAULT_SETTINGS = {
    # DEBUG
    'DEBUG': False,

    # MIDI
    'PERFORMANCE_MODE': False,
    'DEFAULT_MIDIBANK_IDX': 3,
    'MIDI_CHANNEL': 0,  
    'DEFAULT_VELOCITY': 120,
    'DEFAULT_SINGLENOTE_MODE_VELOCITIES':[8,15,22,29,36,43,50,57,64,71,78,85,92,99,106,127],
    'MIDI_NOTES_DEFAULT': [36 + i for i in range(16)],  # 36 = C1

    # LOOPER
    'MIDI_NOTES_LIMIT': 50,

    # MENUS / NAVIGATION
    'STARTUP_MENU_IDX' : 0,
    'NAV_BUTTONS_POLL_S': 1,
    'BUTTON_HOLD_THRESH_S': 0.5,  # If held for this long, it counts as "holding" or a long hold.
    'DBL_PRESS_THRESH_S': 0.4,

    # DISPLAY 
    'NOTIFICATION_THRESH_S': 2,
    'DISPLAY_NOTIFICATION_METERING_THRESH': 0.08, 
}


def compile_settings():

    SETTINGS = DEFAULT_SETTINGS # Set default, then override based on loopster_settings.json            
    settings_from_file = ""

    # Open the settings json file that exists, or that we just made
    try:
        with open(FILENAME, 'r') as json_file:
            settings_from_file = json.load(json_file)
        
        # Replace defaults with stuff from the .json file, if it exists.
        if len(settings_from_file) > 0:
            for key in DEFAULT_SETTINGS:   
                if key in settings_from_file:
                    SETTINGS[key] = settings_from_file[key]

        if SETTINGS['DEBUG']:
            print("------------ Settings File Related -------------.") #
    except:
        if SETTINGS['DEBUG']:
            print(f"File '{FILENAME}' not found.")

    if SETTINGS['DEBUG']:
        print(f"\n\n{settings_from_file}\n\n")
    
    return SETTINGS

SETTINGS = compile_settings()