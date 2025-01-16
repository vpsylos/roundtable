# Create a script, which will create a virtual environment, install all the dependencies and run the app
from setuptools import setup, find_packages
import os

with open('requirements.txt', 'r') as f:
    DEPENDENCIES = [line.strip() for line in f.readlines()]

def create_virtualenv():
    os.system('python3 -m venv venv')
    os.system('source venv/bin/activate')
    os.system('pip install -r requirements.txt')

setup(
    name='roundtable',
    version='1.0.0',
    description='A Flask web application',
    author='Your Name',
    author_email='your@email.com',
    packages=find_packages(),
    install_requires=DEPENDENCIES,
    extras_require={
        'dev': ['python>=3.8', 'pip>=20.0.0', 'setuptools>=50.0.0', 'wheel>=0.35.0'],
    },
    entry_points={
        'console_scripts': [
            'roundtable=app:main',
        ],
    },
)

create_virtualenv()