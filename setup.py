from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='home',
    version='0.9',
    packages=['home'],
    url='',
    license='MIT',
    author="Keane O'Kelley",
    author_email='keane.m.okelley@gmail.com',
    description='',
    install_requires=required,
    scripts=['run.py'],
)
