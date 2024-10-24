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

# Load config
if not 'RS_CONFIG_PATH' in os.environ:
    raise ValueError("RS_CONFIG_PATH not found in environment variables")
else:
    RS_CONFIG_PATH = os.environ['RS_CONFIG_PATH']

assert os.path.exists(RS_CONFIG_PATH), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

with open(RS_CONFIG_PATH, "r") as f:
    rs_config = yaml.safe_load(f)


# Define variables for setup of custom init protocol for DB
GUNICORN_NUM_WORKERS = rs_config['django']['gunicorn_num_workers']
RUN_GUNICORN_LAUNCH = rs_config['django']['gunicorn_run']

DB_PATH = rs_config['django']['db_path']
HOST = rs_config['django']['host']
PORT = str(rs_config['django']['port'])

GUNICORN_ACCESS_LOG = rs_config['django']['gunicorn_access_logfile']
GUNICORN_ERROR_LOG = rs_config['django']['gunicorn_error_logfile']

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
