#!/usr/bin/env python3
import os
import random
import sys
import threading
from time import sleep

from bulb import Bulb


b = Bulb(host='192.168.4.170')

reg_color = [0, 0, 0, 255]
reg_brightness = 100

threading.Thread(target=b.change_color,
                 args=(*reg_color, reg_brightness)).start()

while True:
    sleep(random.randint(4, 5))
    for i in range(random.randint(1, 7)):
        sleep(random.randint(0, 200) / 1000)
        threading.Thread(target=b.change_color,
                         args=(*reg_color, 0)).start()
        sleep(random.randint(100, 300) / 1000)
        threading.Thread(target=b.change_color,
                         args=(*reg_color, reg_brightness)).start()
