# DJBB-Midi-Loopster

The Midi Loopster is a MIDI 4x4 drum pad and midi looper based on the Raspberry Pi Pico.

<img src="https://github.com/derrickthomin/DJBB-Midi-Loopster/assets/47721204/eee5f843-ab71-4f21-882a-3ed96a75d85b" width="300">


Demo:          https://www.youtube.com/watch?v=YDxO62Sy1Qc&lc=UgxtoEvjVZX9zsOcOUB4AaABAg

Build Video:   https://youtu.be/qznFqSrzPKM

## Background
I created the [DJBB Arcade Button MIDI Drumpad](https://github.com/derrickthomin/djbb-midi-box) as an experiment on how to use a Raspberry Pi Pico microcontroller as a Midi controller.

It worked pretty well but I honestly don't like the super loud arcade buttons so I never really used it. I wanted an excuse to try designing my first PCB, so I decided to go for a version two of my original design except with these changes:

- Use Cherry style key switches for the buttons (quieter but still feel nice. Also smaller)

- Uses a custom PCB for max compactness and ease of build

- Switch out controls for a function button and encoder

- Firmware re-write

  
## Components
[DigiKey List with most parts](https://www.digikey.com/en/mylists/list/QX3GPIZNYA)

Also see BOM csv in this repo



1 x DJBB Midi Loopster PCB

1 x Raspberry Pi Pico or Pico W With Headers **djt depends on wifi stuff

1 x SSD1306 OLED Screen

5 x 10k Resistors

1 x 10 Ohm Resistor

1 x 33 Ohm Resistor

17 x Cherry MX Style key switches

1 x Rotary Encoder 

1 x 3.5mm Audio Jack

3 x 10nF Capacitors

17 x Cherry style keycaps (technically optional... but you want em)

1 x 3D printed case (optional)

1 x 3D printed screen case (optional)

1 x 4 pin female large headers for screen (optional)

4 x m2.5 screws - for screen case (optional) 

4 x m3 screws - for case (optional)

## Assembly
[See my guide here](https://www.djbajablast.com/post/djbb-midi-loopster) for in depth assembly instructions.

In short:
- Solder the fn button and top left pad to the front of the board. You must do this first!! These are the top-leftmost buttons.
- Solder everything else (The pico, aux, and 2 resistors go on the back).
- Follow [Adafruit's guide](https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython?gclid=CjwKCAjw6p-oBhAYEiwAgg2PghND96Zkn-Pus4noFSVOym_cpsFfdWGF-w9weuVSVz8qTd52cKaOGBoCJ0QQAvD_BwE) for installing CircuitPython on your Pico

## Firmware Upload (use this to update as well)
- Delete everything from the Pico on your computer (should be showing up as a USB drive on your computer).
- Download and copy everything from "src" in this repo to the Pico

## Usage
See "djbb loopster manual.pdf" in this repo.

I also sell PCBs/Kits here if ya want: https://djbajablast.etsy.com

## Changelog

Nov 23
- Created loopster_settings.json file for easy default config
- Added performance mode config option
- Added looper feature - twist encoder CCW to remove a random loop note
- Added more scales
