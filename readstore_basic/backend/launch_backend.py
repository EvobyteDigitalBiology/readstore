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
import argparse

def setup_argument_parser():
    """Set up argument parser for the launch_backend script.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Launch ReadStore backend with optional user creation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--create-default-user-with-password',
        type=str,
        metavar='PASSWORD',
        help='Create a default user with the specified password. Environment variable DEFAULT_USER_PWD overrides this.'
    )
    
    parser.add_argument(
        '--create-admin-user-with-password', 
        type=str,
        metavar='PASSWORD',
        help='Create an admin user with the specified password. Environment variable ADMIN_USER_PWD overrides this.'
    )
    
    parser.add_argument(
        '--rs-config-path',
        type=str,
        metavar='PATH',
        help='Path to ReadStore config file. Environment variable RS_CONFIG_PATH overrides this.'
    )
    
    parser.add_argument(
        '--rs-key-path',
        type=str,
        metavar='PATH',
        help='Path to ReadStore secret key file. Environment variable RS_KEY_PATH overrides this.'
    )
    
    parser.add_argument(
        '--create-examples-with-default-user',
        action='store_true',
        help='Create example project and dataset.'
    )
    
    return parser

# Parse command line arguments
parser = setup_argument_parser()
args = parser.parse_args()

# Handle RS_CONFIG_PATH
if args.rs_config_path:
    config_path_from_arg = args.rs_config_path
    # Check for environment variable override
    if 'RS_CONFIG_PATH' in os.environ:
        print('Found RS_CONFIG_PATH in Environment Variables - using environment variable')
        RS_CONFIG_PATH = os.environ['RS_CONFIG_PATH']
    else:
        print(f'Setting RS_CONFIG_PATH from argument: {config_path_from_arg}')
        os.environ['RS_CONFIG_PATH'] = config_path_from_arg
        RS_CONFIG_PATH = config_path_from_arg
else:
    # Use existing logic
    if not 'RS_CONFIG_PATH' in os.environ:
        raise ValueError("RS_CONFIG_PATH not found in environment variables")
    else:
        RS_CONFIG_PATH = os.environ['RS_CONFIG_PATH']

# Handle RS_KEY_PATH
if args.rs_key_path:
    key_path_from_arg = args.rs_key_path
    # Check for environment variable override
    if 'RS_KEY_PATH' in os.environ:
        print('Found RS_KEY_PATH in Environment Variables - using environment variable')
    else:
        print(f'Setting RS_KEY_PATH from argument: {key_path_from_arg}')
        os.environ['RS_KEY_PATH'] = key_path_from_arg

# Load config
assert os.path.exists(RS_CONFIG_PATH), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

with open(RS_CONFIG_PATH, "r") as f:
    rs_config = yaml.safe_load(f)

# Set DJANGO SETTINGS module env if not set
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    print('DJANGO_SETTINGS_MODULE not found in environment variables - setting it to readstore_basic.settings')
    os.environ['DJANGO_SETTINGS_MODULE'] = rs_config['django']['django_settings_module']

DB_PATH = rs_config['django']['db_path']
PYTHON_EXEC = rs_config['django']['python_exec']

# Handle user creation if requested
setup_user_cmd = [PYTHON_EXEC, 'setup_user.py']

if args.create_default_user_with_password or args.create_admin_user_with_password or args.create_examples_with_default_user:
    print('User creation or examples requested - will invoke setup_user.py')
    user_creation_needed = True
    
    # Add default user creation if requested
    if args.create_default_user_with_password:
        # Check if DEFAULT_USER_PWD environment variable is not set
        if 'DEFAULT_USER_PWD' not in os.environ:
            default_password = args.create_default_user_with_password
            setup_user_cmd.extend(['--create-default-user-with-password', default_password])
            print('Adding --create-default-user-with-password to setup_user.py command')
        else:
            print('DEFAULT_USER_PWD environment variable found - setup_user.py will use it')
    
    # Add admin user creation if requested  
    if args.create_admin_user_with_password:
        # Check if ADMIN_USER_PWD environment variable is not set
        if 'ADMIN_USER_PWD' not in os.environ:
            admin_password = args.create_admin_user_with_password
            setup_user_cmd.extend(['--create-admin-user-with-password', admin_password])
            print('Adding --create-admin-user-with-password to setup_user.py command')
        else:
            print('ADMIN_USER_PWD environment variable found - setup_user.py will use it')
    
    # Add examples creation if requested
    if args.create_examples_with_default_user:
        setup_user_cmd.append('--create-examples-with-default-user')
        print('Adding --create-examples to setup_user.py command')

# Set up the Django environment
print('Run Migrations')

subprocess.run([PYTHON_EXEC,"manage.py","makemigrations","app"])
subprocess.run([PYTHON_EXEC,"manage.py","migrate","--fake-initial"])

print('Configure Permissions and Groups')

print('Running setup_user.py')
res = subprocess.call(setup_user_cmd)

if res != 0:
    print('ERROR: Failed to setup user permissions and groups!')
    sys.exit(1)

# Change wr permission to the database owner only
os.chmod(DB_PATH, 0o600)