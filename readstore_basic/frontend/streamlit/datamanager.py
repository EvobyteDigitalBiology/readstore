# readstore-basic/frontend/streamlit/datamanager.py


"""

Privides methods to manage and load data for the streamlit app.
Contains (cached) methods for loading data from the backend API or S3 bucket
to the app app_pages.

"""

from typing import List, Tuple
import time
import datetime

import streamlit as st
import pandas as pd
import os
import requests

import extensions
import uiconfig
import exceptions

from uidataclasses import Group
from uidataclasses import User
from uidataclasses import OwnerGroup
from uidataclasses import Project
from uidataclasses import ProjectAttachmentPost
from uidataclasses import ProjectAttachment
from uidataclasses import FqFile
from uidataclasses import FqDataset
from uidataclasses import FqAttachment
from uidataclasses import FqAttachmentPost
from uidataclasses import URL
from uidataclasses import LicenseKey
from uidataclasses import FqQueue
from uidataclasses import FqFileUploadApp
from uidataclasses import InvalidPath
from uidataclasses import ProData
from uidataclasses import TransferOwner

#region basic functions
@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_my_user(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['user'], 'my_user/')
    df = extensions.detail_request_to_model(endpoint, User, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_user_groups(headers: dict) -> pd.DataFrame:
    
    endpoint = uiconfig.ENDPOINT_CONFIG['get_user_groups']
    df = extensions.get_request_to_df(endpoint, Group, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_group(headers: dict) -> pd.DataFrame:

    endpoint = uiconfig.ENDPOINT_CONFIG['group']
    df = extensions.get_request_to_df(endpoint, Group, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_user(headers: dict) -> pd.DataFrame:

    endpoint = uiconfig.ENDPOINT_CONFIG['user']
    df = extensions.get_request_to_df(endpoint, User, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_appuser(headers: dict) -> pd.DataFrame:
    
    endpoint = uiconfig.ENDPOINT_CONFIG['user']
    df = extensions.get_request_to_df(endpoint,
                                      User,
                                      headers=headers,
                                      query_params = {'group_name' : 'appuser'})
    
    # Cast df app_user dicts
    appuser = df.pop('appuser').tolist()
    appuser_df = pd.DataFrame(appuser)
    
    df = pd.concat([df, appuser_df], axis=1)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_owner_group(headers: dict) -> pd.DataFrame:
    
    endpoint = uiconfig.ENDPOINT_CONFIG['owner_group']
    df = extensions.get_request_to_df(endpoint, OwnerGroup, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_owner_group(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['project'], 'owner_group/')
    df = extensions.get_request_to_df(endpoint, Project, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_collab(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['project'], 'collab/')
    df = extensions.get_request_to_df(endpoint, Project, headers=headers)
    
    return df


@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_owner(headers: dict, owner: int) -> pd.DataFrame:
    
    query_params = {'owner' : owner}
    
    df = extensions.get_request_to_df(uiconfig.ENDPOINT_CONFIG['project'],
                                      Project,
                                      headers=headers,
                                      query_params=query_params)
    
    return df


@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_my_owner_group(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['user'], 'my_owner_group/')
    # TODO Shoudl be detail request
    df = extensions.get_request_to_df(endpoint, OwnerGroup, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_attachments(headers: dict, project_id: int | None = None) -> pd.DataFrame:
    
    if project_id:
        endpoint = uiconfig.ENDPOINT_CONFIG['project_attachment']
        endpoint = endpoint + 'project/' + str(project_id) + '/'
        df = extensions.get_request_to_df(endpoint, ProjectAttachment, headers=headers)
    
    else:
        endpoint_collab = os.path.join(uiconfig.ENDPOINT_CONFIG['project_attachment'], 'collab/')
        endpoint_owner_group = os.path.join(uiconfig.ENDPOINT_CONFIG['project_attachment'], 'owner_group/')
        
        df_collab = extensions.get_request_to_df(endpoint_collab, ProjectAttachment, headers=headers)
        df_owner_group = extensions.get_request_to_df(endpoint_owner_group, ProjectAttachment, headers=headers)

        df = pd.concat([df_collab, df_owner_group], axis=0)
        
    df = df[['id', 'name', 'description', 'project']]
    df = df.rename(columns={'project' : 'project_id'})
                
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_file_staging(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_file'], 'staging/')
    df = extensions.get_request_to_df(endpoint,
                                    FqFile,
                                    headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_file_owner(headers: dict, owner: int) -> pd.DataFrame:
    
    query_params = {'owner' : owner}
    
    df = extensions.get_request_to_df(uiconfig.ENDPOINT_CONFIG['fq_file'],
                                    FqFile,
                                    headers=headers,
                                    query_params=query_params)
    
    return df


@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_file_owner_group(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_file'], 'owner_group/')
    df = extensions.get_request_to_df(endpoint,
                                      FqFile,
                                      headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_file_detail(headers: dict, fq_file_id: int) -> FqFile:
    
    fq_file_id = int(fq_file_id)
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_file']
    fq_file = extensions.detail_request_to_model(endpoint + str(fq_file_id) + '/', FqFile, headers=headers)
    
    return fq_file

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_file_download_url(headers: dict, fq_file_id: int) -> bytes:
    
    fq_file_id = int(fq_file_id)
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_file'], 'download_url/', str(fq_file_id) + '/')
    
    url = extensions.detail_request_to_model(endpoint, URL, headers=headers)
    
    return url.url

def get_fq_file_invalid_upload_paths(headers: dict) -> List[dict]:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_file'],'validate_upload_path/')
    df = extensions.get_request_to_df(endpoint, InvalidPath, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')   
def get_fq_dataset(headers: dict, owner: int | None = None) -> pd.DataFrame:
    
    if owner:
        query_params = {'owner' : owner}
    else:
        query_params = None
    
    df = extensions.get_request_to_df(uiconfig.ENDPOINT_CONFIG['fq_dataset'],
                                    FqDataset,
                                    headers=headers,
                                    query_params=query_params)
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_owner_group(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_dataset'], 'owner_group/')
    df = extensions.get_request_to_df(endpoint,
                                    FqDataset,
                                    headers=headers)
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_collab(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_dataset'], 'collab/')
    df = extensions.get_request_to_df(endpoint,
                                    FqDataset,
                                    headers=headers)
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_attachments(headers: dict, fq_dataset_id: int | None = None) -> pd.DataFrame:
    
    if fq_dataset_id:
        
        endpoint = uiconfig.ENDPOINT_CONFIG['fq_attachment']
        endpoint = endpoint + 'fq_dataset/' + str(fq_dataset_id) + '/'
        
        df = extensions.get_request_to_df(endpoint, FqAttachment, headers=headers)
    
    else:
        endpoint_collab = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_attachment'], 'collab/')
        endpoint_owner_group = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_attachment'], 'owner_group/')
        
        df_collab = extensions.get_request_to_df(endpoint_collab, FqAttachment, headers=headers)
        df_owner_group = extensions.get_request_to_df(endpoint_owner_group, FqAttachment, headers=headers)

        df = pd.concat([df_collab, df_owner_group], axis=0)
    
    df = df[['id', 'name', 'description', 'fq_dataset']]
    df = df.rename(columns={'fq_dataset' : 'fq_dataset_id'})
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_pro_data(headers: dict, fq_dataset_id: int) -> pd.DataFrame:
    
    fq_dataset_id = int(fq_dataset_id)
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['pro_data'], 'fq_dataset/', str(fq_dataset_id) + '/')
    df = extensions.get_request_to_df(endpoint, ProData, headers=headers)

    df = df[['id', 'name', 'data_type', 'description', 'version', 'valid_to', 'owner_username']]
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_detail(headers: dict, fq_dataset_id: int) -> Tuple[pd.DataFrame,pd.DataFrame]:
    
    fq_dataset = extensions.detail_request_to_model(
        uiconfig.ENDPOINT_CONFIG['fq_dataset'] + str(fq_dataset_id) + '/',
        FqDataset,
        headers=headers
    )
    
    return fq_dataset

# Add empty fastq requests
@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_empty(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['fq_dataset'], 'empty/')
    df = extensions.get_request_to_df(endpoint,
                                    FqDataset,
                                    headers=headers)
    return df

def get_license_key(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['license_key'],'latest/')
    df = extensions.get_request_to_df(endpoint, LicenseKey, headers=headers)
    
    return df

def valid_license(headers: dict) -> bool:
    
    license_key = get_license_key(headers)
    
    if len(license_key) == 1:
        expiration_date = license_key['expiration_date'].values[0]
        expiration_date = pd.to_datetime(expiration_date).date()
    
        if expiration_date >= datetime.datetime.now().date():
            return True
        else:
            return False
    else:
        return False

def get_license_seats(headers: dict) -> int:
    
    license_key = get_license_key(headers)
    
    if len(license_key) == 1:
        seats = license_key['seats'].values[0]
    else:
        seats = 0
    
    return seats

def get_fq_queue_jobs(headers: dict) -> int:
    
    endpoint = os.path.join(uiconfig.BACKEND_API_ENDPOINT, 'fq_queue/')
    fq_queue_model = extensions.detail_request_to_model(endpoint, FqQueue, headers=headers)
    
    num_jobs = fq_queue_model.num_jobs
    
    return num_jobs

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_pro_data_owner_group(headers: dict) -> pd.DataFrame:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['pro_data'], 'owner_group/')
    df = extensions.get_request_to_df(endpoint, ProData, headers=headers)
    
    return df

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_pro_data_detail(headers: dict, pro_data_id: int) -> ProData:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['pro_data'], str(pro_data_id) + '/')
    pro_data = extensions.detail_request_to_model(endpoint, ProData, headers=headers)
    
    return pro_data

def get_pro_data_invalid_upload_paths(headers: dict) -> List[dict]:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['pro_data'],'validate_upload_path/')
    df = extensions.get_request_to_df(endpoint, InvalidPath, headers=headers)
    
    return df

#region COMBINED

# ADMIN

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_appuser_overview(headers: dict) -> pd.DataFrame:
    
    appusers = get_appuser(headers = headers)
    groups = get_group(headers = headers)
    owner_groups = get_owner_group(headers = headers)
    
    return_cols =[
        'id_user',
        'username',
        'owner_group',
        'name',
        'email',
        'is_active',
        'staging',
        'token',
        'date_joined'
    ]
    
    # Check for empty df
    if appusers.empty:
        return pd.DataFrame(columns=return_cols)
    else:
        
        # Reformat groups for each user in binary wide df
        groups.index = groups.pop('id')
        groups_map = groups.to_dict(orient='dict')['name']
        
        appuser_groups = appusers.pop('groups').reset_index()    
        appuser_groups = appuser_groups.explode('groups')
        appuser_groups['groups'] = appuser_groups['groups'].map(groups_map)
        appuser_groups['val'] = True
        
        appuser_groups = pd.pivot(appuser_groups,
                                index='index',
                                columns='groups',
                                values='val')
        appuser_groups = appuser_groups.fillna(False)
        appuser_groups = appuser_groups.drop(columns = ['appuser'])
        
        if not 'staging' in appuser_groups.columns:
            appuser_groups['staging'] = False
        
        # # Merge in 
        appusers = pd.concat([appusers, appuser_groups],axis=1)
        
        # Add in owner group TODO Add archived 
        owner_groups = owner_groups[['id', 'name']]
        
        appusers = appusers.merge(owner_groups, left_on = 'owner_group', right_on='id', suffixes=('_user', '_og'))
            
        appusers = appusers[return_cols]
    
    return appusers
    
    
# Return owners of an owner group
@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_owner_group_owner(headers: dict) -> pd.DataFrame:
    
    owner_group = get_owner_group(headers)
    users = get_user(headers)
    
    valid_to_nat = ~pd.isna(owner_group['valid_to'])
    owner_group['archived'] = valid_to_nat
    
    users = users[['id', 'username']]
    owner_group = owner_group[['id', 'name', 'created', 'archived', 'owner']]
    
    merged = owner_group.merge(users, left_on='owner', right_on='id', suffixes=('_og', '_user'))
    merged = merged[['id_og','name', 'username', 'created', 'archived']]
    
    return merged


# Get owner groups for all users
# If No Users are Found or No Owner Groups are found
@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_owner_group_appusers(headers: dict, owner_group_name: str | None = None) -> pd.DataFrame:
    
    app_users = get_appuser(headers)
    owner_group = get_owner_group(headers)
    
    return_cols =[
        'id',
        'username',
        'name'
    ]
    
    if app_users.empty or owner_group.empty:
        return pd.DataFrame(columns=return_cols)
    else:    
        owner_group = owner_group[['id', 'name']]
        
        app_users = app_users[['id', 'username', 'owner_group']]
        og_users = app_users.merge(owner_group, left_on = 'owner_group', right_on = 'id', suffixes=('', '_og'))
        og_users = og_users[return_cols]        
        
        if owner_group_name:
            og_users = og_users.loc[
                og_users['name'] == owner_group_name,:
            ]
        
        return og_users

# PROJECT

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_appuser(headers: dict) -> pd.DataFrame:
    
    projects = get_project_owner_group(headers)
    collabs = get_project_collab(headers)
    
    projects = pd.concat([projects, collabs], axis=0)

    return projects

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_metadata_overview(headers: dict) -> Tuple[pd.DataFrame,pd.DataFrame]:
    
    owner_groups = get_owner_group(headers)
    appuser = get_appuser(headers)
    projects = get_project_appuser(headers)
    
    req_columns = [
            'id_project',
            'name_project',
            'description',
            'name_og',
            'created',
            'owner_username',
            'collaborators',
            'dataset_metadata_keys',
        ]
    
    if projects.empty:
        return pd.DataFrame(columns=req_columns), pd.DataFrame()
    else:
        # Merge in owner group
        owner_groups = owner_groups[['id', 'name']]
        
        projects = projects.merge(owner_groups,
                                left_on = 'owner_group',
                                right_on='id',
                                suffixes=('_project', '_og'))

        # TODO Needs revision
        projects['archived'] = ~pd.isna(projects['valid_to'])
                
        # Bring metadata in df format
        metadata = projects.pop('metadata')
        metadata = pd.DataFrame(metadata.tolist())
        
        projects = projects[req_columns]
        
        return projects, metadata


@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_project_collaborators(headers: dict, project_id: int) -> pd.DataFrame:
    
    app_users = get_appuser(headers)
    
    endpoint = uiconfig.ENDPOINT_CONFIG['project']
    headers=headers
    project = extensions.detail_request_to_model(endpoint + str(project_id) + '/', Project, headers=headers)
    
    collaborators = project.collaborators
    app_users = app_users[['id', 'username']]
    app_users = app_users.loc[app_users['id'].isin(collaborators)]
    
    return app_users  


def infer_dataset(query: str) -> str:
    """Method to infer default dataset name from fq_file name

    # Strip extensions from fq_file name and set as dataset
    # Strip trailing underscores, dots and dashes
    
    Args:
        query (str): query fq_file name
        
    Returns:
        str: inferred dataset name
    """
    
    def test_ext_readset(q, ext: List[str]):
        for e in ext:
            if q.endswith(e):
                q = q.replace(e, '')
                q = q.strip('_').strip('.').strip('-')
                return q
        else:
            return None
    
    for exts in [uiconfig.VALID_READ1_SUFFIX,
                 uiconfig.VALID_READ2_SUFFIX,
                 uiconfig.VALID_INDEX1_SUFFIX,
                 uiconfig.VALID_INDEX2_SUFFIX]:
        
        q = test_ext_readset(query, exts)
        if q: return q    
    else:
        q = query.rstrip('_').rstrip('.').rstrip('-')
        return q
        
        
@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_file_staging_overview(headers: dict) -> pd.DataFrame:
    
    fq_files = get_fq_file_staging(headers)
    
    # Clip Extensions from name and set as dataset
    fq_files['dataset'] = fq_files['name'].apply(infer_dataset)
    fq_files = fq_files.sort_values(by='dataset')
    
    fq_files = fq_files[['id',
                         'dataset',
                         'name',
                         'read_type',
                         'created',
                         'qc_passed',
                         'upload_path',
                         'bucket',
                         'key',
                         'read_length',
                         'num_reads',
                         'qc_phred_mean',
                         'qc_phred',
                         'size_mb',
                         'md5_checksum',
                         'pipeline_version']]
    
    
    
    # Split Datasets into individual dfs
    return fq_files

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_fq_dataset_meta_overview(headers: dict) -> Tuple[pd.DataFrame,pd.DataFrame]:
    
    # Get Fq Datasets where user is in owner group
    fq_datasets_owner_group = get_fq_dataset_owner_group(headers)
    fq_datasets_collab = get_fq_dataset_collab(headers)
    
    # All projects both from owner_group and collab for the current appuser
    projects_appuser = get_project_appuser(headers)[['id', 'name']]
    # Get all project ids that the appuser has access to
    projects_appuser_ids = projects_appuser['id'].tolist()
    
    return_cols =[
        'id',
        'name',
        'description',
        'project',
        'project_names',
        'owner_group_name',
        'qc_passed',
        'paired_end',
        'index_read',
        'created',
        'owner_username',
        'fq_file_r1',
        'fq_file_r2',
        'fq_file_i1',
        'fq_file_i2'
    ]
    
    merge = pd.concat([fq_datasets_owner_group, fq_datasets_collab], axis=0, ignore_index=True)
    # Error comes when not all projects are shared 
    
    def _map_project_name(project_id):
        return projects_appuser.loc[projects_appuser['id'] == project_id, 'name'].values[0]
    
    # Map project ids to project names, ONLY if appuser has access to project via owner_group or collab
    
    # Filter project ids
    merge['project'] = merge['project'].apply(lambda x: [i for i in x if i in projects_appuser_ids])
    merge['project_names'] = merge['project'].apply(lambda x: [_map_project_name(i) for i in x])
    
    metadata = merge.pop('metadata')
    metadata = pd.DataFrame(metadata.tolist())
    
    merge = merge[return_cols]
    
    return merge, metadata
    

@st.cache_data(ttl=uiconfig.CACHE_TTL_SECONDS, show_spinner='Loading data...')
def get_pro_data_meta_overview(headers: dict) -> Tuple[pd.DataFrame,pd.DataFrame]:
        
    pro_data_owner_group = get_pro_data_owner_group(headers)
    
    return_cols =[
        'fq_dataset',
        'id',
        'name',
        'description',
        'data_type',
        'version',
        'created',
        'valid_to',
        'owner_username',
        'upload_path',
    ]
    
    metadata = pro_data_owner_group.pop('metadata')
    metadata = pd.DataFrame(metadata.tolist())
    
    pro_data_owner_group = pro_data_owner_group[return_cols]
    
    return pro_data_owner_group, metadata


#region  CREATE
 
def create_owner_group(name: str):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['owner_group']
    owner_group = OwnerGroup(name=name)
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=owner_group,
        headers=st.session_state['jwt_auth_header']
    )

def create_user(headers: dict,
                username: str,
                email: str,
                password: str,
                owner_group_name: str,
                staging: bool):
    
    # Get owner_group_id
    owner_groups = get_owner_group(headers)
    owner_group_id = owner_groups.loc[
        owner_groups['name'] == owner_group_name,'id'
    ]
    owner_group_id = int(owner_group_id)
    
    # groups
    groups = get_group(headers)
    
    # Reformat groups for each user in binary wide df
    groups.index = groups.pop('id')
    groups_map = groups.to_dict(orient='dict')['name']
    groups_map_inv = {v:k for k,v in groups_map.items()}
    
    # Get appuser group id and staging group id
    groups_create = [groups_map_inv['appuser']]
    
    if staging:
        groups_create.append(groups_map_inv['staging'])
    
    user = User(
        username=username,
        email = email,
        is_active = True,
        password = password,
        groups = groups_create,
        appuser = {
            'owner_group' : owner_group_id,
        }
    )
    
    endpoint = uiconfig.ENDPOINT_CONFIG['user']
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=user,
        headers=headers
    )


def create_owner_group(name: str):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['owner_group']
    owner_group = OwnerGroup(name=name)
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=owner_group,
        headers=st.session_state['jwt_auth_header']
    )


def create_project(headers: dict,
                    name: str,
                    description: str,
                    metadata: dict,
                    dataset_metadata_keys: dict) -> int:
    
    owner_group_id = get_my_owner_group(headers)['id'].values[0]
    
    project = Project(
        name = name,
        description = description,
        metadata = metadata,
        dataset_metadata_keys = dataset_metadata_keys,
        owner_group = owner_group_id,
    )
    
    endpoint = uiconfig.ENDPOINT_CONFIG['project']
    project_id = extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=project,
        headers=headers
    ) 
    
    return project_id


def create_project_attachment(filename: str,
                              body: bytes,
                              project_id: int):
    
    #  Could need update for archives
    filetype = filename.split('.')[-1]
    size_mb = int(len(body) / (1024 * 1024))
    
    project_attachment = ProjectAttachmentPost(
        name = filename,
        description = '',
        path = filename,
        filetype = filetype,
        size_mb = size_mb,
        body = body,
        project = project_id
    )
     
    endpoint = uiconfig.ENDPOINT_CONFIG['project_attachment']
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=project_attachment,
        headers=st.session_state['jwt_auth_header'],
        method='data'
    )

def create_fq_dataset(
                    headers: dict,
                    name: str,
                    description: str,
                    qc_passed: bool,
                    index_read: bool,
                    fq_file_r1: int | None,
                    fq_file_r2: int | None,
                    fq_file_i1: int | None,
                    fq_file_i2: int | None,
                    paired_end: bool,
                    project: List[int],
                    metadata: dict):

    owner_group_id = get_my_owner_group(headers)['id'].values[0]

    fq_dataset = FqDataset(
        name = name,
        description = description,
        qc_passed = qc_passed,
        fq_file_r1 = fq_file_r1,
        fq_file_r2 = fq_file_r2,
        fq_file_i1 = fq_file_i1,
        fq_file_i2 = fq_file_i2,
        paired_end = paired_end,
        index_read = index_read,
        owner_group = owner_group_id,
        project = project,
        metadata = metadata
    )
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
    pk = extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=fq_dataset,
        headers=headers
    )
    return pk



def create_fq_attachment(filename: str,
                              body: bytes,
                              fq_dataset_id: int):
    
    #  Could need update for archives
    filetype = filename.split('.')[-1]
    size_mb = int(len(body) / (1024 * 1024))
    
    fq_attachment = FqAttachmentPost(
        name = filename,
        description = '',
        path = filename,
        filetype = filetype,
        size_mb = size_mb,
        body = body,
        fq_dataset = fq_dataset_id
    )
     
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_attachment']
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=fq_attachment,
        headers=st.session_state['jwt_auth_header'],
        method='data'
    )

def create_pro_data(headers: dict,
                    name: str,
                    data_type: str,
                    description: str,
                    upload_path: str,
                    metadata: dict,
                    fq_dataset: int):
                    
    pro_data = ProData(
        name = name,
        data_type = data_type,
        description = description,
        upload_path = upload_path,
        metadata = metadata,
        fq_dataset = fq_dataset
    )

    endpoint = uiconfig.ENDPOINT_CONFIG['pro_data']
    
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=pro_data,
        headers=headers,
    )
            

def create_license_key(headers: dict, key: str, seats: int, expiration_date: datetime.datetime):
    
    license_key = LicenseKey(
        key = key,
        seats = seats,
        expiration_date = expiration_date
    )
    
    endpoint = uiconfig.ENDPOINT_CONFIG['license_key']
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model=license_key,
        headers=headers,
        method='data'
    )


def submit_fq_queue_job(headers: dict, fq_file_name: str, fq_file_path: str, read_type: str):
    
    fq_file_upload_app = FqFileUploadApp(
        fq_file_name = fq_file_name,
        fq_file_path = fq_file_path,
        read_type = read_type
    )
    
    endpoint = os.path.join(uiconfig.BACKEND_API_ENDPOINT,'fq_file_upload_app/')
    
    res = requests.post(endpoint, 
                        json=fq_file_upload_app.dict(),
                        headers=headers)
    
    return res    


#region UPDATE

def user_regenerate_token():
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['user'], 'regenerate_token/')
    res = requests.post(endpoint, headers=st.session_state['jwt_auth_header'])
    
    if res.status_code != 200:
        raise AssertionError(f"Error: {res.status_code}, Message: {res.json()}")

def user_reset_password(old_pwd: str, new_pwd: str) -> bool:
    
    endpoint = os.path.join(uiconfig.ENDPOINT_CONFIG['user'], 'reset_password/')
    res = requests.post(endpoint,
                        headers=st.session_state['jwt_auth_header'],
                        json={'old_password' : old_pwd,
                              'new_password' : new_pwd})
    
    if res.status_code != 200:
        message = res.json()['detail']
        if message == 'password incorrect':
            return False
        else:
            raise AssertionError(f"Error: {res.status_code}, Message: {res.json()}")    
    else:
        return True

def transfer_owner(source_owner_id: int, dest_owner_id: int):
    
    source_owner_id = int(source_owner_id)
    dest_owner_id = int(dest_owner_id)
    
    endpoint = os.path.join(uiconfig.BACKEND_API_ENDPOINT, 'transfer_owner/')
    
    transfer_owner = TransferOwner(
        source_owner_id = source_owner_id,
        dest_owner_id = dest_owner_id
    )
    
    extensions.model_to_post_request(
        endpoint = endpoint,
        base_model = transfer_owner,
        headers=st.session_state['jwt_auth_header']
    )
    

def update_owner_group(owner_group_id: int, name: str):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['owner_group']
    owner_group = OwnerGroup(name=name)
    
    extensions.model_to_put_request(
        endpoint = uiconfig.ENDPOINT_CONFIG['owner_group'],
        pk=owner_group_id,
        base_model = owner_group,
        headers=st.session_state['jwt_auth_header']
    )


def update_user(headers: dict,
                pk_id: int,
                username: str,
                email: str,
                password: str | None,
                owner_group_name: str,
                staging: bool,
                is_active: bool,
                token: str):
    
    # Get owner_group_id
    owner_groups = get_owner_group(headers)
    owner_group_id = owner_groups.loc[
        owner_groups['name'] == owner_group_name,'id'
    ]
    owner_group_id = int(owner_group_id)
    
    # groups
    groups = get_group(headers)
    
    # Reformat groups for each user in binary wide df
    groups.index = groups.pop('id')
    groups_map = groups.to_dict(orient='dict')['name']
    groups_map_inv = {v:k for k,v in groups_map.items()}
    
    # Get appuser group id and staging group id
    groups_create = [groups_map_inv['appuser']]
    
    if staging:
        groups_create.append(groups_map_inv['staging'])
    
    user = User(
        username=username,
        email = email,
        is_active = is_active,
        password = password,
        groups = groups_create,
        appuser = {
            'owner_group' : owner_group_id,
            'token' : token
        }
    )
        
    extensions.model_to_put_request(
        endpoint = uiconfig.ENDPOINT_CONFIG['user'],
        pk=pk_id,
        base_model = user,
        headers=headers
    )

def update_project(headers: dict,
                    project_id: int,
                    name: str,
                    description: str,
                    metadata: dict,
                    dataset_metadata_keys: dict,
                    collaborators: List[int]):
    
    owner_group_id = get_my_owner_group(headers)['id'].values[0]
    
    project = Project(
        id = project_id,
        name = name,
        description = description,
        metadata = metadata,
        dataset_metadata_keys = dataset_metadata_keys,
        owner_group = owner_group_id,
        collaborators = collaborators
    )
    
    endpoint = uiconfig.ENDPOINT_CONFIG['project']
    project_id = extensions.model_to_put_request(
        endpoint = endpoint,
        pk = project_id,
        base_model=project,
        headers=headers
    )


def update_project_collabs(project_id: int,
                        user_ids: str):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['project']
    headers=st.session_state['jwt_auth_header']
    project = extensions.detail_request_to_model(endpoint + str(project_id) + '/', Project, headers=headers)
    
    project.collaborators = user_ids
    
    # Reste timestamps to None to avoid seruialization error
    project.created = None
    project.updated = None
    project.valid_from = None
    project.valid_to = None
            
    project_id = extensions.model_to_put_request(
        endpoint = endpoint,
        pk = project_id,
        base_model=project,
        headers=st.session_state['jwt_auth_header'],
    )

def update_fq_dataset_project(fq_dataset_id: int,
                              add_project_id: int | List[int] = [],
                              remove_project_id: int | List[int] = []):
    
    if isinstance(add_project_id, int):
        add_project_id = [add_project_id]
    if isinstance(remove_project_id, int):
        remove_project_id = [remove_project_id]
    
    # Get Fq Dataset
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
    headers=st.session_state['jwt_auth_header']
    fq_dataset = extensions.detail_request_to_model(endpoint + str(fq_dataset_id) + '/', FqDataset, headers=headers)
    
    # Get project ids associated with fq_dataset
    project = fq_dataset.project
    # Add new project ids
    project.extend(add_project_id)
    # Remove project ids specified in remove_project_id
    project = [p for p in project if p not in remove_project_id]
    
    fq_dataset.project = project
    
    # Reset timestamps to None to avoid serialization error
    fq_dataset.created = None
    fq_dataset.updated = None
    fq_dataset.valid_from = None
    fq_dataset.valid_to = None
    
    # Put Request
    extensions.model_to_put_request(
        endpoint = endpoint,
        pk = fq_dataset_id,
        base_model=fq_dataset,
        headers=st.session_state['jwt_auth_header']
    )

def update_fq_dataset(fq_dataset_id: int,
                    name: str,
                    description: str,
                    metadata: dict,
                    projects: List[int]):
    
    fq_dataset_id = int(fq_dataset_id)
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
    headers=st.session_state['jwt_auth_header']
    fq_dataset = extensions.detail_request_to_model(endpoint + str(fq_dataset_id) + '/', FqDataset, headers=headers)
    
    fq_dataset.name = name
    fq_dataset.description = description
    fq_dataset.metadata = metadata
    fq_dataset.project = projects
    
    # Reset timestamps to None to avoid serialization error
    fq_dataset.created = None
    fq_dataset.updated = None
    fq_dataset.valid_from = None
    fq_dataset.valid_to = None
    
    # Put Request
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
    extensions.model_to_put_request(
        endpoint = endpoint,
        pk = fq_dataset_id,
        base_model=fq_dataset,
        headers=st.session_state['jwt_auth_header']
    )
    
def checkin_fq_file_staging(headers: dict,
                            fq_file_id: int,
                            name: str,
                            bucket: str,
                            key: str,
                            upload_path: str,
                            qc_passed: bool,
                            read_type: str,
                            read_length: int,
                            num_reads: int,
                            qc_phred_mean: float,
                            qc_phred: dict,
                            size_mb: int,
                            md5_checksum: str,
                            pipeline_version: str):
    
    owner = get_my_user(headers).id
    
    fq_file = FqFile(
        id = fq_file_id,
        name = name,
        bucket = bucket,
        key = key,
        upload_path = upload_path,
        qc_passed = qc_passed,
        read_type = read_type,
        read_length = read_length,
        num_reads = num_reads,
        qc_phred_mean = qc_phred_mean,
        qc_phred = qc_phred,
        size_mb = size_mb,
        staging = False,
        md5_checksum = md5_checksum,
        pipeline_version = pipeline_version,
        owner = owner)
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_file']
    extensions.model_to_put_request(
        endpoint = endpoint,
        pk = fq_file_id,
        base_model=fq_file,
        headers=headers
    )                      

def update_fq_file(fq_file: FqFile):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_file']
    
    fq_file.created = None
    fq_file.updated = None
    fq_file.valid_from = None
    fq_file.valid_to = None
    
    extensions.model_to_put_request(
        endpoint = endpoint,
        pk = fq_file.id,
        base_model=fq_file,
        headers=st.session_state['jwt_auth_header']
    )

#region DELETE
def delete_owner_group(headers: dict,
                    owner_group_name: str):
    
    owner_groups = get_owner_group(headers)
    owner_group_users = get_owner_group_appusers(headers)
        
    assert owner_group_name in owner_groups['name'].tolist(), 'Owner Group not Found for Delete'
    
    delete_group_users = owner_group_users.loc[
        owner_group_users['name'] == owner_group_name,:
    ]
        
    # Check that so users are attached to group
    if delete_group_users.empty:
        
        # Get primary key for owner_group
        pk = owner_groups.loc[
            owner_groups['name'] == owner_group_name,'id'
        ]
        
        endpoint = uiconfig.ENDPOINT_CONFIG['owner_group']
    
        extensions.pk_to_delete_request(
            endpoint,
            int(pk),
            headers=headers
        )

    else:
        raise exceptions.UIAppError('Owner Group not Empty')

def delete_user(user_id: int):
    
    user_id = int(user_id)
    
    endpoint = uiconfig.ENDPOINT_CONFIG['user']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(user_id),
        headers=st.session_state['jwt_auth_header']
    )

def delete_project(project_id: int):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['project']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(project_id),
        headers=st.session_state['jwt_auth_header']
    )

def delete_project_attachment(project_attachment_id: int):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['project_attachment']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(project_attachment_id),
        headers=st.session_state['jwt_auth_header']
    )

def delete_fq_file(fq_file_id: int):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_file']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(fq_file_id),
        headers=st.session_state['jwt_auth_header']
    )

def delete_fq_dataset(fq_dataset_id: int):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(fq_dataset_id),
        headers=st.session_state['jwt_auth_header']
    )

def delete_fq_attachment(fq_attachment_id: int):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_attachment']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(fq_attachment_id),
        headers=st.session_state['jwt_auth_header']
    )

def delete_pro_data(pro_data_id: int):
    
    endpoint = uiconfig.ENDPOINT_CONFIG['pro_data']
    
    extensions.pk_to_delete_request(
        endpoint,
        int(pro_data_id),
        headers=st.session_state['jwt_auth_header']
    )

#region FILES

def get_project_attachment_file_download(pk: int) -> bytes:
        
    endpoint = uiconfig.ENDPOINT_CONFIG['project_attachment']
    headers=st.session_state['jwt_auth_header']
    model = extensions.detail_request_to_model(endpoint + str(pk) + '/', ProjectAttachment, headers=headers)

    return model.body

def get_fq_attachment_file_download(pk: int) -> bytes:
        
    endpoint = uiconfig.ENDPOINT_CONFIG['fq_attachment']
    headers=st.session_state['jwt_auth_header']
    model = extensions.detail_request_to_model(endpoint + str(pk) + '/', FqAttachment, headers=headers)

    return model.body
