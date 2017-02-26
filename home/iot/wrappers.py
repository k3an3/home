from shlex import quote

import paramiko


class SSH:
    def __init__(self, host, port=22, keyfile="~/.ssh/id_rsa", username="root", password=None):
        self.username = username
        self.password = password
        self.keyfile = keyfile
        self.port = port
        self.host = host
        self.ssh = paramiko.SSHClient()

    def send(self, command):
        self.ssh.connect(self.host,
                         self.port,
                         self.username,
                         self.password,
                         key_filename=self.keyfile)
        return self.ssh.exec_command(quote(command))
