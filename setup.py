# Create a script, which will create a virtual environment, install all the dependencies and run the app
from setuptools import setup, find_packages
import os
import subprocess

with open('requirements.txt', 'r') as f:
    DEPENDENCIES = [line.strip() for line in f.readlines()]

# Create a virtual environment
venv_dir = './venv'
if not os.path.exists(venv_dir):
    print("Creating virtual environment...")
    subprocess.run(f'python -m venv {venv_dir}', shell=True, cwd=os.path.abspath('.'))

# Activate the virtual environment
print("Activating virtual environment...")
activate_script = f'{venv_dir}/bin/activate' if os.name == 'posix' else f'{venv_dir}/Scripts/activate'
activate_cmd = f'source {activate_script}' if os.name == 'posix' else f'{activate_script}'
subprocess.run(activate_cmd, shell=True)

print("Installing dependencies...")
subprocess.run('pip install -r requirements.txt', shell=True)

print("Installation complete!")