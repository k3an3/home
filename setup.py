import os
from shutil import copyfile

from setuptools import setup
from setuptools.command.install import install

path = os.path.dirname(os.path.realpath(__file__))
unit_dir = os.path.join(path, 'scripts', 'systemd')


class CustomInstallCommand(install):
    def run(self):
        if os.path.isdir('/etc/systemd/system'):
            for file in os.listdir(unit_dir):
                if os.path.isfile(os.path.join(unit_dir, file)) and file.endswith('.service'):
                    copyfile(os.path.join(unit_dir, file), os.path.join('/etc/systemd/system', file))
        super().run()


setup(
    name='home',
    version='0.12',
    packages=['home'],
    url='',
    license='MIT',
    author="Keane O'Kelley",
    author_email='keane.m.okelley@gmail.com',
    description='',
    dependency_links=[
        'git+git://github.com/keaneokelley/pyelliptic.git#egg=pyelliptic',
    ],
    install_requires=[
        'raven',
        'amqp',
        'appdirs',
        'APScheduler',
        'asn1crypto',
        'astral',
        'bcrypt',
        'billiard',
        'blinker',
        'broadlink==0.3',
        'celery',
        'certifi',
        'cffi',
        'chardet',
        'click',
        'cryptography',
        'cssmin',
        'ecdsa',
        'enum-compat',
        '#eventlet',
        'flake8',
        'Flask',
        'Flask-Assets',
        'Flask-Login',
        '#flask_oauthlib',
        'Flask-SocketIO',
        'future',
        'gevent',
        'gevent-websocket',
        'greenlet',
        'http-ece',
        'idna',
        'ifaddr',
        'itsdangerous',
        'Jinja2',
        'jsmin',
        'kombu',
        'ldap3',
        'logbook',
        'MarkupSafe',
        'mccabe',
        'netifaces',
        '#oauthlib',
        'packaging',
        'paramiko',
        'passlib',
        'peewee',
        'pillow',
        'protobuf',
        'pyasn1',
        'PyChromecast',
        'pycodestyle',
        'pycparser',
        'pycryptodome',
        'pyflakes',
        'pynacl',
        'python-engineio',
        'python-jose',
        'python-socketio',
        'pytz',
        'py_vapid',
        'pywebpush',
        'PyYAML',
        'qrcode',
        'redis',
        'requests',
        'six',
        'tzlocal',
        'urllib3',
        'vine',
        'wakeonlan',
        'Wave',
        'webassets',
        'websocket-client',
        'Werkzeug',
        'wheel',
        'zeroconf',
    ],
    scripts=['run.py'],
)
