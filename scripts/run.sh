#!/bin/bash

cd /app
celery worker -c 10 -A home.core.tasks.queue
