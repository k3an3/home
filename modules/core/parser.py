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

from modules.core.models import class_from_name, installed_devices, installed_sensors

# TODO: user specified config
with open('../../config.yml') as f:
    y = yaml.load(f)
    print("Installed device drivers:")
    for device in installed_devices:
        print(device)
    print("Installed sensors drivers:")
    for sensor in installed_sensors:
        print(sensor)
