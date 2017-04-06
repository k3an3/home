"""
test.py
~~~~~~~

A fake IoT node for testing.
"""
import socket


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 1234))
    s.listen(10)
    while True:
        a, addr = s.accept()
        print("Received connection from", addr[0])
        print(a.recv(1024).decode())
        a.close()
        print('-')


if __name__ == '__main__':
    main()
