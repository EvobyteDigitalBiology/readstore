# readstore-basic/cli/rsclient.py

import requests
from urllib.parse import urlparse
import json
import hashlib
import os
import math
import datetime
import uuid
import base64
import string
import random
from typing import Tuple, List, Dict

import rsexceptions


class RSClient():
    
    REST_API_VERSION = "api_v1/"
    USER_AUTH_TOKEN_ENDPOINT = "user/auth_token/"
    FASTQ_UPLOAD_ENDPOINT = "fq_file_upload/"
    FQ_DATASET_ENDPOINT = "fq_dataset/token/"
    FQ_FILE_ENDPOINT = "fq_file/token/"
    FQ_ATTACHMENT_ENDPOINT = "fq_attachment/token/"
    PROJECT_ENDPOINT = "project/token/"
    PROJECT_ATTACHMENT_ENDPOINT = "project_attachment/token/"
    UPLOAD_CHUNK_SIZE_MB = 100
    
    def __init__(self, username: str, token: str, endpoint_url: str, output_format: str):
        
        self.username = username
        self.token = token
        self.endpoint = f"{endpoint_url}/{self.REST_API_VERSION}"
        self.output_format = output_format
        
        if not self._test_server_connection():
            raise rsexceptions.ReadStoreError(f'Server Connection Failed\nEndpoint URL: {self.endpoint}')

        if not self._auth_user_token():
            raise rsexceptions.ReadStoreError(f'User Authentication Failed\nUsername: {self.username}')

    def _test_server_connection(self) -> bool:
        """
            Validate server URL
            
            Returns:
                True if server can be reached else False
        """
        
        parsed_url = urlparse(self.endpoint)
        
        if not parsed_url.scheme in ["http", "https"]:
            return False
        else:
            try:
                response = requests.head(self.endpoint)
                
                if response.status_code == 200:
                    return True
                else:
                    return False
            except requests.exceptions.ConnectionError:
                return False
    
    def _auth_user_token(self) -> bool:
        """
            Validate user and token
            
            Returns:
                True if user token is valid else False
        """
        
        try:
            auth_endpoint = os.path.join(self.endpoint, self.USER_AUTH_TOKEN_ENDPOINT)
            
            payload = {'username': self.username,
                        'token': self.token}
            
            res = requests.post(auth_endpoint, json=payload)
            
            if res.status_code != 200:
                return False
            else:
                return True
        
        except requests.exceptions.ConnectionError:
            return False
        
    # def _generate_short_uuid(self) -> str:
    #     """Generate short uuid.

    #     Generate a short uuid.
    #     Length is defined to 22 chars.
    #     UUIDs contain only alphanumeric characters.
        
    #     Returns:
    #         (str): short uuid
    #     """
        
    #     # Generate a UUID4
    #     uuid_bytes = uuid.uuid4().bytes
        
    #     # Encode the UUID bytes to base64
    #     base64_uuid = base64.urlsafe_b64encode(uuid_bytes)
        
    #     # Decode base64 bytes to string and remove padding characters
    #     short_uuid = base64_uuid.decode('utf-8').rstrip('=')
        
    #     allowed_chars = string.digits + string.ascii_lowercase + string.ascii_uppercase
        
    #     # Remove any underscores and dashes by random char
    #     short_uuid = short_uuid.replace('_',
    #                                     allowed_chars[random.randint(0, len(allowed_chars) - 1)])
    #     short_uuid = short_uuid.replace('-',
    #                                     allowed_chars[random.randint(0, len(allowed_chars) - 1)])
        
    #     return short_uuid
    
    # def _get_fastq_presigned_url(self, s3_key: str) -> Tuple[str, dict]: 
    #     """Get presigned URL for Fastq Upload

    #     Args:
    #         s3_key: AWS S3 key for upload

    #     Raises:
    #         rsexceptions.ReadStoreError: If request failed

    #     Returns:
    #         Tuple[str, dict]: URL and fields
    #     """
        
    #     payload = {'username': self.username,
    #                 'token': self.token,
    #                 'fastq_s3_key': s3_key}
        
    #     upload_url_endpoint = os.path.join(self.endpoint, self.PRESIGNED_FASTQ_URL_ENDPOINT)
    #     upload_url_endpoint = upload_url_endpoint.strip('/') + '/'
        
    #     res = requests.post(upload_url_endpoint, json=payload)
        
    #     if res.status_code != 200:
    #         res_message = res.json().get('message', 'No Message')
    #         raise rsexceptions.ReadStoreError(f'Upload URL Request Failed: {res_message}')
    #     else:
    #         assert 'url' in res.json(), 'fastq_url Presigned URL Not Found'
        
    #     # Get url and fields
    #     url = res.json().get('url')['url']
    #     fields = res.json().get('url')['fields']
        
    #     return url, fields
    
    def get_output_format(self) -> str:
        """
            Get Output Format set for client
            
            Return:
                str output format
        """
        
        return self.output_format
    
    def upload_fastq(self, fastq_files: List[str] | str):
        """
            Upload Fastq Files
        """
        
        if isinstance(fastq_files, str):
            fastq_files = [fastq_files]
        
        fq_upload_endpoint = os.path.join(self.endpoint, self.FASTQ_UPLOAD_ENDPOINT)
        
        # Run parallel uploads of fastq files
        for fq_file in fastq_files:
            
            fq_file = os.path.abspath(fq_file)
            
            # Make sure file exists and 
            if not os.path.exists(fq_file):            
                raise rsexceptions.ReadStoreError(f'File Not Found: {fq_file}')
            elif not os.access(fq_file, os.R_OK):
                raise rsexceptions.ReadStoreError(f'No read permissions: {fq_file}')
            
            payload = {'username': self.username,
                        'token': self.token,
                        'fq_file_path': fq_file}
            
            res = requests.post(fq_upload_endpoint, json=payload)
        
            if not res.status_code in [200,204]:        
                res_message = res.json().get('message', 'No Message')
                raise rsexceptions.ReadStoreError(f'Upload URL Request Failed: {res_message}')
            
        
    def get_fq_file(self, fq_file_id: int) -> Dict:
        """
            Get Fastq File
            
            Args:
                fq_file_id: ID of fq_file
                
            Return dict with fq file data
        """
        
        fq_file_endpoint = os.path.join(self.endpoint, self.FQ_FILE_ENDPOINT)
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token,
            'fq_file_id': fq_file_id
        }
        
        res = requests.post(fq_file_endpoint, json = json)
        
        if not res.status_code in [200,204]:                
            raise rsexceptions.ReadStoreError(f'get_fq_file Failed')
        else:
            return res.json()[0]
    
    def get_fq_file_upload_path(self, fq_file_id: int) -> str:
        """Get FASTQ file upload  path
        
        Get upload path for FASTQ file

        Args:
            fq_file_id: ID of FASTQ file

        Raises:
            rsexceptions.ReadStoreError: If upload_path is not found

        Returns:
            str: Upload path
        """
        
        fq_file = self.get_fq_file(fq_file_id)
        
        if not 'upload_path' in fq_file:
            raise rsexceptions.ReadStoreError('upload_path Not Found in FqFile entry')
    
        return fq_file.get('upload_path')
    
    def list_fastq_datasets(self,
                            project_name: str | None = None,
                            project_id: int | None = None,
                            role: str | None = None) -> List[dict]:
        """
            List FASTQ Datasets
            
            List FASTQ datasets and filter by project_name, project_id and role
            
            Args:
                project_name: Filter for project name
                project_id: Filter for project ID
                role: Filter for owner role (owner, collaborator, creator)
                
            Raises:
                rsexceptions.ReadStoreError if role is not valid or if request failed
                
            Returns:
                List[Dict]: FASTQ datasets
        """
        
        fq_dataset_endpoint = os.path.join(self.endpoint, self.FQ_DATASET_ENDPOINT)
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token,
        }
        
        if role:
            if role.lower() in ['owner', 'collaborator', 'creator']:
                json['role'] = role
            else:
                raise rsexceptions.ReadStoreError('Invalid Role') 
        
        if project_name:
            json['project_name'] = project_name
        if project_id:
            json['project_id'] = project_id
        
        res = requests.post(fq_dataset_endpoint, json = json)
        
        if not res.status_code in [200,204]:                
            raise rsexceptions.ReadStoreError(f'list_fastq_datasets Failed')
        else:
            return res.json()
    

    def get_fastq_dataset(self,
                        dataset_id: int | None = None,
                        dataset_name: str | None = None) -> Dict:
        """Get FASTQ dataset

        Get FASTQ dataset by provided dataset_id and name
        
        If dataset_name is not unique an error is printed
        
        Args:
            dataset_id: ID to select
            dataset_name: Name to select

        Raises:
            rsexceptions.ReadStoreError: If backend request failed

        Returns:
            Dict: Detail response
        """
        
        
        fq_dataset_endpoint = os.path.join(self.endpoint, self.FQ_DATASET_ENDPOINT)
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token
        }
        if dataset_id:
            json['dataset_id'] = dataset_id
        if dataset_name:
            json['dataset_name'] = dataset_name
            
        res = requests.post(fq_dataset_endpoint, json = json)
        
        # Remove entries not requested
        if not res.status_code in [200,204]:
            raise rsexceptions.ReadStoreError(f'get_fastq_dataset Failed')
        else:
            # If no dataset found, return empty dict
            if len(res.json()) == 0:
                return {}
            # If several datasets found, return error
            elif len(res.json()) > 1:
                raise rsexceptions.ReadStoreError(f'Multiple Datasets Found.\nThis can happen if datasets with identical name were shared with you.\nUse dataset_id to get the correct dataset.')
            else:
                return res.json()[0]
            return res_json
    
    
    def list_projects(self,
                    role: str | None = None) -> List[Dict]:
        """
            List Projects
            
            Filter projects by role
            
            Args:
                role: Owner role to filter (owner, collaborator, creator)
            
            Raises: rsexceptions.ReadStoreError
            
            Returns:
                List[Dict]: List of projects
        """
        
        project_endpoint = os.path.join(self.endpoint, self.PROJECT_ENDPOINT)
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token
        }
        
        if role:
            if role.lower() in ['owner', 'collaborator', 'creator']:
                json['role'] = role
            else:
                raise rsexceptions.ReadStoreError('Invalid Role') 
        
        res = requests.post(project_endpoint, json = json)
        
        if not res.status_code in [200,204]:                
            raise rsexceptions.ReadStoreError(f'list_projects Failed')
        else:
            return res.json()

    def get_project(self,
                    project_id: int | None = None,
                    project_name: str | None = None) -> Dict:
        """
            Get Project by id or name
            
            Return project by id or name
            If name is duplicated, print error message
            
            Args:
                project_id: Project ID
                project_name: Project Name

            Raise
                rsexceptions.ReadStoreError: If request failed
                rsexceptions.ReadStoreError: If duplicate names are found
            
            Returns:
                project detail response
        """
        
        assert project_id or project_name, 'project_id or project_name Required'
        
        project_endpoint = os.path.join(self.endpoint, self.PROJECT_ENDPOINT)
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token
        }
        
        if project_id:
            json['project_id'] = project_id
        if project_name:
            json['project_name'] = project_name
        
        res = requests.post(project_endpoint, json = json)
        
        if not res.status_code in [200,204]:                
            raise rsexceptions.ReadStoreError(f'get_project Failed')
        else:
            if len(res.json()) == 0:
                return {}
            # If several datasets found, return error
            elif len(res.json()) > 1:
                raise rsexceptions.ReadStoreError(f'Multiple Projects Found.\nThis can happen if Projects with identical name were shared with you.\nUse unique Project ID to access the correct dataset.')
            else:
                return res.json()[0]
            
            
    def download_project_attachment(self,
                                    attachment_name: str,
                                    outpath: str,
                                    project_id: int | None = None,
                                    project_name: str | None = None):
        """Project Attachments
        
        Download Project Attachments

        Args:
            attachment_name: Attachment name
            outpath: Path to write to
            project_id: Id of project
            project_name: Project name.

        Raises:
            rsexceptions.ReadStoreError: Request failed
            rsexceptions.ReadStoreError: Attachment not Found
            rsexceptions.ReadStoreError: Multiple Attachments Found for Project.
        """
        
        
        project_attachment_endpoint = os.path.join(self.endpoint, self.PROJECT_ATTACHMENT_ENDPOINT)
        
        assert project_id or project_name, 'project_id or project_name Required'
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token,
            'attachment_name' : attachment_name
        }
        
        if project_id:
            json['project_id'] = project_id
        if project_name:
            json['project_name'] = project_name
        
        res = requests.post(project_attachment_endpoint, json = json)
        
        if not res.status_code in [200,204]:                
            raise rsexceptions.ReadStoreError(f'download_project_attachment failed')
        elif len(res.json()) == 0:
            raise rsexceptions.ReadStoreError(f'Attachment Not Found')
        elif len(res.json()) > 1:
            raise rsexceptions.ReadStoreError(f'Multiple Attachments Found For Project.This can happen if Projects with identical name were shared with you.\nUse unique Project ID to access the correct attachment.')
        else:
            attachment = res.json()[0]
            with open(outpath, 'wb') as fh:
                fh.write(base64.b64decode(attachment['body']))
                
    def download_fq_dataset_attachment(self,
                                       attachment_name: str,
                                       outpath: str,
                                       dataset_id: int | None = None,
                                       dataset_name: str | None = None):
        """Fastq Attachments
        
        Download Fastq Attachments

        Args:
            attachment_name: Attachment name
            outpath: Path to write to
            dataset_id: Id of project
            dataset_name: Project name.

        Raises:
            rsexceptions.ReadStoreError: Request failed
            rsexceptions.ReadStoreError: Attachment not Found
            rsexceptions.ReadStoreError: Multiple Attachments Found for Project.
        """

        
        fq_dataset_endpoint = os.path.join(self.endpoint, self.FQ_ATTACHMENT_ENDPOINT)
        
        assert dataset_id or dataset_name, 'dataset_id or dataset_name required'
        
        # Define json for post request
        json = {
            'username': self.username,
            'token': self.token,
            'attachment_name' : attachment_name
        }
        
        if dataset_id:
            json['dataset_id'] = dataset_id
        if dataset_name:
            json['dataset_name'] = dataset_name
        
        res = requests.post(fq_dataset_endpoint, json = json)
        
        if not res.status_code in [200,204]:                
            raise rsexceptions.ReadStoreError(f'download_fq_dataset_attachment failed')
        elif len(res.json()) == 0:
            raise rsexceptions.ReadStoreError(f'Attachment Not Found')
        elif len(res.json()) > 1:
            raise rsexceptions.ReadStoreError(f'Multiple Attachments Found For Dataset.This can happen if Datasets with identical name were shared with you.\nUse unique Dataset ID to access the correct attachment.')
        else:
            attachment = res.json()[0]
            with open(outpath, 'wb') as fh:
                fh.write(base64.b64decode(attachment['body']))
