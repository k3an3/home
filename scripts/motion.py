#!/usr/bin/env python3
"""
motion.py
~~~~~~~~~

Script to be called from the motion daemon when a motion event begins
or ends. Sends a request to the security controller's command HTTP API.

Usage: ./motion.py <camera_key> <start_or_end>
"""
import sys

import requests

CONTROLLER_URL = "http://localhost:5000/api/command"

if len(sys.argv) < 3:
    print("Usage: ./motion.py <camera_key> <action>")
    sys.exit(0)

data = {
    'key': sys.argv[1],
    'action': sys.argv[2],
}

requests.post(CONTROLLER_URL, data=data)
