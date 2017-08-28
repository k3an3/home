"""
test.py
~~~~~~~

Module for communicating with the test node.
"""
import socket
from time import sleep


class Test:
    widget = {
        'buttons': (
            {
                'text': 'Test',
                'function': 'test',
                'class': 'btn-info',
            },
        )
    }

    def __init__(self, host="localhost", port=1234):
        self.host = host
        self.port = port

    def test(self, msg="Just a test"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(msg.encode())
        s.close()

    def test_long_run(self, msg="Just a long test", interval=10):
        while True:
            self.test(msg=msg)
            sleep(interval)
