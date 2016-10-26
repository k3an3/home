from time import sleep
import random
import threading

from bulb import Bulb


b = Bulb()
b2 = Bulb(host='172.16.42.203')

reg_color = [0, 0, 0, 255]
reg_brightness = 100

while True:
    sleep(random.randint(1, 2))
    for i in range(random.randint(1, 7)):
        sleep(random.randint(0, 200) / 1000)
        threading.Thread(target=b.change_color, args=(*reg_color,
                0)).start()#random.randint( 0, reg_brightness / 4))
        threading.Thread(target=b2.change_color, args=(*reg_color,
                0)).start()#random.randint( 0, reg_brightness / 4))
        sleep(random.randint(100, 300) / 1000)
        threading.Thread(target=b.change_color,
                      args=(*reg_color, reg_brightness))
        threading.Thread(target=b2.change_color,
                      args=(*reg_color, reg_brightness))
