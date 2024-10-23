# readstore-basic/backend/app/models.py

import string
import uuid
import base64
import random

from django.db import models
from django.contrib.auth.models import User


def generate_short_uuid() -> str:
    """Generate short uuid.

    Generate a short uuid.
    Length is defined to 22 chars.
    UUIDs contain only alphanumeric characters.
    
    Returns:
        (str): short uuid
    """
    
    ALNUM_CHARS = string.ascii_letters + string.digits
    
    # Generate a UUID4
    uuid_bytes = uuid.uuid4().bytes
    
    # Encode the UUID bytes to base64
    base64_uuid = base64.urlsafe_b64encode(uuid_bytes)
    
    # Decode base64 bytes to string and remove padding characters
    short_uuid = base64_uuid.decode('utf-8').rstrip('=')
    
    # Remove any underscores and dashes by random char
    short_uuid = short_uuid.replace('_',
                                    ALNUM_CHARS[random.randint(0, len(ALNUM_CHARS) - 1)])
    short_uuid = short_uuid.replace('-',
                                    ALNUM_CHARS[random.randint(0, len(ALNUM_CHARS) - 1)])

    return short_uuid


# Extend User class for project
class AppUser(models.Model):
    """
        Profile for User Model
    """
    
    user = models.OneToOneField(User, related_name='appuser', on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=200, default=generate_short_uuid)
    owner_group = models.ForeignKey('OwnerGroup', on_delete=models.PROTECT, null=True)
    
    def __str__(self):
        return self.user.username
    
    def regenerate_token(self):
        self.token = generate_short_uuid()
        self.save()
    
# Abstract models for Django
class BasicModel(models.Model):  
    """
        Basic Model extension for Django models.Model
        Add default fields generally used in Evo Models
    """
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    valid_from = models.DateTimeField(auto_now=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        abstract = True

class PipelineModel(BasicModel):
    """
        Pipeline Model extension for Django models.Model
        Add default fields generally used in Evo Models
    """
    
    pipeline_version = models.TextField()
    
    class Meta:
        abstract = True

class BasicFileModel(BasicModel):
    
    """
        BasicFileModel extension for BasicModel
        Add default fields generally used for file definitions
    """
    
    name = models.TextField(unique=True) # Needs to be updated
    description = models.TextField(blank=True, null=True)
    path = models.TextField()
    filetype = models.CharField(max_length=150)
    size_mb = models.IntegerField()
    
    class Meta:
        abstract = True

class FlatFileModel(BasicFileModel):
    
    """
        Flat File Model extension for Django models.Model
        Add default fields generally used in Evo Models
    """
    
    body = models.TextField()
    
    class Meta:
        abstract = True

class BinaryFileModel(BasicFileModel):
    
    """
        Flat File Model extension for Django models.Model
        Add default fields generally used in Evo Models
    """
    
    body = models.BinaryField()
    
    class Meta:
        abstract = True
        
class ObjectStoreModel(BasicFileModel):
    
    """
        Object Store Model extension for Django models.Model
        Add default fields generally used in Evo Models
    """
    
    s3_bucket = models.TextField()
    s3_key = models.TextField()
    
    class Meta:
        abstract = True
    
# MODELS

class OwnerGroup(BasicModel):
    
    """
        OwnerGroup Model
    """
    
    name = models.CharField(max_length=200, unique=True)
    
    class Meta:
        db_table = 'owner_group'


class FqFile(PipelineModel):
    
    """
        FqFile Model to manage uploaded files
        with S3 bucket and key fields
    """
    
    class ReadType(models.TextChoices):
        READ1 = 'R1'
        READ2 = 'R2'
        INDEX1 = 'I1'
        INDEX2 = 'I2'
        NA = 'NA'
    
    name = models.TextField()
    bucket = models.TextField(blank=True, null=True)
    key = models.TextField(blank=True, null=True)
    upload_path = models.TextField()
    qc_passed = models.BooleanField()
    read_type = models.CharField(choices=ReadType.choices, default=ReadType.NA, max_length=20)
    read_length = models.IntegerField()
    num_reads = models.IntegerField()
    qc_phred_mean = models.FloatField()
    qc_phred = models.JSONField() 
    size_mb = models.IntegerField()
    staging = models.BooleanField()
    md5_checksum = models.TextField()
    
    class Meta:
        db_table = 'fq_file'
        #unique_together = ('bucket', 'key')
        
class Project(BasicModel):
    
    """
        Project Model
    """
    
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    metadata  = models.JSONField()
    dataset_metadata_keys = models.JSONField()
    collaborators = models.ManyToManyField(User, related_name='projects', blank=True)
    owner_group = models.ForeignKey(OwnerGroup, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'project'
        unique_together = ('name', 'owner_group')
        
                
class ProjectAttachment(BinaryFileModel):
    
    """
        Project Attachments to store binary files. 
    """
    
    name = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'project_attachment'
        unique_together = ('name', 'project')
       

class FqDataset(BasicModel):
    
    """
        Model to organize FqFiles and metadata
    """
    
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    qc_passed = models.BooleanField()
    fq_file_r1 = models.OneToOneField(FqFile, related_name='fq_file_r1', on_delete=models.CASCADE, null=True, blank=True)
    fq_file_r2 = models.OneToOneField(FqFile, related_name='fq_file_r2', on_delete=models.CASCADE, null=True, blank=True)
    fq_file_i1 = models.OneToOneField(FqFile, related_name='fq_file_i1', on_delete=models.CASCADE, null=True, blank=True)
    fq_file_i2 = models.OneToOneField(FqFile, related_name='fq_file_i2', on_delete=models.CASCADE, null=True, blank=True)
    paired_end = models.BooleanField()
    index_read = models.BooleanField()
    owner_group = models.ForeignKey(OwnerGroup, on_delete=models.CASCADE)
    project = models.ManyToManyField(Project, related_name='fq_datasets', blank=True)
    metadata = models.JSONField()

    class Meta:
        db_table = 'fq_dataset'
        unique_together = ('name', 'owner_group')


class FqAttachment(BinaryFileModel):
    
    """
        Model to store binary files for FqDatasets. 
    """
    
    name = models.TextField()
    fq_dataset = models.ForeignKey(FqDataset, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'fq_attachment'
        unique_together = ('name', 'fq_dataset')
        
class LicenseKey(BasicModel):
    
    """
        LicenseKeys Model
    """
    
    key = models.TextField()
    seats = models.IntegerField()
    expiration_date = models.DateTimeField()
    
    class Meta:
        db_table = 'license_keys'
        
    