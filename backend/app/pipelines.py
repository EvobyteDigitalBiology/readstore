# readstore-basic/backend/app/pipelines.py

import gzip
from typing import Tuple, List
import numpy as np
from itertools import islice
import hashlib
import os
import threading
import queue
import time

import pysam
from django.contrib.auth.models import User

from .models import FqFile

from settings.base import FQ_QUEUE_NUM_WORKERS
from settings.base import FQ_QUEUE_MAX_SIZE

def stage_fastq(fq_file_path: str, fq_name: str, owner: User, read_type: str):
    """Get stats from Fastq File

    Return stats from Fastq File and if it is valid
    Errors in reading file will return False
    
    Args:
        fq_file_path: Path to Fastq File
    """
    
    filesize_mb = int(os.path.getsize(fq_file_path) / (1024 * 1024))
    
    # Read in chunks of 1 GB to calculate MD5
    hasher = hashlib.md5()
    
    with open(fq_file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk) 

    md5_checksum = hasher.hexdigest()
    phred_qualities = []
    
    fq_cnt = 0
    
    try:
        with pysam.FastxFile(fq_file_path, persist = False) as fh:
            for entry in fh:
                fq_cnt += 1

                # TODO adapt for fastq files with very few reads
                if (fq_cnt % 1000) == 0:
                    seq_len = len(entry.sequence)
                    phred_qualities.append(entry.get_quality_array())
        
        phred_ar = np.array(phred_qualities)
        phred_ar = np.mean(phred_ar, axis=0)
        mean_phred = np.mean(phred_ar)
        
        phred = phred_ar.tolist()
        phred_dict = {i : phred[i] for i in range(len(phred))}
        
        qc_passed = True
    
    except Exception as e:
        qc_passed = False
        seq_len = 0
        mean_phred = 0
        phred_dict = {}
    
    FqFile.objects.create(
        name = fq_name,
        bucket = '',
        key = '',
        upload_path = fq_file_path,
        qc_passed = qc_passed,
        read_type = read_type,
        read_length = seq_len,
        num_reads = fq_cnt,
        qc_phred_mean = mean_phred,
        qc_phred = phred_dict,
        size_mb = filesize_mb,
        staging = True,
        pipeline_version = 'basic_qc_v1',
        md5_checksum = md5_checksum,
        owner = owner
    )
    
    dataset_queue.pop(0)
    
    print('Created FqFile object for ', fq_name)
    print('Created FqFile path for ', fq_file_path)
    

# Worker function to pick up and process jobs from the queue
def staging_worker():
    while True:
        job = job_queue.get()
        if job is None:
            break  # Exit if a None job is received, signaling the end
        stage_fastq(**job)
        job_queue.task_done()

# Define the queue to hold jobs // 
job_queue = queue.Queue()
dataset_queue = []

num_worker_threads = FQ_QUEUE_NUM_WORKERS # Adjust the number of threads as needed
threads = []
for i in range(num_worker_threads):
    t = threading.Thread(target=staging_worker)
    t.start()
    threads.append(t)

def get_queue_jobs() -> int:
    return len(dataset_queue)
        
def exec_staging_job(fq_file_path: str, fq_name: str, owner: User, read_type: str):
    
    queue_size = get_queue_jobs()
    if queue_size >= FQ_QUEUE_MAX_SIZE:
        return False
    
    dataset_queue.append(fq_file_path)
    
    job_queue.put({'fq_file_path': fq_file_path,
                   'fq_name': fq_name,
                   'owner': owner,
                   'read_type': read_type})
    
    return True