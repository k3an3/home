"""
simplesocket.py
~~~~~~~~~~~~~~~

Send arbitrary network traffic.
"""
from socket import SOCK_STREAM, socket, AF_INET, SOCK_DGRAM, SHUT_RDWR

TIMEOUT = 10


class SimpleSocket:
    @staticmethod
    def tcp(host: str, port: int, message: str = "", payload: bytes = None, timeout: int = TIMEOUT):
        if message:
            payload = message.encode()
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(payload)
        s.shutdown(SHUT_RDWR)
        s.close()

    @staticmethod
    def udp(host: str, port: int, message: str = "", payload: bytes = None, timeout: int = TIMEOUT):
        if message:
            payload = message.encode()
        s = socket(AF_INET, SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(payload, (host, port))
        s.shutdown(SHUT_RDWR)
        s.close()
