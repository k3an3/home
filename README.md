# home
A python3.5+ home automation system. Supports dynamic module loading so that any device or integration can be added. Uses Flask for the web frontend and RESTful API.

The application is in the early stages and is under rapid development. APIs may change without warning. I can't recommend that anyone use it but myself.

## Install
For dev:
```
$ pyvenv-3.x env
$ . env/bin/activate
$ pip install -r requirements.txt --no-deps
$ vim home/settings_local.py # Do local configuration
$ cp example-config.yml config.yml # Set up devices
$ ./run.py
```
For production:
```
# python3 setup.py install
### Configure nginx/apache to reverse proxy
$ sudo cp scripts/systemd/* /etc/systemd/system # Edit path to install dir in both files
$ sudo systemctl start home
```
