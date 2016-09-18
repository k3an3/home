#!/usr/bin/env python3
"""
parser.py
~~~~~~~~~

Parses YAML configuration files.
"""
import os
import sys
import yaml

from modules.core.models import drivers, devices

# TODO: remove
sys.path.append(os.path.dirname("/home/keane/dev/home/modules"))


# TODO: user specified config
with open('../../config.yml') as f:
    y = yaml.load(f)
    print("Installed drivers:")
    for device in drivers:
        print(device)
    for group in y['devices']:
        for device in y['devices'][group]:
            devices.append(device)
    print("Active devices:")
    for device in devices:
        print(device)
