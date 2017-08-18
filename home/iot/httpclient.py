"""
http.py
~~~~~~~

Send arbitrary HTTP requests.
"""
import requests

TIMEOUT = 10


class Http:
    def get(self, url, data=None, headers=None):
        requests.get(url, params=data, headers=headers, timeout=TIMEOUT)

    def post(self, url, data=None, headers=None):
        requests.post(url, data=data, headers=headers, timeout=TIMEOUT)
