#!/usr/bin/env python3

import time
import sqlite3
import datetime
from pathlib import Path
import yaml
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.

if not 'RS_CONFIG_PATH' in os.environ:
    raise ValueError("RS_CONFIG_PATH not found in environment variables")
else:
    RS_CONFIG_PATH = os.environ['RS_CONFIG_PATH']

assert os.path.exists(RS_CONFIG_PATH), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

with open(RS_CONFIG_PATH, "r") as f:
    rs_config = yaml.safe_load(f)

DB_PATH = rs_config['django']['db_path']
BACKUP_INTERVAL_HOURS = rs_config['django']['backup_interval_hours']
BACKUP_MAX_FILES = rs_config['django']['backup_max_files']
BACKUP_DIR = rs_config['django']['db_backup_dir']

def backup_db(source_db_path: str, backup_db_path: str):
    try:
        # Connect to the source database
        source_conn = sqlite3.connect(source_db_path)
        # Create a backup connection
        backup_conn = sqlite3.connect(backup_db_path)
        
        # Perform the backup
        source_conn.backup(backup_conn)
        
        # Close the connections
        backup_conn.close()
        source_conn.close()
        
        # Lock permissions for owner
        os.chmod(backup_db_path, 0o600)
        
        print(f"Backup successful: {backup_db_path}")
    except sqlite3.Error as e:
        print(f"Error during backup: {e}")
        
        
def periodic_backup(source_db_path: str,
                    backup_db_dir: str,
                    max_backup_files: int):
    
    assert os.path.exists(source_db_path), f"Database not found at {source_db_path}"
    assert os.access(source_db_path, os.R_OK), f"Database not readable at {source_db_path}"
    assert os.path.isdir(backup_db_dir), f"Backup directory not found at {backup_db_dir}"

    # Run backup
    date_fmt = datetime.datetime.now().strftime("%y-%m-%d_%H-%M")
    backup_filename = 'readstore_db_backup_' + date_fmt + '.sqlite3'
    backup_filename = os.path.join(backup_db_dir, backup_filename)
    
    print(f"Run Backup to {backup_filename}")
    backup_db(source_db_path, backup_filename)
    
    # Delete oldest backup
    backup_files = [f for f in os.listdir(backup_db_dir) if f.endswith('.sqlite3')]
    backup_files = [os.path.join(backup_db_dir, f) for f in backup_files]
    
    if len(backup_files) > max_backup_files:
                
        creation_times = [os.path.getctime(f) for f in backup_files]
        oldest_backup = backup_files[creation_times.index(min(creation_times))]
        os.remove(oldest_backup)
        print(f"Deleted oldest backup: {oldest_backup}")

    
if __name__ == '__main__':
    
    print("Start Backup Operation")
    
    while True:
        periodic_backup(DB_PATH, BACKUP_DIR, BACKUP_MAX_FILES)
        time.sleep(int(BACKUP_INTERVAL_HOURS*60*60))