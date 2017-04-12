"""
http.py
~~~~~~~

Send arbitrary HTTP requests.
"""
import requests

TIMEOUT = 10


class HTTP:
    def get(self, url, data, headers):
        requests.get(url, params=data, headers=headers, timeout=TIMEOUT)

    def post(self, url, data, headers):
        requests.post(url, data=data, headers=headers, timeout=TIMEOUT)
