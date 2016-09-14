#!/usr/bin/env python3
import os
import sys

from web.main import socketio, app

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

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
socketio.run(app, debug=True)
