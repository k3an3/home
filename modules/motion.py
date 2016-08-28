"""
motion.py
~~~~~~~~~

Module to interact with Motion's HTTP API.
"""
import requests


# 0 is all threads, get this from somewhere else?
BASE_URL = 'http://localhost:8080/0/'


class MotionController:
    def __init__(self):
        self.base_url = BASE_URL

    def get(url):
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
