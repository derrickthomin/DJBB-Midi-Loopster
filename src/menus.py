import midi
import display
import looper
from debug import DEBUG_MODE

NOTIFICATION_THRESH_S = 2

class Menu:

    # Class level biz
    menus = []             # List of all menu objects created
    current_menu_idx = 0
    number_of_menus = 0    # Used in displaying which menu u are on eg. "1/4"
    current_menu = ""      # Points to current menu object
    menu_nav_mode = False  # True = controls change menus. False = controls change settings on current menu
    notification_text_title = None     # If populated, flash this on the screen temporarily
    notification_ontime = -1          # Turn off notification after so long using this timer
    cur_top_text = ""       
    prev_top_text = ""                  # Re-display this after notificaton
    cur_mid_text = ""
    prev_mid_text = ""

    def __init__(self, menu_title, 
                 primary_display_function,
                 encoder_change_function, 
                 fn_button_press_function, 
                 fn_button_dbl_press_function, 
                 fn_button_held_function,
                 fn_button_held_and_btn_click_function):
        
        self.menu_number = Menu.number_of_menus + 1
        self.menu_title = menu_title
        self.options = []
        self.current_option_idx = 0

        # Set up functions
        self.primary_display_function = primary_display_function
        self.encoder_change_function = encoder_change_function
        self.fn_button_press_function = fn_button_press_function
        self.fn_button_dbl_press_function = fn_button_dbl_press_function
        self.fn_button_held_function = fn_button_held_function
        self.fn_button_held_and_btn_click_function = fn_button_held_and_btn_click_function

        Menu.number_of_menus += 1
        Menu.menus.append(self)
        Menu.current_menu = Menu.menus[0]  # Default current menu to 0 idx
    
    # Pass in boolean for which direction to go.
    @classmethod
    def change_menu(self,upOrDown):

        if upOrDown:
            Menu.current_menu_idx += 1
        else:
            Menu.current_menu_idx -= 1
        
        # Loop around if index out of range
        if Menu.current_menu_idx < 0:
            Menu.current_menu_idx = Menu.number_of_menus - 1
        if Menu.current_menu_idx > Menu.number_of_menus - 1:
            Menu.current_menu_idx = 0
    
        # Update things based on new menu
        Menu.current_menu = Menu.menus[Menu.current_menu_idx]
        display.display_text_top(Menu.get_current_title_text())
        Menu.current_menu.display()
    
    @classmethod
    def toggle_nav_mode(self,onOrOff=None):

        if onOrOff is None:
            Menu.menu_nav_mode = not Menu.menu_nav_mode
        
        elif onOrOff == True or onOrOff == False:
            Menu.menu_nav_mode = onOrOff
    
        else:
            if DEBUG_MODE is True: print("onOrOff must be boolean or None. Doing nothing.")
            return
        
        display.toggle_menu_navmode_icon(Menu.menu_nav_mode)

    @classmethod       
    def toggle_select_button_icon(self,onOrOff):
        display.toggle_select_button_icon(onOrOff)

    # Function to add a temporary notification banner to top of screen
    @classmethod
    def display_notification(self, msg=None):

        if not msg:
            if DEBUG_MODE is True: print("No notification message passed in. Doing nothing.")
            return

        display.display_notification(msg)

    # Function to check and clear notifications from top bar if necessary
    @classmethod
    def display_clear_notifications(self):

        display.display_clear_notifications(Menu.get_current_title_text())
    
    # Call once in code.py to display the initial menu
    @classmethod
    def initialize(self):
        menu = Menu.current_menu
        menu.display()
        display.display_text_top(Menu.get_current_title_text())

    # Returns the text to display on the top of the screen
    @classmethod
    def get_current_title_text(self):
        menu = Menu.current_menu
        disp_text = f"[{menu.menu_number}/{Menu.number_of_menus}] - {menu.menu_title}"
        return disp_text
    
    # Display menu contents, as determined by the primary_display_function set in the menu.
    def display(self):
        display_text = self.primary_display_function()
        display.display_text_middle(display_text)
        return 

# ------------- Functions Used by Menus --------------- #
def voidd(x=False):
    return None

# ------------- Set up each menu ---------------------- #

"""""
Use the below template to add new  menus. Use voidd function if nothing should happen.

Template
my_new_menu = Menu("Name of Menu",                            # Title that is displayed
                     primary_display_function,                # Displays main value in middl eof screen
                     secondary_display_function,              # Displays text on btm of screen. Useful for helptext.                 
                     encoder_change_function,                 # Gets called when Encoder value changes (no other buttons held)
                     fn_button_press_function,                 # Gets called when function Button pressed
                     fn_button_dbl_press_function,         # Gets called when function btn double clicked
                     fn_button_held_function,                 # Gets called when function button is held
                     fn_button_held_and_btn_click_function)   # Gets called when fn button held, and another drumpad button is clicked.

"""
# 1) Change Midi Bank
midibank_menu = Menu("Play",
                     midi.get_midi_bank_display_text,
                     midi.chg_midi_bank,
                     voidd,
                     midi.double_click_func_btn,
                     voidd,
                     voidd)

# 2) Change Scale
scale_menu = Menu("Scale Select",
                  midi.get_scale_display_text,
                  midi.chg_scale,
                  voidd,
                  voidd,
                  voidd,
                  voidd)

# 3) Looper Settings
looper_menu = Menu("Looper Mode",
                   looper.get_loopermode_display_text,
                   voidd,
                   looper.process_select_btn_press,
                   looper.toggle_loops_playstate,
                   looper.clear_all_loops,
                   voidd)