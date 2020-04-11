#!/usr/bin/env python3
import base64
import hmac
import json
import os
import shlex
import socket
import subprocess
import traceback
from base64 import b64decode
from datetime import datetime

BIN = '/usr/sbin/nft'


def main_loop(sock):
    while True:
        # noinspection PyBroadException
        try:
            conn, addr = sock.accept()
            print("Incoming connection from", addr)
            data, sent_signature = conn.recv(1024).split(b".")
            data = base64.b64decode(data)
            if secret:
                msg_signature = hmac.digest(secret, data, 'sha512')
                if not hmac.compare_digest(base64.b64decode(sent_signature), msg_signature):
                    print("Signature mismatch!")
                    continue
            data = json.loads(data.decode())
            if abs((datetime.fromtimestamp(data['timestamp']) - datetime.utcnow()).total_seconds()) >= 300:
                print("Timestamp expired")
                continue
            print("Got command:", data)
            if data.get('custom'):
                cmd = shlex.split("{} {}".format(BIN, data['custom']).format(saddr=data['saddr']))
            else:
                cmd = [BIN, 'insert', 'rule', *data['table'].split(),
                       data['chain'], 'ip', 'saddr', data['saddr'],
                       data['proto'], 'dport', data['dport'],
                       'counter', 'accept']
            if sudo:
                cmd.insert(0, 'sudo')
            print("Exec:", cmd)
            subprocess.run(cmd)
        except KeyboardInterrupt:
            sock.close()
        except Exception:
            print("Unhandled exception:", traceback.format_exc())


if __name__ == '__main__':
    try:
        secret = b64decode(os.environ['SECRET'].encode())
    except KeyError:
        print("No secret provided. HMAC disabled.")
    sudo = False
    if os.getuid():
        print("Using sudo")
        sudo = True
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", 51814))
    server.listen(3)
    main_loop(server)
