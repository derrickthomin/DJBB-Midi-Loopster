import json
import os
from debug import DEBUG_MODE

FILENAME = "\loopster_settings.json"
DEFAULT_SETTINGS = {

    # MIDI
    'DEFAULT_MIDIBANK_IDX': 3,
    'MIDI_CHANNEL': 0,  
    'MIDI_NOTES_DEFAULT': [36 + i for i in range(16)],  # 36 = C1
    # LOOPER
    'MIDI_NOTES_LIMIT': 50,
    # MENUS / NAVIGATION
    'NAV_BUTTONS_POLL_S': 1,
    'BUTTON_HOLD_THRESH_S': 0.100,  # If held for this long, it counts as "holding" or a long hold.
    'DBL_PRESS_THRESH_S': 0.4,
    # DISPLAY 
    'NOTIFICATION_THRESH_S': 2,
    'DISPLAY_NOTIFICATION_METERING_THRESH': 0.08, 
}
SETTINGS = DEFAULT_SETTINGS # Set default, then override based on loopster_settings.json            
settings_from_file = ""

if DEBUG_MODE:
    print("------------ Settings File Related -------------.") #

# Open the settings json file that exists, or that we just made
try:
    with open(FILENAME, 'r') as json_file:
        settings_from_file = json.load(json_file)
    
    # Replace defaults with stuff from the .json file, if it exists.
    if len(settings_from_file) > 0:
        for key,item in DEFAULT_SETTINGS.items():   
            if key in settings_from_file:
                SETTINGS[key] = settings_from_file[key]
except:
    if DEBUG_MODE:
        print(f"File '{FILENAME}' not found.")

if DEBUG_MODE:
    print(f"\n\n{settings_from_file}\n\n")
