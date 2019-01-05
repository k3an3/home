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
    scripts=['run.py'],
)
