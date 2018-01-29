"""
motion.py
~~~~~~~~~

Module to interact with Motion's HTTP API.
"""
import requests
from flask import abort, make_response
from flask_login import login_required, current_user

from home.core.models import get_device
from home.web.web import app

BASE_URL = 'http://{}:{}/{}/'


class MotionController:
    """
    Driver for interfacing with the Motion API.
    """
    widget = {
        'buttons': (
            {
                'text': 'Enable',
                'method': 'start_detection',
                'class': 'btn-success'
            },
            {
                'text': 'Disable',
                'method': 'stop_detection',
                'class': 'btn-danger'
            },
        )
    }

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
    """
    Requires nginx to be configured properly
    :param camera: 
    :return: 
    """
    try:
        camera = get_device(camera)
    except StopIteration:
        abort(404)
    if not camera.driver.klass == MotionController:
        raise NotImplementedError
    if current_user.has_permission(camera):
        response = make_response()
        response.headers['X-Accel-Redirect'] = '/stream/' + camera.name
        return response


@app.route("/security/recordings/<path:video>")
@login_required
def recordings(video):
    """
    Requires nginx to be configured properly
    :param camera: 
    :return: 
    """
    if not current_user.admin:
        abort(403)
    response = make_response()
    response.headers['X-Accel-Redirect'] = '/videos/' + video
    return response
