#!/usr/bin/env python3
"""
parser.py
~~~~~~~~~

Parses YAML configuration files.
"""
import yaml

from home.core.models import drivers, devices, actions, interfaces, add_scheduled_job
from home.core.utils import clear_scheduled_jobs


def parse(file='config.yml', data=None):
    """
    Load device config from a YAML file or blob.
    :param file: File to parse
    :param data: TODO
    """
    with open(file) as f:
        drivers.clear()
        devices.clear()
        actions.clear()
        interfaces.clear()
        clear_scheduled_jobs()
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
                print(device)
        print("Configured actions:")
        for action in y['actions']:
            actions.append(action)
            action.setup()
            print(action.devices)
        for job in y['cron']:
            add_scheduled_job(job)
