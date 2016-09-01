#!/usr/bin/env python3
"""
motion.py
~~~~~~~~~

Script to be called from the motion daemon when a motion event begins
or ends. Sends a request to the security controller's command HTTP API.

Usage: ./motion.py <camera_key> <start_or_end>
"""
import requests
import sys

CONTROLLER_URL = "http://localhost:5000/api/command"

if len(sys.argv) < 3 or sys.argv[2] not in ['start', 'end']:
    print("Usage: ./motion.py <camera_key> <start_or_end>")
    sys.exit(0)

data = {
    'device': sys.argv[1],
    'command': 'event' + sys.argv[2],
}

requests.post(CONTROLLER_URL, data=data)
