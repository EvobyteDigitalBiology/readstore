# readstore-basic/backend/app/serializers.py

"""
    Module containing serializers for the Django REST API.
"""

import os
import base64
import string

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework import status

from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings

from .models import AppUser
from .models import OwnerGroup
from .models import FqFile
from .models import FqDataset
from .models import FqAttachment
from .models import Project
from .models import ProjectAttachment
from .models import LicenseKey
from .models import ProData

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.models import update_last_login

from settings.base import VALID_READ_TYPE
from settings.base import METADATA_RESERVED_KEYS


# Validation Functions
def _validate_charset(query_str: str) -> bool:
    """
    Validate charset for query string

    Args:
        query_str (str): Query string to validate

    Returns:
        bool: 
    """
    
    allowed = string.digits + string.ascii_lowercase + string.ascii_uppercase + '_-.@'
    allowed = set(allowed)
    
    return set(query_str) <= allowed


def _validate_metadata(metadata: dict) -> dict:
    """
    Validate metadata dict

    Ensure keys are non-empty, valid charset and not reserved

    Args:
        metadata (dict): Metadata dict to validate

    Returns:
        dict: Validated metadata dict
    
    Raises:
        rsexceptions.ReadStoreError: If key is invalid
    """
    
    for key, value in metadata.items():
        if key == '':
            raise ValidationError({'detail' : 'Empty metadata key'}, code=400)
        if not _validate_charset(key):
            raise ValidationError({'detail' : 'Invalid character in metadata key. Must be alphanumeric or _-.@'}, code=400)
        if key in METADATA_RESERVED_KEYS:
            raise ValidationError({'detail' : f'Reserved Keyword not allowed in metadata key: {key}'}, code=400)
        
        # Replace None values with empty string
        if value is None:
            metadata[key] = ''
    else:
        return metadata


# Additional Fields
class BinarySerializerField(serializers.Field):
    """
        Custom serializer field for binary data
    """
    def to_representation(self, value):
        # Takes incoming bytes and encodes to base64 encoded UTF8 string to serialize
        #return base64.b64encode(value).decode('utf-8')
        return base64.b64encode(value)

    def to_internal_value(self, value):
        # Takes incoming base64 encoded UTF8 string and decodes to bytes
        # return base64.b64decode(value.encode('utf-8'))
        return base64.b64decode(value)

# Extended JWT Auth Method
 
class InActiveUser(AuthenticationFailed):
    """HTTP Response for inactive user
    """
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "User is inactive"
    default_code = 'user_is_inactive'

class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    """Custom Serializer for JWT Token Obtain Pair 

    Raises:
        ValidationError: If username not in request json data
        InActiveUser: If user is inactive

    Returns:
        data: Validated serialized data
    """
    
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):

        # Try to get user and check if user is active
        username = attrs.get(self.username_field)
        if username is None:
            raise ValidationError('No username provided')

        user = User.objects.filter(username=username).first()
        if user and (not user.is_active):
            raise InActiveUser()

        # This step sets the user
        data = super().validate(attrs)
        
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class GroupSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Group
        fields = ['id', 'name']


class OwnerGroupSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OwnerGroup
        fields = '__all__'
        
        extra_kwargs = {
                "owner": {"read_only": True},
            }


class AppUserSerializer(serializers.ModelSerializer):
    
    # Like this?
    owner_group = serializers.PrimaryKeyRelatedField(queryset=OwnerGroup.objects.all(),
                                                     many=False,
                                                     allow_null=True)
        
    class Meta:
        model = AppUser
        fields = ['token', 'owner_group']


class UserSerializer(serializers.ModelSerializer):
    
    appuser = AppUserSerializer(many=False, required=False)
    
    class Meta:
        model = User
        fields = ['id','username', 'password', 'email', 'is_active', 'groups', 'date_joined', 'appuser']
        
        extra_kwargs = {
                "password": {"write_only": True, "required": False, "allow_null": True},
                "username": {"required": True},
                "date_joined" :{"read_only" : True}
            }
        
    def create(self, validated_data: dict) -> User:
        """Create User and AppUser objects

        Create AppUser object if appuser_data are in dict
        
        Args:
            validated_data: Serialized data

        Returns:
            User: Created User object
        """
        
        # Extract appuser, groups and pwd from validated_data
        # TODO Check accepts Empty password
        appuser_data = validated_data.pop('appuser', None)
        groups = validated_data.pop('groups', None)
        pwd = validated_data.pop('password')
        
        # Create User object
        user = User.objects.create(**validated_data)
        user.set_password(pwd)
        user.groups.set(groups)
        user.save()
        
        #  Create AppUser object if appuser_data is present
        if appuser_data:
            app_user = AppUser(
                user = user,
                owner_group = appuser_data['owner_group']
            )
            app_user.save()
        
        return user

    def update(self, instance, validated_data: dict):
        """Update User and AppUser objects
        
        Update AppUser object if appuser_data are in dict
        Update password if password is in dict
        Set groups if groups are in dict

        Args:
            instance: User object
            validated_data: Serialized data

        Returns:
            instance: Updated User object
        """
        
        object_id = instance.id

        # Extract appuser, groups and pwd from validated_data
        appuser_data = validated_data.pop('appuser', None)
        groups = validated_data.pop('groups', [])
        pwd = validated_data.pop('password', None)
        
        # Update validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if appuser_data:       
            # Check if appuser exists
            if hasattr(instance, 'appuser'):
                for attr, value in appuser_data.items():
                        setattr(instance.appuser, attr, value)
                else:
                    instance.appuser.save()
            else:
                app_user = AppUser(user = instance,
                        owner_group = appuser_data['owner_group'])
                
                app_user.save()
        
        # Update groups
        if groups:
            instance.groups.set(groups)
        
        # Update password
        if pwd:
            instance.set_password(pwd)    
        
        instance.save()
        return instance

class TransferOwnerSerializer(serializers.Serializer):
    
    source_owner_id = serializers.PrimaryKeyRelatedField(queryset = User.objects.all())
    dest_owner_id = serializers.PrimaryKeyRelatedField(queryset = User.objects.all())
    

class FqFileRStoreURLSerializer(serializers.Serializer):
    
    username = serializers.CharField(max_length=150, required=True, trim_whitespace=True)
    token = serializers.CharField(max_length=200,required=True, trim_whitespace=True)
    s3_key = serializers.CharField(max_length=1000,required=True, trim_whitespace=True)


class FqFileMultiPartURLSerializer(serializers.Serializer):
    
    username = serializers.CharField(max_length=150, required=True, trim_whitespace=True)
    token = serializers.CharField(max_length=200,required=True, trim_whitespace=True)
    fastq_s3_key = serializers.CharField(max_length=1000,required=True, trim_whitespace=True)


class FqFileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FqFile
        fields = '__all__'

    # TODO: Add validations for fields

class FqFileCLISerializer(serializers.Serializer):
    
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    read_type = serializers.CharField()
    qc_passed = serializers.BooleanField()
    read_length = serializers.IntegerField()
    num_reads = serializers.IntegerField()
    size_mb = serializers.IntegerField()
    qc_phred_mean = serializers.FloatField()
    created = serializers.DateTimeField()
    creator = serializers.CharField()
    upload_path = serializers.CharField()
    md5_checksum = serializers.CharField()

class FqFileCLIUploadSerializer(serializers.Serializer):
    
    name = serializers.CharField(max_length=200,trim_whitespace=True)
    read_type = serializers.CharField(max_length=10,trim_whitespace=True)
    qc_passed = serializers.BooleanField()
    read_length = serializers.IntegerField()
    num_reads = serializers.IntegerField()
    size_mb = serializers.IntegerField()
    qc_phred_mean = serializers.FloatField()
    qc_phred = serializers.JSONField()
    upload_path = serializers.CharField()
    md5_checksum = serializers.CharField()
    staging = serializers.BooleanField()
    pipeline_version = serializers.CharField()

    def validate(self, attrs):
        
        # Validate charset in name
        name = attrs.get('name')
        read_type = attrs.get('read_type')
        upload_path = attrs.get('upload_path')
        qc_phred = attrs.get('qc_phred')
        
        if not _validate_charset(name):
            raise ValidationError({'detail' : 'Invalid character in name. Must be alphanumeric or _-.@'}, code=400)
        
        # Validate that read type is valid
                    
        # Validate that qc phred is a valid dict
        qc_phred_index_pos = list(qc_phred.keys())
        qc_phred_values = list(qc_phred.values())
        
        if not all([x.isnumeric() for x in qc_phred_index_pos]):
            raise ValidationError({'detail' : 'Invalid qc_phred index values. Must be numeric string'}, code=400)
        if not all(isinstance(x, float) for x in qc_phred_values):
            raise ValidationError({'detail' : 'Invalid qc_phred values. Must be float'}, code=400)
        if not qc_phred_index_pos[0] == '0':
            raise ValidationError({'detail' : 'qc_phred index must start with 0'}, code=400)
        # Check that qc_phred index is continuous
        
        qc_phred_index_int = [int(x) for x in qc_phred_index_pos]
        if not qc_phred_index_int == list(range(0, len(qc_phred_index_int))):
            raise ValidationError({'detail' : 'qc_phred index must be continuous'}, code=400)
        # Check that qc_phred_values are > 0
        if not all([x > 0 for x in qc_phred_values]):
            raise ValidationError({'detail' : 'qc_phred values must be > 0'}, code=400)
            
        if not read_type in VALID_READ_TYPE:
            raise ValidationError({'detail' : 'Invalid read type'}, code=400)

        # Check that file path is found
        if not os.path.exists(upload_path):
            raise ValidationError({'detail' : 'File not found'}, code=400)
        elif not os.access(upload_path, os.R_OK):
            raise ValidationError({'detail' : 'No Read Permission'}, code=400)
        
        return attrs

class FqDatasetSerializer(serializers.ModelSerializer):

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    owner_group = serializers.PrimaryKeyRelatedField(queryset=OwnerGroup.objects.all())
    owner_group_name = serializers.CharField(source='owner_group.name', read_only=True)
    
    class Meta:
        model = FqDataset
        fields = '__all__'
        
        # Check if needed
        extra_kwargs = {
            "owner": {"read_only": True},
        }

    # TODO: Add validations for fields, e.g. metadata

class FqDatasetCLISerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    qc_passed = serializers.BooleanField()
    paired_end = serializers.BooleanField()
    index_read = serializers.BooleanField()
    project_ids = serializers.ListField(child=serializers.IntegerField())
    project_names = serializers.ListField(child=serializers.CharField())
    metadata = serializers.JSONField()
    attachments = serializers.ListField(child=serializers.CharField())
    pro_data = serializers.ListField(child=serializers.JSONField())
    
    
class FqDatasetCLIDetailSerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    qc_passed = serializers.BooleanField()
    paired_end = serializers.BooleanField()
    index_read = serializers.BooleanField()
    project_ids = serializers.ListField(child=serializers.IntegerField())
    project_names = serializers.ListField(child=serializers.CharField())
    created = serializers.DateTimeField()
    fq_file_r1 = serializers.PrimaryKeyRelatedField(read_only=True)
    fq_file_r2 = serializers.PrimaryKeyRelatedField(read_only=True)
    fq_file_i1 = serializers.PrimaryKeyRelatedField(read_only=True)
    fq_file_i2 = serializers.PrimaryKeyRelatedField(read_only=True)
    metadata = serializers.JSONField()
    attachments = serializers.ListField(child=serializers.CharField())
    pro_data = serializers.ListField(child=serializers.JSONField())


class FqDatasetCLIUploadSerializer(serializers.Serializer):
    
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    description = serializers.CharField(allow_blank=True)
    qc_passed = serializers.BooleanField()
    paired_end = serializers.BooleanField()
    index_read = serializers.BooleanField()
    project_ids = serializers.ListField(child=serializers.IntegerField())
    project_names = serializers.ListField(child=serializers.CharField())
    fq_file_r1 = serializers.IntegerField(allow_null=True)
    fq_file_r2 = serializers.IntegerField(allow_null=True)
    fq_file_i1 = serializers.IntegerField(allow_null=True)
    fq_file_i2 = serializers.IntegerField(allow_null=True)
    metadata = serializers.JSONField()
        
    def validate(self, attrs):
        
        name = attrs.get('name')
        metadata = attrs.get('metadata')
        
        if not _validate_charset(name):
            raise ValidationError({'detail' : 'Invalid character in name. Must be alphanumeric or _-.@'}, code=400)
        
        # # Perform validation of metadata
        metadata = _validate_metadata(metadata)
        
        return attrs
    
        
class FqAttachmentListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FqAttachment
        exclude = ['body']

class FqAttachmentSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = FqAttachment
        fields = '__all__'

        extra_kwargs = {
            "owner": {"read_only": True},
        }
    
    body = BinarySerializerField()


class ProjectSerializer(serializers.ModelSerializer):
    
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id',
                  'name',
                  'description',
                  'owner',
                  'owner_username',
                  'created',
                  'updated',
                  'valid_from', 
                  'valid_to',
                  'metadata',
                  'dataset_metadata_keys',
                  'owner_group',
                  'collaborators']
        
        extra_kwargs = {
            "id": {"read_only": True},
            "owner": {"read_only": True},
        }

    # TODO: Add validations for fields, e.g. metadata

class ProjectAttachmentListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProjectAttachment
        exclude = ['body']


class ProjectAttachmentSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = ProjectAttachment
        fields = '__all__'

        extra_kwargs = {
            "owner": {"read_only": True},
        }
    
    body = BinarySerializerField()


class ProjectCLISerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    metadata = serializers.JSONField()
    attachments = serializers.ListField(child=serializers.CharField())


class ProjectCLIDetailSerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    created = serializers.DateTimeField()
    creator = serializers.CharField(source='owner.username', read_only=True)
    attachments = serializers.ListField(child=serializers.CharField())
    metadata = serializers.JSONField()


class ProjectCLIUploadSerializer(serializers.Serializer):   
    
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    description = serializers.CharField(allow_blank=True)
    metadata = serializers.JSONField()
    dataset_metadata_keys = serializers.JSONField()
    
    def validate(self, attrs):
        
        name = attrs.get('name')
        metadata = attrs.get('metadata')
        dataset_metadata_keys = attrs.get('dataset_metadata_keys')
        
        if not _validate_charset(name):
            raise ValidationError({'detail' : 'Invalid character in name. Must be alphanumeric or _-.@'}, code=400)
        
        # # Perform validation of metadata
        metadata = _validate_metadata(metadata)
        
        # Validate dataset_metadata_keys
        # Must be keys with empty values
        dataset_metadata_keys = _validate_metadata(dataset_metadata_keys)
        
        return attrs
    
class PwdSerializer(serializers.Serializer):
    """
        Serializer for password based authentication
    """
    
    old_password = serializers.CharField(max_length=200, required=True, trim_whitespace=True)
    new_password = serializers.CharField(max_length=200, required=True, trim_whitespace=True)
    

class FqUploadSerializer(serializers.Serializer):
    """
        Serializer for uploading Fastq files
    """
    
    fq_file_path = serializers.CharField(max_length=1000,required=True, trim_whitespace=True)
    fq_file_name = serializers.CharField(max_length=200,required=False, trim_whitespace=True)
    read_type = serializers.CharField(max_length=10,required=False, trim_whitespace=True)
    
class LicenseKeySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LicenseKey
        fields = '__all__'
        
        extra_kwargs = {
                "owner": {"read_only": True},
            }
        
class ProDataSerializer(serializers.ModelSerializer):
    
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = ProData
        fields = '__all__'
        
        extra_kwargs = {
                "owner": {"read_only": True},
                "version": {"read_only": True},
            }

class ProDataUploadSerializer(serializers.Serializer):
    
    name = serializers.CharField(max_length=200,required=True, trim_whitespace=True)
    data_type = serializers.CharField(max_length=200,required=True, trim_whitespace=True)
    description = serializers.CharField(required=True, allow_blank=True)
    upload_path = serializers.CharField(required=True)
    metadata = serializers.JSONField(required=False, default={})
    dataset_id = serializers.IntegerField(required=False)
    dataset_name = serializers.CharField(max_length=200,required=False)
    
    def validate(self, attrs):
        
        name = attrs.get('name')
        data_type = attrs.get('data_type')
        metadata = attrs.get('metadata')
        upload_path = attrs.get('upload_path')

        if not _validate_charset(name):
            raise ValidationError({'detail' : 'Invalid character in name. Must be alphanumeric or _-.@'}, code=400)
        
        if not _validate_charset(data_type):
            raise ValidationError({'detail' : 'Invalid character in data_type. Must be alphanumeric or _-.@'}, code=400)
        
        # Check that file path is found
        if not os.path.exists(upload_path):
            raise ValidationError({'detail' : 'File not found'}, code=400)
        elif not os.access(upload_path, os.R_OK):
            raise ValidationError({'detail' : 'No Read Permission'}, code=400)
        
        # # Perform validation of metadata
        metadata = _validate_metadata(metadata)
        
        return attrs
    
class ProDataCLISerializer(serializers.Serializer):

    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    data_type = serializers.CharField()
    version = serializers.IntegerField()
    dataset_id = serializers.PrimaryKeyRelatedField(source='fq_dataset',read_only=True)
    dataset_name = serializers.CharField(source='fq_dataset.name', read_only=True)
    upload_path = serializers.CharField()
    metadata = serializers.JSONField()

class ProDataCLIDetailSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    data_type = serializers.CharField()
    version = serializers.IntegerField()
    created = serializers.DateTimeField()
    valid_to = serializers.DateTimeField()
    creator = serializers.CharField(source='owner.username', read_only=True)
    dataset_id = serializers.PrimaryKeyRelatedField(source='fq_dataset',read_only=True)
    dataset_name = serializers.CharField(source='fq_dataset.name', read_only=True)
    upload_path = serializers.CharField()
    metadata = serializers.JSONField()