#!/usr/bin/env python3
"""
parser.py
~~~~~~~~~

Parses YAML configuration files.
"""
import os
import sys
import yaml

from home.core.models import drivers, devices, actions


def parse(config):
    with open(config) as f:
        y = yaml.load(f)
        print("Installed drivers:")
        for driver in y['installed_drivers']:
            drivers.append(driver)
        for driver in drivers:
            print(driver)
        for group in y['devices']:
            for device in y['devices'][group]:
                device.group = group
                devices.append(device)
        print("Active devices:")
        for device in devices:
            print(device)
        for action in y['actions']:
            actions.append(action)
        print("Configured actions:")
        for action in actions:
            print(action.devices)
