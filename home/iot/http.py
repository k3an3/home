"""
http.py
~~~~~~~

Send arbitrary HTTP requests.
"""
import requests

TIMEOUT = 10


class Http:
    @staticmethod
    def get(url, data=None, headers=None):
        requests.get(url, params=data, headers=headers, timeout=TIMEOUT)

    @staticmethod
    def post(url, data=None, headers=None):
        requests.post(url, data=data, headers=headers, timeout=TIMEOUT)
