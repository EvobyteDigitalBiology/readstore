#!/usr/bin/env python3

"""
    Script launch_backend.py is the entry point for the Django application.
    It sets up the Django environment, runs migrations, and creates a
    superuser, runs a custom init script, and starts the Django application.
"""

import os
from pathlib import Path
import yaml
import subprocess
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
RS_CONFIG_PATH = BASE_DIR / "rs_config.yaml"
assert RS_CONFIG_PATH.exists(), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

def load_rs_config():
    with open(RS_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

RS_CONFIG = load_rs_config()

# Define variables for setup of custom init protocol for DB
GUNICORN_NUM_WORKERS = RS_CONFIG['django']['gunicorn_num_workers']
RUN_GUNICORN_LAUNCH = RS_CONFIG['django']['gunicorn_run']

DB_PATH = RS_CONFIG['django']['db_path']
HOST = RS_CONFIG['django']['host']
PORT = str(RS_CONFIG['django']['port'])

GUNICORN_ACCESS_LOG = RS_CONFIG['django']['gunicorn_access_logfile']
GUNICORN_ERROR_LOG = RS_CONFIG['django']['gunicorn_error_logfile']

# Set up the Django environment
print('Run Migrations')

subprocess.run(["python3","manage.py","makemigrations","app"])
subprocess.run(["python3","manage.py","migrate","--fake-initial"])

print('Configure Permissions and Groups')
res = subprocess.call(["python3",os.path.join('setup_user.py')])

if res != 0:
    print('ERROR: Failed to setup user permissions and groups!')
    sys.exit(1)

# Change wr permission to the database owner only
os.chmod(DB_PATH, 0o600)

# Run custom init script locally
if RUN_GUNICORN_LAUNCH:
    print('Run Django Backend Gunicorn Launch')
    django_cmd = ["gunicorn",
                    "backend.wsgi:application",
                    "--bind",
                    HOST+":"+str(PORT),
                    "--workers",
                    str(GUNICORN_NUM_WORKERS),
                    "--access-logfile",GUNICORN_ACCESS_LOG,
                    "--error-logfile",GUNICORN_ERROR_LOG]
else:
    print('Run Django Backend in Debug Mode')
    django_cmd = ["python3",
                'manage.py',
                "runserver",
                HOST+":"+str(PORT)]
    
subprocess.run(django_cmd)
