# readstore-basic/frontend/streamlit/uiconfig.py


from enum import Enum
from pathlib import Path
import yaml
import os

# TODO Needs UPdate
from __version__ import __version__

# List possible authentication methods
class AuthMethod(Enum):
    BASIC = "BASIC"
    JWT = "JWT"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RS_CONFIG_PATH = BASE_DIR / "rs_config.yaml"
assert RS_CONFIG_PATH.exists(), f"rs_config.yaml not found at {RS_CONFIG_PATH}"

def load_rs_config():
    with open(RS_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

RS_CONFIG = load_rs_config()

# Define config constants
BACKEND_API_ENDPOINT_HOST = RS_CONFIG['django']['host']
BACKEND_API_ENDPOINT_PORT = str(RS_CONFIG['django']['port'])
BACKEND_API_VERSION = RS_CONFIG['django']['api_version']
BACKEND_API_ENDPOINT = os.path.join('http://', BACKEND_API_ENDPOINT_HOST + ':' + BACKEND_API_ENDPOINT_PORT, BACKEND_API_VERSION)

STATIC_PATH_PREFIX = RS_CONFIG['streamlit']['static_path_prefix']

AUTH_METHOD = AuthMethod.JWT
AUTH_USER_GROUP = ["appuser", "admin"]

# Refesh token every 10 minutes
ACCESS_TOKEN_REFESH_SECONDS = 10*60
CACHE_TTL_SECONDS=15*60

DEFAULT_OWNER_GROUP = 'default'

# Define ReadEndings
VALID_READ1_SUFFIX = RS_CONFIG['global']['valid_read1_suffix'].split(',')
VALID_READ2_SUFFIX = RS_CONFIG['global']['valid_read2_suffix'].split(',')
VALID_INDEX1_SUFFIX = RS_CONFIG['global']['valid_index1_suffix'].split(',')
VALID_INDEX2_SUFFIX = RS_CONFIG['global']['valid_index2_suffix'].split(',')

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
                          'dataset_metadata_keys']

# # Endpoint config. Register and check access to all endpoints here
# URLs must end with a slash
ENDPOINT_CONFIG = {
    'user' : '/'.join([BACKEND_API_ENDPOINT, 'user/']),
    #'my_owner_group': '/'.join([BACKEND_API_ENDPOINT, 'user/my_owner_group/']),
    'group' : '/'.join([BACKEND_API_ENDPOINT, 'group/']),
    'owner_group' : '/'.join([BACKEND_API_ENDPOINT, 'owner_group/']),
    'get_user_groups' : '/'.join([BACKEND_API_ENDPOINT, 'get_user_groups/']),
    'project' : '/'.join([BACKEND_API_ENDPOINT, 'project/']),
    #'project_collab' : '/'.join([BACKEND_API_ENDPOINT, 'project/collab/']),
    #'project_owner_group' : '/'.join([BACKEND_API_ENDPOINT, 'project/owner_group/']),
    'project_attachment' : '/'.join([BACKEND_API_ENDPOINT, 'project_attachment/']),
    #'project_attachment_project' : '/'.join([BACKEND_API_ENDPOINT, 'project_attachment/project/1/']) # TODO Check how to deal with mandatory PKs
    'fq_file' : '/'.join([BACKEND_API_ENDPOINT, 'fq_file/']),
    'fq_dataset' : '/'.join([BACKEND_API_ENDPOINT, 'fq_dataset/']),
    'fq_attachment' : '/'.join([BACKEND_API_ENDPOINT, 'fq_attachment/']),
}