# readstore-basic/frontend/streamlit/app_pages/staging.py

from typing import List
import time
import uuid
import string
import json
import itertools
import os

import streamlit as st
import pandas as pd
import openpyxl

import st_yled
from st_yled import split_button

import extensions
import datamanager
import exceptions

from uidataclasses import OwnerGroup
from uidataclasses import Project

import uiconfig

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

st_yled.init()

if not 'dataset_select_project_names' in st.session_state:
    st.session_state['dataset_select_project_names'] = []

if not 'dataset_name_active' in st.session_state:
    st.session_state['dataset_name_active'] = (None, None)  # (dataset_name, is_preexist)

if not 'toast_cache' in st.session_state:
    st.session_state['toast_cache'] = None

if not 'error_cache' in st.session_state:
    st.session_state['error_cache'] = None

def show_updated(ix):
    
    change = st.session_state[f"fq_sd_{ix}"]
    edited = change['edited_rows']
    st.session_state['update_field_state'] = (ix, edited)

def update_active_dataset_name():
    
    dataset_select_value = st.session_state['staging_dataset_preexist']
    dataset_select_name = st.session_state['staging_dataset_name']

    if dataset_select_value is not None:
        st.session_state['dataset_name_active'] = (dataset_select_value.strip(), 'preexist')
    else:
        st.session_state['dataset_name_active'] = (dataset_select_name.strip(), 'new')

    # if not dataset_select_name is None:
    #     st.session_state['preexist_dataset_name'] = dataset_select_name
    # else:
    #     del st.session_state['preexist_dataset_name']



    
# Print Info about User
# colh1, colh2 = st.columns([11,1], vertical_alignment='top')

# with colh1:
#     st.markdown(
#         """
#         <div style="text-align: right;">
#             <b>Username</b> {username}
#         </div>
#         """.format(username=st.session_state['username']),
#         unsafe_allow_html=True
#     )
# with colh2:
#     st.page_link('app_pages/settings.py', label='', icon=':material/settings:')

# Change top margin of app

# st.markdown(
#     """
#     <style>
#         .stAppViewBlockContainer {
#             margin-top: 0px;
#             padding-top: 80px;
#         }
#     </style>
#     """,
#     unsafe_allow_html=True)

# Reset session state for selecting datasets for projects
if 'available_staging' in st.session_state:
    del st.session_state['available_staging']
if 'selected_staging' in st.session_state:
    del st.session_state['selected_staging']
# if 'selected_input' in st.session_state:
#     del st.session_state['selected_input']
# if 'available_input' in st.session_state:
#     del st.session_state['available_input']

# Assign and remove datasets to project
def add_selected_datasets(fq_datasets, selected_rows):
                
    if len(selected_rows) == 0:
        return
    else:    
        # Get ID of selected dataset
        select_dataset_r = fq_datasets.iloc[selected_rows,:]
        # Append to selected datasets
        st.session_state['selected_staging'] = pd.concat([
            st.session_state['selected_staging'],
            select_dataset_r
        ], axis=0)

        # Filter out prev selected ID
        st.session_state['available_staging'] = st.session_state['available_staging'].loc[
            ~st.session_state['available_staging']['name'].isin(select_dataset_r['name']),:]
               
def remove_selected_datasets(fq_datasets, selected_rows):
    
    if len(selected_rows) == 0:
        return
    else:    
        # Get ID of selected dataset
        select_dataset_r = fq_datasets.iloc[selected_rows,:]
        # Append to selected datasets
        st.session_state['available_staging'] = pd.concat([
            st.session_state['available_staging'],
            select_dataset_r
        ], axis=0)

        # Filter out prev selected ID
        st.session_state['selected_staging'] = st.session_state['selected_staging'].loc[
            ~st.session_state['selected_staging']['name'].isin(select_dataset_r['name']),:]

def update_selected_project_names():
    st.session_state['dataset_select_project_names'] = st.session_state['multiselect_staging_project_names']

def reset_selected_project_names():
    st.session_state['dataset_select_project_names'] = []


# region Check In
@st.dialog('Check In Dataset', width='large', on_dismiss='rerun')
def checkin_df(fq_file_df: pd.DataFrame,
               projects_owner_group: pd.DataFrame,
               fq_datasets_empty: pd.DataFrame,
               reference_fq_dataset_names: pd.Series):
    
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()
    
    empty_dataset_names = fq_datasets_empty['name'].tolist()
    
    project_names_select = st.session_state['dataset_select_project_names']

    read_long_map = {
        'R1' : 'Read 1',
        'R2' : 'Read 2',
        'I1' : 'Index 1',
        'I2' : 'Index 2',
    }
    
    # Used to define the updated fastq files
    read_fq_map = {
    }
    
    read_types = fq_file_df['read_type'].unique()
    read_types = sorted(read_types)
    
    if 'NA' in read_types:
        st.session_state['error_cache'] = "Please set Read type (R1, R2, I1, I2) of ALL FASTQ files."

    elif fq_file_df['read_type'].duplicated().any():
        st.session_state['error_cache'] = "Read types must be unique for each dataset. Do not use duplicate R1 or R2 entries."
    else:
        
        # region Project Tab
        tab_names = [read_long_map[rt] for rt in read_types]
        fq_file_names = ['NA'] * len(read_types)
        
        tab_names_format = ["Features",
                            "Projects",
                            "Attachments"]
        tab_names_format.extend([f"{tn}" for tn in tab_names])
        reads_offset = 3
        
        # Add Metadata and Attachments Tabs
        tabs = st_yled.tabs(tab_names_format, font_size=14, font_weight=500)

        # region Metadata Tab
        with tabs[0]:
            
            st_yled.markdown('Set Dataset Attributes and Metadata or attach to an existing Dataset.', font_size=12, color='#808495')

            with st.container(horizontal=True):

                name_old = fq_file_df['dataset'].iloc[0]

                if st.session_state['dataset_name_active'][1] is None:
                    display_name = name_old
                else:
                    display_name = st.session_state['dataset_name_active'][0]

                if st.session_state['dataset_name_active'][1] == 'preexist':
                    disable_input = True
                else:
                    disable_input = False

                # Set dataset name
                st_yled.text_input("Dataset Name",
                                    max_chars=150,
                                    help = 'Name must only contain [0-9][a-z][A-Z][.-_@ ]',
                                    width = 320,
                                    disabled = disable_input,
                                    value = display_name,
                                    border_style='none',
                                    border_width='0px',
                                    key='staging_dataset_name',
                                    on_change = update_active_dataset_name)
                
                if len(empty_dataset_names) > 0:
            
                    st_yled.selectbox('Select existing Dataset',
                                    options=empty_dataset_names,
                                    index=None,
                                    border_style='none',
                                    border_width='0px',
                                    width = 240,
                                    key='staging_dataset_preexist',
                                    on_change = update_active_dataset_name)

            if st.session_state['dataset_name_active'][1] == 'preexist':
                description_template = fq_datasets_empty.loc[
                    fq_datasets_empty['name'] == display_name,'description'].iloc[0]
            else:
                description_template = ''

            metadata_keys = projects_owner_group.loc[
                projects_owner_group['name'].isin(project_names_select),'dataset_metadata_keys'].to_list()
            metadata_keys = [list(m.keys()) for m in metadata_keys]
            metadata_keys = itertools.chain.from_iterable(metadata_keys)
            metadata_keys = sorted(list(set(metadata_keys)))
            
            metadata_df_template = pd.DataFrame({
                'key' : metadata_keys,
                'value' : ''
            })
            
            st.write('')

            description = st_yled.text_area("Dataset Description",
                                    help = 'Description of the project.',
                                    width = 512,
                                    border_style='none',
                                    border_width='0px',
                                    placeholder = description_template,
                                    disabled = disable_input,
                                    key = 'create_project_description_input')

            st.write("")

            st_yled.markdown('Metadata', font_size=14, font_weight=500)

            if disable_input:

                st_yled.info(':material/notifications: Metadata cannot be modified when checking in to an existing Dataset',
                            border_width="2.0px",
                            border_color="#808495",
                            border_style="solid",
                            color="#808495",
                            key='info-staging-metadata-disabled',
                            width=400)

            else:

                with st_yled.container(key='staging-dataset-metadata-info'):
                    st_yled.markdown("Project metadata must be provided as key-value pairs.", font_size=12, color='#808495')
                    st_yled.markdown("Metadata facilitate grouping and filtering of projects by pre-defined features.", font_size=12, color='#808495')

                metadata_df_template = metadata_df_template.astype(str)
                metadata_df = st.data_editor(
                    metadata_df_template,
                    hide_index=True,
                    column_config = {
                        'key' : st.column_config.TextColumn('Key'),
                        'value' : st.column_config.TextColumn('Value')
                    },
                    num_rows ='dynamic',
                    key = 'create_metadata_df',
                    width=400
                )

        with tabs[1]:
            
            # Input is disabled when checking in to existing dataset
            if disable_input:
                    
                st.write("")

                st_yled.info(':material/notifications: Projects cannot be modified when checking in to an existing Dataset',
                            border_width="2.0px",
                            border_color="#808495",
                            border_style="solid",
                            color="#808495",
                            key='info-staging-project-disabled',
                            width=400)
            
            else:
                st_yled.markdown('Attach the Dataset to one or more Projects', font_size=12, color='#808495')
                
                project_names_select = st.multiselect("Select Projects",
                                                    sorted(projects_owner_group['name'].unique()),
                                                    help = 'Attach the dataset to Project(s).',
                                                    key = 'multiselect_staging_project_names',
                                                    disabled = disable_input,
                                                    on_change=update_selected_project_names,
                                                    width = 400)
                
            st.write("")
            st.write("")

        # region Projects Tab
        with tabs[2]:
            
            with st.container(key='staging-attachments-info'):
                
                if disable_input:
                    
                    st.write("")

                    st_yled.info(':material/notifications: Attachments cannot be added when checking in to an existing Dataset',
                                border_width="2.0px",
                                border_color="#808495",
                                border_style="solid",
                                color="#808495",
                                key='info-staging-attachment-disabled',
                                width=400)

                else:
                    st_yled.markdown('Attach Files to the Dataset', font_size=12, color='#808495')
                
                    st.write("")
                    st.write("")

                    uploaded_files = st.file_uploader(
                        "Choose Files to Upload",
                        help = "Upload Attachments for the Dataset. Attachments can be any File Type.",
                        accept_multiple_files=True,
                        width = 400
                    )
                    
                st.write("")
                st.write("")
        
        # Show reads
        for ix, rt in enumerate(read_types):
            
            # region Read Tab
            with tabs[reads_offset+ix]:
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    
                    with st_yled.container(height=460, padding='32px', border_style='none'):
                    
                        # Get id of the fq file for read
                        fq_file_read = fq_file_df.loc[fq_file_df['read_type'] == rt,:]
                        fq_file_id = fq_file_read.copy()

                        fq_file_name_old = fq_file_id.pop('name').iloc[0]
                        phred_values = fq_file_id.pop('qc_phred').iloc[0]
                        
                        fq_file_id.pop('id')
                        fq_file_id.pop('read_type')
                        fq_file_id.pop('dataset')
                        fq_file_id.pop('num_files')
                        fq_file_id.pop('pipeline_version')
                        fq_file_id.pop('bucket')
                        fq_file_id.pop('key')
                        
                        fq_file_id.index = ['FASTQ Stats']
                        
                        fq_file_id['created'] = fq_file_id['created'].dt.strftime('%Y-%m-%d %H:%M')
                        fq_file_id['qc_phred_mean'] = fq_file_id['qc_phred_mean'].round(2)
                        
                        fq_file_id.columns = [
                            'Created',
                            'QC Passed',
                            'Upload Path',
                            'Read Length',
                            'Num Reads',
                            'Mean Phred Score',
                            'Size (MB)',
                            'MD5 Checksum',
                        ]
                                        
                        fq_file_names[ix] = st_yled.text_input("FASTQ File",
                                                                value=fq_file_name_old,
                                                                key=f'fq_name_{ix}',
                                                                width = 300,
                                                                border_style='none',
                                                                border_width='0px',
                                                                )
                        
                        st.write(fq_file_id.T)
                
                with col2:
                    
                    with st.container(border=True, height=460):
                        
                        st.subheader('Per Base Phred Score')
                        
                        st.write('')
                        st.write('')
                        
                        #  Reformart Phred Values only if string
                        if isinstance(phred_values, str):
                            phred_values = json.loads(phred_values.replace("'", "\""))
                        
                        phred_base_pos = [i for i in range(1, len(phred_values)+1)]
                        phres_val = [phred_values[str(k-1)] for k in phred_base_pos]
                        
                        phred_df = pd.DataFrame({'Base Position' : phred_base_pos, 'Phred Score' : phres_val})
                        
                        st.line_chart(phred_df, x='Base Position', y='Phred Score')

                # Define updated fastq files
                fq_file_read =  fq_file_read.iloc[0]
                fq_file_read['name'] = fq_file_names[ix]
                fq_file_read['qc_phred'] = phred_values
                read_fq_map[rt] = fq_file_read
                
        # region Check In Button  
        with st.container(horizontal=True, horizontal_alignment='right'):

            if st.button('Cancel'):
                reset_selected_project_names()
                st.rerun()

            if st.button('Confirm', type ='primary'):

                checkin_complete = False
                
                # Input is disabled when checking in to existing dataset
                if not disable_input:

                    # Remove na values from metadata key column
                    metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
                    # Replace all None values with empty string
                    metadata_df = metadata_df.fillna('')
                        
                    keys = metadata_df['key'].tolist()
                    keys = [k.lower() for k in keys]
                    values = metadata_df['value'].tolist()
                    metadata = {k:v for k,v in zip(keys,metadata_df['value'])}

                    # Validate uploaded files
                    file_names = [file.name for file in uploaded_files]
                    file_bytes = [file.getvalue() for file in uploaded_files]
                    
                    # Prep project ids
                    project_ids = projects_owner_group.loc[
                        projects_owner_group['name'].isin(project_names_select),'id'].tolist()
                    

                    # Check if dataset name is no yet used and adreres to naming conventions
                    # 1) First check for dataset name
                    if display_name == '':
                        st.session_state['error_cache'] = "Please enter a Dataset Name."
                    elif display_name.lower() in reference_fq_dataset_names:
                        st.session_state['error_cache'] = "Dataset name already exists in Group. Please choose another name."
                    elif not extensions.validate_charset(display_name):
                        st.session_state['error_cache'] = 'Dataset Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.'
                    else:
                        # 2) Second check for fq file names
                        for v in read_fq_map.values():
                            if not extensions.validate_charset(v['name']):
                                st.session_state['error_cache'] = 'FASTQ Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.'
                                break
                            if v['name'] == '':
                                st.session_state['error_cache'] = "Please enter a FASTQ File Name"
                                break
                        else:
                            # 3) Third check for metadata
                            for k, v in zip(keys, values):
                                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                                    st.session_state['error_cache'] = f'Key {k}: Only [0-9][a-z][.-_] allowed. no whitespaces..'
                                    break
                                if k in uiconfig.METADATA_RESERVED_KEYS:
                                    st.session_state['error_cache'] = f'Metadata key {k}: Reserved keyword, please choose another key'
                                    break
                            # 4) Execute Upload
                            else:
                                dataset_qc_passed = True
                                
                                # Update FqFiles
                                for v in read_fq_map.values():
                                    
                                    if not v['qc_passed']:
                                        dataset_qc_passed = False
                                    
                                    datamanager.checkin_fq_file_staging(
                                        st.session_state["jwt_auth_header"],
                                        v['id'],
                                        v['name'],
                                        v['bucket'],
                                        v['key'],
                                        v['upload_path'],
                                        v['qc_passed'],
                                        v['read_type'],
                                        v['read_length'],
                                        v['num_reads'],
                                        v['qc_phred_mean'],
                                        v['qc_phred'],
                                        v['size_mb'],
                                        v['md5_checksum'],
                                        v['pipeline_version']
                                    )
                                
                                # Create FqDataset
                                
                                # Define Read PKs
                                fq_file_r1 = None
                                fq_file_r2 = None
                                fq_file_i1 = None
                                fq_file_i2 = None
                                
                                if 'R1' in read_fq_map:
                                    fq_file_r1 = read_fq_map['R1']['id']
                                if 'R2' in read_fq_map:
                                    fq_file_r2 = read_fq_map['R2']['id']
                                if 'I1' in read_fq_map:
                                    fq_file_i1 = read_fq_map['I1']['id']
                                if 'I2' in read_fq_map:
                                    fq_file_i2 = read_fq_map['I2']['id']
                                
                                if fq_file_r1 and fq_file_r2:
                                    paired_end = True
                                else:
                                    paired_end = False
                                if fq_file_i1 or fq_file_i2:
                                    index_read = True
                                else:
                                    index_read = False
                                                                                
                                fq_pk = datamanager.create_fq_dataset(
                                    st.session_state["jwt_auth_header"],
                                    name = display_name,
                                    description = description,
                                    qc_passed=dataset_qc_passed,
                                    index_read=index_read,
                                    fq_file_r1=fq_file_r1,
                                    fq_file_r2=fq_file_r2,
                                    fq_file_i1=fq_file_i1,
                                    fq_file_i2=fq_file_i2,
                                    paired_end=paired_end,
                                    project=project_ids,
                                    metadata=metadata
                                )
                                
                                # Upload Attachments
                                for file_name, file_byte in zip(file_names, file_bytes):
                                    datamanager.create_fq_attachment(file_name,
                                                                        file_byte,
                                                                        fq_pk)
                                
                                checkin_complete = True
                    
                else:
                    
                    fq_dataset_id = fq_datasets_empty.loc[fq_datasets_empty['name'] == display_name,
                                                          'id'].iloc[0]
                    
                    fq_dataset_select = datamanager.get_fq_dataset_detail(
                        st.session_state["jwt_auth_header"],
                        fq_dataset_id
                    )
                    
                    # Validate FQ files
                    
                    for v in read_fq_map.values():
                        if not extensions.validate_charset(v['name']):
                            st.session_state['error_cache'] = 'FASTQ Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.'
                            break
                        if v['name'] == '':
                            st.session_state['error_cache'] = "Please enter a FASTQ File Name"
                            break
                    else:
                        dataset_qc_passed = True
                                
                        # Update FqFiles
                        for v in read_fq_map.values():
                            
                            if not v['qc_passed']:
                                dataset_qc_passed = False
                            
                            datamanager.checkin_fq_file_staging(
                                st.session_state["jwt_auth_header"],
                                v['id'],
                                v['name'],
                                v['bucket'],
                                v['key'],
                                v['upload_path'],
                                v['qc_passed'],
                                v['read_type'],
                                v['read_length'],
                                v['num_reads'],
                                v['qc_phred_mean'],
                                v['qc_phred'],
                                v['size_mb'],
                                v['md5_checksum'],
                                v['pipeline_version']
                            )
                        
                        # Create FqDataset
                        
                        # Define Read PKs
                        fq_file_r1 = None
                        fq_file_r2 = None
                        fq_file_i1 = None
                        fq_file_i2 = None
                        
                        if 'R1' in read_fq_map:
                            fq_file_r1 = int(read_fq_map['R1']['id'])
                        if 'R2' in read_fq_map:
                            fq_file_r2 = int(read_fq_map['R2']['id'])
                        if 'I1' in read_fq_map:
                            fq_file_i1 = int(read_fq_map['I1']['id'])
                        if 'I2' in read_fq_map:
                            fq_file_i2 = int(read_fq_map['I2']['id'])
                        
                        if fq_file_r1 and fq_file_r2:
                            paired_end = True
                        else:
                            paired_end = False
                        if fq_file_i1 or fq_file_i2:
                            index_read = True
                        else:
                            index_read = False
                        
                        fq_dataset_select.paired_end = paired_end
                        fq_dataset_select.index_read = index_read
                        fq_dataset_select.fq_file_r1 = fq_file_r1
                        fq_dataset_select.fq_file_r2 = fq_file_r2
                        fq_dataset_select.fq_file_i1 = fq_file_i1
                        fq_dataset_select.fq_file_i2 = fq_file_i2
                        fq_dataset_select.valid_to = None
                        fq_dataset_select.valid_from = None
                        fq_dataset_select.created = None
                        fq_dataset_select.updated = None
                        
                        fq_dataset_select.qc_passed = dataset_qc_passed
                        
                        endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
                        extensions.model_to_put_request(
                            endpoint = endpoint,
                            pk = int(fq_dataset_id),
                            base_model=fq_dataset_select,
                            headers=st.session_state['jwt_auth_header']
                        )
                        
                        checkin_complete = True
                    
                if checkin_complete:
                    del st.session_state['fq_data_staging']
                    del st.session_state['staging_dataset_preexist']
                    del st.session_state['staging_dataset_name']
                    del st.session_state['dataset_name_active']
                    st.cache_data.clear()
                    st.rerun()
            
        if st.session_state['error_cache'] is not None:
            st.error(st.session_state['error_cache'])
            st.session_state['error_cache'] = None
        
# region Batch Check In
@st.dialog('Check In All Datasets', width='small', on_dismiss='rerun')
def bulk_checkin_df(fq_files_staging_df: pd.DataFrame,
                    projects_owner_group: pd.DataFrame,
                    fq_datasets_empty: pd.DataFrame,
                    reference_fq_dataset_names: pd.Series):
    
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()

    empty_dataset_names = fq_datasets_empty['name'].str.lower()
    empty_dataset_names = empty_dataset_names.tolist()
    
    # Group by datasets and check in each dataset if fastq files are valid
    fq_files_staging_df = fq_files_staging_df.copy()
    
    # What is exact format here?
    fq_files_staging_datasets = fq_files_staging_df.groupby('dataset')

    total_input_datasets = len(fq_files_staging_datasets)
    valid_datasets = {}
    
    validation_warnings = {
        'na_in_read_types': [],
        'duplicated_read_types': [],
        'dataset_exists': [],
        'empty_dataset_name': [],
        'invalid_dataset_chars': [],
        'invalid_fq_file_name': [],
        'empty_fq_file_name': []
    }
    
    for dataset, fq_files in fq_files_staging_datasets:
        
        read_types = fq_files['read_type'].unique()
        read_types = sorted(read_types)
        
        # Check if NA is in read types
        if 'NA' in read_types:
            validation_warnings['na_in_read_types'].append(dataset)
            continue # consider warning
        
        # Check if read types are unique
        elif fq_files['read_type'].duplicated().any():
            validation_warnings['duplicated_read_types'].append(dataset)
            continue
        
        # Check if dataset name is no yet used and adreres to naming conventions
        elif dataset.lower() in reference_fq_dataset_names:
            
            # Check if dataset is empty
            if not dataset.lower() in empty_dataset_names:                       
                validation_warnings['dataset_exists'].append(dataset)
                continue
        
        # Empty dataset name
        elif dataset == '':
            validation_warnings['empty_dataset_name'].append(dataset)
            continue
        
        # Check if characters in dataset are valid
        elif not extensions.validate_charset(dataset):
            validation_warnings['invalid_dataset_chars'].append(dataset)
            continue
        
        # Check if fq file names are valid
        elif not all([extensions.validate_charset(fq) for fq in fq_files['name']]):
            validation_warnings['invalid_fq_file_name'].append(dataset)
            continue
        
        elif not all([fq != '' for fq in fq_files['name']]):
            validation_warnings['empty_fq_file_name'].append(dataset)
            continue
        
        # All aall quality criteria succeeded, then add to valid datasets
        valid_datasets[dataset] = fq_files
    
    num_valid_datasets = len(valid_datasets)
    valid_dataset_names_df = pd.DataFrame({'name' : list(valid_datasets.keys())})
    
    if num_valid_datasets > 0:

        disable_check_in = False

        project_names_select = st.multiselect("Attach all Datasets to one or more Projects (optional)",
            sorted(projects_owner_group['name'].unique()),
            help = 'Select Project(s) to attach Datasets to after Check In',
            placeholder='',
            width = 400)

        st.space(8)

        valid_dataset_df = pd.DataFrame({
            'dataset_name' : sorted(list(valid_datasets.keys())),
            'check_in' : [True] * len(valid_datasets)
        })

        valid_dataset_df = st.data_editor(
            valid_dataset_df,
            column_config = {
                "dataset_name" : st.column_config.TextColumn('Dataset', disabled = True, width='medium'),
                "check_in": st.column_config.CheckboxColumn('Check In', help='Select to Check In Dataset', width=100)
            },
            hide_index=True,
            width='content'
        )

        num_selected = valid_dataset_df['check_in'].sum()
        st_yled.markdown(f"{num_selected} of {num_valid_datasets} Datasets selected for Check In", font_size=12, color='#808495')

        if num_selected == 0:
            disable_check_in = True

        st.space(8)

        # Overview of valid datasets

        # if 'available_staging' not in st.session_state:
        #     st.session_state['available_staging'] = valid_dataset_names_df
        #     #st.session_state['available_staging_input'] = fq_datasets_avail['id'].tolist()
            
        # if 'selected_staging' not in st.session_state:
        #     st.session_state['selected_staging'] = pd.DataFrame(columns=['name'])
        #     #st.session_state['selected_staging_input'] = pd.DataFrame(columns=['name'])

        # @st.fragment
        # def update_select_form_fq_datasets():               
            
        #     col1, col2, col3 = st.columns([5.5,1,5.5])
            
        #     # First col to select available datasets
        #     with col1:
                
        #         with st.container(border = True):
                    
        #             st.write('Available Datasets')
                                
        #             datasets_available = st.session_state['available_staging']
                    
        #             search_value_fq_ds = st.text_input("Search Datasets",
        #                             help = 'Search in available Datasets',
        #                             placeholder='Search Available Datasets',
        #                             key = 'update_search_fq_datasets_staging',
        #                             label_visibility = 'collapsed')
                                    
        #             fq_datasets_show = datasets_available.loc[
        #                 datasets_available['name'].str.contains(search_value_fq_ds, case=False) 
        #             ]
                    
        #             fq_avail_df = st.dataframe(fq_datasets_show,
        #                                         use_container_width=True,
        #                                         hide_index = True,
        #                                         column_config = {
        #                                             'name' : st.column_config.Column('Name'),
        #                                         },
        #                                         key='update_datasets_df_staging',
        #                                         on_select = 'rerun',
        #                                         selection_mode='multi-row')

        #     # Column with selected datasets
        #     with col3:
        #         with st.container(border = True):              
                    
        #             st.write('Selected Datasets')
                    
        #             datasets_selected = st.session_state['selected_staging']
                    
        #             search_value_fq_ds_select = st.text_input("Search Datasets",
        #                                                     help = 'Search in Selected Datasets',
        #                                                     placeholder='Search Selected Datasets',
        #                                                     key = 'update_search_attached_fq_datasets_staging',
        #                                                     label_visibility = 'collapsed')
                                    
        #             fq_datasets_select_show = datasets_selected.loc[
        #                     datasets_selected['name'].str.contains(search_value_fq_ds_select, case=False) 
        #                 ]
                    
        #             fq_select_df = st.dataframe(fq_datasets_select_show,
        #                                         use_container_width=True,
        #                                         hide_index = True,
        #                                         column_config = {
        #                                             'name' : st.column_config.TextColumn('Name'),
        #                                         },
        #                                         key='update_datasets_select_df_staging',
        #                                         on_select = 'rerun',
        #                                         selection_mode='multi-row')

        #         with col2:
                    
        #             # CONTINUE HERE
                    
        #             # Spacer Container
        #             st.container(height = 100, border = False)
        #             st.button(':material/arrow_forward:', use_container_width=True, type='primary', on_click=add_selected_datasets, args = (fq_datasets_show, fq_avail_df.selection['rows']))
        #             st.button(':material/arrow_back:', use_container_width=True, type='primary', on_click=remove_selected_datasets, args = (fq_datasets_select_show, fq_select_df.selection['rows']))
            

        # update_select_form_fq_datasets()

    else:
        st_yled.info('''
:material/notifications: No valid Datasets to Check In.

Check warnings for invalid FASTQ files or Dataset names.
''',
                            border_width="2.0px",
                            border_color="#808495",
                            border_style="solid",
                            background_color="#f0f2f6",
                            color="#808495",
                            width=440)

        disable_check_in = True
        st.space(8)
    

    # region Check In Button  
    with st.container(horizontal=True, horizontal_alignment='right'):

        if st.button('Cancel'):
            st.rerun()

        if st.button('Confirm', key='confirm_bulk_checkin', type = 'primary', disabled=disable_check_in):
            
            selected_datasets = valid_dataset_df.loc[valid_dataset_df['check_in'],'dataset_name'].tolist()
                            
            # Prep project ids
            project_ids = projects_owner_group.loc[
                projects_owner_group['name'].isin(project_names_select),'id'].tolist()
            
            # Get metadata keys for selected projects returns list of dicts
            project_dataset_metadata_keys = projects_owner_group.loc[
                projects_owner_group['name'].isin(project_names_select),'dataset_metadata_keys'].tolist()
            
            project_dataset_metadata_keys = [list(m.keys()) for m in project_dataset_metadata_keys]
            project_dataset_metadata_keys = itertools.chain.from_iterable(project_dataset_metadata_keys)
                            
            dataset_metadata = {k:'' for k in project_dataset_metadata_keys}
            
            with st.spinner('Checking In Datasets'):
                
                for dataset_name in selected_datasets:
                    dataset_df = valid_datasets[dataset_name]
                    dataset_qc_passed = True
                    
                    fq_file_r1 = None
                    fq_file_r2 = None
                    fq_file_i1 = None
                    fq_file_i2 = None
                    
                    # Loop over fq files and check in
                    for ix, fq_file in dataset_df.iterrows():
                        
                        if fq_file['read_type'] == 'R1':
                            fq_file_r1 = fq_file['id']
                        elif fq_file['read_type'] == 'R2':
                            fq_file_r2 = fq_file['id']
                        elif fq_file['read_type'] == 'I1':
                            fq_file_i1 = fq_file['id']
                        elif fq_file['read_type'] == 'I2':
                            fq_file_i2 = fq_file['id']
                        
                        if not fq_file['qc_passed']:
                            dataset_qc_passed = False
                        
                        if isinstance(fq_file['qc_phred'], str):
                            fq_file['qc_phred'] = json.loads(fq_file['qc_phred'].replace("'", "\""))                        
                    
                        # Check in Fq Files
                        datamanager.checkin_fq_file_staging(
                            st.session_state["jwt_auth_header"],
                            fq_file['id'],
                            fq_file['name'],
                            fq_file['bucket'],
                            fq_file['key'],
                            fq_file['upload_path'],
                            fq_file['qc_passed'],
                            fq_file['read_type'],
                            fq_file['read_length'],
                            fq_file['num_reads'],
                            fq_file['qc_phred_mean'],
                            fq_file['qc_phred'],
                            fq_file['size_mb'],
                            fq_file['md5_checksum'],
                            fq_file['pipeline_version']
                        )
                    
                    if fq_file_r1 and fq_file_r2:
                        paired_end = True
                    else:
                        paired_end = False
                    if fq_file_i1 or fq_file_i2:
                        index_read = True
                    else:
                        index_read = False
                                            
                    # Check if dataset name is in existing group
                    if dataset_name in empty_dataset_names:
                        
                        fq_dataset_id = fq_datasets_empty.loc[
                            fq_datasets_empty['name'] == dataset_name,'id'
                        ].values[0]
                
                        fq_dataset = datamanager.get_fq_dataset_detail(
                            st.session_state["jwt_auth_header"],
                            fq_dataset_id=fq_dataset_id
                        )
                        
                        fq_dataset.qc_passed = dataset_qc_passed
                        fq_dataset.fq_file_r1 = fq_file_r1
                        fq_dataset.fq_file_r2 = fq_file_r2
                        fq_dataset.fq_file_i1 = fq_file_i1
                        fq_dataset.fq_file_i2 = fq_file_i2
                        fq_dataset.paired_end = paired_end
                        fq_dataset.index_read = index_read
                        fq_dataset.valid_to = None
                        fq_dataset.valid_from = None
                        fq_dataset.created = None
                        fq_dataset.updated = None
                        
                        fq_dataset.qc_passed = dataset_qc_passed
                    
                        endpoint = uiconfig.ENDPOINT_CONFIG['fq_dataset']
                        extensions.model_to_put_request(
                            endpoint = endpoint,
                            pk = int(fq_dataset_id),
                            base_model=fq_dataset,
                            headers=st.session_state['jwt_auth_header']
                        )
                        
                    else:
                        # Create FqDataset
                        fq_pk = datamanager.create_fq_dataset(
                            st.session_state["jwt_auth_header"],
                            name = dataset_name,
                            description = '',
                            qc_passed=dataset_qc_passed,
                            index_read=index_read,
                            fq_file_r1=fq_file_r1,
                            fq_file_r2=fq_file_r2,
                            fq_file_i1=fq_file_i1,
                            fq_file_i2=fq_file_i2,
                            paired_end=paired_end,
                            project=project_ids,
                            metadata=dataset_metadata
                        )
            
            del st.session_state['fq_data_staging']
            # del st.session_state['available_staging']
            # del st.session_state['selected_staging']
            st.cache_data.clear()
            st.rerun()

    # Display Warnings
    for warning_type, datasets in validation_warnings.items():
        if len(datasets) > 0:
            st.warning(f"Datasets Excluded - ({warning_type.replace('_', ' ').title()}): {', '.join(datasets)}")

    
def delete_fastq_files(fq_file_ids: List[int]):
    for fq_file_id in fq_file_ids:
        datamanager.delete_fq_file(fq_file_id)
    
    del st.session_state['fq_data_staging']
    st.cache_data.clear()
    st.rerun()  


@st.dialog('Remove All Staged FASTQ Files', width='small', on_dismiss='rerun')
def bulk_delete_fq_files(fq_file_ids: List[int]):
    num_files = len(fq_file_ids)
    
    st.warning(f'Confirm deletion of {num_files} staged files from ReadStore Database.')

    st_yled.markdown("NOTE: This will **NOT** delete the original files from disk",
                        font_weight=500,
                        font_size=12,
                        color='#808495',
                        key='remove-fq-note')
    
    st.write("")
    st.write("")

    with st.container(horizontal=True, gap='small', horizontal_alignment='right'):

        if st.button('Cancel', key='cancel_delete'):
            st.rerun()

        if st.button('Confirm', key='confirm_delete', type='primary'):
            delete_fastq_files(fq_file_ids)


@st.dialog("Remove FASTQ File", width='small', on_dismiss='rerun')
def delete_single_fastq_file(fq_file_ids: List[int]):
    
    st.warning("Remove non-staged FASTQs from ReadStore Database?")
    st_yled.markdown("NOTE: This will **NOT** delete the original files from disk",
                        font_weight=500,
                        font_size=12,
                        color='#808495',
                        key='remove-fq-note')

    st.write("")
    st.write("")

    with st.container(horizontal=True, gap='small', horizontal_alignment='right'):

        if st.button('Cancel', key=f"delete_cancel"):
            st.rerun()

        if st.button('Confirm', key=f"delete_ok", type='primary'):
            delete_fastq_files(fq_file_ids)


#region Import FASTQ from file

@st.dialog('Import FASTQ from File', width='medium', on_dismiss='rerun')
def import_from_file():

    disable_confirm = True

    with st.container(key='import-fastq-main'):

        # Import Instructions
        with st_yled.container(key='import-instructions', gap='xsmall'):
            st_yled.markdown('Imported FASTQ files from a filled Excel or .csv template', font_size=12, color='#808495')
            st_yled.markdown('Download template below. [How to fill a Template file?](https://www.google.de)', font_size=12, color='#808495')

        # Upload File
        upload_template = st.file_uploader("**Upload template for FASTQ import**",
                                            help = "Upload a template file to import FASTQ files.",
                                            type = ['.csv', '.xlsx'],
                                            accept_multiple_files = False)
            
        if upload_template:
            if upload_template.name.endswith('.csv'):
                try:
                    upload_template = pd.read_csv(upload_template, header=0)
                except pd.errors.EmptyDataError:
                    st.error('No data found in template .csv file')

            elif upload_template.name.endswith('.xlsx'):
                try:
                    upload_template = pd.read_excel(upload_template, header=0)
                except pd.errors.EmptyDataError:
                    st.error('No data found in template .excel file')
            else:
                st.error('Please upload a valid CSV or Excel file.')
            
            # Get number of fq files in queue
            num_queue_jobs = datamanager.get_fq_queue_jobs(st.session_state["jwt_auth_header"])
            max_jobs_queue = uiconfig.BACKEND_MAX_QUEUE_SIZE
            max_allowed_jobs = max_jobs_queue - num_queue_jobs

            # Strip leading and trailing spaces from column entries
            upload_template = upload_template.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            # Validate uploaded template
            if not upload_template.shape[1] == 3:
                st.session_state['error_cache'] = 'Invalid number of columns in template file. Please use Dataset, ReadType, FilePath'
            
            # Check if any rows present
            elif upload_template.shape[0] == 0:
                st.session_state['error_cache'] = 'No FASTQ files found in template file'
            
            # Check max allowed jobs in queue
            elif upload_template.shape[0] > max_allowed_jobs:
                st.session_state['error_cache'] = f'Not enough space in jobs queue. Maximum allowed files for upload: {max_jobs_queue}'
                st.session_state['error_cache'] += f'Currently running jobs: {num_queue_jobs}'
                    
            # Check column names
            elif not all(upload_template.columns == ['Dataset', 'ReadType', 'FilePath']):
                st.session_state['error_cache'] = 'Invalid column names in template file. Please use Dataset, ReadType, FilePath'
            # Check valid read types
            elif not upload_template['ReadType'].isin(['R1', 'R2', 'I1', 'I2']).all():
                st.session_state['error_cache'] = 'Invalid ReadType in template file. Please use only R1, R2, I1, I2'
            else:
                # Validate FASTQ File Names
                for fq_name in upload_template['Dataset']:
                    
                    if (fq_name == '') or (pd.isna(fq_name)):
                        st.session_state['error_cache'] = 'Empty FASTQ name found'
                        break
                    elif not extensions.validate_charset(fq_name):
                        st.session_state['error_cache'] = f'**{fq_name}**: Error in FASTQ name found. Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces'
                        break
                    
                    # Check if corresponding upload path exists
                    upload_path = upload_template.loc[upload_template['Dataset'] == fq_name, 'FilePath'].iloc[0]
                    if not (os.path.exists(upload_path) and os.access(upload_path, os.R_OK)):
                        st.session_state['error_cache'] = f'**{fq_name}**: Upload Path not found or not accessible'
                        break
                    
                else:
                    # If all checks passed, show preview of uploaded template
                    with st.container():
                        #st.write('**FASTQ Files to Import**')
                        disable_confirm = False

                        st.dataframe(upload_template,
                                    width='stretch',
                                    hide_index=True,
                                    column_config = {
                                        'Dataset' : st.column_config.TextColumn('Dataset', help="Name of dataset created for FASTQ files"),
                                        'ReadType' : st.column_config.SelectboxColumn('Read Type', help="Read or Index Type (R1, R2, I1, I2)", options = ['R1', 'R2', 'I1', 'I2']),
                                        'FilePath' : st.column_config.TextColumn('File Path', help="Original path of the uploaded FASTQ file")
                                    })

        bnt_group = st.container(horizontal=True, horizontal_alignment ='distribute')

        with bnt_group:

            with st.popover('Download Templates', width='content'):
                
                excel_template_path = os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/readstore_upload_template.xlsx")
                csv_template_path = os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/readstore_upload_template.csv")
                
                excel_template = open(excel_template_path, 'rb').read()
                csv_template = open(csv_template_path, 'rb').read()

                st.download_button('Download Excel Template',
                                excel_template,
                                'readstore_template.xlsx',
                                width='stretch')
                st.download_button('Download .csv Template',
                                csv_template,
                                'readstore_template.csv',
                                width='stretch')
                
        conf_cancel = bnt_group.container(horizontal=True, horizontal_alignment ='right', width="content")

        with conf_cancel:

            if st.button('Cancel', key='cancel_update_project'):
                st.rerun()

            if st.button('Confirm', key='confirm_import_fastq', type='primary', width='stretch', disabled=disable_confirm):
                
                if not upload_template is None:
                    for ix, row in upload_template.iterrows():
                        res = datamanager.submit_fq_queue_job(
                                st.session_state["jwt_auth_header"],
                                row['Dataset'],
                                row['FilePath'],
                                row['ReadType']
                        )
                        
                        if res.status_code != 200:
                            st.session_state['error_cache'] = f"Error with file **{row['Dataset']}** \n {res.json()['detail']} \n Quit Import"
                            break
                    else:        
                        st.cache_data.clear()
                        st.rerun()

    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None

@st.dialog('Help')
def staging_help():
    
    st.markdown("ReadStore groups **Dataset**s based on the filename of each **FASTQ** file.\n")
    st.markdown("The **Read** type is also infered. [Read1/R1, Read2/R2, Index1/I1, Index2/I2]\n")
                
    st.markdown("Click *Check In* to validate and register the **Dataset**s \n")
    
    st.markdown("If the infered **Datasets** are not correct, you can change the name in the Dataset columns below.\n")
    st.markdown("Also the **Read** type can be changed by clicking the column blow.\n")
    
    st.link_button('Manual in ReadStore Blog', 'https://evo-byte.com/readstore-tutorial-uploading-staging-fastq-files/')


#region UI
@st.fragment
def uimain(fq_files_staging: pd.DataFrame,
           projects_owner_group: pd.DataFrame,
           fq_dataset_empty: pd.DataFrame,
           fq_dataset_names_owner_group: pd.Series):

    # Show Toast Cache
    if st.session_state['toast_cache']:
        st.toast(st.session_state['toast_cache'])
        st.session_state['toast_cache'] = None

    # Define Main Container
    with st_yled.container(key='work-ui'):

        st.space(8)

        col_config = {
                'id' : None,
                'dataset' : st.column_config.TextColumn('Dataset', width="medium", help="Each Dataset Combines Read Files for Sample"),
                'name' : None,
                'read_type' : st.column_config.SelectboxColumn('Read', width ="small", options = ['R1', 'R2', 'I1', 'I2'], help = "Read or Index Type (R1, R2, I1, I2)", required =True),
                'created' : None,
                'qc_passed' : st.column_config.CheckboxColumn('QC Passed', width ='small', help = "FASTQ 0uality Control Passed", disabled = True),
                'upload_path' : st.column_config.TextColumn('Upload Path', help = "Original path of the uploaded file", disabled = True),
                'bucket' : None,
                'key' : None,
                'read_length' : None,
                'num_reads' : None,
                'qc_phred_mean' : None,
                'qc_phred' : None,
                'size_mb' : None,
                'md5_checksum' : None,
                'pipeline_version' : None,
                'num_files' : None
            }

        fq_files_staging_update = []
        do_rerun = False

        # Header Line with Status on Uploaded Files
        with st.container(horizontal=True, width='content', vertical_alignment='center'):

            # Differ between case where FQ files are ready for staging
            if fq_files_staging.shape[0] > 0:
                st_yled.info(f"{len(fq_files_staging)} FASTQ files waiting for Check In", key='staging-info-fq', width=256)
            else:
                st_yled.success("No FASTQ Files to Check In.", icon=":material/check:", key='staging-success-no-fq', width=240)
            
            if num_jobs > 0:
                st_yled.warning(str(num_jobs) + ' Jobs in QC Queue, available soon. Click :material/refresh: Refresh to update')
            else:
                st_yled.markdown('0 Jobs in QC Queue', key='staging-jobs-queue', font_size=14, color='#808495')

        st.space(8)

        # Button Header Line with Status on Uploaded Files
        with st.container(horizontal=True):
            
            with st.container(horizontal_alignment='left', 
                              vertical_alignment='center',
                              horizontal=True,
                                gap='small',
                                width=144):
                
                # Create hash for button key
                if not 'staging_split_but_hash' in st.session_state:
                    st.session_state['staging_split_but_hash'] = str(uuid.uuid4())
                

                with st.container(key='upload-header-split-button-container'):

                    split_but = split_button(label='Import',
                                            options=['Check In All', 'Remove All'],
                                            icon=':material/upload:',
                                            key=f'staging_split_button-{st.session_state['staging_split_but_hash']}')

                    if split_but == 'Import':

                        st.session_state['staging_split_but_hash'] = str(uuid.uuid4())
                        import_from_file()

                    elif split_but == 'Check In All':
                        
                        st.session_state['staging_split_but_hash'] = str(uuid.uuid4())

                        if fq_files_staging.shape[0] > 0:
                            bulk_checkin_df(fq_files_staging,
                                            projects_owner_group,
                                            fq_dataset_empty,
                                            fq_dataset_names_owner_group)
                        else:
                            st.session_state['toast_cache'] = 'No FASTQ files to Check In'
                            st.rerun()

                    elif split_but == 'Remove All':
                        
                        st.session_state['staging_split_but_hash'] = str(uuid.uuid4())

                        if fq_files_staging.shape[0] > 0:
                            bulk_delete_fq_files(fq_files_staging['id'].tolist())
                        else:
                            st.session_state['toast_cache'] = 'No FASTQ files to Remove'
                            st.rerun()


                
            search_value_fastq = st_yled.text_input("Search FASTQ",
                                help = 'Search FASTQ Files and Datasets',
                                placeholder='Search FASTQ',
                                key = 'search_fastq',
                                label_visibility = 'collapsed',
                                border_width=2,
                                width = 256)


            with st.container(horizontal_alignment='right', horizontal=True, vertical_alignment='center'):
                
                
                st_yled.markdown("Upload explained", width=104, color='#808495', font_size='12px', key='staging-upload-explained')

                upload_explained_link_cont = st.container(key='staging-upload-explained-link-container',
                                                        width='content')
                
                upload_explained_link_cont.page_link('app_pages/getting_started.py',
                                                     label=":material/help_outline:",
                                                     query_params={'page':'file-upload'},)

                # st_yled.button(':material/help_outline:',
                #                     help='Upload Help',
                #                     key='staging-help',
                #                     type='tertiary',
                #                     font_weight='500',
                #                     font_size='16px',
                #                     width='content')

                if st_yled.button(':material/refresh:',
                                    help='Refresh Upload Status',
                                    key='staging-refresh',
                                    type='tertiary',
                                    font_weight='500',
                                    font_size='16px',
                                    width='content'):
                    
                    if 'fq_data_staging' in st.session_state:
                        del st.session_state['fq_data_staging']
                    extensions.refresh_page()

        st.space(8)

        # Show columns if there are fq files in staging
        if fq_files_staging.shape[0] > 0:

            dataset_check = fq_files_staging['dataset'].str.contains(search_value_fastq, case=False, na=False) 
            fastq_check = fq_files_staging['name'].str.contains(search_value_fastq, case=False, na=False)
            
            fq_staging_filter_pos = fq_files_staging.loc[dataset_check | fastq_check,:]
            fq_staging_filter_neg = fq_files_staging.loc[~(dataset_check | fastq_check),:]
            
            # Add number of dataset grouped fastq files to df
            # Sort datasets by number of files for each dataset (usually 1-2)
            dataset_counts = fq_staging_filter_pos.groupby('dataset').size().reset_index(name='num_files')
            if 'num_files' in fq_staging_filter_pos.columns:
                fq_staging_filter_pos = fq_staging_filter_pos.drop(columns=['num_files'])
            # Sort all datasets in filter by number of files and dataset name
            fq_staging_filter_pos = fq_staging_filter_pos.merge(dataset_counts, on='dataset')
            fq_staging_filter_pos = fq_staging_filter_pos.sort_values(by=['num_files', 'dataset'])

            fq_files_staging_split = [v for k, v in fq_staging_filter_pos.groupby(['num_files','dataset'])]

            fq_files_staging_split_show = fq_files_staging_split[:num_fq_data_staging_staging]
            fq_files_staging_split_left = fq_files_staging_split[num_fq_data_staging_staging:]
            
            # Loop over selection of FASTQ files to show
            for ix, fq_file_df in enumerate(fq_files_staging_split_show):
                
                with st_yled.container(key=f'staging-fq-dataset-container-{ix}',
                                        width=720,
                                        background_color='#F0F2F680'):

                # col1, col2 = st.columns([1.5, 10.5], vertical_alignment='center')
                
                # with col1:
                #     if st.button("Check In", key=f"checkin_{ix}", type = 'primary', help='Validate and Register Dataset'):
                        
                #         if 'preexist_dataset_name' in st.session_state:
                #             del st.session_state['preexist_dataset_name']
                        
                #         checkin_df(fq_file_df,
                #                 projects_owner_group,
                #                 fq_dataset_empty,
                #                 fq_dataset_names_owner_group)
                    
                #     with st.popover(':material/delete_forever:', help="Delete FASTQ Files"):
                #             if st.button('Confirm Delete', key=f"delete_ok_{ix}", use_container_width=True):
                                
                #                 fq_file_ids = fq_file_df['id'].tolist()
                #                 delete_fastq_files(fq_file_ids)
                    
                    if 'update_field_state' in st.session_state:
                        field_ix, edited = st.session_state['update_field_state']
                        if field_ix == ix:
                            df_ix = list(edited.keys())[0]
                            col = list(edited[df_ix].keys())[0]
                            val = edited[df_ix][col]
                            
                            fq_file_df[col].iloc[df_ix] = val
                            do_rerun = True
                                
                            del st.session_state['update_field_state']
                    
                    editor_height = (fq_file_df.shape[0]+1) * 32 + 5

                    df_set = st.data_editor(fq_file_df,
                                    hide_index=True,
                                    key=f"fq_sd_{ix}",
                                    column_config=col_config,
                                    on_change=show_updated,
                                    height=editor_height,   
                                    args=(ix,))
                    

                    with st.container(horizontal=True, horizontal_alignment='right', gap='small'):
                        

                        if st.button("Remove",
                                    icon=':material/delete_forever:',
                                    key=f"remove_{ix}"):
                            
                            delete_single_fastq_file(fq_file_df['id'].tolist())

                        # with st.popover("Remove",icon=':material/delete_forever:'):
                            
                        #     st.markdown("Remove FASTQs from ReadStore Database?")
                        #     st_yled.markdown("NOTE: This will **NOT** delete the original files from disk",
                        #                      font_weight=500,
                        #                      font_size=12,
                        #                      color='#808495',
                        #                      key=f'remove-fq-note-{ix}')
                            
                        #     with st.container(horizontal=True, gap='small', horizontal_alignment='right'):
                                
                        #         # if not 'staging_cancel_remove_bnt_hash' in st.session_state:
                        #         #     print("Creating staging_cancel_remove_bnt_hash")
                        #         #     st.session_state['staging_cancel_remove_bnt_hash'] = str(uuid.uuid4())

                        #         # btn_key = f"delete_cancel_{ix}_{st.session_state['staging_cancel_remove_bnt_hash']}"
                        #         # print(f"btn_key: {btn_key}")

                        #         if st.button('Cancel', key=f"delete_cancel_{ix}"):
                        #             st.session_state['staging_cancel_remove_bnt_hash'] = str(uuid.uuid4())

                        #             st.rerun()

                        #         if st.button('Confirm', key=f"delete_ok_{ix}", type='primary'):
                        #             fq_file_ids = fq_file_df['id'].tolist()
                        #             delete_fastq_files(fq_file_ids)

                        if st.button("Check In", icon=':material/check_box:', key=f"checkin_{ix}", type = 'primary'):
                        
                            if 'preexist_dataset_name' in st.session_state:
                                del st.session_state['preexist_dataset_name']
                            
                            checkin_df(fq_file_df,
                                    projects_owner_group,
                                    fq_dataset_empty,
                                    fq_dataset_names_owner_group)

                    # List of (displayed) datasets
                    fq_files_staging_update.append(df_set)

                st.space(8)

            else:
                # Combine all updated fastq files
                if len(fq_files_staging_update) > 0:
                    fq_files_staging_update = pd.concat(fq_files_staging_update)
                else:
                    fq_files_staging_update = pd.DataFrame()
                # Add in the remaining fastq files
                fq_files_staging_update = pd.concat([fq_files_staging_update, fq_staging_filter_neg] + fq_files_staging_split_left)
                
                st.session_state['fq_data_staging'] = fq_files_staging_update

                if do_rerun:
                    st.rerun()
                
                # If there are more fastq files to show, display a button to show more
                if len(fq_files_staging_split_left) > 0:
                    
                    _, col_more, _ = st.columns([5, 2, 5])
                    with col_more:    
                        if st.button('More', key='more_fq_data_staging', help='Show More FASTQ Files', width='stretch', type='primary'):
                            st.session_state['num_fq_data_staging_staging'] = num_fq_data_staging_staging + 10                    
                            st.rerun()

        else:
            
            with st_yled.container(
                gap='small',
                width='content',
                key='staging-no-fq-container',
                background_color = '#F0F2F6'
            ):
                st_yled.markdown("Start by uploading your NGS FASTQ files", font_size=14, key='staging-no-fq-cont-info')
                st_yled.markdown("Click **Import** to upload from a template file,", font_size=14, key='staging-no-fq-cont-info1')
                st_yled.markdown("or use the ReadStore **Command Line Interface**", font_size=14, key='staging-no-fq-cont-info2')
                
                st_yled.code("readstore upload dataset_1_R1.fastq dataset_1_R2.fastq", language="bash", key='staging-no-fq-cont-cli-code')

                st_yled.markdown("More information here", font_size=12, font_weight="medium", color="#808495", key='staging-no-fq-cont-more-info')
                



#region DATA

# Define the number of fastq files to display to avoid long loading times
if 'num_fq_data_staging_staging' in st.session_state:
    num_fq_data_staging_staging = st.session_state['num_fq_data_staging_staging']
else:
    num_fq_data_staging_staging = 10

if 'fq_data_staging' in st.session_state:
    fq_files_staging = st.session_state['fq_data_staging']
else:
    fq_files_staging = datamanager.get_fq_file_staging_overview(st.session_state["jwt_auth_header"])
    st.session_state['fq_data_staging'] = fq_files_staging

# Get fqdataset names for owner group
fq_dataset_names_owner_group = datamanager.get_fq_dataset_owner_group(st.session_state["jwt_auth_header"])['name']

# Get empty fqdatasets for owner group
fq_dataset_empty = datamanager.get_fq_dataset_empty(st.session_state["jwt_auth_header"])

projects_owner_group = datamanager.get_project_owner_group(st.session_state["jwt_auth_header"])[['id', 'name', 'dataset_metadata_keys']]

# Get number of running jobs in QC queue
num_jobs = datamanager.get_fq_queue_jobs(st.session_state["jwt_auth_header"])


uimain(fq_files_staging,
        projects_owner_group,
        fq_dataset_empty,
        fq_dataset_names_owner_group)