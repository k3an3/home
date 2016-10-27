#!/usr/bin/env python3
from time import sleep
import random
import threading
import os
import sys

sys.path.append(os.path.dirname('../'))

from home.iot.bulb import Bulb


b = Bulb(host='172.16.42.201')
b2 = Bulb(host='172.16.42.203')

reg_color = [0, 0, 0, 255]
reg_brightness = 100

threading.Thread(target=b.change_color,
              args=(*reg_color, reg_brightness)).start()
threading.Thread(target=b2.change_color,
        args=(*reg_color, reg_brightness)).start()

while True:
    sleep(random.randint(30, 240))
    for i in range(random.randint(1, 7)):
        sleep(random.randint(0, 200) / 1000)
        threading.Thread(target=b.change_color, args=(*reg_color,
                0)).start()
        threading.Thread(target=b2.change_color,
                args=(*reg_color, 0)).start()
        sleep(random.randint(100, 300) / 1000)
        threading.Thread(target=b.change_color,
                      args=(*reg_color, reg_brightness)).start()
        threading.Thread(target=b2.change_color,
                args=(*reg_color, reg_brightness)).start()
