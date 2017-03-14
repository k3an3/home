import socket

from home.web.utils import send_to_subscribers


class Ping:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def ping(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.shutdown(2)
            s.close()
        except Exception as e:
            send_to_subscribers("Failed to ping " + self.host)
            return e
