# readstore-basic/backend/app/views.py

"""

    Class Views for ReadStore Django Backend
    
    Classes:
        -
        -
        -
        -
        

"""

#import re
from collections import defaultdict
import os
import sys
import datetime

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import DjangoModelPermissions

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .serializers import UserSerializer
from .serializers import OwnerGroupSerializer
from .serializers import GroupSerializer
from .serializers import AppUserSerializer
from .serializers import FqFileSerializer
from .serializers import FqDatasetSerializer
from .serializers import FqAttachmentSerializer
from .serializers import FqAttachmentListSerializer
from .serializers import ProjectSerializer
from .serializers import ProjectAttachmentSerializer
from .serializers import ProjectAttachmentListSerializer
from .serializers import PwdSerializer
from .serializers import FqUploadSerializer
from .serializers import LicenseKeySerializer
from .serializers import ProDataSerializer
from .serializers import ProDataUploadSerializer
from .serializers import TransferOwnerSerializer


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


class TransferOwnerView(APIView):
    """
        APIView GetUserGroupsView

        Transfer Ownership for objects
        
        Requesting user must be admin
    """
    
    # Set permission classes, i.e. user must be authenticated to DB
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        serializer = TransferOwnerSerializer(data=request.data)
        
        if serializer.is_valid():
            
            source_owner = serializer.validated_data.get('source_owner_id')
            dest_owner = serializer.validated_data.get('dest_owner_id')
            
            # Check that request user is admin
            if request.user \
                        .groups \
                        .filter(name__in=['admin']) \
                        .exists():

                Project.objects.filter(owner=source_owner).update(owner=dest_owner)
                ProjectAttachment.objects.filter(owner=source_owner).update(owner=dest_owner)
                FqDataset.objects.filter(owner=source_owner).update(owner=dest_owner)
                FqAttachment.objects.filter(owner=source_owner).update(owner=dest_owner)
                FqFile.objects.filter(owner=source_owner).update(owner=dest_owner)
                ProData.objects.filter(owner=source_owner).update(owner=dest_owner)
                
                out_serializer = UserSerializer(dest_owner)
                
                return Response(out_serializer.data, status=201)
                
            else:
                return Response({'detail' : 'Request is not admin'}, status=400)
        else:        
            return(Response(serializer.errors, status=400))

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
        
        # TODO V1.3.1: Check if FqFiles provided are associated with other FqDatasets
        
        serializer.save(owner=self.request.user)
    
    def perform_destroy(self, instance):
        """Delete FqDataset

        Delete FqDataset and attached FqFiles
        
        """
        
        try:
            # Delete FqFiles // Need to filter for None?
            fq_files = [instance.fq_file_r1,
                        instance.fq_file_r2,
                        instance.fq_file_i1,
                        instance.fq_file_i2]
            
            for fq in fq_files:
                if fq:
                    fq.delete()
                        
            instance.delete()
            
            return Response({'detail' : 'FqDataset deleted'}, status=204)
            
        except FqDataset.DoesNotExist:
            return Response({'detail' : 'FqDataset not found'}, status=404)
    
    
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

    @action(detail=False, methods=['get'])
    def empty(self, request):
        """FqDataset without FqFiles

        Returns FqDataset without FqFiles
        
        """
        
        qset = FqDataset.objects.filter(fq_file_r1=None,
                                        fq_file_r2=None,
                                        fq_file_i1=None,
                                        fq_file_i2=None).all().order_by("-created")
        
        serializer = self.get_serializer(qset, many=True)        
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

            
class ProjectViewSet(viewsets.ModelViewSet):
    """
        API endpoint that allows Projects to be viewed or edited.
    """
    
    permission_classes = [IsAuthenticated,
                        DjangoModelPermissions]

    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        
        name = self.request.query_params.get('name', None)
        owner = self.request.query_params.get('owner', None)
        
        # Add endpoints for restricted access to projects
        name_check = Q()
        if name:
            name_check = Q(name=name)
        owner_check = Q()
        if owner:
            owner_check = Q(owner=owner)
            
        queryset = Project.objects.filter(name_check & owner_check).all().order_by("-created")
            
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
    
    
    def get_queryset(self):
        
        owner = self.request.query_params.get('owner', None)
        
        owner_check = Q()
        if owner:
            owner_check = Q(owner=owner)
            
        queryset = ProData.objects.filter(owner_check).all().order_by("-created")
            
        return queryset
    
    
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