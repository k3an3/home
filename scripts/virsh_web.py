import subprocess

from flask import Flask

HOST = '0.0.0.0'
PORT = 8888
DEBUG = False

app = Flask(__name__)


@app.route("/list")
def list_vms():
    return subprocess.run(['sudo', 'virsh', 'list', '--all'], capture_output=True).stdout.decode()


@app.route("/vm/<vm>/power/<action>")
def vm_power(vm, action):
    if action in ('start', 'shutdown', 'reboot', 'suspend', 'resume'):
        subprocess.run(['sudo', 'virsh', action, vm], check=True)
        return '', 204


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
