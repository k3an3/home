"""
unifiedremote.py
~~~~~~~~~~~~~~~~

Controls computers running the Unified Remote server.
"""
import requests

URL = 'http://{}:{}/{}'

class UnifiedRemote:
    def __init__(self, host: str, port: int = 9510, username: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.id = None

    def connect(self):
        r = requests.get(URL.format(self.host, self.port, 'client/request')).json()
        self.id = r['id']
        print(self.id)