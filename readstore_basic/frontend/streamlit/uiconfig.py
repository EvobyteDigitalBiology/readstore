# readstore-basic/frontend/streamlit/uiconfig.py


from enum import Enum
from pathlib import Path
import yaml
import os

# List possible authentication methods
class AuthMethod(Enum):
    BASIC = "BASIC"
    JWT = "JWT"

if not 'RS_CONFIG_PATH' in os.environ:
    raise ValueError("RS_CONFIG_PATH not found in environment variables")
else:
    RS_CONFIG_PATH = os.environ['RS_CONFIG_PATH']

assert os.path.exists(RS_CONFIG_PATH), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

with open(RS_CONFIG_PATH, "r") as f:
    rs_config = yaml.safe_load(f)

__version__ = rs_config['global']['readstore_version']

# TODO: Update once ST fixed config setting
if rs_config['django']['django_settings_module'] == 'settings.production':
    import sys
    sys.tracebacklimit = 0
    
    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

# Define config constants
BACKEND_API_ENDPOINT_HOST = rs_config['django']['host']
BACKEND_API_ENDPOINT_PORT = str(rs_config['django']['port'])
BACKEND_API_VERSION = rs_config['django']['api_version']
BACKEND_API_ENDPOINT = os.path.join('http://', BACKEND_API_ENDPOINT_HOST + ':' + BACKEND_API_ENDPOINT_PORT, BACKEND_API_VERSION)
BACKEND_MAX_QUEUE_SIZE = rs_config['django']['fq_queue_maxsize']

STATIC_PATH_PREFIX = rs_config['streamlit']['static_path_prefix']

AUTH_METHOD = AuthMethod.JWT
AUTH_USER_GROUP = ["appuser", "admin"]

# Refesh token every 10 minutes
ACCESS_TOKEN_REFESH_SECONDS = 10*60
CACHE_TTL_SECONDS=15*60

DEFAULT_OWNER_GROUP = 'default'

# Define Height of detail view
DETAIL_VIEW_HEIGHT = 400

# Define ReadEndings
VALID_READ1_SUFFIX = rs_config['global']['valid_read1_suffix'].split(',')
VALID_READ2_SUFFIX = rs_config['global']['valid_read2_suffix'].split(',')
VALID_INDEX1_SUFFIX = rs_config['global']['valid_index1_suffix'].split(',')
VALID_INDEX2_SUFFIX = rs_config['global']['valid_index2_suffix'].split(',')

# These keys cannot be used as metadata keys, as they are reserved for internal use
# TODO: Solution to enable use of these keys as metadata keys, for instance split metdata dataframe from presenting
METADATA_RESERVED_KEYS = ['id',
                          'name',
                          'project',
                          'project_ids',
                          'project_names',
                          'owner_group_name',
                          'qc_passed',
                          'paired_end',
                          'index_read',
                          'created',
                          'description',
                          'owner_username',
                          'fq_file_r1',
                          'fq_file_r2',
                          'fq_file_i1',
                          'fq_file_i2',
                          'id_project',
                          'name_project',
                          'name_og',
                          'archived',
                          'collaborators',
                          'dataset_metadata_keys',
                          'data_type',
                          'version',
                          'valid_to',
                          'upload_path',
                          'owner_username',
                          'fq_dataset',
                          'id_fq_dataset',
                          'name_fq_dataset']

# # Endpoint config. Register and check access to all endpoints here
# URLs must end with a slash
ENDPOINT_CONFIG = {
    'user' : '/'.join([BACKEND_API_ENDPOINT, 'user/']),
    'group' : '/'.join([BACKEND_API_ENDPOINT, 'group/']),
    'owner_group' : '/'.join([BACKEND_API_ENDPOINT, 'owner_group/']),
    'get_user_groups' : '/'.join([BACKEND_API_ENDPOINT, 'get_user_groups/']),
    'project' : '/'.join([BACKEND_API_ENDPOINT, 'project/']),
    'project_attachment' : '/'.join([BACKEND_API_ENDPOINT, 'project_attachment/']),
    'fq_file' : '/'.join([BACKEND_API_ENDPOINT, 'fq_file/']),
    'fq_dataset' : '/'.join([BACKEND_API_ENDPOINT, 'fq_dataset/']),
    'fq_attachment' : '/'.join([BACKEND_API_ENDPOINT, 'fq_attachment/']),
    'license_key' : '/'.join([BACKEND_API_ENDPOINT, 'license_key/']),
    'pro_data' : '/'.join([BACKEND_API_ENDPOINT, 'pro_data/']),
}