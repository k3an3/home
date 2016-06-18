# leds.py
# Support for 4 RGBW leds or 5-pin RGBW LED strips
# requires gpiozero and raspberry pi
#
# Outputs (determined arbitrarily):
# 4  - red
# 17 - green
# 22 - blue
# 18 - white
from gpiozero import RGBLED, LED
