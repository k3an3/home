"""
motion.py
~~~~~~~~~

Module to interact with Motion's HTTP API.
"""
import requests
from flask import abort, make_response
from flask_login import login_required

from home.core.models import get_device
from home.web.web import app

BASE_URL = 'http://{}:{}/{}/'


class MotionController:
    """
    Driver for interfacing with the Motion API.
    """

    def __init__(self, thread=0, host="localhost", control_port=8080, feed_port=8081):
        self.base_url = BASE_URL.format(host, control_port, thread)
        self.host = host
        self.port = feed_port

    def get(self, url):
        return requests.get(self.base_url + url)

    def set_config(self, key, value):
        return self.get('config/set?{}={}'.format(key, value))

    def get_config(self, key):
        return self.get('config/get?query={}'.format(key))

    def get_detection_status(self):
        return self.get('detection/status')

    def start_detection(self):
        return self.get('detection/start')

    def stop_detection(self):
        return self.get('detection/pause')

    def get_feed_url(self):
        return "http://{}:{}".format(self.host, self.port)


@app.route("/security/stream/<camera>/")
@login_required
def stream(camera):
    try:
        camera = get_device(camera)
    except StopIteration:
        abort(404)
    if not camera.driver.klass == MotionController:
        raise NotImplementedError
    response = make_response()
    response.headers['X-Accel-Redirect'] = '/stream/' + camera.name
    return response
