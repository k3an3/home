#!/usr/bin/env python3
"""
leds.py
~~~~~~~

Module to handle 4 RGBW LEDs and 5-pin RGBW LED strips.

Requires gpiozero and a Raspberry Pi.
"""
import sys

from gpiozero import RGBLED, PWMLED

# Default pin outputs (determined arbitrarily):
RED_PIN = 4
GREEN_PIN = 17
BLUE_PIN = 22
WHITE_PIN = 18
# End defaults

class gpioLEDstrip:
    """
    A class representing a 5-pin RGBW LED strip.
    """
    def __init__(self, red=RED_PIN, green=GREEN_PIN, blue=BLUE_PIN, white=WHITE_PIN):
        """
        Initializer with default pins for each color.
        """
        # This next line or two requires a version of gpiozero newer
        # than May 8 2016, which was when something happened.
        # Without this, it will complain about the pins
        # not supporting pwm. We also don't want to disable pwm,
        # because that prevents us from setting the brightness.
        self.rgb = RGBLED(red=red, green=green, blue=blue)
        self.white = PWMLED(white)

    def change_color(self, red=0, green=0, blue=0, white=0):
        """
        Given RGBW values, changes the color of the LEDs.
        """
        self.rgb.color = (red / 255, green / 255, blue / 255)
        self.white.value = white / 255


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit('Nope')
    colors = list(map(lambda x: int(x), sys.argv[1:]))
    print(colors)
    l = gpioLEDstrip()
    l.change_color(*colors)
