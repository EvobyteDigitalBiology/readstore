# readstore-basic/frontend/streamlit/uidataclasses.py

from pydantic import BaseModel, Json

"""
Provides pydantic data classes for data validation and serialization.

Classes:

Usage:

Example:

"""

import base64
from typing_extensions import Annotated
from typing import Optional
import datetime

from pydantic import BaseModel
from pydantic import EncoderProtocol
from pydantic import EncodedBytes
from pydantic import Base64Bytes

# ENCODERS

class Base64Encoder(EncoderProtocol):
    """Encode bytes to base64 string for serialization.

    Input bytes are base 64 encoded adn concerted to UTF-8 string 
    for serialization (decode).
    If attibute string is encoded, only the string is returned,
    for instance for calling model dump method
    """
    
    @classmethod
    # Encoded value is returned to string
    def encode(cls, value: str) -> str:
        return value
    
    @classmethod
    def decode(cls, value: EncodedBytes) -> bytes:
        return base64.b64encode(value)

Base64EncodedBytes = Annotated[bytes, EncodedBytes(encoder=Base64Encoder)]

class Group(BaseModel):
    id: int
    name: str

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    password: Optional[str] = None
    is_active: bool
    groups: list[int]
    date_joined: Optional[datetime.datetime] = None
    appuser: Optional[dict] = None

class OwnerGroup(BaseModel):
    id: Optional[int] = None
    name: str
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None

class Project(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    metadata: dict
    dataset_metadata_keys: dict
    collaborators: list[int] = []
    owner_group: int
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None
    owner_username: Optional[str] = None

class ProjectAttachment(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    path: str
    filetype: str
    size_mb: float
    body: Optional[Base64Bytes] = None
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None
    project: int

class ProjectAttachmentPost(BaseModel):
    name: str
    description: str
    path: str
    filetype: str
    size_mb: float
    body: Base64EncodedBytes
    project: int
    
class FqFile(BaseModel):
    id: int
    name: str
    bucket: str
    key: str
    upload_path: str
    qc_passed: bool
    read_type: str
    read_length: int
    num_reads: int
    qc_phred_mean: float
    qc_phred: dict
    size_mb: int
    staging: bool
    md5_checksum: str
    pipeline_version: str
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: int

class FqDataset(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    qc_passed: bool
    fq_file_r1: Optional[int] = None    
    fq_file_r2: Optional[int] = None
    fq_file_i1: Optional[int] = None
    fq_file_i2: Optional[int] = None
    paired_end: bool
    index_read: bool
    owner_group: int
    owner_group_name: Optional[str] = None
    project: list[int] = []
    metadata: dict
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None
    owner_username: Optional[str] = None

class FqAttachment(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    path: str
    filetype: str
    size_mb: float
    body: Optional[Base64Bytes] = None
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None
    fq_dataset: int

class FqAttachmentPost(BaseModel):
    name: str
    description: str
    path: str
    filetype: str
    size_mb: float
    body: Base64EncodedBytes
    fq_dataset: int
    
class URL(BaseModel):
    url: str
    
class LicenseKey(BaseModel):
    id: Optional[int] = None
    key: str
    seats: int
    expiration_date: datetime.datetime
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None
    
class FqQueue(BaseModel):
    num_jobs: int
    
class FqFileUploadApp(BaseModel):
    fq_file_name: str
    fq_file_path: str
    read_type: str

class InvalidPath(BaseModel):
    id: int
    upload_path: str
    
class ProData(BaseModel):
    id: Optional[int] = None
    name: str
    data_type: str
    description: str
    version: Optional[int] = None
    upload_path: str
    metadata: dict
    fq_dataset: int
    created: Optional[datetime.datetime] = None
    updated: Optional[datetime.datetime] = None
    valid_from: Optional[datetime.datetime] = None
    valid_to: Optional[datetime.datetime] = None
    owner: Optional[int] = None
    owner_username: Optional[str] = None
    
class TransferOwner(BaseModel):
    source_owner_id: int
    dest_owner_id: int