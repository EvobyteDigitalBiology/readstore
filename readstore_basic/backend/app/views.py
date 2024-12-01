# readstore-basic/backend/app/views.py

"""

    Class Views for ReadStore Django Backend
    
    Classes:
        -
        -
        -
        -
        

"""

import re
from collections import defaultdict
import os
import sys
import datetime
import base64

#from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import DjangoModelPermissions

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .authentication import RSClientTokenAuth
from .permissions import RSClientHasStaging

from .serializers import UserSerializer
from .serializers import OwnerGroupSerializer
from .serializers import GroupSerializer
from .serializers import AppUserSerializer
from .serializers import FqFileSerializer
from .serializers import FqFileCLISerializer
from .serializers import FqDatasetSerializer
from .serializers import FqDatasetCLISerializer
from .serializers import FqDatasetCLIDetailSerializer
from .serializers import FqAttachmentSerializer
from .serializers import FqAttachmentListSerializer
from .serializers import ProjectSerializer
from .serializers import ProjectAttachmentSerializer
from .serializers import ProjectAttachmentListSerializer
from .serializers import ProjectCLISerializer
from .serializers import ProjectCLIDetailSerializer
from .serializers import PwdSerializer
from .serializers import FqUploadSerializer
from .serializers import LicenseKeySerializer
from .serializers import ProDataSerializer
from .serializers import ProDataUploadSerializer
from .serializers import ProDataCLISerializer
from .serializers import ProDataCLIDetailSerializer


from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate

from django.db.models import Q

from .models import AppUser
from .models import OwnerGroup
from .models import FqFile
from .models import FqDataset
from .models import FqAttachment
from .models import Project
from .models import ProjectAttachment
from .models import LicenseKey
from .models import ProData

from settings.base import VALID_FASTQ_EXTENSIONS
from settings.base import VALID_READ1_SUFFIX
from settings.base import VALID_READ2_SUFFIX
from settings.base import VALID_INDEX1_SUFFIX
from settings.base import VALID_INDEX2_SUFFIX


# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    """
        Class View for User Model
        
        - get_queryset: Subset queryset by query_params
        - my_owner_group: Return OwnerGroup for authenticated request
        - my_user: Return User for for authenticated request
        
        Requires authentication and table permission
    """

    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]

    serializer_class = UserSerializer
    
    
    def get_queryset(self):
        
        group_name = self.request.query_params.get('group_name', None)
        username = self.request.query_params.get('username', None)
        
        if group_name:
            group_check = Q(groups__name=group_name)
        else:
            group_check = Q()
            
        if username:
            usercheck1 = Q(username=username)
        else:
            usercheck1 = Q()
            
        queryset = User.objects.filter(group_check & usercheck1).all().order_by("-date_joined")
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_owner_group(self, request):
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            serializer = OwnerGroupSerializer(owner_group)
            return Response([serializer.data])
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
        
    @action(detail=False, methods=['get'])
    def my_user(self, request):
        
        user = User.objects.get(username=request.user)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def regenerate_token(self, request):
        
        if hasattr(request.user, 'appuser'):
            appuser = request.user.appuser
            appuser.regenerate_token()
            
            return Response({'detail' : 'Token regenerated'}, status=200)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    @action(detail=False, methods=['post'], serializer_class=PwdSerializer)
    def reset_password(self, request):
        
        data = request.data
        serializer = PwdSerializer(data=data)
        
        if serializer.is_valid():
        
            group_names = request.user.groups.all()
        
            if group_names.filter(name__in=['admin', 'appuser']).exists():
                
                pwd_old = request.data.get('old_password')
                pwd_new = request.data.get('new_password')
                
                if request.user.check_password(pwd_old):
                    request.user.set_password(pwd_new)
                    request.user.save()
                    return Response({'detail' : 'password correct'}, status=200)
                else:
                    return Response({'detail' : 'password incorrect'}, status=400)    
                return Response({'detail' : 'password reset'}, status=200)
            else:
                return Response({'detail' : 'user is not an appuser or admin'}, status=400)        
        else:
            return Response(serializer.errors, status=400)

class TokenExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        return view_permissions
    
    def post(self, request):        
        return Response({'detail' : 'token valid'}, status=200)

   
class GroupViewSet(viewsets.ModelViewSet):
    """
        Class View for Group Model
        Requires authentication and table permission
    """
    
    # Set permission classes, i.e. user must be authenticated to DB
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
class GetUserGroupsView(APIView):
    """
    APIView GetUserGroupsView

    Return groups attached to user making request
    """

    # Set permission classes, i.e. user must be authenticated to DB
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, format=None):

        u_groups = (
            User.objects.get(username=request.user)
            .groups
            .all()
        )

        serializer = GroupSerializer(u_groups, many=True)
        return Response(serializer.data)


class OwnerGroupViewSet(viewsets.ModelViewSet):
    """
        Class View for OwnerGroup Model
        Requires authentication and table permission
    """
    
    # Set permission classes, i.e. user must be authenticated to DB
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    queryset = OwnerGroup.objects.all().order_by("-created")
    serializer_class = OwnerGroupSerializer
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

        
class AppUserViewSet(viewsets.ModelViewSet):
    """
        Class View for AppUser Model.
        
        Requires authentication and table permission.
    """
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    queryset = AppUser.objects.all()
    serializer_class = AppUserSerializer


class FqFileViewSet(viewsets.ModelViewSet):
    """
        Class View for FqFile Model.
        
        Requires authentication and table permission.
        
        - get_queryset: Subset queryset by query_params
        - perform_destroy: Delete FqFile from database and S3 bucket
        - my_fq_file: Return FqFile for authenticated request
        - staging: Get all FqFiles in staging state for user
    """
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    serializer_class = FqFileSerializer

    def get_queryset(self):
        """Subset queryset

        Subset queryset by request query_params key, bucket and owner
        
        Returns:
            FqFile queryset
        """
                
        key = self.request.query_params.get('key', None)
        bucket = self.request.query_params.get('bucket', None)
        owner = self.request.query_params.get('owner', None)
        
        # Add endpoints for restricted access to projects
        key_check = Q()
        bucket_check = Q()
        owner_check = Q()
        if key:
            key_check = Q(key=key)
        if bucket:
            bucket_check = Q(bucket=bucket)
        if owner:
            owner_check = Q(owner=owner)
            
        queryset = FqFile.objects.filter(key_check & bucket_check & owner_check).all().order_by("-created")
            
        return queryset

    @action(detail=False, methods=['get'])
    def owner_group(self, request):
        """Get FqFiles for owner_group

        Return FqFile where user is part of owner_group
        
        Args:
            request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            fq_datasets = FqDataset.objects.filter(owner_group=owner_group).all()
            
            Q_comb = Q(fq_file_r1__in=fq_datasets) | \
                     Q(fq_file_r2__in=fq_datasets) | \
                     Q(fq_file_i1__in=fq_datasets) | \
                     Q(fq_file_i2__in=fq_datasets)
            
            qset = FqFile.objects.filter(Q_comb).all()
            
            serializer = self.get_serializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    @action(detail=False, methods=['get'])
    def collab(self, request):
        """Get FqFiles for owner_group

        Return FqFile where user is part of owner_group
        
        Args:
            request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):    
            username = request.user.username
            fq_datasets = FqDataset.objects.filter(project__collaborators__username=username).all()
            
            Q_comb = Q(fq_file_r1__in=fq_datasets) | \
                     Q(fq_file_r2__in=fq_datasets) | \
                     Q(fq_file_i1__in=fq_datasets) | \
                     Q(fq_file_i2__in=fq_datasets)
            
            qset = FqFile.objects.filter(Q_comb).all()
            
            serializer = self.get_serializer(qset, many=True)        
            return Response(serializer.data)
        
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
        
        
        pk = request.user.pk
        owner_check = Q(owner=pk)
        
        qset = FqFile.objects.filter(owner_check).all().order_by("-created")
        
        serializer = self.get_serializer(qset, many=True)        
        return Response(serializer.data)
    
    
    @action(detail=False, methods=['get'])
    def staging(self, request):
        """FqFile for authenticated user in staging state

        Return FqFile objects for authenticated user with staging is true
        
        Args:
            request

        Returns:
            Response serialized queryset
        """
        
        username = request.user.username
        owner_check = Q(owner__username=username)
        staging_check = Q(staging = True)
        
        qset = FqFile.objects.filter(owner_check & staging_check).all().order_by("-created")
        
        serializer = self.get_serializer(qset, many=True)        
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def validate_upload_path(self, request):
        """Validate Upload Path

        Validate upload path for FqFile
        
        Args:
            request

        Returns:
            Response: List of invalid paths
        """
        
        if not 'pipelines' in sys.modules:
            from app import pipelines
        
        # TODO: Needs restricting by owner group
        invalid_paths = pipelines.get_model_invalid_upload_paths(FqFile.objects.all())
        
        return Response(invalid_paths)

class FqFileExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == 'POST':
            view_permissions.append(RSClientHasStaging())
        return view_permissions
    
    def get(self, request, pk=None):
        
        user = request.user
        
        og_check = Q(owner_group=user.appuser.owner_group)
        collab_check = Q(project__collaborators=user)

        # Get read type for fq file
        if pk:
            if not FqFile.objects.filter(pk=pk).exists():
                return Response({'detail' : 'FqFile not found'}, status=400)
            
            fq_read_type = FqFile.objects.get(pk=pk).read_type
                
            # Not check if there is a daatset that user has access to,
            # that contains the fq file for selected read type
            match fq_read_type:
                case 'R1':
                    read_type_check = Q(fq_file_r1=pk)
                    read_fk_name = 'fq_file_r1'
                case 'R2':
                    read_type_check = Q(fq_file_r2=pk)
                    read_fk_name = 'fq_file_r2'
                case 'I1':
                    read_type_check = Q(fq_file_i1=pk)
                    read_fk_name = 'fq_file_i1'
                case 'I2':
                    read_type_check = Q(fq_file_i2=pk)
                    read_fk_name = 'fq_file_i2'
                case _:
                    Response({'detail' : 'Invalid read type for FqFile'}, status=400)
            
            # Check if user has permission to access dataset that fq file is part of
            if FqDataset.objects.filter(og_check | collab_check, read_type_check).exists():
                # If true get fq file
                qset = FqFile.objects.filter(pk=pk).all()
                
                # Add creator name as attribute
                for q in qset:
                    q.creator = q.owner.username
                
                serializer = FqFileCLISerializer(qset, many=True)        
                return Response(serializer.data)

        # Get all fq files where user has access
        else:
            # Get all fq datasets where user has access
            qset_fq_ds = FqDataset.objects.filter(og_check | collab_check).all()
            
            # Extract IDs from all fq datasets for fq_file_r1, fq_file_r2, fq_file_i1, fq_file_i2
            fq_file_r1 = qset_fq_ds.values_list('fq_file_r1', flat=True)
            fq_file_r2 = qset_fq_ds.values_list('fq_file_r2', flat=True)
            fq_file_i1 = qset_fq_ds.values_list('fq_file_i1', flat=True)
            fq_file_i2 = qset_fq_ds.values_list('fq_file_i2', flat=True)
            
            # Combine all IDs
            fq_file_ids = list(fq_file_r1) + list(fq_file_r2) + list(fq_file_i1) + list(fq_file_i2)
            
            # Get corresponding fq files
            qset = FqFile.objects.filter(pk__in=fq_file_ids).all()
            
            # Add creator name as attribute
            for q in qset:
                q.creator = q.owner.username    
            
            serializer = FqFileCLISerializer(qset, many=True)        
            return Response(serializer.data)
        
          
class FqFileUploadExt(APIView):
    
    # Set permission classes, i.e. user must be authenticated to DB
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == 'POST':
            view_permissions.append(RSClientHasStaging())
        return view_permissions
    
    def post(self, request):
        
        user = request.user
        data = request.data
        serializer = FqUploadSerializer(data=data)
        
        if serializer.is_valid():
            filepath = request.data.get('fq_file_path')
            filepath = os.path.abspath(filepath)
            fq_name = request.data.get('fq_file_name', None)
            read_type = request.data.get('read_type', None)
                        
            # Check if file exists and read permissions
            if not os.path.exists(filepath):
                return Response({'detail' : 'File not found'}, status=400)
            elif not os.access(filepath, os.R_OK):
                return Response({'detail' : 'No Read Permission'}, status=400)
            
            # Get Fq Stats
            else:
                # Validate Fastq File Extension
                for ext in VALID_FASTQ_EXTENSIONS:
                    if filepath.endswith(ext):
                        filepath_stub = filepath.replace(ext, '')
                        break
                else:
                    return Response({'detail' : 'Invalid Fastq extension.'}, status=400)
                
                if read_type is None:
                    # Set read type
                    # Infer Read Type
                    if any([filepath_stub.endswith(suffix) for suffix in VALID_READ1_SUFFIX]):
                        read_type = 'R1'
                    elif any([filepath_stub.endswith(suffix) for suffix in VALID_READ2_SUFFIX]):
                        read_type = 'R2'
                    elif any([filepath_stub.endswith(suffix) for suffix in VALID_INDEX1_SUFFIX]):
                        read_type = 'I1'
                    elif any([filepath_stub.endswith(suffix) for suffix in VALID_INDEX2_SUFFIX]):
                        read_type = 'I2'
                    else:
                        read_type = 'NA'
                # Case that read_type is provided
                else:
                    if not read_type in ['R1', 'R2', 'I1', 'I2']:
                        read_type = 'NA'
                        
                if not 'pipelines' in sys.modules:
                    from app import pipelines
                
                if fq_name is None:                    
                    file_name = os.path.basename(filepath_stub)
                else:
                    file_name = fq_name
                    
                res = pipelines.exec_staging_job(filepath,
                                                file_name,
                                                user,
                                                read_type)
                
                if res:                    
                    return Response({'detail' : 'fastq upload submitted'}, status=200)
                else:
                    return Response({'detail' : 'fastq upload failed since queue is full. Try later.'}, status=400)
        else:
            return Response(serializer.errors, status=400)

class FqFileUploadAppView(APIView):
    
     # Set permission classes, i.e. user must be authenticated to DB
    permission_classes = [IsAuthenticated]
    serializer_class = FqUploadSerializer
        
    def post(self, request):
        
        data = request.data
        serializer = FqUploadSerializer(data=data)
        
        if serializer.is_valid():
            filepath = request.data.get('fq_file_path')
            file_name = request.data.get('fq_file_name')
            read_type = request.data.get('read_type')
            filepath = os.path.abspath(filepath)
            
            if hasattr(request.user, 'appuser'):
                
                usercheck1 = Q(username=request.user.username)
                staging_check = Q(groups__name='staging')
                
                if User.objects.filter(usercheck1 & staging_check).exists():
                    if not os.path.exists(filepath):
                        return Response({'detail' : 'File not found'}, status=400)
                    elif not os.access(filepath, os.R_OK):
                        return Response({'detail' : 'No Read Permission'}, status=400)
                    # Get Fq Stats
                    else:
                        # Validate Fastq File Extension
                        for ext in VALID_FASTQ_EXTENSIONS:
                            if filepath.endswith(ext):
                                filepath_stub = filepath.replace(ext, '')
                                break
                        else:
                            return Response({'detail' : 'Invalid fastq extension.'}, status=400)
                        
                        if not read_type in ['R1', 'R2', 'I1', 'I2']:
                            return Response({'detail' : 'Invalid read type'}, status=400)
                        
                        if not 'pipelines' in sys.modules:
                            from app import pipelines
                        
                        res = pipelines.exec_staging_job(filepath,
                                                        file_name,
                                                        request.user,
                                                        read_type)
                        
                        if res:                    
                            return Response({'detail' : 'fastq upload submitted'}, status=200)
                        else:
                            return Response({'detail' : 'fastq upload failed since queue is full. Try later.'}, status=400)                    
                else:
                    return Response({'detail' : 'User has no staging'}, status=400)
            else:
                return Response({'detail' : 'User is not an appuser'}, status=400)          
        else:
            return Response(serializer.errors, status=400)  

      
class FqQueueView(APIView):
    
    # Set permission classes, i.e. user must be authenticated to DB
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        
        if not 'pipelines' in sys.modules:
            from app import pipelines
        
        return Response({'num_jobs' : pipelines.get_queue_jobs()},
                        status=200)


class FqDatasetViewSet(viewsets.ModelViewSet):
    """
    Class View for FqDataset Model.
        
    Requires authentication and table permission.

    - get_queryset
    - perform_create
    - owner_group
    - collab
    - my_fq_dataset
    """
    
    permission_classes = [IsAuthenticated,
                DjangoModelPermissions]

    serializer_class = FqDatasetSerializer
    
    def get_queryset(self):
        """Get queryset
        
        Get queryset with option to subset query parameter owner

        Returns:
            Queryset FqDataset objects
        """
        
        owner = self.request.query_params.get('owner', None)
        
        # Add endpoints for restricted access to projects
        owner_check = Q()
        if owner:
            owner_check = Q(owner=owner)
        
        queryset = FqDataset.objects.filter(owner_check).all().order_by("-created")
            
        return queryset
    
    def perform_create(self, serializer):
        """Create FqDataset

        Create FqDataset and set authenticated user as owner
        
        Args:
            serializer
        """
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def owner_group(self, request):
        """Get FqDataset for owner_group

        Return FqDatasts where user is part of owner_group
        
        Args:
            request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            qset = FqDataset.objects.filter(owner_group=owner_group).all().distinct().order_by("-created")
            serializer = self.get_serializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)

    @action(detail=False, methods=['get'])
    def collab(self, request):
        """Get FqDataset where user is collaborator

        Return FqDatasts where user is a collaborator on a project that user shared
        
        Args:
            Request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):    
            username = request.user.username
            qset = FqDataset.objects.filter(project__collaborators__username=username).all().distinct().order_by("-created")
            
            serializer = self.get_serializer(qset, many=True)        
            return Response(serializer.data)
        
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)

    @action(detail=False, methods=['get'])
    def my_fq_dataset(self, request):
        """Get FqDataset where user is owner

        Return FqDatasts where user is a owner of FqDataset (and FqFiles)
        
        Args:
            Request

        Returns:
            Response
        """
        
        pk = request.user.pk
        owner_check = Q(owner=pk)
        
        qset = FqDataset.objects.filter(owner_check).all().order_by("-created")
        
        serializer = self.get_serializer(qset, many=True)        
        return Response(serializer.data)


class FqDatasetExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == 'POST':
            view_permissions.append(RSClientHasStaging())
        return view_permissions
    
    def get(self, request, pk=None):
        
        user = request.user
        
        og_check = Q(owner_group=user.appuser.owner_group)
        collab_check = Q(project__collaborators=user)
        creator_check = Q(owner=user)
        
        # Else run routine get dataset - list
        project_name = self.request.query_params.get('project_name', None)
        project_id = self.request.query_params.get('project_id', None)
        
        role = request.query_params.get('role', None)
                        
        # If dataset id or name is provided, run routine get dataset - detail
        dataset_id = request.query_params.get('id', None)
        dataset_name = request.query_params.get('name', None)
        
        # Return FqDataset by ID or Name or if pk is provided
        # Primary key has precedence
        if dataset_id or dataset_name or pk:
            dataset_id_check = Q()
            dataset_name_check = Q()
            if pk:
                dataset_id_check = Q(id=pk)
            else:
                if dataset_id:
                    dataset_id_check = Q(id=dataset_id)
                if dataset_name:
                    dataset_name_check = Q(name=dataset_name)
            
            # Combine Q Objects # TODO: Check this for the case that identical
            # names exist in different project groups
            qset = FqDataset.objects \
                    .filter(dataset_id_check & dataset_name_check) \
                    .filter(og_check | collab_check) \
                    .all().distinct() \
                    .order_by("-created")    
            
            # Get all attachments
            fq_attach = FqAttachment.objects \
                .defer('body') \
                .filter(fq_dataset__in=qset) \
                .all() \
                .order_by("-created")
            
            # Convert to dict of list
            attach_dict = defaultdict(list)
            
            for attach in fq_attach.values('fq_dataset_id','name'):
                attach_dict[attach['fq_dataset_id']].append(attach['name'])
            
            # Get all pro_data
            pro_data = ProData.objects \
                .filter(fq_dataset__in=qset, valid_to=None) \
                .all() \
                .order_by("-created")
            
            pro_data_dict = defaultdict(list)
            
            for data in pro_data.values('fq_dataset_id', 'id', 'name','upload_path'):
                pro_data_dict[data['fq_dataset_id']].append({'id' : data['id'],
                                                            'name' : data['name'],
                                                            'upload_path' : data['upload_path']})
            
            # add attachments to fq datasets
            for p in qset:
                p.attachments = attach_dict[p.id]
                p.pro_data = pro_data_dict[p.id]

                names = p.project.all().values_list('name', flat=True)
                ids = p.project.all().values_list('id', flat=True)
                    
                p.project_names = list(names)
                p.project_ids = list(ids)
                
            serializer = FqDatasetCLIDetailSerializer(qset, many=True)
            return Response(serializer.data)
    
        else:
            project_name_check = Q()
            if project_name:
                project_name_check = Q(project__name=project_name)
            project_id_check = Q()
            if project_id:
                project_id_check = Q(project__id=project_id)
        
            # Combine Q Objects and select depending on owner status
            Q_comb = project_name_check & project_id_check
            
            qset = FqDataset.objects.filter(Q_comb)
            
            # Check role
            if role:
                if role == 'owner':
                    Q_check = og_check
                elif role == 'collaborator':
                    Q_check = collab_check
                elif role == 'creator': # Only creator and owner, since users can change groups
                    Q_check = creator_check & og_check
                else:
                    return Response({'detail' : 'invalid role'}, status=400)
            else:
                Q_check = og_check | collab_check                            
            
            # Distinct is needed when matcing against M2M
            qset = qset.filter(Q_check) \
                .all() \
                .distinct() \
                .order_by("-created")
            
            # Get all attachments
            fq_attach = FqAttachment.objects \
                .only('fq_dataset_id','name') \
                .filter(fq_dataset__in=qset) \
                .all() \
                .order_by("-created")
            
            # Convert to dict of list
            attach_dict = defaultdict(list)
            for attach in fq_attach.values('fq_dataset_id','name'):
                attach_dict[attach['fq_dataset_id']].append(attach['name'])
            
            # Get all pro_data
            pro_data = ProData.objects \
                .filter(fq_dataset__in=qset, valid_to=None)  \
                .all() \
                .order_by("-created")
            
            pro_data_dict = defaultdict(list)
            
            for data in pro_data.values('fq_dataset_id', 'id', 'name','upload_path'):
                pro_data_dict[data['fq_dataset_id']].append({'id' : data['id'],
                                                            'name' : data['name'],
                                                                'upload_path' : data['upload_path']})
            
            # add attachments to project
            for p in qset:
                p.attachments = attach_dict[p.id]
                p.pro_data = pro_data_dict[p.id]

                names = p.project.all().values_list('name', flat=True)
                ids = p.project.all().values_list('id', flat=True)
                    
                p.project_names = list(names)
                p.project_ids = list(ids)
                                            
            serializer = FqDatasetCLISerializer(qset, many=True)                    
            return Response(serializer.data)


class FqAttachmentViewSet(viewsets.ModelViewSet):
    """
        Class View for FqAttachment Model.
        Requires authentication and table permission.
        
        - get_serializer_class
        - perform_create
        - fq_dataset
    """
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    queryset = FqAttachment.objects.defer('body').all().order_by("-created")
    
    def get_serializer_class(self):
        """Get Serializer Class
        
        Get serializer class depending on type of request
        List and fq_dataset request have no body field containing binary data
        
        Returns:
            Serializer
        """
        if self.action in ['list', 'fq_dataset']:
            return FqAttachmentListSerializer
        else:
            return FqAttachmentSerializer
    
    def perform_create(self, serializer):
        """Create FqAttachment

        Create FqAttachment and set authenticated user as owner
        
        Args:
            serializer
        """ 
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def owner_group(self, request):
        """Get FqAttachment for owner_group
        
        Get FqAttachment for owner_group
        
        Args:
            request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            
            qset = FqAttachment.objects \
                    .defer('body') \
                    .filter(fq_dataset__owner_group=owner_group) \
                    .all() \
                    .distinct() \
                    .order_by("-created")
            
            serializer = FqAttachmentListSerializer(qset, many=True)        
            
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    @action(detail=False, methods=['get'])
    def collab(self, request):
        """Get FqAttachment for collaborator
        
        Get FqAttachment for collaborator
        
        Args:
            request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):
            username = request.user.username
            
            qset = FqAttachment.objects \
                .defer('body') \
                .filter(fq_dataset__project__collaborators__username=username) \
                .all() \
                .distinct() \
                .order_by("-created")
            
            serializer = FqAttachmentListSerializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    @action(detail=False, methods=['get'])
    def fq_dataset(self, request, pk):
        """Get FqAttachment for FqDataset
        
        Get FqAttachment for FqDataset defined by FqDataset PK
        Check if authenticated user has permission FqDataset by checking
        owner_group or if user is a collaborator on associated project

        Args:
            request
            pk: FqDataset Primary Key

        Returns:
            Response
        """
        
        # Check if owner has permission to access project
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            
            # In this case user is part of owner group
            if FqDataset.objects.filter(owner_group=owner_group, pk=pk).exists():
                qset = FqAttachment.objects.defer('body').filter(fq_dataset_id=pk).all().order_by("-created")
                serializer = FqAttachmentListSerializer(qset, many=True)        
                return Response(serializer.data)
            
            # Check of FqDataset is part of project where user has collaborator access
            elif FqDataset.objects.filter(project__collaborators__username=request.user.username, pk=pk).exists():
                qset = FqAttachment.objects.defer('body').filter(fq_dataset_id=pk).all().order_by("-created")
                serializer = FqAttachmentListSerializer(qset, many=True)        
                return Response(serializer.data)
            else:
                return Response({'detail' : 'User does not have permission to access project'}, status=400)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)


class FqAttachmentExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == 'POST':
            view_permissions.append(RSClientHasStaging())
        return view_permissions

    def get(self, request, pk=None):
        
        user = request.user
        
        # Only access attachments where user is owner or collaborator
        og_check = Q(fq_dataset__owner_group=user.appuser.owner_group)
        collab_check = Q(fq_dataset__project__collaborators=user)
        
        # Else run routine get dataset - list
        dataset_name = request.query_params.get('dataset_name', None)
        dataset_id = request.query_params.get('dataset_id', None)
        attachment_name = request.query_params.get('attachment_name', None)
        
        if dataset_id or dataset_name or pk:
            
            dataset_id_check = Q()
            dataset_name_check = Q()
            
            if pk:
                Q_comb = Q(pk=pk) \
                    & (og_check | collab_check)
            else:
                if attachment_name is None:
                    return Response({'detail' : 'Provide attachment_name'}, status=400)
                
                if dataset_id:
                    dataset_id_check = Q(fq_dataset__id=dataset_id)
                if dataset_name:
                    dataset_name_check = Q(fq_dataset__name=dataset_name)
                
                attachment_name_check = Q(name=attachment_name)
            
                # Combine Q Objects and select depending on owner status
                Q_comb = dataset_id_check \
                    & dataset_name_check \
                    & (og_check | collab_check) \
                    & attachment_name_check
            
            qset = FqAttachment.objects.filter(Q_comb).distinct().all()
            
            serializer = FqAttachmentSerializer(qset, many=True)
            return Response(serializer.data)

        else:
            Q_comb = og_check | collab_check
            qset = FqAttachment.objects.filter(Q_comb).all().distinct().order_by("-created")
            serializer = FqAttachmentListSerializer(qset, many=True)
            return Response(serializer.data)
            
            
class ProjectViewSet(viewsets.ModelViewSet):
    """
        API endpoint that allows Projects to be viewed or edited.
    """
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        
        name = self.request.query_params.get('name', None)
        
        # Add endpoints for restricted access to projects
        name_check = Q()
        if name:
            name_check = Q(name=name)
            
        queryset = Project.objects.filter(name_check).all().order_by("-created")
            
        return queryset
    
    def perform_create(self, serializer):    
        serializer.save(owner=self.request.user)
    
    
    @action(detail=False, methods=['get'])            
    def collab(self, request):
        
        username = request.user.username
        qset = Project.objects \
            .filter(collaborators__username=username) \
            .all() \
            .distinct() \
            .order_by("-created")
        
        serializer = self.get_serializer(qset, many=True)        
        return Response(serializer.data)

    
    @action(detail=False, methods=['get'])
    def owner_group(self, request):
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            
            qset = Project.objects.filter(owner_group=owner_group).all().distinct().order_by("-created")
            
            serializer = self.get_serializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)


class ProjectExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == 'POST':
            view_permissions.append(RSClientHasStaging())
        return view_permissions
    
    def get(self, request, pk=None):
        
        user = request.user
        
        og_check = Q(owner_group=user.appuser.owner_group)
        collab_check = Q(collaborators=user)
        creator_check = Q(owner=user)
        
        # Else run routine get dataset - list
        project_name = self.request.query_params.get('name', None)
        project_id = self.request.query_params.get('id', None)
        role = self.request.query_params.get('role', None)
        
        if project_id or project_name or pk:
            project_id_check = Q()
            project_name_check = Q()
            if pk:
                project_id_check = Q(pk=pk)
            else:
                if project_id:
                    project_id_check = Q(id=project_id)
                if project_name:
                    project_name_check = Q(name=project_name)
            
            # Distinct is needed when matcing against M2M
            qset = Project.objects \
                .filter(project_id_check & project_name_check) \
                .filter(og_check | collab_check) \
                .all() \
                .distinct() \
                .order_by("-created")

            # Get all attachments for projects
            project_attach = ProjectAttachment.objects \
                .defer('body') \
                .filter(project__in=qset) \
                .all() \
                .order_by("-created")
                                                
            # Convert to dict of list
            attach_dict = defaultdict(list)
            for attach in project_attach.values('project_id','name'):
                attach_dict[attach['project_id']].append(attach['name'])
                        
            # add attachments to project
            for p in qset:
                p.attachments = attach_dict[p.id]
            
            serializer = ProjectCLIDetailSerializer(qset, many=True)
            return Response(serializer.data)
        else:
            
            # All projects where user is owner or collaborator
            if role:
                if role == 'owner':
                    Q_check = og_check
                elif role == 'collaborator':
                    Q_check = collab_check
                elif role == 'creator':
                    Q_check = creator_check & og_check
                else:
                    return Response({'detail' : 'invalid role '}, status=400)
            else:
                Q_check = og_check | collab_check

            qset = Project.objects \
                .filter(Q_check) \
                .all() \
                .distinct() \
                .order_by("-created")
            
            # Get all attachments for projects
            project_attach = ProjectAttachment.objects \
                .defer('body') \
                .filter(project__in=qset) \
                .all() \
                .order_by("-created")
            
            # Convert to dict of list
            attach_dict = defaultdict(list)
            for attach in project_attach.values('project_id','name'):
                attach_dict[attach['project_id']].append(attach['name'])
            
            # add attachments to project
            for p in qset:
                p.attachments = attach_dict[p.id]
            
            serializer = ProjectCLISerializer(qset, many=True)
            
            return Response(serializer.data)


class ProjectAttachmentViewSet(viewsets.ModelViewSet):
    """
        API endpoint that allows ProjectAttachments to be viewed or edited.
    """
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    queryset = ProjectAttachment.objects.defer('body').all().order_by("-created")
    
    def get_serializer_class(self):
        if self.action in ['list', 'project']:
            return ProjectAttachmentListSerializer
        else:
            return ProjectAttachmentSerializer
    
    def perform_create(self, serializer):    
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def owner_group(self, request):
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            
            qset = ProjectAttachment.objects \
                .defer('body') \
                .filter(project__owner_group=owner_group) \
                .all() \
                .distinct() \
                .order_by("-created")
            
            serializer = ProjectAttachmentListSerializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    @action(detail=False, methods=['get'])
    def collab(self, request):
            
        if hasattr(request.user, 'appuser'):
            username = request.user.username
            qset = ProjectAttachment.objects \
                .defer('body') \
                .filter(project__collaborators__username=username) \
                .all() \
                .distinct() \
                .order_by("-created")
            
            serializer = ProjectAttachmentListSerializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
        
    
    @action(detail=False, methods=['get'])
    def project(self, request, pk):
        
        # Check if owner has permission to access project
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            
            # In this case user is part of owner group
            if Project.objects.filter(owner_group=owner_group, pk=pk).exists():
                qset = ProjectAttachment.objects \
                    .defer('body') \
                    .filter(project_id=pk) \
                    .all() \
                    .order_by("-created")
                
                serializer = ProjectAttachmentListSerializer(qset, many=True)        
                return Response(serializer.data)
            
            # In this case user is collaborator
            elif Project.objects.filter(collaborators__username=request.user.username, pk=pk).exists():
                qset = ProjectAttachment.objects \
                    .defer('body') \
                    .filter(project_id=pk) \
                    .all() \
                    .order_by("-created")
                
                serializer = ProjectAttachmentListSerializer(qset, many=True)        
                return Response(serializer.data)
            else:
                return Response({'detail' : 'User does not have permission to access project'}, status=400)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)


class ProjectAttachmentExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == 'POST':
            view_permissions.append(RSClientHasStaging())
        return view_permissions
    
    def get(self, request, pk=None):
        
        user = request.user
        
        # Only access attachments where user is owner or collaborator
        og_check = Q(project__owner_group=user.appuser.owner_group)
        collab_check = Q(project__collaborators=user)
        
        # Else run routine get dataset - list
        project_name = request.query_params.get('project_name', None)
        project_id = request.query_params.get('project_id', None)
        attachment_name = request.query_params.get('attachment_name', None)
        
        if project_id or project_name or pk:
            
            project_id_check = Q()
            project_name_check = Q()
            
            if pk:
                Q_comb = Q(pk=pk) \
                    & (og_check | collab_check)
            else:
                if attachment_name is None:
                    return Response({'detail' : 'Provide attachment_name'}, status=400)
                
                if project_id:
                    project_id_check = Q(project__id=project_id)
                if project_name:
                    project_name_check = Q(project__name=project_name)
                
                attachment_name_check = Q(name=attachment_name)
            
                # Combine Q Objects and select depending on owner status
                Q_comb = project_id_check \
                    & project_name_check \
                    & (og_check | collab_check) \
                    & attachment_name_check
            
            qset = ProjectAttachment.objects.filter(Q_comb).distinct().all()
            serializer = ProjectAttachmentSerializer(qset, many=True)
            return Response(serializer.data)

        else:
            Q_comb = og_check | collab_check
            qset = ProjectAttachment.objects.filter(Q_comb).all().distinct().order_by("-created")
            serializer = ProjectAttachmentListSerializer(qset, many=True)
            return Response(serializer.data)

class LicenseKeyViewSet(viewsets.ModelViewSet):
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]
    
    queryset = LicenseKey.objects.all().order_by("-created")
    
    serializer_class = LicenseKeySerializer
    
    def perform_create(self, serializer):
        # Invalidate previous license keys
        qset = LicenseKey.objects.filter(valid_to__isnull=True).all()
        
        if qset:
            for q in qset:
                q.valid_to = datetime.datetime.now()
                q.save()
        
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        
        qset = LicenseKey.objects.filter(valid_to__isnull=True).all()
        
        serializer = self.get_serializer(qset, many=True)        
        return Response(serializer.data)
    
class ProDataViewSet(viewsets.ModelViewSet):
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]
    
    queryset = ProData.objects.all().order_by("-created")
    serializer_class = ProDataSerializer
    
    def perform_create(self, serializer):
        
        name = serializer.validated_data.get('name')
        fq_dataset = serializer.validated_data.get('fq_dataset')
        
        # Update last dataset
        # Versioning is developed into fq_dataset, name, owner_group 
        q_last = ProData.objects.filter(valid_to=None,
                                        name=name,
                                        fq_dataset=fq_dataset).first()
                
        if q_last:
            q_last.valid_to = datetime.datetime.now()
            new_version = q_last.version + 1
            
            q_last.save()
        else:
            new_version = 1
        
        serializer.save(owner=self.request.user, version=new_version)
    
    @action(detail=False, methods=['get'])
    def valid(self, request):
        
        qset = ProData.objects.filter(valid_to=None).all().order_by("-created")
        
        serializer = self.get_serializer(qset, many=True)        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def fq_dataset(self, request, pk):
        """Get ProData for FqDataset
        
        Get ProData for FqDataset defined by FqDataset PK
        Check if authenticated user has permission FqDataset

        Args:
            request
            pk: FqDataset Primary Key

        Returns:
            Response
        """
        
        # Check if owner has permission to access project
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            
            # In this case user is part of owner group
            if FqDataset.objects.filter(owner_group=owner_group, pk=pk).exists():
                qset = ProData.objects.filter(fq_dataset_id=pk).all().order_by("-created")
                serializer = ProDataSerializer(qset, many=True)
                return Response(serializer.data)
            else:
                return Response({'detail' : 'FqDataset does not exists'}, status=400)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    
    @action(detail=False, methods=['get'])
    def owner_group(self, request):
        """Get ProData for owner_group

        Return ProData where user is part of owner_group
        
        Args:
            request

        Returns:
            Response
        """
        
        if hasattr(request.user, 'appuser'):
            owner_group = request.user.appuser.owner_group
            fq_datasets = FqDataset.objects.filter(owner_group=owner_group).all()
            qset = ProData.objects.filter(fq_dataset__in=fq_datasets).all().order_by("-created")
            
            serializer = self.get_serializer(qset, many=True)        
            return Response(serializer.data)
        else:
            return Response({'detail' : 'User is not an appuser'}, status=400)
    
    @action(detail=False, methods=['get'])
    def validate_upload_path(self, request):
        """Validate Upload Path

        Validate upload path for FqFile
        
        Args:
            request

        Returns:
            Response: List of invalid paths
        """
        
        if not 'pipelines' in sys.modules:
            from app import pipelines
        
        invalid_paths = pipelines.get_model_invalid_upload_paths(ProData.objects.filter(valid_to=None).all())
        
        return Response(invalid_paths)
    
class ProDataExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method in ['POST', 'DELETE']:
            view_permissions.append(RSClientHasStaging())
        return view_permissions

    def get(self, request, pk=None):
        
        user = request.user
        
        og_check = Q(fq_dataset__owner_group=user.appuser.owner_group)
        collab_check = Q(fq_dataset__project__collaborators=user)
        
        # Else run routine get dataset - list
        project_id = self.request.query_params.get('project_id', None)
        project_name = self.request.query_params.get('project_name', None)
        dataset_id = self.request.query_params.get('dataset_id', None)
        dataset_name = self.request.query_params.get('dataset_name', None)
        name = self.request.query_params.get('name', None)
        data_type = self.request.query_params.get('data_type', None)
        valid = self.request.query_params.get('valid', None)
        detail = self.request.query_params.get('detail', None)
        version = self.request.query_params.get('version', None)
        
        # Convert valid flag to boolean
        if valid:
            valid = True if valid.lower() == 'true' else False
        else:
            valid = False
        
        if detail:
            detail = True if detail.lower() == 'true' else False
        
        if any([project_id,
                project_name,
                dataset_id,
                dataset_name,
                name,
                data_type,
                valid]) or pk:
            
            project_id_check = Q()
            project_name_check = Q()
            fq_dataset_id_check = Q()
            fq_dataset_name_check = Q()
            name_check = Q()
            data_type_check = Q()
            valid_check = Q()
            version_check = Q()
            
            if pk:
                Q_comb = Q(pk=pk) \
                    & (og_check | collab_check)
                detail = True
            else:
                if project_id:
                    project_id_check = Q(fq_dataset__project__id=project_id)
                if project_name:
                    project_name_check = Q(fq_dataset__project__name=project_name)
                if dataset_id:
                    fq_dataset_id_check = Q(fq_dataset__id=dataset_id)
                if dataset_name:
                    fq_dataset_name_check = Q(fq_dataset__name=dataset_name)
                if name:
                    name_check = Q(name=name)
                if data_type:
                    data_type_check = Q(data_type=data_type)
                if version:
                    version_check = Q(version=version)
                if valid:
                    valid_check = Q(valid_to=None)
                    
                Q_comb = project_id_check \
                    & project_name_check \
                    & fq_dataset_id_check \
                    & fq_dataset_name_check \
                    & name_check \
                    & data_type_check \
                    & valid_check \
                    & version_check \
                    & (og_check | collab_check)
            
            qset = ProData.objects.filter(Q_comb).distinct().all()
            
            if detail:
                serializer = ProDataCLIDetailSerializer(qset, many=True)
            else:
                serializer = ProDataCLISerializer(qset, many=True)
                            
            return Response(serializer.data)
        else:
            Q_comb = og_check | collab_check
            qset = ProData.objects.filter(Q_comb).all().distinct().order_by("-created")
            serializer = ProDataCLISerializer(qset, many=True)
            return Response(serializer.data)


    def post(self, request):
        
        # Validate the Serializer
        serializer = ProDataUploadSerializer(data=request.data)
                
        if serializer.is_valid():
            
            name = serializer.validated_data.get('name')
            data_type = serializer.validated_data.get('data_type')
            description = serializer.validated_data.get('description')
            upload_path = serializer.validated_data.get('upload_path')
            metadata = serializer.validated_data.get('metadata')        
            dataset_id = serializer.validated_data.get('dataset_id', None)
            dataset_name = serializer.validated_data.get('dataset_name', None)

            if dataset_id:
                fq_dataset = FqDataset.objects.filter(id=dataset_id).all()
            elif dataset_name:
                fq_dataset = FqDataset.objects.filter(name=dataset_name).all()
            else:
                return Response({'detail' : 'Provide dataset_id or dataset_name'}, status=400)
                        
            if len(fq_dataset) == 0:
                return Response({'detail' : 'FqDataset not found'}, status=400)
            elif len(fq_dataset) > 1:
                return Response({'detail' : 'Multiple FqDatasets found'}, status=400)
            else:
                fq_dataset = fq_dataset.first()
                
                owner = request.user
                
                # Get ProData object with highest version
                qset = ProData.objects.filter(name=name,
                                                fq_dataset=fq_dataset).order_by('-version').first()
                
                if qset:
                    # If valid to is None, set valid to to now
                    if qset.valid_to is None:
                        qset.valid_to = datetime.datetime.now()
                        qset.save()
                    new_version = qset.version + 1
                else:
                    new_version = 1
                
                # Create ProData // No check if Path Exists?
                res = ProData.objects.create(name=name,
                                            data_type=data_type,
                                            description=description,
                                            upload_path=upload_path,
                                            metadata=metadata,
                                            owner=owner,
                                            fq_dataset=fq_dataset,
                                            version=new_version)
            
            return Response({'id' : res.id}, status=201)
        else:
            return Response(serializer.errors, status=400)
        
    
    def delete(self, request, pk=None):

        dataset_id = self.request.query_params.get('dataset_id', None)
        dataset_name = self.request.query_params.get('dataset_name', None)
        name = self.request.query_params.get('name', None)
        version = self.request.query_params.get('version', None)

        if pk:
            if ProData.objects.filter(pk=pk).exists():
                qset = ProData.objects.filter(pk=pk).delete()
                return Response({'detail' : 'ProData deleted', 'id' : pk}, status=200)
            else:
                return Response({'detail' : 'ProData not found'}, status=400)
        else:
            if name and (dataset_id or dataset_name):
                name_check = Q(name=name)
                dataset_id_check = Q()
                dataset_name_check = Q()
                version_check = Q()

                if dataset_id:
                    dataset_id_check = Q(fq_dataset__id=dataset_id)
                if dataset_name:
                    dataset_name_check = Q(fq_dataset__name=dataset_name)

                if version:
                    version_check = Q(version=version)
                else:
                    version_check = Q(valid_to=None)    

                Q_comb = name_check & dataset_id_check & dataset_name_check & version_check

                if ProData.objects.filter(Q_comb).exists():
                    qset = ProData.objects.filter(Q_comb).first()
                    pro_data_id = qset.id
                    qset.delete()

                    return Response({'detail' : 'ProData deleted', 'id' : pro_data_id}, status=200)
                else:
                    return Response({'detail' : 'ProData not found'}, status=400)
            else:
                return Response({'detail' : 'Provide name and (dataset_id or dataset_name)'}, status=400)
