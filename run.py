#!/usr/bin/env python3
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from home import settings
from home.core.parser import parse
from home.web.models import db_init
from home.web.web import socketio, app

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

db_init()
try:
    import eventlet

    eventlet.monkey_patch()
    print('Using eventlet')
    create_thread_func = lambda f: f
    start_thread_func = lambda f: eventlet.spawn(f)
except ImportError:
    try:
        import gevent
        import gevent.monkey

        gevent.monkey.patch_all()
        print('Using gevent')
        create_thread_func = lambda f: gevent.Greenlet(f)
        start_thread_func = lambda t: t.start()
    except ImportError:
        import threading

        print('Using threading')
        create_thread_func = lambda f: threading.Thread(target=f)
        start_thread_func = lambda t: t.start()

parse(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yml'))
handler = RotatingFileHandler('home.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
socketio.run(app, debug=settings.DEBUG)
