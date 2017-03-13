import re

import paramiko


class SSH:
    def __init__(self, host, port=22, keyfile="~/.ssh/id_rsa", username="root", password=None):
        self.username = username
        self.password = password
        self.keyfile = keyfile
        # the key can't be pickled with the CFFI proxy, so just store as plaintext
        self.pkey = paramiko.RSAKey(data=open(keyfile).read())
        self.port = port
        self.host = host
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def send(self, command: str) -> str:
        self.ssh.connect(self.host,
                         self.port,
                         self.username,
                         self.password,
                         pkey=self.pkey)
        r = self.ssh.exec_command(escape(command))[2].readlines()
        self.ssh.close()
        return r


def escape(command):
    return re.sub(r'[;&|]', '', command)
