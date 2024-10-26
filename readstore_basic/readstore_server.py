#!/usr/bin/env python3  

import argparse
import os
import sys
import string
from getpass import getpass
import yaml
import subprocess
import logging
import time
import shutil
import random
import pathlib
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RS_CONFIG_PATH = os.path.join(BASE_DIR, 'readstore_server_config.yaml')

parser = argparse.ArgumentParser(
    prog='readstore_server',
    usage='%(prog)s <command> [options]',
    description="ReadStore Server",
    epilog='For help on a specific command, type "readstore <command> <subcommand> -h"')

parser.add_argument(
    '--db-directory', type=str, help='Directory for Storing ReadStore Database.', metavar='', required=True)

parser.add_argument(
    '--db-backup-directory', type=str, help='Directory for Storing ReadStore Database Backups', metavar='', required=True)

parser.add_argument(
    '--log-directory', type=str, help='Directory for Storing ReadStore Logs', metavar='', required=True)

parser.add_argument(
    '--config-directory', type=str, help='Directory for storing readstore_server_config.yaml (~/.readstore)', metavar='', default='~/.readstore')

parser.add_argument(
    '--django-port', type=int, default=8000, help='Port of Django Backend', metavar='')
parser.add_argument(
    '--streamlit-port', type=int, default=8501, help='Port of Streamlit Frontend', metavar='')
parser.add_argument(
    '--debug', action='store_true', help='Run In Debug Mode')

def _get_path(path: str):
    if '~' in path:
        return os.path.expanduser(path)
    return os.path.abspath(path)

def _is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_rs_server(db_directory: str,
                  db_backup_directory: str,
                  log_directory: str,
                  config_directory: str,
                  django_port: int,
                  streamlit_port: int,
                  debug: bool):
    """
        Run ReadStore Server
    """
    
    rs_log_path = os.path.join(log_directory, 'readstore_server.log')
    
    file_handler = logging.FileHandler(filename=rs_log_path)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s"))
    stdout_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    
    logging.basicConfig(
        level=logging.DEBUG, 
        handlers=handlers
    )
    logger = logging.getLogger('readstore_logger')
    
    logger.info('Start ReadStore Server\n')
    
    if not os.path.exists(RS_CONFIG_PATH):
        logger.error(f'ERROR: readstore_server_config.yaml not found at {RS_CONFIG_PATH}')
        return
        
    logger.info('Check Available Ports\n')
    
    if _is_port_in_use(django_port):
        logger.error(f'ERROR: Port {django_port} is already in use!')
        return
    if _is_port_in_use(streamlit_port):
        logger.error(f'ERROR: Port {streamlit_port} is already in use!')
        return
    
    # Check streamlit availability
    try:
        subprocess.check_call(['streamlit', 'version'])
    except:
        logger.error(f'ERROR: Streamlit not found in PATH!')
        return
    
    init_wd = os.getcwd()
    
    db_directory = _get_path(db_directory)
    db_backup_directory = _get_path(db_backup_directory)
    log_directory = _get_path(log_directory)
    config_directory = _get_path(config_directory)
    
    # Check permissions for db_directory and db_backup_directory
    assert os.path.isdir(db_directory), f'ERROR: db_directory {db_directory} does not exist!'
    assert os.path.isdir(db_backup_directory), f'ERROR: db_backup_directory {db_backup_directory} does not exist!'
    assert os.path.isdir(log_directory), f'ERROR: db_backup_directory {db_backup_directory} does not exist!'
    assert os.path.isdir(config_directory), f'ERROR: config_directory {config_directory} does not exist!'
    
    assert os.access(db_directory, os.W_OK), f'ERROR: db_directory {db_directory} is not writable!'
    assert os.access(db_backup_directory, os.W_OK), f'ERROR: db_backup_directory {db_backup_directory} is not writable!'
    assert os.access(log_directory, os.W_OK), f'ERROR: db_backup_directory {db_backup_directory} is not writable!'
    assert os.access(config_directory, os.W_OK), f'ERROR: config_directory {config_directory} is not writable!'
    
    assert os.access(db_directory, os.R_OK), f'ERROR: db_directory {db_directory} is not readable!'
    assert os.access(db_backup_directory, os.R_OK), f'ERROR: db_backup_directory {db_backup_directory} is not readable!'
    assert os.access(config_directory, os.R_OK), f'ERROR: config_directory {config_directory} is not writable!'
    
    logger.info(f'Prepare ReadStore Server Config')
    
    config_path = os.path.join(config_directory, 'readstore_server_config.yaml')
            
    # Check if config file exists
    if not os.path.exists(config_path):    
        # Copy over config file
        logger.info(f'Copy config file to {config_path}')
        shutil.copy(RS_CONFIG_PATH, os.path.join(config_directory, 'readstore_server_config.yaml'))
        os.chmod(config_path, 0o600)
    else:
        logger.info(f'Config file already exists at {config_path}')
    
    # Open and edit config file
    with open(config_path, "r") as f:
        rs_config = yaml.safe_load(f)
    
    rs_config['django']['gunicorn_access_logfile'] = os.path.join(log_directory, 'readstore_gunicorn_access.log')
    rs_config['django']['gunicorn_error_logfile'] = os.path.join(log_directory, 'readstore_gunicorn_error.log')
    rs_config['django']['logger_path'] = os.path.join(log_directory, 'readstore_django.log')
    
    rs_config['django']['db_path'] = os.path.join(db_directory, 'readstore_db.sqlite3')
    rs_config['django']['db_backup_dir'] = db_backup_directory
    
    rs_config['django']['port'] = django_port
    rs_config['streamlit']['port'] = streamlit_port

    # Define 
    if debug:
        rs_config['django']['django_settings_module'] = 'settings.development'
    else:
        rs_config['django']['django_settings_module'] = 'settings.production'
    
    with open(config_path, "w") as f:
        yaml.dump(rs_config, f)

    logger.info(f'Prepare Secret Key')

    secret_key_path = os.path.join(config_directory, 'server_key')
    if not os.path.exists(secret_key_path):
        logger.info(f'Create Secret Key')
        key = ''.join(random.sample(string.ascii_letters + string.digits, 50))
        with open(secret_key_path, 'w') as f:
            f.write(key)
        os.chmod(secret_key_path, 0o600)
    else:
        logger.info(f'Secret Key already exists at {secret_key_path}')
    
    
    # Export DJANGO_SETTINGS_MODULE
    os.environ['DJANGO_SETTINGS_MODULE'] = rs_config['django']['django_settings_module']
    os.environ['RS_CONFIG_PATH'] = config_path
    os.environ['RS_KEY_PATH'] = secret_key_path
    
    logger.info('Start Streamlit Frontend')
    
    os.chdir(os.path.join(init_wd, 'frontend/streamlit'))
    
    streamlist_host = rs_config['streamlit']['host']
    
    streamlit_cmd = ['streamlit',
                    'run',
                    'app.py',
                    '--server.port', str(streamlit_port),
                    '--server.address', streamlist_host,
                    '--ui.hideTopBar', 'true',
                    '--browser.gatherUsageStats', 'false',
                    '--client.toolbarMode', 'minimal',
                    '--client.showErrorDetails', 'false']
    
    st_process = subprocess.Popen(streamlit_cmd)
    
    os.chdir(init_wd)
    
    logger.info('Start Backup Process')
    
    os.chdir(os.path.join(init_wd, 'backend')) 
    # Start Django Backend
    
    logger.info('Setup Django Backend')
    launch_backend_cmd = ["python3",os.path.join('launch_backend.py')]
    launch_backend_process = subprocess.Popen(launch_backend_cmd, )
    
    launch_backend_process.wait()
    
    
    logger.info('Setup Backup')
            
    backup_cmd = ["python3",os.path.join('backup.py')]
    backup_process = subprocess.Popen(backup_cmd)
    
    logger.info('Start Django Backend Server')
    
    # Define variables for setup of custom init protocol for DB
    GUNICORN_NUM_WORKERS = rs_config['django']['gunicorn_num_workers']
    RUN_GUNICORN_LAUNCH = rs_config['django']['gunicorn_run']
    HOST = rs_config['django']['host']
    PORT = str(rs_config['django']['port'])
    GUNICORN_ACCESS_LOG = rs_config['django']['gunicorn_access_logfile']
    GUNICORN_ERROR_LOG = rs_config['django']['gunicorn_error_logfile']
    
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
        
    django_process = subprocess.Popen(django_cmd)

    
    os.chdir(init_wd)
    
    try:
        backup_process.wait()
        st_process.wait()
        django_process.wait()
        
        os.environ['RS_CONFIG_PATH'] = ''
        os.environ['RS_KEY_PATH'] = ''
        
        
    except KeyboardInterrupt:
        st_process.terminate()
        backup_process.terminate()
        django_process.terminate()
        
        os.environ['RS_CONFIG_PATH'] = ''
        os.environ['RS_KEY_PATH'] = ''
        
def main():
    
    args = parser.parse_args()
    db_directory = args.db_directory
    db_backup_directory = args.db_backup_directory
    log_directory = args.log_directory
    config_directory = args.config_directory
    
    django_port = args.django_port
    streamlit_port = args.streamlit_port
    debug = args.debug
    
    # Define logger    
    run_rs_server(db_directory,
                  db_backup_directory,
                  log_directory,
                  config_directory,
                  django_port,
                  streamlit_port,
                  debug)


if __name__ == '__main__':
    main()