#!/usr/bin/env python3  

import argparse
import importlib.metadata
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
import base64

import pandas as pd

# Define version, check case if readstore is installed as package or run from source
try:
    from readstore_basic.__version__ import __version__
except ModuleNotFoundError:
    from __version__ import __version__


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RS_CONFIG_PATH = os.path.join(BASE_DIR, 'readstore_server_config.yaml')

parser = argparse.ArgumentParser(
    prog='readstore-server',
    usage='%(prog)s <command> [options]',
    description="ReadStore Server",
    epilog='For help on a specific command, type "readstore <command> <subcommand> -h"')

subparsers = parser.add_subparsers(title="Commands")

parser.add_argument(
    '--db-directory', type=str, help='Directory for Storing ReadStore Database (required)', metavar='')

parser.add_argument(
    '--db-backup-directory', type=str, help='Directory for Storing ReadStore Database Backups (required)', metavar='')

parser.add_argument(
    '--log-directory', type=str, help='Directory for Storing ReadStore Logs (required)', metavar='')

parser.add_argument(
    '--config-directory', type=str, help='Directory for storing readstore_server_config.yaml (~/.rs-server)', metavar='', default='~/.rs-server')

parser.add_argument(
    '--django-port', type=int, default=8000, help='Port of Django Backend', metavar='')
parser.add_argument(
    '--streamlit-port', type=int, default=8501, help='Port of Streamlit Frontend', metavar='')
parser.add_argument(
    '--debug', action='store_true', help='Run In Debug Mode')

parser.add_argument(
    '-v', '--version', action='store_true', help='Show Version Information')

export_parser = subparsers.add_parser("export",
                                      help='Export ReadStore Database',
                                      add_help=True)

export_parser.add_argument(
    '--db-directory', type=str, help='Directory containing ReadStore database (required)', metavar='')

export_parser.add_argument(
    '--config-directory', type=str, help='Directory containing ReadStore config files (required)', metavar='')

export_parser.add_argument(
    '--export_directory', type=str, help='Directory for storing exported ReadStore database files (required)', metavar='')

export_parser.set_defaults(export_run=True)


def _get_path(path: str):
    if '~' in path:
        return os.path.expanduser(path)
    return os.path.abspath(path)    

def _is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def validate_requirements():
    """Validate package requirements
    
    Check if requirements specified in requirements.txt are
    found in current python environment.
    
    Print error message if not
    """
    
    print("Validate Requirements for ReadStore Basic Server")
    
    requirements_abs = os.path.join(BASE_DIR, 'requirements.txt')
    
    if os.path.exists('requirements.txt'):
        requirements_path = 'requirements.txt'
    elif os.path.exists(requirements_abs):
        requirements_path = requirements_abs
    else:
        sys.stderr.write('ERROR: requirements.txt not found in current directory!\n')
        return False
        
    requirements = []
    with open(requirements_path, 'r') as fh:
        for line in fh:
            if '==' in line:
                package, version = line.strip().split('==')
                requirements.append((package.lower(), version))
    
    # List of installed packages
    distributions = importlib.metadata.distributions()
    
    installed_versions = {}
    for dist in distributions:
        pkg_name = dist.metadata['Name'].lower()
        pkg_version = dist.version
        
        installed_versions[pkg_name] = pkg_version
        
    # Check if all requirements are installed
    for package, version in requirements:
        if package in installed_versions:
            pkg_version = installed_versions[package]
            
            pkg_version_split = pkg_version.split('.')
            req_version_split = version.split('.')
            
            #Compare max 2 version digits
            min_len = min(len(pkg_version_split), len(req_version_split), 2)
            
            for i in range(min_len):
                # Case that package version is lower than required version
                if int(pkg_version_split[i]) < int(req_version_split[i]):
                    sys.stderr.write(f'ERROR: Package {package} version {pkg_version} is lower than required version {version}!\n')
                    return False
                elif int(pkg_version_split[i]) > int(req_version_split[i]):
                    break
                # Case that both versions are equal, continue loop, if loop ends, package version is equal to required version, OK
                else:
                    continue    
        else:
            sys.stderr.write(f'ERROR: Package {package} not found in current Python environment!\n')
            return False

    print("All package requirements found.")
    
    return True    


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
    
    # Validate paths
    db_directory = _get_path(db_directory)
    db_backup_directory = _get_path(db_backup_directory)
    log_directory = _get_path(log_directory)
    config_directory = _get_path(config_directory)
    
    if not os.path.isdir(config_directory):
        os.makedirs(config_directory, exist_ok=True)
    
    # Check permissions for db_directory and db_backup_directory
    assert os.path.isdir(db_directory), f'ERROR: db_directory {db_directory} does not exist!'
    assert os.path.isdir(db_backup_directory), f'ERROR: db_backup_directory {db_backup_directory} does not exist!'
    assert os.path.isdir(log_directory), f'ERROR: db_backup_directory {db_backup_directory} does not exist!'
    
    assert os.access(db_directory, os.W_OK), f'ERROR: db_directory {db_directory} is not writable!'
    assert os.access(db_backup_directory, os.W_OK), f'ERROR: db_backup_directory {db_backup_directory} is not writable!'
    assert os.access(log_directory, os.W_OK), f'ERROR: db_backup_directory {db_backup_directory} is not writable!'
    assert os.access(config_directory, os.W_OK), f'ERROR: config_directory {config_directory} is not writable!'
    
    assert os.access(db_directory, os.R_OK), f'ERROR: db_directory {db_directory} is not readable!'
    assert os.access(db_backup_directory, os.R_OK), f'ERROR: db_backup_directory {db_backup_directory} is not readable!'
    assert os.access(config_directory, os.R_OK), f'ERROR: config_directory {config_directory} is not writable!'
    
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
    
        # Check if st is set as ENV variable
    if 'RS_STREAMLIT' in os.environ:
        print('Found RS_STREAMLIT in Environment Variables')
        streamlist_exec = os.environ['RS_STREAMLIT']
    else:
        streamlist_exec = 'streamlit'
    
    if 'RS_PYTHON' in os.environ:
        print('Found RS_PYTHON in Environment Variables')
        python_exec = os.environ['RS_PYTHON']
    else:
        python_exec = 'python3'
    
    if 'RS_GUNICORN' in os.environ:
        print('Found RS_GUNICORN in Environment Variables')
        gunicorn_exec = os.environ['RS_GUNICORN']
    else:
        gunicorn_exec = 'gunicorn'
    
    # Check streamlit availability
    try:
        subprocess.check_call([streamlist_exec, 'version'])
    except:
        logger.error(f'ERROR: Streamlit not found in PATH!')
        return
    
    # Check python availability
    try:
        subprocess.check_call([python_exec, '--version'])
    except:
        logger.error(f'ERROR: Python not found in PATH!')
        return
    
    if not debug:
        # Check gunicorn availability
        try:
            subprocess.check_call([gunicorn_exec, '--version'])
        except:
            logger.error(f'ERROR: Gunicorn not found in PATH!')
            return
    
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

    rs_config['streamlit']['port'] = streamlit_port    
    rs_config['global']['readstore_version'] = __version__
    
    rs_config['django']['gunicorn_access_logfile'] = os.path.join(log_directory, 'readstore_gunicorn_access.log')
    rs_config['django']['gunicorn_error_logfile'] = os.path.join(log_directory, 'readstore_gunicorn_error.log')
    rs_config['django']['logger_path'] = os.path.join(log_directory, 'readstore_django.log')
    rs_config['django']['db_path'] = os.path.join(db_directory, 'readstore_db.sqlite3')
    rs_config['django']['db_backup_dir'] = db_backup_directory
    rs_config['django']['port'] = django_port
    rs_config['django']['python_exec'] = python_exec
    
    # Define 
    if debug:
        rs_config['django']['django_settings_module'] = 'settings.development'
    else:
        rs_config['django']['django_settings_module'] = 'settings.production'
    
    with open(config_path, "w") as f:
        yaml.dump(rs_config, f)

    logger.info(f'Prepare Secret Key')

    secret_key_path = os.path.join(config_directory, 'secret_key')
    if not os.path.exists(secret_key_path):
        logger.info(f'Create Secret Key')
        key = ''.join(random.sample(string.ascii_letters + string.digits, 50))
        with open(secret_key_path, 'w') as f:
            f.write(key)
        os.chmod(secret_key_path, 0o600)
    else:
        logger.info(f'Secret Key already exists at {secret_key_path}')
    
    # TODO If set already
    
    # Export DJANGO_SETTINGS_MODULE
    os.environ['DJANGO_SETTINGS_MODULE'] = rs_config['django']['django_settings_module']
    os.environ['RS_CONFIG_PATH'] = config_path
    os.environ['RS_KEY_PATH'] = secret_key_path
    
    logger.info('Start Streamlit Frontend')
    
    os.chdir(os.path.join(BASE_DIR, 'frontend/streamlit'))
    
    streamlist_host = rs_config['streamlit']['host']

    streamlit_cmd = [streamlist_exec,
                    'run',
                    'app.py',
                    '--server.port', str(streamlit_port),
                    '--server.address', streamlist_host,
                    '--ui.hideTopBar', 'true',
                    '--browser.gatherUsageStats', 'false',
                    '--client.toolbarMode', 'minimal',
                    '--client.showErrorDetails', 'false']
    
    st_process = subprocess.Popen(streamlit_cmd)
    
    os.chdir(BASE_DIR)
    
    logger.info('Start Backup Process')
    
    os.chdir(os.path.join(BASE_DIR, 'backend')) 
    # Start Django Backend
    
    logger.info('Setup Django Backend')
    launch_backend_cmd = [python_exec,os.path.join('launch_backend.py')]
    launch_backend_process = subprocess.Popen(launch_backend_cmd, )
    
    launch_backend_process.wait()
    
    logger.info('Setup Backup')
            
    backup_cmd = [python_exec,os.path.join('backup.py')]
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
        django_cmd = [gunicorn_exec,
                        "backend.wsgi:application",
                        "--bind",
                        HOST+":"+str(PORT),
                        "--workers",
                        str(GUNICORN_NUM_WORKERS),
                        "--access-logfile",GUNICORN_ACCESS_LOG,
                        "--error-logfile",GUNICORN_ERROR_LOG]
    else:
        print('Run Django Backend in Debug Mode')
        django_cmd = [python_exec,
                    'manage.py',
                    "runserver",
                    HOST+":"+str(PORT)]
    
    django_process = subprocess.Popen(django_cmd)

    os.chdir(BASE_DIR)
    
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
        
        
def run_db_export(db_directory: str,
                  config_directory: str,
                  export_directory: str):
    """
        Run ReadStore Server
    """
    
    print("Run DB Export")
    
    # Validate paths
    db_directory = _get_path(db_directory)
    config_directory = _get_path(config_directory)
    export_directory = _get_path(export_directory)
    
    # Check permissions for db_directory and db_backup_directory
    assert os.path.isdir(db_directory), f'ERROR: db_directory {db_directory} does not exist!'
    assert os.path.isdir(export_directory), f'ERROR: db_backup_directory {export_directory} does not exist!'
    
    assert os.access(db_directory, os.W_OK), f'ERROR: db_directory {db_directory} is not writable!'
    assert os.access(export_directory, os.W_OK), f'ERROR: db_backup_directory {export_directory} is not writable!'
    
    assert os.access(db_directory, os.R_OK), f'ERROR: db_directory {db_directory} is not readable!'
    assert os.access(export_directory, os.R_OK), f'ERROR: db_backup_directory {export_directory} is not readable!'
    assert os.access(config_directory, os.R_OK), f'ERROR: config_directory {config_directory} is not readable!'
    
    
    if 'RS_PYTHON' in os.environ:
        print('Found RS_PYTHON in Environment Variables')
        python_exec = os.environ['RS_PYTHON']
    else:
        python_exec = 'python3'
    
    # Check python availability
    try:
        subprocess.check_call([python_exec, '--version'])
    except:
        print(f'ERROR: Python not found in PATH!')
        return
    
    config_path = os.path.join(config_directory, 'readstore_server_config.yaml')
    secret_key_path = os.path.join(config_directory, 'secret_key')
    
    # Open and edit config file
    print(f'Load Config File {config_path}')
    with open(config_path, "r") as f:
        rs_config = yaml.safe_load(f)

    os.environ['DJANGO_SETTINGS_MODULE'] = rs_config['django']['django_settings_module']
    os.environ['RS_CONFIG_PATH'] = config_path
    os.environ['RS_KEY_PATH'] = secret_key_path
    
    # Dump files to json

    dump_table_names = ['app.project',
                        'app.fqdataset',
                        'app.fqfile',
                        'app.prodata',
                        'app.fqattachment',
                        'app.projectattachment']
    
    backend_dir = os.path.join(BASE_DIR, 'backend')
    os.chdir(backend_dir)
    
    for table_name in dump_table_names:
        print(f'Dump Table {table_name}')
        export_filename = table_name.replace('.','_') + '.json'
        export_path = os.path.join(export_directory, export_filename)
        export_cmd = [python_exec,'manage.py','dumpdata','--output',export_path,table_name]
        export_process = subprocess.Popen(export_cmd)
        export_process.wait()
    
    # Reformat all tables except attachments    
    export_filenames = ['app_project.json', 'app_fqdataset.json', 'app_fqfile.json', 'app_prodata.json']
    
    print('Reformat JSON Dump')
    
    for file_name in export_filenames:
        export_path = os.path.join(export_directory, file_name)
        
        with open(export_path, 'r') as fh:
            export_data = yaml.safe_load(fh)

        export_data_format = []
        for row in export_data:
            pk = row['pk']
            col_data = row['fields']
            col_data['id'] = pk
            export_data_format.append(col_data)
    
        export_df = pd.DataFrame(export_data_format)
        export_df.to_csv(export_path.replace('.json','.csv'), index=False, sep=',')
    
    # Reformat json for attachments files / i.e. convert base64 data back to files stored alongside json
    print('Reformat Attachments')
    
    attachment_file_names = ['app_fqattachment.json', 'app_projectattachment.json']
    
    for file_name in attachment_file_names:
        
        print(f'Reformat Attachment File {file_name}')
        attachment_path = os.path.join(export_directory, file_name)
        
        with open(attachment_path, 'r') as fh:
            attachment_data = yaml.safe_load(fh)
        
        attachment_data_format = [] 
        for attachment in attachment_data:
            
            pk = attachment['pk']
            
            # Check if attachments refer to project or dataset
            if 'fq_dataset' in attachment['fields']:
                attach_fk_id = attachment['fields']['fq_dataset']
                attach_fk_name = 'fq_dataset'
            elif 'project' in attachment['fields']:
                attach_fk_id = attachment['fields']['project']
                attach_fk_name = 'project'
            else:
                print(attachment['fields'].keys())
                sys.stderr.write(f'ERROR: Invalid column names in attachment files!\n')
                return
            
            # Create output directory for project
            dump_dir = os.path.join(export_directory, f'{attach_fk_name}_{attach_fk_id}')
            os.makedirs(dump_dir, exist_ok=True)
            
            filename = attachment['fields']['name']
            file_path = os.path.join(dump_dir, filename)
            
            data_b64 = attachment['fields']['body']
            data_binary = base64.b64decode(data_b64)
            
            with open(file_path, 'wb') as fh:
                fh.write(data_binary)
    
            col_data = attachment['fields']
            col_data['id'] = pk
            _ = col_data.pop('body')
        
            attachment_data_format.append(col_data)

        attachment_df = pd.DataFrame(attachment_data_format)
        attachment_df.to_csv(attachment_path.replace('.json','.csv'), index=False, sep=',')
        
        
def main():
    
    args = parser.parse_args()
    db_directory = args.db_directory
    db_backup_directory = args.db_backup_directory
    log_directory = args.log_directory
    config_directory = args.config_directory
    
    django_port = args.django_port
    streamlit_port = args.streamlit_port
    debug = args.debug

    version = args.version
    
    # Check if requirements are met
    if not validate_requirements():
        print('Install requirements specified in requirements.txt')
        return
    
    if 'export_run' in args:
        
        print('Export ReadStore Database')
        
        export_directory = args.export_directory
        
        if 'RS_DB_DIRECTORY' in os.environ:
            print('Found RS_DB_DIRECTORY in Environment Variables')
            db_directory = os.environ['RS_DB_DIRECTORY']
        
        if 'RS_CONFIG_DIRECTORY' in os.environ:
            print('Found RS_CONFIG_DIRECTORY in Environment Variables')
            config_directory = os.environ['RS_CONFIG_DIRECTORY']
        
        if db_directory is None:
            export_parser.print_help()
            print('ERROR: --db-directory is required')
            return
        
        if config_directory is None:
            export_parser.print_help()
            print('ERROR: --config-directory is required')
            return
        
        if export_directory is None:
            export_parser.print_help()
            print('ERROR: --export_directory is required')
            return
                
        run_db_export(db_directory, config_directory, export_directory)
        
    elif version:
        print(f'ReadStore Basic Version: {__version__}')
        return
    else:
        # Try to set from environment variables
        if 'RS_DB_DIRECTORY' in os.environ:
            print('Found RS_DB_DIRECTORY in Environment Variables')
            db_directory = os.environ['RS_DB_DIRECTORY']
        if 'RS_DB_BACKUP_DIRECTORY' in os.environ:
            db_backup_directory = os.environ['RS_DB_BACKUP_DIRECTORY']
            print('Found RS_DB_BACKUP_DIRECTORY in Environment Variables')
        if 'RS_LOG_DIRECTORY' in os.environ:        
            log_directory = os.environ['RS_LOG_DIRECTORY']
            print('Found RS_LOG_DIRECTORY in Environment Variables')
        if 'RS_CONFIG_DIRECTORY' in os.environ:
            config_directory = os.environ['RS_CONFIG_DIRECTORY']
            print('Found RS_CONFIG_DIRECTORY in Environment Variables')
        if 'RS_DJANGO_PORT' in os.environ:
            django_port = int(os.environ['RS_DJANGO_PORT'])
            print('Found RS_DJANGO_PORT in Environment Variables')
        if 'RS_STREAMLIT_PORT' in os.environ:
            streamlit_port = int(os.environ['RS_STREAMLIT_PORT'])
            print('Found RS_STREAMLIT_PORT in Environment Variables')
        
        if db_directory is None:
            parser.print_help()
            print('ERROR: --db-directory is required')
            return
        if db_backup_directory is None:
            parser.print_help()
            print('ERROR: --db_backup_directory is required')
            return
        if log_directory is None:
            parser.print_help()
            print('ERROR: --log_directory is required')
            return
        
        #Define logger    
        run_rs_server(db_directory,
                    db_backup_directory,
                    log_directory,
                    config_directory,
                    django_port,
                    streamlit_port,
                    debug)


if __name__ == '__main__':
    main()