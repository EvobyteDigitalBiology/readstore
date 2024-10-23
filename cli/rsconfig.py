# readstore-basic/cli/rsconfig.py

import os
import configparser
from typing import List, Tuple

import rsexceptions


def load_rs_config(filename: str | None = None,
                   default_endpoint_url: str | None = None,
                   default_fastq_extensions: List[str] | None = None,
                   default_output: str | None = None) -> Tuple[str, str, str, List[str], str]:
    """
        Load And VaidateReadStore Configuration
    """
        
    # If filename is provided, check if file exists
    # Then load configuration
    
    # If not provided, check if ENV variable are set and override config
    
    if filename and os.path.isfile(filename):
    
        rs_config = configparser.ConfigParser()
        rs_config.read(filename)
        
        username = rs_config.get('credentials', 'username', fallback=None)
        token = rs_config.get('credentials', 'token', fallback=None)
        endpoint_url = rs_config.get('general', 'endpoint_url', fallback=None)
        fastq_extensions = rs_config.get('general', 'fastq_extensions', fallback=None)
        output = rs_config.get('general', 'output', fallback=None)
    # If file is not found, init empty variables
    else:
        username = None
        token = None
        endpoint_url = None
        fastq_extensions = None
        output = None
    
    # Check if ENV variables are set
    # Overwrite config if found
    if 'READSTORE_USERNAME' in os.environ:
        username = os.environ['READSTORE_USERNAME']
    if 'READSTORE_TOKEN' in os.environ:
        token = os.environ['READSTORE_TOKEN']
    if 'READSTORE_ENDPOINT_URL' in os.environ:
        endpoint_url = os.environ['READSTORE_ENDPOINT_URL']
    if 'READSTORE_FASTQ_EXTENSIONS' in os.environ:
        fastq_extensions = os.environ['READSTORE_FASTQ_EXTENSIONS']
        fastq_extensions = fastq_extensions.split(',')
    if 'READSTORE_DEFAULT_OUTPUT' in os.environ:
        output = os.environ['READSTORE_DEFAULT_OUTPUT']
    
    # If config parameters are not found in file or ENV, try to use defaukt arguments if provided
    if not username:
        raise rsexceptions.ReadStoreError('Username Not Found')
    if not token:
        raise rsexceptions.ReadStoreError('Token Not Found')
    if not endpoint_url:
        # Check if default is provided
        if default_endpoint_url:
            endpoint_url = default_endpoint_url
        else:
            raise rsexceptions.ReadStoreError('Config: Endpoint URL Not Found')
    if not fastq_extensions:
        if default_fastq_extensions:
            fastq_extensions = default_fastq_extensions
        else:
            raise rsexceptions.ReadStoreError('Config: Fastq Extensions Not Found')
    if not output:        
        if default_output:
            output = default_output
        else:
            raise rsexceptions.ReadStoreError('Config: Output Format Not Found')
    
    return (username, token, endpoint_url, fastq_extensions, output)
    
    
def write_rs_config(filename: str,
                   username: str,
                   token: str,
                   endpoint_url: str,
                   fastq_extensions: List[str],
                   output: str):
    """
        Save ReadStore Configuration
    """
    
    assert os.path.isdir(os.path.dirname(filename)), 'Directory Not Found'
    
    # TODO Validate Server URL
    
    config = configparser.ConfigParser()
    
    config['general'] = {'endpoint_url': endpoint_url,
                         'fastq_extensions': fastq_extensions,
                         'output': output}
    
    config['credentials'] = {'username': username,
                            'token' : token}
    
    with open(filename, 'w') as f:
        config.write(f)
    
        