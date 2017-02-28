import re

import paramiko


class SSH:
    def __init__(self, host, port=22, keyfile="~/.ssh/id_rsa", username="root", password=None):
        self.username = username
        self.password = password
        self.keyfile = keyfile
        self.port = port
        self.host = host
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def send(self, command: str) -> str:
        self.ssh.connect(self.host,
                         self.port,
                         self.username,
                         self.password,
                         key_filename=self.keyfile)
        r = self.ssh.exec_command(escape(command))[2].readlines()
        self.ssh.close()
        return r


def escape(command):
    return re.sub(r'[;&|]', '', command)
