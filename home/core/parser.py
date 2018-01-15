#!/usr/bin/env python3
"""
parser.py
~~~~~~~~~

Parses YAML configuration files.
"""
import yaml

from home.core.models import drivers, devices, actions, interfaces, add_scheduled_job, widgets, get_action, \
    WidgetSetupError, displays
from home.core.utils import clear_scheduled_jobs


def parse(file: str = None, data: str = None):
    """
    Load device config from a YAML file or blob.
    :param file: File to parse
    :param data: YAML text to parse
    """
    if file:
        with open(file) as f:
            d = f.read()
    else:
        d = data

    drivers.clear()
    devices.clear()
    actions.clear()
    displays.clear()
    interfaces.clear()
    widgets.clear()
    clear_scheduled_jobs()
    y = yaml.load(d)
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
    if y.get('actions'):
        for group in y['actions']:
            for action in y['actions'][group]:
                action.group = group
                actions.append(action)
                action.setup()
                print(action.devices)
    if y.get('displays'):
        for group in y['displays']:
            for display in y['displays'][group]:
                display.group = group
                displays.append(display)
    # During device setup, couldn't pair widget buttons to actions since they didn't exist yet. Here, we match up
    #  the actions and save the actual action object in the widget dict
    for w in widgets:
        wi = widgets[w]
        if wi[0] == 'action':
            try:
                act = get_action(wi[1])
                widgets[w] = (wi[0], act, wi[2], wi[3])
            except StopIteration:
                raise WidgetSetupError("Failed to find action '{}' while configuring widget".format(widgets[w][1]))
    if y.get('cron'):
        for job in y['cron']:
            add_scheduled_job(job)
