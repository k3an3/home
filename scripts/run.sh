#!/bin/bash

cd /app
celery multi start -c 10 -A home.core.tasks.queue
./run.py
