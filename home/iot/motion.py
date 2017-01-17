"""
motion.py
~~~~~~~~~

Module to interact with Motion's HTTP API.
"""
import requests


BASE_URL = 'http://{}/{}/'


class MotionController:
    def __init__(self, thread=0, host="localhost:8080"):
        self.base_url = BASE_URL.format(host, thread)

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
