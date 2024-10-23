#!/usr/bin/env python3  

import argparse
import os
import sys
import string
from getpass import getpass
import yaml
import subprocess
import logging

RS_CONFIG_PATH = 'rs_config.yaml'
    
file_handler = logging.FileHandler(filename='readstore_server.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)
#stderr_handler = logging.StreamHandler(stream=sys.stderr)
handlers = [file_handler, stdout_handler]

file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s"))
stdout_handler.setFormatter(logging.Formatter(fmt="%(message)s"))
#stderr_handler.setFormatter(logging.Formatter(fmt="%(message)s"))

logging.basicConfig(
    level=logging.DEBUG, 
    handlers=handlers
)

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
    '--django-port', type=int, default=8000, help='Port of Django Backend', metavar='')
parser.add_argument(
    '--streamlit-port', type=int, default=8501, help='Port of Streamlit Frontend', metavar='')
parser.add_argument(
    '--debug', action='store_true', help='Run In Debug Mode')

def run_rs_server(db_directory: str,
                  db_backup_directory: str,
                  django_port: int,
                  streamlit_port: int,
                  debug: bool,
                  rs_config_path: str,
                  logger: logging.Logger):
    """
        Run ReadStore Server
    """

    logger.info('Start ReadStore Server\n')
    
    with open(rs_config_path, "r") as f:
        rs_config = yaml.safe_load(f)
    
    init_wd = os.getcwd()
    
    db_directory = os.path.abspath(db_directory)
    db_backup_directory = os.path.abspath(db_backup_directory)
    
    # Check permissions for db_directory and db_backup_directory
    assert os.path.isdir(db_directory), f'ERROR: db_directory {db_directory} does not exist!'
    assert os.path.isdir(db_backup_directory), f'ERROR: db_backup_directory {db_backup_directory} does not exist!'
    
    assert os.access(db_directory, os.W_OK), f'ERROR: db_directory {db_directory} is not writable!'
    assert os.access(db_backup_directory, os.W_OK), f'ERROR: db_backup_directory {db_backup_directory} is not writable!'
    
    assert os.access(db_directory, os.R_OK), f'ERROR: db_directory {db_directory} is not readable!'
    assert os.access(db_backup_directory, os.R_OK), f'ERROR: db_backup_directory {db_backup_directory} is not readable!'
    
    logger.info('Set SECRET_KEY')
    logger.info('NOTE: SECRET_KEY must be kept secretly stored by the end user at all times since loss of the key will result in loss of data!')
    logger.info('NOTE: Keep the SECRET_KEY in a secure location and do not share it with anyone!')
    logger.info('NOTE: SECRET_KEY should be at least 50 characters long and contain a mix of letters, numbers, and special characters.\n')
    
    secret_key = getpass('Enter SECRET_KEY:')
    
    if len(secret_key) < 50:
        logger.error('ERROR: SECRET_KEY must be at least 50 characters long!')
        return
    
    os.environ['RS_SECRET_KEY'] = secret_key
    
    print('\n')
    
    rs_config['django']['db_path'] = os.path.join(db_directory, 'readstore_db.sqlite3')
    rs_config['django']['db_backup_dir'] = db_backup_directory
    
    rs_config['django']['port'] = django_port
    rs_config['streamlit']['port'] = streamlit_port
    
    if debug:
        rs_config['django']['django_settings_module'] = 'settings.development'
    else:
        rs_config['django']['django_settings_module'] = 'settings.production'
    
    with open(rs_config_path, "w") as f:
        yaml.dump(rs_config, f)

    # Start Django Backend
    logger.info('Start Django Backend')
        
    # Export DJANGO_SETTINGS_MODULE
    os.environ['DJANGO_SETTINGS_MODULE'] = rs_config['django']['django_settings_module']
    
    logger.info('Start Django Backend')
    os.chdir('backend')
    django_cmd = ["python3",os.path.join('launch_backend.py')]
    dj_server_process = subprocess.Popen(django_cmd, )
    
    logger.info('Start Backup Process')
    backup_cmd = ["python3",os.path.join('backup.py')]
    backup_process = subprocess.Popen(backup_cmd)
    
    os.chdir(init_wd)
    
    logger.info('Start Streamlit Frontend')
    
    os.chdir('frontend/streamlit')
    
    streamlist_host = rs_config['streamlit']['host']
    
    streamlit_cmd = ['streamlit',
                    'run',
                    'app.py',
                    '--server.port', str(streamlit_port),
                    '--server.address', streamlist_host,
                    '--ui.hideTopBar', 'True',
                    '--browser.gatherUsageStats', 'False',
                    '--client.toolbarMode', 'viewer',
                    '--client.showErrorDetails', 'False']
    
    st_process = subprocess.Popen(streamlit_cmd)
    
    os.chdir(init_wd)
    
    try:
        dj_server_process.wait()
        backup_process.wait()
        st_process.wait()
        
        os.environ['RS_SECRET_KEY'] = ''
        
    except KeyboardInterrupt:
        dj_server_process.terminate()
        backup_process.terminate()
        st_process.terminate()
        
        os.environ['RS_SECRET_KEY'] = ''
        

if __name__ == '__main__':

    logger = logging.getLogger('readstore_logger')
    
    if not os.path.exists(RS_CONFIG_PATH):
        logger.error(f'ERROR: rs_config.yaml not found at {RS_CONFIG_PATH}')
        sys.exit(1)
    
    args = parser.parse_args()
    db_directory = args.db_directory
    db_backup_directory = args.db_backup_directory
    django_port = args.django_port
    streamlit_port = args.streamlit_port
    debug = args.debug
    
    run_rs_server(db_directory,
                  db_backup_directory,
                  django_port,
                  streamlit_port,
                  debug,
                  RS_CONFIG_PATH,
                  logger)
