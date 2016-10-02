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
        for driver in drivers:
            driver.setup()
            print(driver)
        for group in y['devices']:
            for device in y['devices'][group]:
                device.group = group
                devices.append(device)
        print("Active devices:")
        for device in devices:
            device.setup()
            print(device)
        for action in y['actions']:
            actions.append(action)
        print("Configured actions:")
        for action in actions:
            print(action.devices)
