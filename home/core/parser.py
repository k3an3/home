#!/usr/bin/env python3
"""
parser.py
~~~~~~~~~

Parses YAML configuration files.
"""
import yaml

from home.core.models import drivers, devices, actions, interfaces


def parse(config):
    with open(config) as f:
        y = yaml.load(f)
        for interface in y['interfaces']:
            interfaces.append(interface)
        print("Installed drivers:")
        for driver in y['installed_drivers']:
            drivers.append(driver)
            driver.setup()
            print(driver)
        print("Active devices:")
        for group in y['devices']:
            for device in y['devices'][group]:
                device.group = group
                devices.append(device)
                device.setup()
        print("Configured actions:")
        for action in y['actions']:
            actions.append(action)
            print(action.devices)
