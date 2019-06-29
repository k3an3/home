# home
A python3.5+ home automation system. Supports dynamic module loading so that any device or integration can be added. Uses Flask for the web frontend and RESTful API.

The application is in the early stages and is under rapid development. APIs may change without warning. I can't recommend that anyone use it but myself.

## Install
For dev:
```
$ python3.x -m venv env
$ . env/bin/activate
$ pip install -r requirements.txt --no-deps
$ pip install -e .
$ vim home/settings_local.py # Do local configuration
$ cp example-config.yml config.yml # Set up devices
$ ./run.py
```
For production:
```
# pip3 install .
# pip3 install -r requirements.txt --no-deps
### Configure nginx/apache to reverse proxy
$ sudo systemctl start home
```

Why do I have a separate command to install the requirements when this all could be done in `setup.py`? As far as I know, 
there is no way to achieve the same behavior with setuptools.

## API
IOT modules can register an HTTP endpoint at `/api/*` or a custom path, and may integrate with the app's authentication (see below). 
```python
from home.web.utils import api_auth_required
from home.web.web import app


@app.route('/api/myiotdevice', methods=['GET', 'POST'])
@api_auth_required(check_device=True)
def my_endpoint(device, client):
    # do whatever
```

The same can be performed with websockets powered by SocketIO.
```python
from home.web.utils import ws_login_required
from home.web.web import socketio


@socketio.on('do something cool')
@ws_auth_required(check_device=True)
def my_ws_endpoint(message, device):
    # do whatever
```

Valid authentication methods for passing API tokens include:
* HTTP header `X-Auth-Token`
* JSON parameter `{"key": "apikeyblah"}`
* In the parameters of a GET or POST request