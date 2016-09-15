#!/usr/bin/env python3
import os
import sys
import yaml

sys.path.append(os.path.dirname("/home/keane/dev/home/modules"))

from modules.core.models import *

with open('../../config.yml') as f:
    y = yaml.load_all(f)
    for thing in y:
        print(thing)
