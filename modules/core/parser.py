#!/usr/bin/env python3
"""
parser.py
~~~~~~~~~

Parses YAML configuration files.
"""
import os
import sys
import yaml

# TODO: remove
sys.path.append(os.path.dirname("/home/keane/dev/home/modules"))

from modules.core.models import installed_devices, installed_sensors, devices, sensors

# TODO: user specified config
with open('../../config.yml') as f:
    y = yaml.load(f)
    print("Installed device drivers:")
    for device in installed_devices:
        print(device)
    print("Installed sensor drivers:")
    for sensor in installed_sensors:
        print(sensor)
    for group in y['devices']:
        for device in y['devices'][group]:
            if 'Device' in type(device).__name__:
                devices.append(device)
            elif 'Sensor' in type(device).__name__:
                sensors.append(device)
            else:
                print(type(device))
    print("Active devices:")
    for device in devices:
        print(device)
    for sensor in sensors:
        print(sensor)
