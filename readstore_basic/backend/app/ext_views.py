# readstore-basic/backend/app/ext_views.py

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

from .authentication import RSClientTokenAuth
from .permissions import RSClientHasStaging

from .serializers import FqFileSerializer
from .serializers import FqFileCLISerializer
from .serializers import FqFileCLIUploadSerializer

from .serializers import FqDatasetCLISerializer
from .serializers import FqDatasetCLIDetailSerializer
from .serializers import FqDatasetCLIUploadSerializer
from .serializers import ProjectCLISerializer
from .serializers import ProjectCLIDetailSerializer
from .serializers import ProjectCLIUploadSerializer
from .serializers import ProDataCLISerializer
from .serializers import ProDataCLIDetailSerializer
from .serializers import ProjectAttachmentSerializer
from .serializers import ProjectAttachmentListSerializer
from .serializers import FqUploadSerializer
from .serializers import FqAttachmentSerializer
from .serializers import FqAttachmentListSerializer
from .serializers import ProDataUploadSerializer


from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate

from django.shortcuts import get_object_or_404

from django.db.models import Q

from .models import AppUser
from .models import FqFile
from .models import FqDataset
from .models import FqAttachment
from .models import Project
from .models import ProjectAttachment
from .models import ProData

from settings.base import VALID_FASTQ_EXTENSIONS
from settings.base import VALID_READ1_SUFFIX
from settings.base import VALID_READ2_SUFFIX
from settings.base import VALID_INDEX1_SUFFIX
from settings.base import VALID_INDEX2_SUFFIX


class TokenExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        return view_permissions
    
    def post(self, request):        
        return Response({'detail' : 'token valid'}, status=200)

class FqFileExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method in ['POST', 'PUT', 'DELETE']:
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

            qset = FqFile.objects.filter(pk=pk).all()            
            
            # Add creator name as attribute
            for q in qset:
                q.creator = q.owner.username  
            
            serializer = FqFileCLISerializer(qset, many=True)        
            return Response(serializer.data)

        # Get all fq files where user has access
        else:
            # Get corresponding fq files
            qset = FqFile.objects.all()
            
            # Add creator name as attribute
            for q in qset:
                q.creator = q.owner.username   
            
            serializer = FqFileCLISerializer(qset, many=True)        
            return Response(serializer.data)
    
    
    def post(self, request):
        
        serializer = FqFileCLIUploadSerializer(data=request.data)
      
        if serializer.is_valid():
            
            owner = request.user
            
            # Validate that read type is valid
            read_type = serializer.validated_data.get('read_type')

            upload_path = serializer.validated_data.get('upload_path')
                        
            # Validate that qc phred is a valid dict
            qc_phred = serializer.validated_data.get('qc_phred')
            qc_phred_index_pos = list(qc_phred.keys())
            qc_phred_values = list(qc_phred.values())
            
            if not all([x.isnumeric() for x in qc_phred_index_pos]):
                return Response({'detail' : 'Invalid qc_phred index values. Must be numeric string'}, status=400)
            if not all(isinstance(x, float) for x in qc_phred_values):
                return Response({'detail' : 'Invalid qc_phred values. Must be float'}, status=400)
                
            if not read_type in ['R1', 'R2', 'I1', 'I2']:
                return Response({'detail' : 'Invalid read type'}, status=400)

            # Check that file path is found
            if not os.path.exists(upload_path):
                return Response({'detail' : 'File not found'}, status=400)
            elif not os.access(upload_path, os.R_OK):
                return Response({'detail' : 'No Read Permission'}, status=400)
            
            # Option: Check for file extension
            
            # Create FqFile
            
            fq_file = FqFile.objects.create(name=serializer.validated_data.get('name'),
                                            read_type=read_type,
                                            qc_passed=serializer.validated_data.get('qc_passed'),
                                            read_length=serializer.validated_data.get('read_length'),
                                            num_reads=serializer.validated_data.get('num_reads'),
                                            size_mb=serializer.validated_data.get('size_mb'),
                                            qc_phred_mean=serializer.validated_data.get('qc_phred_mean'),
                                            qc_phred=qc_phred,
                                            upload_path=upload_path,
                                            md5_checksum=serializer.validated_data.get('md5_checksum'),
                                            owner=owner,
                                            pipeline_version=serializer.validated_data.get('pipeline_version'),
                                            staging = serializer.validated_data.get('staging'))
            
            out_serializer = FqFileSerializer(fq_file)
            
            return Response(out_serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
        
        
    def put(self, request, pk):
      
        serializer = FqFileCLIUploadSerializer(data=request.data)
      
        if serializer.is_valid():
            
            fq_file = get_object_or_404(FqFile, pk=pk)
            
            # Validate that read type is valid
            read_type = serializer.validated_data.get('read_type')

            upload_path = serializer.validated_data.get('upload_path')
                        
            # Validate that qc phred is a valid dict
            qc_phred = serializer.validated_data.get('qc_phred')
            qc_phred_index_pos = list(qc_phred.keys())
            qc_phred_values = list(qc_phred.values())
            
            if not all([x.isnumeric() for x in qc_phred_index_pos]):
                return Response({'detail' : 'Invalid qc_phred index values. Must be numeric string'}, status=400)
            if not all(isinstance(x, float) for x in qc_phred_values):
                return Response({'detail' : 'Invalid qc_phred values. Must be float'}, status=400)
                
            if not read_type in ['R1', 'R2', 'I1', 'I2']:
                return Response({'detail' : 'Invalid read type'}, status=400)

            # Check that file path is found
            if not os.path.exists(upload_path):
                return Response({'detail' : 'File not found'}, status=400)
            elif not os.access(upload_path, os.R_OK):
                return Response({'detail' : 'No Read Permission'}, status=400)
      
            fq_file.name = serializer.validated_data.get('name')
            fq_file.read_type = read_type
            fq_file.qc_passed = serializer.validated_data.get('qc_passed')
            fq_file.read_length = serializer.validated_data.get('read_length')
            fq_file.num_reads = serializer.validated_data.get('num_reads')
            fq_file.size_mb = serializer.validated_data.get('size_mb')
            fq_file.qc_phred_mean = serializer.validated_data.get('qc_phred_mean')
            fq_file.qc_phred = qc_phred
            fq_file.upload_path = upload_path
            fq_file.md5_checksum = serializer.validated_data.get('md5_checksum')
            fq_file.pipeline_version = serializer.validated_data.get('pipeline_version')
            fq_file.staging = serializer.validated_data.get('staging')
            
            fq_file.save()
            
            out_serializer = FqFileSerializer(fq_file)
            
            return Response(out_serializer.data, status=200)
        
        else:
            return Response(serializer.errors, status=400)
    
    
    def delete(self, request, pk):
        
        fq_file = get_object_or_404(FqFile, pk=pk)
        
        fq_file.delete()
        
        return Response({'detail' : 'FqFile deleted'}, status=200)
    
    
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
         
class FqDatasetExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method in ['POST', 'PUT', 'DELETE']:
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
        
        
    def post(self, request):
        
        # Validate the Serializer
        serializer = FqDatasetCLIUploadSerializer(data=request.data)
        
        
        if serializer.is_valid():
            
            owner = request.user
            owner_group = owner.appuser.owner_group
            
            name = serializer.validated_data.get('name')
            project_ids = serializer.validated_data.get('project_ids')
            project_names = serializer.validated_data.get('project_names')
            
            fq_file_r1 = serializer.validated_data.get('fq_file_r1')
            fq_file_r2 = serializer.validated_data.get('fq_file_r2')
            fq_file_i1 = serializer.validated_data.get('fq_file_i1')
            fq_file_i2 = serializer.validated_data.get('fq_file_i2')
            
            # Check if fq file with this name exists
            if FqDataset.objects.filter(name=name).exists():
                return Response({'detail' : 'FqDataset with this name exists'}, status=400)
            
            # Check if projects exists and unify project_ids and project_names to ids
            if len(project_ids) > 0:
                qset = Project.objects.filter(id__in=project_ids).all()
                project_ids_qset = list(qset.values_list('id', flat=True))
                
                if set(project_ids) != set(project_ids_qset):
                    diff_ids = set(project_ids) - set(project_ids_qset)
                    return Response({'detail' : f'Project IDs not found {diff_ids}'}, status=400)
            
            # Check if project names exists and unify project_ids and project_names to ids
            project_ids_from_names = []
            if len(project_names) > 0:
                qset = Project.objects.filter(name__in=project_names).all()
                project_names_qset = list(qset.values_list('name', flat=True))
                
                if set(project_names) != set(project_names_qset):
                    diff_names = set(project_names) - set(project_names_qset)
                    return Response({'detail' : f'Project Names not found {diff_names}'}, status=400)
                else:
                    project_ids_from_names = list(qset.values_list('id', flat=True))
            project_ids = list(set(project_ids + project_ids_from_names))
            
            # Check if fq files exists
            if fq_file_r1:
                if not FqFile.objects.filter(pk=fq_file_r1).exists():
                    return Response({'detail' : 'FqFile R1 not found'}, status=400)
                else:
                    fq_file_r1 = FqFile.objects.get(pk=fq_file_r1)
            if fq_file_r2:
                if not FqFile.objects.filter(pk=fq_file_r2).exists():
                    return Response({'detail' : 'FqFile R2 not found'}, status=400)
                else:
                    fq_file_r2 = FqFile.objects.get(pk=fq_file_r2)
            if fq_file_i1:
                if not FqFile.objects.filter(pk=fq_file_i1).exists():
                    return Response({'detail' : 'FqFile I1 not found'}, status=400)
                else:
                    fq_file_i1 = FqFile.objects.get(pk=fq_file_i1)
            if fq_file_i2:
                if not FqFile.objects.filter(pk=fq_file_i2).exists():
                    return Response({'detail' : 'FqFile I2 not found'}, status=400)
                else:
                    fq_file_i2 = FqFile.objects.get(pk=fq_file_i2)
            
            # Create FqDataset
            fq_dataset = FqDataset.objects.create(name=name,
                                                description=serializer.validated_data.get('description'),
                                                qc_passed=serializer.validated_data.get('qc_passed'),
                                                fq_file_r1=fq_file_r1,
                                                fq_file_r2=fq_file_r2,
                                                fq_file_i1=fq_file_i1,
                                                fq_file_i2=fq_file_i2,
                                                paired_end = serializer.validated_data.get('paired_end'),
                                                index_read = serializer.validated_data.get('index_read'),
                                                owner=owner,
                                                owner_group=owner_group,
                                                metadata=serializer.validated_data.get('metadata'))
            
            fq_dataset.project.set(project_ids)
            fq_dataset.save()
            
            output_serializer = FqDatasetCLIDetailSerializer(fq_dataset)
            
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
        
    
    def put(self, request, pk):
        
        # Validate the Serializer
        serializer = FqDatasetCLIUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            
            # Validate that FqDataset for ID can be found
            fq_dataset = get_object_or_404(FqDataset, pk=pk)
            
            name = serializer.validated_data.get('name')
            
            if FqDataset.objects.filter((~Q(pk=pk)) & Q(name=name)).exists():
                return Response({'detail' : 'FqDataset with this name already exists'}, status=400)
            
            project_ids = serializer.validated_data.get('project_ids')
            project_names = serializer.validated_data.get('project_names')
            
            fq_file_r1 = serializer.validated_data.get('fq_file_r1')
            fq_file_r2 = serializer.validated_data.get('fq_file_r2')
            fq_file_i1 = serializer.validated_data.get('fq_file_i1')
            fq_file_i2 = serializer.validated_data.get('fq_file_i2')
            
            # Check if projects exists and unify project_ids and project_names to ids
            if len(project_ids) > 0:
                qset = Project.objects.filter(id__in=project_ids).all()
                project_ids_qset = list(qset.values_list('id', flat=True))
                
                if set(project_ids) != set(project_ids_qset):
                    diff_ids = set(project_ids) - set(project_ids_qset)
                    return Response({'detail' : f'Project IDs not found {diff_ids}'}, status=400)
            
            # Check if project names exists and unify project_ids and project_names to ids
            project_ids_from_names = []
            if len(project_names) > 0:
                qset = Project.objects.filter(name__in=project_names).all()
                project_names_qset = list(qset.values_list('name', flat=True))
                
                if set(project_names) != set(project_names_qset):
                    diff_names = set(project_names) - set(project_names_qset)
                    return Response({'detail' : f'Project Names not found {diff_names}'}, status=400)
                else:
                    project_ids_from_names = list(qset.values_list('id', flat=True))
            project_ids = list(set(project_ids + project_ids_from_names))
            
            # Check if fq files exists
            if fq_file_r1:
                if not FqFile.objects.filter(pk=fq_file_r1).exists():
                    return Response({'detail' : 'FqFile R1 not found'}, status=400)
                else:
                    fq_file_r1 = FqFile.objects.get(pk=fq_file_r1)
            if fq_file_r2:
                if not FqFile.objects.filter(pk=fq_file_r2).exists():
                    return Response({'detail' : 'FqFile R2 not found'}, status=400)
                else:
                    fq_file_r2 = FqFile.objects.get(pk=fq_file_r2)
            if fq_file_i1:
                if not FqFile.objects.filter(pk=fq_file_i1).exists():
                    return Response({'detail' : 'FqFile I1 not found'}, status=400)
                else:
                    fq_file_i1 = FqFile.objects.get(pk=fq_file_i1)
            if fq_file_i2:
                if not FqFile.objects.filter(pk=fq_file_i2).exists():
                    return Response({'detail' : 'FqFile I2 not found'}, status=400)
                else:
                    fq_file_i2 = FqFile.objects.get(pk=fq_file_i2)
            
            # Update entry
            fq_dataset.name = name
            fq_dataset.description = serializer.validated_data.get('description')
            fq_dataset.qc_passed = serializer.validated_data.get('qc_passed')
            fq_dataset.fq_file_r1 = fq_file_r1
            fq_dataset.fq_file_r2 = fq_file_r2
            fq_dataset.fq_file_i1 = fq_file_i1
            fq_dataset.fq_file_i2 = fq_file_i2
            fq_dataset.paired_end = serializer.validated_data.get('paired_end')
            fq_dataset.index_read = serializer.validated_data.get('index_read')
            fq_dataset.metadata = serializer.validated_data.get('metadata')
            
            fq_dataset.project.set(project_ids)
            fq_dataset.save()
            
            output_serializer = FqDatasetCLIDetailSerializer(fq_dataset)
            
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)    

    def delete(self, request, pk):
        
        # Validate that FqDataset for ID can be found
        fq_dataset = get_object_or_404(FqDataset, pk=pk)
        
        # Delete FqDataset
        fq_dataset.delete()
        
        return Response({'detail' : 'FqDataset deleted'}, status=200)



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



class ProjectExt(APIView):
    
    authentication_classes = [RSClientTokenAuth]
    
    def get_permissions(self):
        view_permissions = super().get_permissions()
        view_permissions.append(IsAuthenticated())
        if self.request.method == ['POST', 'PUT', 'DELETE']:
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
    
    def post(self, request):
        
        # Validate the Serializer
        serializer = ProjectCLIUploadSerializer(data=request.data)

        if serializer.is_valid():
            
            owner = request.user
            owner_group = owner.appuser.owner_group
            
            name = serializer.validated_data.get('name')
            
            # Check if fq file with this name exists
            if Project.objects.filter(name=name).exists():
                return Response({'detail' : 'Project with this name exists'}, status=400)

            # Create FqDataset
            project = Project.objects.create(name = name,
                                            description = serializer.validated_data.get('description'),
                                            metadata = serializer.validated_data.get('metadata'),
                                            dataset_metadata_keys = serializer.validated_data.get('dataset_metadata_keys'),
                                            owner = owner,
                                            owner_group = owner_group)

            out_serializer = ProjectCLIUploadSerializer(project)

            return Response(out_serializer.data, status=201)
            
        else:
            return Response(serializer.errors, status=400)
        
        
    def put(self, request, pk):
        
        # Validate the Serializer
        serializer = ProjectCLIUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            
            project = get_object_or_404(Project, pk=pk)

            name = serializer.validated_data.get('name')

            if Project.objects.filter((~Q(pk=pk)) & Q(name=name)).exists():
                return Response({'detail' : 'Project with this name already exists'}, status=400)

            project.name = name
            project.description = serializer.validated_data.get('description')
            project.metadata = serializer.validated_data.get('metadata')
            project.dataset_metadata_keys = serializer.validated_data.get('dataset_metadata_keys')

            project.save()
            
            out_serializer = ProjectCLIUploadSerializer(project)
            
            return Response(out_serializer.data, status=200)
            
        else:
            return Response(serializer.errors, status=400)
            
    def delete(self, request, pk):
        
        # Validate that Project for ID can be found
        project = get_object_or_404(Project, pk=pk)
        
        # Delete Project
        project.delete()
        
        return Response({'detail' : 'Project deleted'}, status=200)
    
    
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
            
                out_serializer = ProDataCLIDetailSerializer(res)
            
            return Response(out_serializer.data, status=201)
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
