# Create a script, which will create a virtual environment, install all the dependencies and run the app
from setuptools import setup, find_packages
import os
import subprocess

with open('requirements.txt', 'r') as f:
    DEPENDENCIES = [line.strip() for line in f.readlines()]

# Create a virtual environment
venv_dir = 'venv'
if not os.path.exists(venv_dir):
    print("Creating virtual environment...")
    subprocess.run(f'python -m venv {venv_dir}', shell=True)

# Activate the virtual environment
print("Activating virtual environment...")
activate_script = f'{venv_dir}/bin/activate' if os.name == 'posix' else f'{venv_dir}/Scripts/activate'
activate_cmd = f'source {activate_script}' if os.name == 'posix' else f'{activate_script}'
subprocess.run(activate_cmd, shell=True)

print("Installing package and dependencies...")
setup(
    name='roundtable',
    version='1.0.0',
    description='A Flask web application',
    author='Vivian Psylos',
    author_email='vpsylos@uchicago.edu',
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

print("Installation complete!")