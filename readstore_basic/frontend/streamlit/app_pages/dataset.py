# readstore-basic/frontend/streamlit/app_pages/dataset.py

from typing import List
import time
import uuid
import string
import json
import copy
import webbrowser
import itertools
import os

import streamlit as st
import pandas as pd
import numpy as np

import extensions
import datamanager
import exceptions
import styles

from uidataclasses import OwnerGroup
from uidataclasses import Project

import uiconfig

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

colh1, colh2 = st.columns([11,1], vertical_alignment='top')

with colh1:
    st.markdown(
        """
        <div style="text-align: right;">
            <b>Username</b> {username}
        </div>
        """.format(username=st.session_state['username']),
        unsafe_allow_html=True
    )
with colh2:
    st.page_link('app_pages/settings.py', label='', icon=':material/settings:')

# Change top margin of app
st.markdown(
    """
    <style>
        .stAppViewBlockContainer {
            margin-top: 0px;
            padding-top: 80px;
        }
    </style>
    """,
    unsafe_allow_html=True)

# Change Button Height
styles.adjust_button_height(25)

# Set sesstion state for downloaing attachments

# Session state for selecting datasets to attach
if not 'dataset_select_id' in st.session_state:
    st.session_state['dataset_select_id'] = None

# Session state for showing archived processed data
if not 'pro_data_show_archived_versions' in st.session_state:
    st.session_state['pro_data_show_archived_versions'] = False

# Session state to hold new ProData during Dataset Creation
if not 'pro_data_new' in st.session_state:
    st.session_state['pro_data_new'] = None

if not 'fq_metadata_select' in st.session_state:
    st.session_state['fq_metadata_select'] = pd.DataFrame()

def update_attachment_select():
    if st.session_state['dataset_select_id']:
        dataset_id = st.session_state['dataset_select_id']
        st.session_state[f'download_fq_attachments_select_{dataset_id}'] = st.session_state['fq_attachment_details_df']

def update_pro_data_select():
    if st.session_state['dataset_select_id']:
        dataset_id = st.session_state['dataset_select_id']
        st.session_state[f'download_pro_data_select_{dataset_id}'] = st.session_state['fq_prodata_details_df']

def update_pro_data_show_archived():
    new_state = st.session_state['checkbox_pro_data_include_archive']
    st.session_state['pro_data_show_archived_versions'] = new_state
    
    # Reset selection to avoid problems with old selection
    if detail_fq_pro_data_key_name in st.session_state:
        del st.session_state[detail_fq_pro_data_key_name]

def filter_df_by_metadata_filter(df: pd.DataFrame, filter_session_prefix = 'fq_dataset_meta_filter_'):
    
    for k in st.session_state:
        if k.startswith(filter_session_prefix):
            meta_key = k.replace(filter_session_prefix, '')
            values = st.session_state[k]
            
            # Add this if to check in case that project_show was updated
            if meta_key in df:            
                if values != []:
                    df = df.loc[df[meta_key].isin(values),:]

    return df


#region Create Dataset
@st.dialog('Create Dataset', width='large')
def create_dataset(reference_fq_dataset_names: pd.Series,
                    reference_project_names_df: pd.DataFrame):

    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()

    # Get reference dataset names
    # Get reference project names
    name = st.text_input("Dataset Name",
                        key='dataset_name',
                        help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')

    tab1, tab2, tab3, tab4 = st.tabs([":blue-background[**Projects**]",
                                    ":blue-background[**Features**]",
                                    ":blue-background[**Attachments**]",
                                    ":blue-background[**ProData**]"])

    # TAB: Features: Project
    with tab1:

        with st.container(height=460, border=False):
                    
            project_options = sorted(reference_project_names_df['name'])
            st.write('Attach the Dataset to one or more Projects')
            
            project_names_select = st.multiselect("Select Projects",
                    project_options,
                    help = 'Attach the dataset to project(s).')

    # TAB: Features: Description and Metadata
    with tab2:

        description = st.text_area("Enter Dataset Description",
                                    help = 'Description of the FASTQ Dataset.')
        
        with st.container(border=True, height=315):
            
            col1c, col2c = st.columns([11,1], vertical_alignment='top')
                
            with col1c:
                
                tab1c = st.tabs([":blue-background[**Metadata**]"])[0]
                
                with tab1c:
                    
                    # Get metadata keys for selected projects
                    metadata_keys = reference_project_names_df.loc[
                            reference_project_names_df['name'].isin(project_names_select),'dataset_metadata_keys'].to_list()
                    metadata_keys = [list(m.keys()) for m in metadata_keys]
                    metadata_keys = itertools.chain.from_iterable(metadata_keys)
                    metadata_keys = sorted(list(set(metadata_keys)))
                                
                    fq_metadata = pd.DataFrame({
                        'key' : metadata_keys,
                        'value' : [''] * len(metadata_keys)
                    })
                    
                    fq_metadata = fq_metadata.astype(str)
                    metadata_df = st.data_editor(
                        fq_metadata,
                        use_container_width=True,
                        hide_index=True,
                        column_config = {
                            'key' : st.column_config.TextColumn('Key'),
                            'value' : st.column_config.TextColumn('Value')
                        },
                        num_rows ='dynamic',
                        key = 'create_metadata_df'
                    )
            
            with col2c:
                with st.popover(':material/help:'):
                    st.write("Key-value pairs to store and group dataset metadata. For example 'species' : 'human'")

    with tab3:
    
        st.write('Attach files to the Dataset.')
        
        uploaded_files = st.file_uploader(
            "Choose Files to Upload",
            help = "Upload attachments for the Dataset. Attachments can be any file type.",
            accept_multiple_files=True
        )
        
        st.write(' ')
    
    with tab4:
                        
        st.write('Attach **Pro**cessed Data.')

        pro_data_name = st.text_input("Enter Name",
                                        max_chars=150,
                                        help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
                                        label_visibility = "collapsed",
                                        placeholder = "Enter Name",
                                        key = 'pro_data_name')
        
        pro_data_type = st.text_input("Enter Data Type",
                                        max_chars=150,
                                        help = 'Data Type, e.g. gene_count. \nName must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
                                        label_visibility = "collapsed",
                                        placeholder = "Enter Data Type",
                                        key = 'pro_data_type')
        
        pro_upload_path = st.text_input("Enter Upload Path",
                                        max_chars=1000,
                                        help = 'Path to File to Upload',
                                        label_visibility = "collapsed",
                                        placeholder = "Path to ProData File",
                                        key = 'pro_upload_path')
        
        pro_description = st.text_area("Enter Description",
                                        help = 'Description of the FASTQ Dataset.',
                                        height = 68,
                                        label_visibility = "collapsed",
                                        placeholder = "Enter Description",
                                        key = 'pro_description')
        
        with st.container(border=True):
            
            col1p, col2p = st.columns([11,1], vertical_alignment='top')
                    
            with col1p:
                
                tab1p = st.tabs([":blue-background[**Metadata**]"])[0]
                
                with tab1p:
                    
                    selected_fq_metadata = pd.DataFrame({
                        'key' : [],
                        'value' : []
                    })
                
                    selected_fq_metadata = selected_fq_metadata.astype(str)
                    pro_metadata_df = st.data_editor(
                        selected_fq_metadata,
                        use_container_width=True,
                        hide_index=True,
                        column_config = {
                            'key' : st.column_config.TextColumn('Key'),
                            'value' : st.column_config.TextColumn('Value')
                        },
                        num_rows ='dynamic',
                        key = 'create_pro_data_metadata_df'
                    )
            
            with col2p:
                with st.popover(':material/help:'):
                    st.write("Key-value pairs to store and group dataset metadata.")
        
        col3, col4 = st.columns([3, 9])
        
        # Need a session state to store ProData which should be added
        
        with col3:
            if st.button('Add ProData'):
                
                # Validate ProData
                if pro_data_name == '':
                    st.error("Please enter a ProData Name.")
                elif not extensions.validate_charset(pro_data_name):
                    st.error('ProData Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                elif pro_data_type == '':
                    st.error("Please enter a ProData Data Type.")
                elif not extensions.validate_charset(pro_data_type):
                    st.error('ProData Data Type: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                elif pro_upload_path == '':
                    st.error("Enter an upload path")
                elif not os.path.isfile(pro_upload_path):
                    st.error("Upload path for ProData File not found")
                else:
                    
                    # Remove na values from metadata key column
                    pro_metadata_df = pro_metadata_df.loc[~pro_metadata_df['key'].isna(),:]
                    # Replace all None values with empty string
                    pro_metadata_df = pro_metadata_df.fillna('')
                  
                    # Validate ProData Metadata
                    pro_metadata_keys = pro_metadata_df['key'].tolist()
                    pro_metadata_values = pro_metadata_df['value'].tolist()
                    pro_metadata_keys = [k.lower() for k in pro_metadata_keys]                  
                    
                    for k, v in zip(pro_metadata_keys, pro_metadata_values):                        
                        if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                            st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                            break
                        if k in uiconfig.METADATA_RESERVED_KEYS:
                            st.error(f'Metadata Key **{k}**: Reserved keyword, please choose another key')
                            break
                    else:
                        
                        pro_data_entry = {
                            'name' : pro_data_name,
                            'data_type' : pro_data_type,
                            'upload_path' : pro_upload_path,
                            'description' : pro_description,
                            'metadata' : {k:v for k,v in zip(pro_metadata_keys, pro_metadata_values)}
                        }
                        
                        
                        # Add validation logic 

                        if not st.session_state['pro_data_new'] is None:
                            # Returns a list of dicts
                            pro_data_new = st.session_state['pro_data_new']
                            pro_data_new_names = [e['name'] for e in pro_data_new]  
                            
                            if pro_data_name in pro_data_new_names:
                                st.error("ProData Name already exists.")
                            else:
                                pro_data_new.append(pro_data_entry)
                                st.session_state['pro_data_new'] = pro_data_new
                        else:
                            # Initialize ProData as list of dicts
                            st.session_state['pro_data_new'] = [pro_data_entry]
                                                    
        with col4:
            if not st.session_state['pro_data_new'] is None:
                names = [e['name'] for e in st.session_state['pro_data_new']]
                
                st.write('ProData added: ' + ', '.join(names))
        
    _ , col_conf = st.columns([9,3])

    #Import processed data

    with col_conf:
        if st.button('Confirm', type ='primary', key='ok_create_dataset', use_container_width=True):
            
            # Get project_ids for selected project names
            project_ids = reference_project_names_df.loc[
                reference_project_names_df['name'].isin(project_names_select),'id'].tolist()
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Replace all None values with empty string
            metadata_df = metadata_df.fillna('')
                        
            keys = metadata_df['key'].tolist()
            keys = [k.lower() for k in keys]
            values = metadata_df['value'].tolist()
            
            # Validate uploaded files
            file_names = [file.name for file in uploaded_files]
            file_bytes = [file.getvalue() for file in uploaded_files]
                        
            # Validate metadata key formats
            # Check if metadata keys are in reserved keywords
            for k, v in zip(keys, values):
                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                    st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                    break
                if k in uiconfig.METADATA_RESERVED_KEYS:
                    st.error(f'Metadata Key **{k}**: Reserved keyword, please choose another key')
                    break
            else:            
                # Validate username / Better use case
                if name == '':
                    st.error('Dataset Name is empty')
                elif not extensions.validate_charset(name):
                    st.error('Dataset Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces')
                elif name.lower() in reference_fq_dataset_names:
                    st.error('Dataset Name already exists in Group')
                else:
                    metadata = {k:v for k,v in zip(keys, metadata_df['value'])}

                    dataset_id = datamanager.create_fq_dataset(st.session_state["jwt_auth_header"],
                                                                name,
                                                                description,
                                                                qc_passed = False,
                                                                index_read = False,
                                                                fq_file_r1 = None,
                                                                fq_file_r2 = None,
                                                                fq_file_i1 = None,
                                                                fq_file_i2 = None,
                                                                paired_end = False,
                                                                project = project_ids,
                                                                metadata = metadata)

                    for file_name, file_byte in zip(file_names, file_bytes):
                        datamanager.create_fq_attachment(file_name,
                                                        file_byte,
                                                        dataset_id)

                    if not st.session_state['pro_data_new'] is None:
                    
                        for pro_data_entry in st.session_state['pro_data_new']:
                            
                            datamanager.create_pro_data(st.session_state["jwt_auth_header"],
                                                        name = pro_data_entry['name'],
                                                        data_type = pro_data_entry['data_type'],
                                                        description = pro_data_entry['description'],
                                                        upload_path = pro_data_entry['upload_path'],
                                                        metadata = pro_data_entry['metadata'],
                                                        fq_dataset = dataset_id)

                    st.cache_data.clear()
                    st.rerun()


#region Update Dataset
@st.dialog('Update Dataset', width='large')
def update_dataset(selected_fq_dataset: pd.DataFrame,
                   selected_fq_metadata: pd.DataFrame,
                   selected_fq_attachments: pd.DataFrame,
                   selected_fq_pro_data: pd.DataFrame,
                    reference_fq_dataset_names: pd.Series,
                    reference_project_names_df: pd.DataFrame):
    
    fq_dataset_input = selected_fq_dataset.copy()
        
    read_long_map = {
        'R1' : 'Read 1',
        'R2' : 'Read 2',
        'I1' : 'Index 1',
        'I2' : 'Index 2',
    }
    
    read_file_file_map = {}
    
    fq_dataset_id = fq_dataset_input['id']
    fq_dataset_name_old = fq_dataset_input['name']
    fq_dataset_description_old = fq_dataset_input['description']
    fq_dataset_project_names = fq_dataset_input['project_names']

    # Map fq file ids to read types
    if extensions.df_not_empty(fq_dataset_input['fq_file_r1']):
        read_file_file_map['R1'] = fq_dataset_input['fq_file_r1']
    if extensions.df_not_empty(fq_dataset_input['fq_file_r2']):
        read_file_file_map['R2'] = fq_dataset_input['fq_file_r2']
    if extensions.df_not_empty(fq_dataset_input['fq_file_i1']):        
        read_file_file_map['I1'] = fq_dataset_input['fq_file_i1']
    if extensions.df_not_empty(fq_dataset_input['fq_file_i2']):
        read_file_file_map['I2'] = fq_dataset_input['fq_file_i2']

    # Remove current name from reference names
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names[
        reference_fq_dataset_names != fq_dataset_name_old.lower()]
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()
    
    # Get fq for all read types
    for k, v in read_file_file_map.items():
        read_file_file_map[k] = datamanager.get_fq_file_detail(st.session_state["jwt_auth_header"], v)
    
    name = st.text_input("Dataset Name",
                         value=fq_dataset_name_old,
                         key='dataset_name',
                         help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')

    tab_names = [read_long_map[rt] for rt in read_file_file_map.keys()]
    tab_names_format = [":blue-background[**Projects**]",
                        ":blue-background[**Features**]",
                        ":blue-background[**Attachments**]",
                        ":blue-background[**ProData**]"]
    tab_names_format.extend([f":blue-background[**{tn}**]" for tn in tab_names])
    fq_file_names = [None] * len(read_file_file_map)
    
    # Add Metadata and Attachments Tabs
    tabs = st.tabs(tab_names_format)
        
    # region Projects Tab
    with tabs[0]:
        
        with st.container(height=495, border=False):
            
            project_options = sorted(reference_project_names_df['name'])
            st.write('Attach the Dataset to one or more Projects')
            
            projects_default = fq_dataset_project_names
            
            project_names_select = st.multiselect("Select Projects",
                    project_options,
                    projects_default,
                    help = 'Attach the dataset to project(s).')

        coldel, _ = st.columns([4,8])
        
        with coldel:
            with st.expander('Delete Dataset', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_fq_dataset'):
                    
                    datamanager.delete_fq_dataset(fq_dataset_id)
                    
                    
                    st.cache_data.clear()
                    st.rerun()
            
    # region Metadata Tab        
    with tabs[1]:
        
        with st.container(border=False, height=560):
            
            description = st.text_area("Enter Dataset Description",
                                        help = 'Description of the FASTQ Dataset.',
                                        value = fq_dataset_description_old)
            
            with st.container(border=True, height=400):
            
                col1c, col2c = st.columns([11,1], vertical_alignment='top')
                
                with col1c:
                
                    tab1c = st.tabs([":blue-background[**Metadata**]"])[0]

                    with tab1c:
                    
                        # Get metadata keys for selected projects
                        metadata_keys = reference_project_names_df.loc[
                                reference_project_names_df['name'].isin(project_names_select),'dataset_metadata_keys'].to_list()
                        metadata_keys = [list(m.keys()) for m in metadata_keys]
                        metadata_keys = itertools.chain.from_iterable(metadata_keys)
                        metadata_keys = sorted(list(set(metadata_keys)))
                
                        # Expand selected_fq_metadata df with metadata keys if not present
                        selected_fq_metadata_keys = selected_fq_metadata['key'].tolist()
                        selected_fq_metadata_values = selected_fq_metadata['value'].tolist()
                        
                        for k in metadata_keys:
                            if not k in selected_fq_metadata_keys:
                                selected_fq_metadata_keys.append(k)
                                selected_fq_metadata_values.append('')
                        
                        selected_fq_metadata = pd.DataFrame({
                            'key' : selected_fq_metadata_keys,
                            'value' : selected_fq_metadata_values
                        })
                        
                        selected_fq_metadata = selected_fq_metadata.astype(str)
                        metadata_df = st.data_editor(
                            selected_fq_metadata,
                            use_container_width=True,
                            hide_index=True,
                            column_config = {
                                'key' : st.column_config.TextColumn('Key'),
                                'value' : st.column_config.TextColumn('Value')
                            },
                            num_rows ='dynamic',
                            key = 'update_metadata_df'
                        )
                
                with col2c:
                    with st.popover(':material/help:'):
                        st.write("Key-value pairs to store and group dataset metadata. For example 'species' : 'human'")

    
    # region Attachment Tab
    with tabs[2]:
        
        with st.container(border=True, height=375):
            
            # Define Max Heigth of attachment select
            # Limit Max Height of Dataframe
            if selected_fq_attachments.shape[0] > 7:
                max_df_height = 290
            else:
                max_df_height = None
            
            attach_select = st.dataframe(selected_fq_attachments,
                                    hide_index = True,
                                    use_container_width = True,
                                    column_config = {
                                        'id' : None,
                                        'name' : st.column_config.TextColumn('Name'),
                                        'description' : None,
                                        'fq_dataset_id' : None},
                                    key='update_attachment_df',
                                    selection_mode='multi-row',
                                    on_select = 'rerun',
                                    height = max_df_height)
                        
        uploaded_files = st.file_uploader("**Upload attachments for the dataset**",
            help = "Upload attachments for the dataset. Attachments can be any file type.",
            accept_multiple_files = True)

        col, _ = st.columns([4,8])
        
        with col:
            with st.expander('Delete Attachment(s)', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_attachments'):
                    
                    attach_ixes = attach_select.selection['rows']
                    attach_ids = selected_fq_attachments.loc[attach_ixes,'id'].tolist()
                    
                    for attach_id in attach_ids:
                        datamanager.delete_fq_attachment(attach_id)
                    else:
                        st.cache_data.clear()
                        # Reset attachment select for project id
                        st.session_state[f'download_fq_attachments_select_{fq_dataset_id}'] = None
                        st.rerun()
    
    # region ProData
    
    with tabs[3]:
        
        with st.container(border=True, height=495):
            
            # List all attachments            
            update_include_archived = st.checkbox('Include archived',
                                                key='pro_data_show_archived_versions_update',
                                                value = False)
            
            if not update_include_archived:
                selected_fq_pro_data = selected_fq_pro_data.loc[
                        selected_fq_pro_data['valid_to'].isna(),:]

            # Define Max Heigth of attachment select
            # Limit Max Height of Dataframe
            if selected_fq_pro_data.shape[0] > 7:
                max_df_height = 350
            else:
                max_df_height = None
            
            pro_data_select = st.dataframe(selected_fq_pro_data,
                                        hide_index = True,
                                        use_container_width = True,
                                        column_config = {
                                            'id' : st.column_config.TextColumn('ID'),
                                            'name' : st.column_config.TextColumn('Name'),
                                            'data_type' : st.column_config.TextColumn('Type'),
                                            'description' : None,
                                            'version' : st.column_config.TextColumn('Version'),
                                            'owner_username' : st.column_config.TextColumn('Creator'),
                                            'valid_to' : None
                                        },
                                        key='update_pro_data_df',
                                        selection_mode='multi-row',
                                        on_select = 'rerun',
                                        height = max_df_height)

        col, _ = st.columns([4,8])

        with col:
            with st.expander('Delete ProData', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_pro_data'):
                    
                    pro_data_ixes = pro_data_select.selection['rows']
                    pro_data_ids = selected_fq_pro_data.loc[pro_data_ixes,'id'].tolist()
                    
                    for pro_data_id in pro_data_ids:
                        datamanager.delete_pro_data(pro_data_id)
                    else:
                        st.cache_data.clear()
                        # Reset selection config for pro data
                        st.session_state[f'download_pro_data_select_{fq_dataset_id}'] = None
                        st.rerun()


    for ix, rt in enumerate(read_file_file_map.keys()):
        
        # region Read Tab
        with tabs[4+ix]:
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                
                with st.container(border=True, height=460):
                    
                    st.subheader('FASTQ Stats')
                    
                    # Get id of the fq file for read
                    fq_file_read = read_file_file_map[rt]
                    
                    fq_file_id = fq_file_read.id
                    fq_file_name_old = fq_file_read.name
                    phred_values = fq_file_read.qc_phred
                    qc_phred_mean = round(fq_file_read.qc_phred_mean,2)
                                        
                    fq_file_created = fq_file_read.created.strftime('%Y-%m-%d %H:%M')
                    
                    fq_file_df = pd.DataFrame({
                        'Created' : [fq_file_created],
                        'QC Passed' : [fq_file_read.qc_passed],
                        'Upload Path' : [fq_file_read.upload_path],
#                        'Bucket' : [fq_file_read.bucket],
#                        'Key' : [fq_file_read.key],
                        'Read Length' : [fq_file_read.read_length],
                        'Num Reads' : [fq_file_read.num_reads],
                        'Mean Phred Score' : [qc_phred_mean],
                        'Size (MB)' : [fq_file_read.size_mb],
                        'MD5 Checksum' : [fq_file_read.md5_checksum],
                    })
                                        
                    fq_file_df = fq_file_df.T
                    fq_file_df.index.name = 'FASTQ File'
                    fq_file_df.columns = [fq_file_id]
                    
                    fq_file_names[ix] = st.text_input("FASTQ File Name", value=fq_file_name_old, key=f'fq_name_{ix}')
                    
                    st.write(fq_file_df)
            
            with col2:
                
                with st.container(border=True, height=460):
                    
                    st.subheader('Per Base Phred Score')
                    
                    st.write('')
                    st.write('')
                    st.write('')
                    
                    phred_base_pos = [i for i in range(1, len(phred_values)+1)]
                    phres_val = [phred_values[str(k-1)] for k in phred_base_pos]
                    phred_df = pd.DataFrame({'Base Position' : phred_base_pos, 'Phred Score' : phres_val})
                    
                    st.line_chart(phred_df, x='Base Position', y='Phred Score')

            # # Define updated fastq files
            fq_file_read.name = fq_file_names[ix]
            read_file_file_map[rt] = fq_file_read


    _, col1d = st.columns([9,3])
    
    with col1d:
        
        # region Confirm Button     
        if st.button('Confirm', key='confirm_ds_update', type = 'primary', use_container_width=True):
            
            # Prep Metadata
            
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
            
            # Get project ids for selected project names
            project_ids = reference_project_names_df.loc[
                reference_project_names_df['name'].isin(project_names_select),'id'].tolist()
                                                    
            # Check if dataset name is no yet used and adreres to naming conventions
            # 1) First check for dataset name
            if name == '':
                st.error("Please enter a Dataset Name.")
            elif name.lower() in reference_fq_dataset_names:
                st.error("Dataset Name already exists in Group. Please choose another name.")
            elif not extensions.validate_charset(name):
                st.error('Dataset Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
            else:
                # Loop over fastq file Pydantic Models
                # There is not constraint on the fastq file name, can be duplicated
                for fq_file in read_file_file_map.values():
                    fq_file_name = fq_file.name
                    if not extensions.validate_charset(fq_file_name):
                        st.error('Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                        break
                    if fq_file_name == '':
                        st.error("Please enter a name for FASTQ file")
                        break
                # If names of all fastq files are valid, continue metadata check
                else:              
                    # 3) Third check for metadata
                    for k, v in zip(keys, values):
                        if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                            st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces.')
                            break
                        if k in uiconfig.METADATA_RESERVED_KEYS:
                            st.error(f'Metadata key **{k}**: Reserved keyword, please choose another key')
                            break
                            
                        # Check if attachment names are valid
                        #selected_fq_attachments
                    else: 
                        # Update FqFiles
                        for v in read_file_file_map.values():
                            datamanager.update_fq_file(v)
                        else:
                            datamanager.update_fq_dataset(fq_dataset_id,
                                                            name,
                                                            description,
                                                            metadata,
                                                            project_ids)
                            
                            # Upload Attachments
                            for file_name, file_byte in zip(file_names, file_bytes):
                                if file_name in selected_fq_attachments['name'].tolist():
                                    st.warning(f'Attachment {file_name} already exists. Skip.')
                                else:
                                    datamanager.create_fq_attachment(file_name,
                                                                        file_byte,
                                                                        fq_dataset_id)
                                
                        st.cache_data.clear()
                        st.rerun()

# region Update Many Datasets
@st.dialog('Update Datasets', width='large')
def update_many_datasets(selected_fq_dataset: pd.DataFrame,
                         selected_fq_metadata: pd.DataFrame,
                        reference_project_names_df: pd.DataFrame):
        
    # Add Metadata and Attachments Tabs
    tabs = st.tabs([":blue-background[**Projects**]"])
    
    with tabs[0]:
        
        with st.container(border=True):
            
            st.subheader('Projects')

            project_options = sorted(reference_project_names_df['name'])
            st.write('Attach the selected Datasets to one or more Projects')
                        
            project_names_select = st.multiselect("Select Projects",
                    project_options,
                    help = 'Attach the dataset to project(s).')
        
        coldel, _ = st.columns([4,8])
        
        with coldel:
            with st.expander('Delete all Datasets', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_fq_dataset_many'):
                
                    # Dataset will automatically be deleted through cascade
                    with st.spinner('Deleting Datasets...'):
                        
                        _ = [datamanager.delete_fq_dataset(fq_id) for fq_id in selected_fq_dataset['id']]
                    
                    st.cache_data.clear()
                    st.rerun()

    _, col1d = st.columns([9,3])
    
    with col1d:
        
        # region Confirm Button     
        if st.button('Confirm', key='confirm_ds_update_many', type = 'primary', use_container_width=True):
            
            # Get project ids for selected project names
            project_ids = reference_project_names_df.loc[
                reference_project_names_df['name'].isin(project_names_select),'id'].tolist()
            
            # Get metadata keys for selected projects returns list of dicts
            project_dataset_metadata_keys = reference_project_names_df.loc[
                reference_project_names_df['name'].isin(project_names_select),'dataset_metadata_keys'].tolist()
            
            project_dataset_metadata_keys = [list(m.keys()) for m in project_dataset_metadata_keys]
            project_dataset_metadata_keys = itertools.chain.from_iterable(project_dataset_metadata_keys)

            # Update selected FqDatasets with new project ids
            for ix, (_, fq_dataset) in enumerate(selected_fq_dataset.iterrows()):
                
                metadata = selected_fq_metadata.iloc[ix,:]
                metadata = metadata.dropna().reset_index()
                metadata.columns = ['key', 'value']
                metadata_dict = {k:v for k,v in zip(metadata['key'],metadata['value'])}

                # Update with new metadata keys
                for k in project_dataset_metadata_keys:
                    if not k in metadata_dict.keys():
                        metadata_dict[k] = ''
                
                # Attach new project metadata keys to metadata
                fq_dataset_id = fq_dataset['id']                
                name = fq_dataset['name']
                description = fq_dataset['description']
                project_ids_old = fq_dataset['project']
                project_ids_update = list(set(project_ids + project_ids_old))
                
                datamanager.update_fq_dataset(fq_dataset_id,
                                              name,
                                              description,
                                              metadata_dict,
                                              project_ids_update)
            
            st.cache_data.clear()
            st.rerun()
            

    
#region Detail Fastq File
def start_fq_file_download(fq_file_id:int):
    
    url = datamanager.get_fq_file_download_url(st.session_state["jwt_auth_header"], fq_file_id)    
    webbrowser.open_new_tab(url)
    
               
@st.dialog('FASTQ Stats', width='large')
def detail_fq_file(fq_file_id: int):
    
    fq_file_read = datamanager.get_fq_file_detail(st.session_state["jwt_auth_header"], fq_file_id)
        
    col1, col2 = st.columns([1, 1])
            
    with col1:
        
        with st.container(border=True, height=400):
            
            # Get id of the fq file for read            
            fq_file_id = fq_file_read.id
            phred_values = fq_file_read.qc_phred
            qc_phred_mean = round(fq_file_read.qc_phred_mean,2)
            
            fq_file_created = fq_file_read.created.strftime('%Y-%m-%d %H:%M')
            
            fq_file_df = pd.DataFrame({
                'Name' : [fq_file_read.name],
                'Created' : [fq_file_created],
                'QC Passed' : [fq_file_read.qc_passed],
                'Upload Path' : [fq_file_read.upload_path],
#                'Bucket' : [fq_file_read.bucket],
#                'Key' : [fq_file_read.key],
                'Read Length' : [fq_file_read.read_length],
                'Num Reads' : [fq_file_read.num_reads],
                'Mean Phred Score' : [qc_phred_mean],
                'Size (MB)' : [fq_file_read.size_mb],
                'MD5 Checksum' : [fq_file_read.md5_checksum],
            })
            fq_file_df = fq_file_df.T
            fq_file_df.index.name = 'FASTQ File'
            fq_file_df.columns = [fq_file_id]
            
            st.write(fq_file_df)
    
    with col2:
        
        with st.container(border=True, height=400):
            
            st.subheader('Per Base Phred Score')
            
            # st.write('')
            # st.write('')
            # st.write(' ')
            
            phred_base_pos = [i for i in range(1, len(phred_values)+1)]
            phres_val = [phred_values[str(k-1)] for k in phred_base_pos]
            
            phred_df = pd.DataFrame({'Base Position' : phred_base_pos, 'Phred Score' : phres_val})
            
            st.line_chart(phred_df, x='Base Position', y='Phred Score')
    
    with st.popover('FASTQ File Path'):
        st.text_input('FASTQ File Path', value=fq_file_read.upload_path)

# region Detail ProData
@st.dialog('Processed Data', width='large')
def detail_pro_data(pro_data_id: int):
    
    pro_data = datamanager.get_pro_data_detail(st.session_state["jwt_auth_header"],
                                               pro_data_id)

    name = pro_data.name
    description = pro_data.description
    created = pro_data.created
    creator = pro_data.owner_username
    metadata = pro_data.metadata
    version = pro_data.version
    upload_path = pro_data.upload_path
    valid_to = pro_data.valid_to
    
    created = created.strftime('%Y-%m-%d %H:%M')
    if valid_to:
        valid_to = valid_to.strftime('%Y-%m-%d %H:%M')
    
    detail_df = pd.DataFrame({
        'Name' : [name],
        'Version' : [version],
        'Creator' : [creator],
        'Created' : [created],
        'Valid To' : [valid_to]
    })
    detail_df = detail_df.T.reset_index()
    
    detail_df.columns = ['ProData ID', pro_data_id]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True, height=400):
            st.subheader('Details')
            
            st.dataframe(detail_df,
                        use_container_width=True,
                        hide_index=True)
        
            st.text_input('File Path',
                          value=upload_path)

    with col2:
        with st.container(border=True, height=400):
            st.subheader('Description')
            
            st.text_area('description',
                         value=description,
                         label_visibility = 'collapsed',
                         height=68)
            
            st.subheader('Metadata')
            
            metadata_df = pd.DataFrame(metadata.items(), columns=['Key', 'Value'])
            
            st.dataframe(metadata_df,
                        use_container_width=True,
                        hide_index=True)
            
    
    # col1, col2 = st.columns([1, 1])
            
    # with col1:
        
    #     with st.container(border=True, height=400):



#region Export Project

@st.dialog('Export Datasets')            
def export_datasets(fq_dataset_view: pd.DataFrame):
    
    st.markdown("""Export Selection as .csv file
- Datasets and Metadata
- Dataset FASTQ stats
- Dataset Processed Data
            """)
    
    st.divider()
            
    if fq_dataset_view.empty:
        st.warning('No Datasets selected for export')
    else:
        export_selection = st.segmented_control(
            '**Export Selection**',
            ['Datasets', 'FASTQ Files', 'Processed Data'],
            key='export_selection',
            default='Datasets'
        ) 
        
        if export_selection == 'FASTQ Files':
            
            # Reduce number of required API calls
            with st.spinner('Exporting Datasets...'):
                            
                fq_dataset_file_ids = []
                
                for _, fq in fq_dataset_view.iterrows():
                    
                    fq_id = fq['id']
                    fq_name = fq['name']
                    creator = fq['owner_username']
                    fq_file_r1 = fq['fq_file_r1']
                    fq_file_r2 = fq['fq_file_r2']
                    fq_file_i1 = fq['fq_file_i1']
                    fq_file_i2 = fq['fq_file_i2']
                    
                    dataset_fq_files = []
                    if extensions.df_not_empty(fq_file_r1):
                        dataset_fq_files.append(fq_file_r1)
                    if extensions.df_not_empty(fq_file_r2):
                        dataset_fq_files.append(fq_file_r2)
                    if extensions.df_not_empty(fq_file_i1):
                        dataset_fq_files.append(fq_file_i1)
                    if extensions.df_not_empty(fq_file_i2):
                        dataset_fq_files.append(fq_file_i2)
                    
                    fq_file_ids = pd.DataFrame(dataset_fq_files, columns=['id'])
                    fq_file_ids['dataset_id'] = fq_id
                    fq_file_ids['dataset_name'] = fq_name
                    fq_file_ids['creator'] = creator
                
                    fq_dataset_file_ids.append(fq_file_ids)
                
                fq_dataset_file_ids = pd.concat(fq_dataset_file_ids, axis=0)
                            
                # # Map in fq_files
                fq_files_og = datamanager.get_fq_file_owner_group(st.session_state["jwt_auth_header"])
                
                fq_files = fq_dataset_file_ids.merge(fq_files_og, on='id', how='left')
                
                fq_files = fq_files[['dataset_id',
                                    'dataset_name',
                                    'id',
                                    'name',
                                    'read_type',
                                    'qc_passed',
                                    'read_length',
                                    'num_reads',
                                    'size_mb',
                                    'qc_phred_mean',
                                    'created',
                                    'creator',
                                    'upload_path',
                                    'md5_checksum']]

                fq_files = fq_files.rename(columns={'id' : 'fq_file_id', 'name' : 'fq_file_name'}) 
                fq_files = fq_files.sort_values(by=['dataset_id', 'read_type'], ascending=[True, True])
                
            st.download_button('Download .csv',
                            fq_files.to_csv(index=False).encode("utf-8"),
                            'fastq_files.csv',
                            'text/csv')
            
        elif export_selection == 'Datasets':
            
            # Get fq_attachments
            fq_attachments = datamanager.get_fq_dataset_attachments(st.session_state["jwt_auth_header"])
            fq_attachments_list = fq_attachments.groupby('fq_dataset_id')['name'].apply(list)
            fq_attachments_list = fq_attachments_list.reset_index()
            fq_attachments_list.columns = ['fq_dataset_id', 'attachments']

            fq_dataset_view = fq_dataset_view.merge(fq_attachments_list,
                                                    left_on='id',
                                                    right_on='fq_dataset_id',
                                                    how='left')
            fq_dataset_view['attachments'] = fq_dataset_view['attachments'
                                                             ].apply(lambda x: [] if x is np.nan else x)
            
            # project_names to projects
            fq_dataset_view = fq_dataset_view.drop(columns=['fq_file_r1',
                                                            'fq_file_r2',
                                                            'fq_file_i1',
                                                            'fq_file_i2',
                                                            'id_str',
                                                            'owner_group_name',
                                                            'fq_dataset_id'])
            
            fq_dataset_view = fq_dataset_view.rename(columns={'project' : 'project_ids',
                                                            'project_names' : 'project_names',
                                                            'owner_username' : 'creator'})
                         
            st.download_button('Download .csv',
                            fq_dataset_view.to_csv(index=False).encode("utf-8"),
                            'datasets.csv',
                            'text/csv')

        elif export_selection == 'Processed Data':
            
            export_include_archived = st.checkbox('Include archived',
                                    key='pro_data_show_archived_versions_export',
                                    value = False)

            # Reduce number of required API calls
            with st.spinner('Exporting Datasets...'):
                
                selected_fq_ids = fq_dataset_view['id'].tolist()
                
                fq_datasets, fq_metadata = datamanager.get_fq_dataset_meta_overview(st.session_state["jwt_auth_header"])
                fq_datasets = fq_datasets[['id', 'name']]
                
                # Subset fq_datasets and metadata to selected ids
                fq_datasets_meta = pd.concat([fq_datasets, fq_metadata], axis=1)
                fq_datasets_meta = fq_datasets_meta.loc[fq_datasets_meta['id'].isin(selected_fq_ids),:]
                
                pro_data, pro_metadata = datamanager.get_pro_data_meta_overview(st.session_state["jwt_auth_header"])
                
                pro_data_meta = pd.concat([pro_data, pro_metadata], axis=1)
                
                pro_data_meta_merge = pro_data_meta.merge(fq_datasets_meta,
                                                          left_on='fq_dataset',
                                                        right_on='id',
                                                        suffixes=('', '_fq_dataset'))
                
                dataset_names = pro_data_meta_merge.pop('name_fq_dataset')
                
                pro_data_meta_merge = pro_data_meta_merge.drop(columns=['id_fq_dataset'])
                pro_data_meta_merge = pro_data_meta_merge.rename(columns={'owner_username' : 'creator',
                                                                        'fq_dataset' : 'dataset_id'})
                    
                # Reorder columns to have all metadata at the end
                pro_data_meta_merge.insert(1, 'dataset_name', dataset_names)
                                 
                if not export_include_archived:
                    pro_data_meta_merge = pro_data_meta_merge.loc[
                        pro_data_meta_merge['valid_to'].isna(),:]
                    
            
            pro_data = datamanager.get_pro_data_owner_group(st.session_state["jwt_auth_header"])
            
            st.download_button('Download .csv',
                            pro_data_meta_merge.to_csv(index=False).encode("utf-8"),
                            'processed_data.csv',
                            'text/csv')
        
        else:
            st.error('Invalid Export Selection')
        
        
#region DATA

# Get overfiew of all fastq datasets

# Get all projects where user is in owner_group
project_owner_group = datamanager.get_project_owner_group(st.session_state["jwt_auth_header"])
# Get all projects where user is a collaborator
project_collab = datamanager.get_project_collab(st.session_state["jwt_auth_header"])
my_projects = pd.concat([project_owner_group, project_collab], axis=0)
my_project_names = my_projects['name'] # All Project the User has access to

# Get all fq_datasets that user is collaborator or member of owner group
fq_datasets, fq_metadata = datamanager.get_fq_dataset_meta_overview(st.session_state["jwt_auth_header"])

# Prepare Project Filter
# Subset project names form fq_datasets overview, filter empty projects columns
# Transform to pandas series and filter out all projects that are empty
# Add 'No Project' and construct filter list
fq_dataset_project_set = fq_datasets['project_names'].apply(lambda x: x != [])
fq_dataset_project = fq_datasets.loc[fq_dataset_project_set, 'project_names']
fq_dataset_project = fq_dataset_project.explode().unique()
fq_dataset_project_filter = sorted(fq_dataset_project)
fq_dataset_project_filter = [fq for fq in fq_dataset_project_filter if fq in my_project_names.tolist() ]
fq_dataset_project_filter.insert(0, 'No Project')

# Reference project names 
reference_owner_group_names = sorted(fq_datasets['owner_group_name'].unique())
reference_project_names_df = project_owner_group[['id', 'name', 'dataset_metadata_keys']]
# Subset dataset names those that are in the owner group
reference_dataset_names = fq_datasets.loc[
    fq_datasets['owner_group_name'] == st.session_state['owner_group'],'name'
    ]

# Add id string for search
fq_datasets['id_str'] = fq_datasets['id'].astype(str)

# UI

col1, col2, col3, col4, col5, col6 = st.columns([3,3,1.75,2.5,1 ,0.75], vertical_alignment='center')


with col1:
    
    search_value_fq_datasets = st.text_input("Search Datasets",
                                    help = 'Search for Datasets',
                                    placeholder='Search Datasets',
                                    key = 'search_datasets',
                                    label_visibility = 'collapsed')

with col2:
    
    projects_filter = st.multiselect('Filter Projects',
                                options = fq_dataset_project_filter,
                                help = 'Filter Projects',
                                placeholder = 'Filter Projects',
                                label_visibility = 'collapsed')

with col4:
    
    st.toggle("Metadata",
              key='show_fq_metadata',
              help='Switch to Datasets Metadata View')

# Dynamic list of checkboxes with distinct values
with col5:
    
    metadata_select = st.session_state['fq_metadata_select']
    
    if metadata_select.empty:
        metadata_filter_disabled = True
    else:
        metadata_filter_disabled = False

    with st.popover(':material/filter_alt:',
                    help='Filter Metadata',
                    disabled = metadata_filter_disabled):
        
        st.write('Filter Metadata Columns')
        
        for k in metadata_select.columns:
            
            options = metadata_select[k].dropna().unique().tolist()
            
            st.multiselect(label = k,
                            options = options,
                            label_visibility = 'collapsed',
                            key = f'fq_dataset_meta_filter_{k}',
                            placeholder = f'Filter {k}')

with col6:
    if st.button(':material/refresh:',
                 key='refresh_projects',
                 help='Refresh Page',
                 type='tertiary',
                 use_container_width = True):
        
        on_click = extensions.refresh_page()

col_config_user = {
    'id': st.column_config.NumberColumn('ID'),
    'name' : st.column_config.TextColumn('Name', help='FASTQ Dataset Name'),
    'project' : None,
    'project_names' : st.column_config.ListColumn('Projects', help='Projects the Dataset is associated with'),
    'owner_group_name' : None,
    'qc_passed' : st.column_config.Column('QC Passed', help='Quality Control Passed', width='small'),
    'paired_end' : st.column_config.Column('Paired End', help='Paired End Dataset', width='small'),
    'index_read' : st.column_config.Column('Index Read', help='Index Read Available', width='small'),
    'created' : st.column_config.DateColumn('Created', help='Creation Date'),
    'description' : None,
    'owner_username' : None,
    'fq_file_r1' : None,
    'fq_file_r2' : None,
    'fq_file_i1' : None,
    'fq_file_i2' : None,
    'id_str' : None,
    'fq_dataset_id' : None,
}

col_config_meta = {
    'id': st.column_config.NumberColumn('ID'),
    'name' : st.column_config.TextColumn('Name', help='FASTQ Dataset Name'),
    'project_names' : None,
    'owner_group_name' : None,
    'id_str' : None
}

fq_datasets_show = pd.concat([fq_datasets,fq_metadata], axis=1)

# Search filter
fq_datasets_show = fq_datasets_show[
    (fq_datasets_show['name'].str.contains(search_value_fq_datasets, case=False) | 
     fq_datasets_show['id_str'].str.contains(search_value_fq_datasets, case=False))]

# Project filter
if projects_filter:
    if 'No Project' in projects_filter:
        projects_filter.remove('No Project')
        fq_datasets_show = fq_datasets_show.loc[
            fq_datasets_show['project_names'].apply(lambda x: any([p in x for p in projects_filter]) or len(x) == 0),:
            ]
    else:
        fq_datasets_show = fq_datasets_show.loc[
            fq_datasets_show['project_names'].apply(lambda x: any([p in x for p in projects_filter])),:
            ]

st.session_state['fq_metadata_select'] = fq_datasets_show[fq_metadata.columns]

# Filter out meta columns from selected view which are all None
fq_datasets_show = filter_df_by_metadata_filter(fq_datasets_show)

# Remove those meta cols from projects_show which are all None
fq_meta_cols_all_none = fq_datasets_show.loc[:,fq_metadata.columns].isna().all()
fq_meta_cols_all_none = fq_meta_cols_all_none[fq_meta_cols_all_none].index
fq_meta_cols_show = list(filter(lambda x: x not in fq_meta_cols_all_none, fq_metadata.columns))

# Add metadata
if st.session_state.show_fq_metadata:
    # How selected datasets metadata only for subset
    show_cols = ['id', 'name', 'project_names', 'owner_group_name'] + fq_meta_cols_show
    
    fq_metadata_col_config = {k : k for k in fq_metadata.columns}
    
    col_config_meta.update(fq_metadata_col_config)
    col_config = col_config_meta
else:
    show_cols = fq_datasets.columns.tolist()
    col_config = col_config_user

# Dynamically adjust height of dataframe
if st.session_state['show_details']:
    if (len(fq_datasets_show) < 10):
        fq_df_height = None
    else:
        fq_df_height = 370 # 7 Rows
elif (len(fq_datasets_show) < 14):
    fq_df_height = None
else:
    # Full Height for 14 rows
    fq_df_height = 500

# For formatting, replace None with empty string
fq_datasets_show = fq_datasets_show.fillna('')


fq_select = st.dataframe(fq_datasets_show[show_cols],
                        column_config = col_config,
                        selection_mode='multi-row',
                        hide_index = True,
                        on_select = 'rerun',
                        use_container_width=True,
                        key='fq_datasets_select_df',
                        height=fq_df_height)

# Define selected dataset(s)

if len(fq_select.selection['rows']) == 1:
    
    # Subset projects and metadata to feed into update/details
    # Get index from selection
    select_row = fq_select.selection['rows'][0]
    
    # Get original index from projects overview before subset
    selected_fq_dataset_ix = fq_datasets_show.iloc[[select_row],:].index[0] # Refers to original index
    
    fq_dataset_detail = fq_datasets.loc[selected_fq_dataset_ix,:]
    fq_metadata_detail = fq_metadata.loc[selected_fq_dataset_ix,:]
    fq_metadata_detail = fq_metadata_detail.dropna().reset_index()
    fq_metadata_detail.columns = ['key', 'value']
    
    fq_dataset_update = fq_dataset_detail.copy()
    fq_metadata_update = fq_metadata_detail.copy()
    
    fq_dataset_detail_id = fq_dataset_detail['id']
    
    select_fq_dataset_attachments = datamanager.get_fq_dataset_attachments(
        st.session_state["jwt_auth_header"],
        fq_dataset_id = fq_dataset_detail_id
    )
    
    select_fq_dataset_pro_data = datamanager.get_fq_dataset_pro_data(
        st.session_state["jwt_auth_header"],
        fq_dataset_id = fq_dataset_detail_id
    )
        
    if st.session_state['show_details']:
        show_project_details = True
    else:
        show_project_details = False
    
    update_disabled = False
    update_one = True
    
    # Would need to only combine with the metadata exactly for the selected dataset
    export_cols = fq_dataset_detail.index.tolist() + fq_metadata_detail['key'].tolist()
    
    # Combinate fq_dataset_detais
    # Remove all metadata columns which arennot in fq_metadata_detail keys
    fq_export_select = fq_datasets_show.loc[[selected_fq_dataset_ix],:]
    fq_export_select = fq_export_select[export_cols]
    
    st.session_state['dataset_select_id'] = fq_dataset_detail_id

elif len(fq_select.selection['rows']) > 1:

    select_row = fq_select.selection['rows']
    
    # Get original index from projects overview before subset
    selected_fq_dataset_ix = fq_datasets_show.iloc[select_row,:].index # Refers to original index
    
    # Would need to only combine with the metadata exactly for the selected dataset
    
    # Get fq datasets and associated metadata assays
    fq_dataset_detail = fq_datasets.loc[selected_fq_dataset_ix,:]
    fq_metadata_detail_many = fq_metadata.loc[selected_fq_dataset_ix,:]
    
    # TODO: Is this necessary?
    fq_dataset_update = fq_dataset_detail.copy()
    fq_metadata_update_many = fq_metadata_detail_many.copy()
    
    show_project_details = False
    update_disabled = False
    update_one = False
    
    # Remove all columns which are all None
    fq_metadata_detail_many = fq_metadata_detail_many.dropna(axis=1, how='all')
    
    fq_export_select = pd.concat([fq_dataset_detail, fq_metadata_detail_many], axis=1)
    
    st.session_state['dataset_select_id'] = None
    
else:
    show_project_details = False
    update_disabled = True
    update_one = False
    
    select_row = None
    selected_fq_dataset_ix = None

    fq_dataset_detail = None
    fq_metadata_detail = None
    
    fq_dataset_update = None
    fq_metadata_update = None
    
    fq_export_select = fq_datasets_show
    
    st.session_state['dataset_select_id'] = None

col_low_1, col_low_2, col_low_3,_, col_low_4 = st.columns([1.75,1.75, 1.75,3.75,3],
                                                          vertical_alignment = 'center')

with col_low_1:
    
    if st.button('Create',
                 key='create_dataset',
                 use_container_width=True,
                 help = 'Create new empty Dataset',
                 type='primary'):
        
        # Reset the session state for pro_data_new
        st.session_state['pro_data_new'] = None        
        
        create_dataset(reference_dataset_names,
                       reference_project_names_df)

with col_low_2:    
    
    if st.button('Update',
                 key='update_dataset',
                 use_container_width=True,
                 disabled = update_disabled,
                 help = 'Update the selected Dataset'):
        
        if update_one:
            update_dataset(fq_dataset_update,
                        fq_metadata_update,
                        select_fq_dataset_attachments,
                        select_fq_dataset_pro_data,
                        reference_dataset_names,
                        reference_project_names_df)

        else:
            update_many_datasets(fq_dataset_update,
                                 fq_metadata_update_many,
                                 reference_project_names_df)
        
with col_low_3:
    
    if st.button('Export',
                 key='export_datasets',
                 use_container_width=True,
                 help = 'Export and download Dataset overview'):
        
        # Prepare input for export
        export_datasets(fq_export_select)

with col_low_4:    
   
   on = st.toggle("Details",
                  key='show_details_dataset',
                  value=st.session_state['show_details'],
                  on_change = extensions.switch_show_details,
                  help='Show Details for selected Dataset')

if show_project_details:
    
    st.divider()
    
    tab1d, tab2d, tab3d, tab4d = st.tabs([':blue-background[**Features**]',
                                   ':blue-background[**Projects**]',
                                   ':blue-background[**Attachments**]',
                                   ':blue-background[**ProData**]'])
    
    with tab1d:
    
        col1d1, col2d1 = st.columns([7,5])
    
        with col1d1:
            
            with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
                
                st.write('**Details**')
                
                fq_dataset_detail_format = fq_dataset_detail.copy()
                project_detail_og = fq_dataset_detail_format['owner_group_name']
                fq_dataset_id = fq_dataset_detail_format.pop('id')
                
                fq_file_r1_id = fq_dataset_detail_format.pop('fq_file_r1')
                fq_file_r2_id = fq_dataset_detail_format.pop('fq_file_r2')
                fq_file_i1_id = fq_dataset_detail_format.pop('fq_file_i1')
                fq_file_i2_id = fq_dataset_detail_format.pop('fq_file_i2')
                
                read1_but_disabled = True
                read2_but_disabled = True
                index1_but_disabled = True
                index2_but_disabled = True
                
                if extensions.df_not_empty(fq_file_r1_id):
                    read1_but_disabled = False
                if extensions.df_not_empty(fq_file_r2_id):
                    read2_but_disabled = False
                if extensions.df_not_empty(fq_file_i1_id):
                    index1_but_disabled = False
                if extensions.df_not_empty(fq_file_i2_id):
                    index2_but_disabled = False
                                
                fq_dataset_detail_format = fq_dataset_detail_format[['name', 'description', 'created', 'owner_username']]
                fq_dataset_detail_format['created'] = fq_dataset_detail_format['created'].strftime('%Y-%m-%d %H:%M')
                
                fq_dataset_detail_format = fq_dataset_detail_format.reset_index()
                fq_dataset_detail_format.columns = ['Dataset ID', fq_dataset_id]
                
                fq_dataset_detail_format['Dataset ID'] = [
                    'Name',
                    'Description',
                    'Created',
                    'Creator'
                ]
                
                # First Reads
                col1r, col2r = st.columns([1,1])
                
                with col1r:
                    if st.button('Read 1', disabled = read1_but_disabled, use_container_width = True, help = 'View and download Read 1'):
                        detail_fq_file(fq_file_r1_id)
                    
                    if not index1_but_disabled:
                        if st.button('Index 1', use_container_width = True, help = 'View and download Index Read 1'):
                            detail_fq_file(fq_file_i1_id)
                        
                with col2r:
                    
                    if st.button('Read 2', disabled = read2_but_disabled, use_container_width = True, help = 'View and download Read 2'):
                        detail_fq_file(fq_file_r2_id)
                    
                    if not index2_but_disabled:    
                        if st.button('Index 2', use_container_width = True, help = 'View and download Index Read 2'):
                            detail_fq_file(fq_file_i2_id)
                    
                st.dataframe(fq_dataset_detail_format,
                            use_container_width = True,
                            hide_index = True,
                            key='project_details_df')
                
        with col2d1:
            with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
                
                st.write('**Metadata**')
                
                st.dataframe(fq_metadata_detail,
                            use_container_width = True,
                            hide_index = True,
                            column_config = {
                                'key' : st.column_config.Column('Key'),
                                'value' : st.column_config.Column('Value'),
                            },
                            key='fq_metadata_details_df')
    
    with tab2d:
        
        with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
            
            st.write('**Projects**')
            
            # Get prject information here: my_projects    
                 
            project_ids = fq_dataset_detail['project']
            dataset_projects_detail = my_projects.loc[my_projects['id'].isin(project_ids),['id', 'name', 'description']]
            
            # Get ID, Name and Description of all projects
            
            # Limit Max Height of Dataframe
            if dataset_projects_detail.shape[0] > 7:
                max_df_height = 315
            else:
                max_df_height = None
            
            st.dataframe(dataset_projects_detail,
                            use_container_width = True,
                            hide_index = True,
                            column_config = {
                                'id' : st.column_config.TextColumn('ID', width='small'),
                                'name' : st.column_config.TextColumn('Name'),
                                'description' : st.column_config.TextColumn('Description')
                            },
                            key='fq_dataset_projects_df',
                            height = max_df_height)
            
    with tab3d:
    
        with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
            
            select_dataset_id = st.session_state['dataset_select_id']
            
            # Value is none if not run
            download_fq_attach_key_name = f'download_fq_attachments_select_{select_dataset_id}'
            
            if download_fq_attach_key_name in st.session_state:
                fq_attach_select = st.session_state[download_fq_attach_key_name]
            else:
                fq_attach_select = None
            
            col1atta, col2atta = st.columns([2,10])
            
            with col1atta:
                st.write('**Attachments**')
            
            with col2atta:
            
                if fq_attach_select and len(fq_attach_select.selection['rows']) == 1:
                    
                    select_ix = fq_attach_select.selection['rows'][0]
                    select_attachment = select_fq_dataset_attachments.iloc[select_ix,:]
                    select_attachment_id = int(select_attachment['id'])
                    select_attachment_name = select_attachment['name']
                    
                    st.download_button('Download',
                                    data=datamanager.get_fq_attachment_file_download(select_attachment_id),
                                    file_name = select_attachment_name,
                                    key='download_attachment')
            
                else:        
                    disable_download = True
                    select_attachment_id = 0

                    st.button('Download',
                              disabled = True,
                              help = 'Select an attachment to download',
                              key='download_attachment')
                
            # Limit Max Height of Dataframe
            if select_fq_dataset_attachments.shape[0] > 7:
                max_df_height = 315
            else:
                max_df_height = None
            
            st.dataframe(select_fq_dataset_attachments,
                        hide_index = True,
                        use_container_width = True,
                        column_config = {
                            'id' : None,
                            'name' : st.column_config.TextColumn('Name'),
                            'description' : None,
                            'fq_dataset_id' : None},
                        on_select = update_attachment_select,
                        selection_mode='single-row',
                        key='fq_attachment_details_df',
                        height = max_df_height)

    with tab4d:
        
        with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
            
            select_dataset_id = st.session_state['dataset_select_id']
            include_archived = st.session_state['pro_data_show_archived_versions']
            
            # Value is none if not run
            detail_fq_pro_data_key_name = f'download_pro_data_select_{select_dataset_id}'
            
            # Filter out all older versions
            if not st.session_state['pro_data_show_archived_versions']:
                select_fq_dataset_pro_data = select_fq_dataset_pro_data.loc[
                    select_fq_dataset_pro_data['valid_to'].isna(),:]

            # Check if a ProData element was selected
            # Get selection from session state {'selection': {'rows': [2], 'columns': []}}
            if detail_fq_pro_data_key_name in st.session_state:
                fq_pro_data_select = st.session_state[detail_fq_pro_data_key_name]
            else:
                fq_pro_data_select = None
            
            col1pro, col2pro, col3pro = st.columns([2,2,8])
            
            with col1pro:
                st.write('**ProData**')
            
            with col2pro:
                if fq_pro_data_select and len(fq_pro_data_select.selection['rows']) == 1:
                    
                    select_ix = fq_pro_data_select.selection['rows'][0]
                    select_pro_data = select_fq_dataset_pro_data.iloc[select_ix,:]
                    select_pro_data_id = int(select_pro_data['id'])
                    
                    st.button('Details',
                              key='download_pro_data',
                              help = 'Download ProData',
                              on_click = detail_pro_data,
                              args = (select_pro_data_id,))
                
                else:
                    st.button('Details',
                              disabled = True)
            
            # Limit Max Height of Dataframe
            if select_fq_dataset_pro_data.shape[0] > 7:
                max_df_height = 260
            else:
                max_df_height = None
            
            st.dataframe(select_fq_dataset_pro_data,
                        hide_index = True,
                        use_container_width = True,
                        column_config = {
                            'id' : st.column_config.TextColumn('ID'),
                            'name' : st.column_config.TextColumn('Name'),
                            'data_type' : st.column_config.TextColumn('Type'),
                            'description' : None,
                            'version' : st.column_config.TextColumn('Version'),
                            'owner_username' : st.column_config.TextColumn('Creator'),
                            'valid_to' : None
                        },
                        on_select = update_pro_data_select,
                        selection_mode='single-row',
                        key='fq_prodata_details_df',
                        height = max_df_height)
            
            st.checkbox('Include archived',
                        key='checkbox_pro_data_include_archive',
                        value = st.session_state['pro_data_show_archived_versions'],
                        on_change = update_pro_data_show_archived)
