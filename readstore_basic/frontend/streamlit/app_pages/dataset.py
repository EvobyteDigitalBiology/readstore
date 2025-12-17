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
import st_yled
from streamlit_split_button import split_button

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

st_yled.init()


# Set sesstion state for downloaing attachments

# Session state for selecting datasets to attach to project
if not 'dataset_select_id' in st.session_state:
    st.session_state['dataset_select_id'] = None

if not 'selected_fq_dataset' in st.session_state:
    st.session_state['selected_fq_dataset'] = None

if not 'selected_fq_metadata' in st.session_state:
    st.session_state['selected_fq_metadata'] = None

if not 'selected_fq_attachments' in st.session_state:
    st.session_state['selected_fq_attachments'] = None

if not 'selected_fq_pro_data' in st.session_state:
    st.session_state['selected_fq_pro_data'] = None

if not 'dataset_select_project_names' in st.session_state:
    st.session_state['dataset_select_project_names'] = []

# Session state for showing archived processed data
if not 'pro_data_show_archived_versions' in st.session_state:
    st.session_state['pro_data_show_archived_versions'] = False

# Session state to hold new ProData during Dataset Creation
if not 'pro_data_new' in st.session_state:
    st.session_state['pro_data_new'] = None

if not 'fq_details_segment_ix' in st.session_state:
    st.session_state['fq_details_segment_ix'] = 0

if not 'fq_dataset_meta_filter_hash' in st.session_state:
    st.session_state['fq_dataset_meta_filter_hash'] = str(uuid.uuid4())

if not 'fq_dataset_meta_filter_applied' in st.session_state:
    st.session_state['fq_dataset_meta_filter_applied'] = False

if not 'dataset_split_but_hash' in st.session_state:
    st.session_state['dataset_split_but_hash'] = str(uuid.uuid4())

if not 'toast_cache' in st.session_state:
    st.session_state['toast_cache'] = None

if not 'error_cache' in st.session_state:
    st.session_state['error_cache'] = None

if not 'show_details' in st.session_state:
    st.session_state['show_details'] = True

if not 'show_metadata' in st.session_state:
    st.session_state['show_metadata'] = False

# Set selected ProData index for an activate dataset for download function
def update_attachment_select():
    if st.session_state['dataset_select_id']:
        dataset_id = st.session_state['dataset_select_id']
        st.session_state[f'download_fq_attachments_select_{dataset_id}'] = st.session_state['fq_attachment_details_df']

def update_pro_data_select():
    if st.session_state['dataset_select_id']:
        dataset_id = st.session_state['dataset_select_id']
        st.session_state[f'download_pro_data_select_{dataset_id}'] = st.session_state['fq_prodata_details_df']

def update_selected_project_names():
    st.session_state['dataset_select_project_names'] = st.session_state['multiselect_dataset_project_names']

def reset_selected_project_names():
    st.session_state['dataset_select_project_names'] = []

def reset_meta_filter_hash():
    """Reset dataset metadata filter hash to force re-rendering of metadata filter UI"""
    st.session_state['fq_dataset_meta_filter_hash'] = str(uuid.uuid4())

def update_segment_default(segment_control_options):
    
    dataset_detail_selection = st.session_state['dataset_detail_selection']
    
    if dataset_detail_selection:
        ix = segment_control_options.index(dataset_detail_selection)
        st.session_state['fq_details_segment_ix'] = ix

def update_pro_data_show_archived():
    new_state = st.session_state['checkbox_pro_data_include_archive']
    st.session_state['pro_data_show_archived_versions'] = new_state
    
    # Reset selection to avoid problems with old selection
    if 'detail_fq_pro_data_key_name' in st.session_state:
        del st.session_state['detail_fq_pro_data_key_name']

#region Create Dataset
@st.dialog('Create Dataset', width='medium', on_dismiss=reset_selected_project_names)
def create_dataset(reference_fq_dataset_names: pd.Series,
                    reference_project_names_df: pd.DataFrame):
    """Create empty dataset

    Args:
        reference_fq_dataset_names (pd.Series): Existing names of fq_datasets
        reference_project_names_df (pd.DataFrame): Existing names of projects
    """
    
    # Get reference dataset and project names
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()

    project_names_select = st.session_state['dataset_select_project_names']

    # Define Tabs
    tab1, tab2, tab3 = st_yled.tabs(["Features", "Projects", "Attachments"], font_size=14, font_weight=500)

    # TAB: Features: Description and Metadata
    with tab1:
        st_yled.markdown('Set Dataset Attributes and Metadata', font_size=12, color='#808495')
        
        # Set dataset name
        name = st_yled.text_input("Dataset Name",
                                    max_chars=150,
                                    help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
                                    width = 400,
                                    border_style='none',
                                    border_width='0px',
                                    key = 'create_dataset_name_input')        
        st.write("")

        description = st_yled.text_area("Dataset Description",
                                    help = 'Description of the project.',
                                    width = 512,
                                    border_style='none',
                                    border_width='0px',
                                    key = 'create_dataset_description_input')

        st.write("")

        st_yled.markdown('Metadata', font_size=14, font_weight=500)

        with st_yled.container(key='dataset-metadata-info'):
            st_yled.markdown("Dataset metadata must be provided as key-value pairs.", font_size=12, color='#808495')
            st_yled.markdown("Metadata facilitate grouping and filtering of datasets by pre-defined features.", font_size=12, color='#808495')
            st_yled.markdown("Attach Project to inherit its Metadata Keys.", font_size=12, color='#808495')

        st.write("")

        # Get metadata keys for selected projects
        metadata_keys = reference_project_names_df.loc[
                reference_project_names_df['name'].isin(project_names_select),'dataset_metadata_keys'].to_list()
        metadata_keys = [list(m.keys()) for m in metadata_keys]
        metadata_keys = itertools.chain.from_iterable(metadata_keys)
        metadata_keys = sorted(list(set(metadata_keys)))

        fq_metadata_keys = []
        fq_metadata_values = []

        for k in metadata_keys:
            fq_metadata_keys.append(k)
            fq_metadata_values.append('')

        selected_fq_metadata = pd.DataFrame({
            'key' : fq_metadata_keys,
            'value' : fq_metadata_values
        })

        if selected_fq_metadata.shape[0] == 0:
            selected_fq_metadata = pd.DataFrame({'key' : [''], 'value' : ['']})
        else:
            selected_fq_metadata = selected_fq_metadata.astype(str)

        metadata_df = st.data_editor(
                            selected_fq_metadata,
                            hide_index=True,
                            column_config = {
                                'key' : st.column_config.TextColumn('Key'),
                                'value' : st.column_config.TextColumn('Value')
                            },
                            num_rows ='dynamic',
                            key = 'create_dataset_metadata_df',
                            width = 400,
                        )

    # TAB: Features: Project
    with tab2:

        st_yled.markdown('Attach the Dataset to one or more Projects', font_size=12, color='#808495')

        project_options = sorted(reference_project_names_df['name'])
        
        # Select project to attach dataset to
        st.multiselect("Select Projects",
                project_options,
                help = 'Attach the Dataset to one or more Projects',
                on_change=update_selected_project_names,
                key='multiselect_dataset_project_names',
                width=400)

        st.write("")
        st.write("")

    # TAB: Attachments
    with tab3:
        # Choose Files to Upload
        with st_yled.container(key='dataset-attachments-info'):
            
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
    
    # TAB: Create ProData Entries for Dataset
    # with tab4:
              
    #     st.write('Attach **Pro**cessed Data.')

    #     pro_data_name = st.text_input("Enter Name",
    #                                     max_chars=150,
    #                                     help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
    #                                     label_visibility = "collapsed",
    #                                     placeholder = "Enter Name",
    #                                     key = 'pro_data_name')
        
    #     pro_data_type = st.text_input("Enter Data Type",
    #                                     max_chars=150,
    #                                     help = 'Data Type, e.g. gene_count. \nName must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
    #                                     label_visibility = "collapsed",
    #                                     placeholder = "Enter Data Type",
    #                                     key = 'pro_data_type')
        
    #     pro_upload_path = st.text_input("Enter Upload Path",
    #                                     max_chars=1000,
    #                                     help = 'Path to File to Upload',
    #                                     label_visibility = "collapsed",
    #                                     placeholder = "Path to ProData File",
    #                                     key = 'pro_upload_path')
        
    #     pro_description = st.text_area("Enter Description",
    #                                     help = 'Description of the FASTQ Dataset.',
    #                                     height = 68,
    #                                     label_visibility = "collapsed",
    #                                     placeholder = "Enter Description",
    #                                     key = 'pro_description')
        
    #     # Metadata for ProData
    #     with st.container(border=True):
            
    #         col1p, col2p = st.columns([11,1], vertical_alignment='top')
                    
    #         with col1p:
                
    #             tab1p = st.tabs([":blue-background[**Metadata**]"])[0]
                
    #             with tab1p:
                    
    #                 selected_fq_metadata = pd.DataFrame({
    #                     'key' : [],
    #                     'value' : []
    #                 })

    #                 # Data Editor for Input
    #                 selected_fq_metadata = selected_fq_metadata.astype(str)
    #                 pro_metadata_df = st.data_editor(
    #                     selected_fq_metadata,
    #                     use_container_width=True,
    #                     hide_index=True,
    #                     column_config = {
    #                         'key' : st.column_config.TextColumn('Key'),
    #                         'value' : st.column_config.TextColumn('Value')
    #                     },
    #                     num_rows ='dynamic',
    #                     key = 'create_pro_data_metadata_df'
    #                 )
            
    #         with col2p:
    #             with st.popover(':material/help:'):
    #                 st.write("Key-value pairs to store and group dataset metadata.")
        
    #     col3, col4 = st.columns([3, 9])
        
    #     # Need a session state to store ProData which should be added
        
    #     with col3:
    #         if st.button('Add ProData'):
                
    #             # Validate ProData
    #             if pro_data_name == '':
    #                 st.error("Please enter a ProData Name.")
    #             elif not extensions.validate_charset(pro_data_name):
    #                 st.error('ProData Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
    #             elif pro_data_type == '':
    #                 st.error("Please enter a ProData Data Type.")
    #             elif not extensions.validate_charset(pro_data_type):
    #                 st.error('ProData Data Type: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
    #             elif pro_upload_path == '':
    #                 st.error("Enter an upload path")
    #             elif not os.path.isfile(pro_upload_path):
    #                 st.error("Upload path for ProData File not found")
    #             else:
                    
    #                 # Remove na values from metadata key column
    #                 pro_metadata_df = pro_metadata_df.loc[~pro_metadata_df['key'].isna(),:]
    #                 # Replace all None values with empty string
    #                 pro_metadata_df = pro_metadata_df.fillna('')
                  
    #                 # Validate ProData Metadata
    #                 pro_metadata_keys = pro_metadata_df['key'].tolist()
    #                 pro_metadata_values = pro_metadata_df['value'].tolist()
    #                 pro_metadata_keys = [k.lower() for k in pro_metadata_keys]                  
                    
    #                 for k, v in zip(pro_metadata_keys, pro_metadata_values):                        
    #                     if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
    #                         st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
    #                         break
    #                     if k in uiconfig.METADATA_RESERVED_KEYS:
    #                         st.error(f'Metadata Key **{k}**: Reserved keyword, please choose another key')
    #                         break
    #                 else:
                        
    #                     pro_data_entry = {
    #                         'name' : pro_data_name,
    #                         'data_type' : pro_data_type,
    #                         'upload_path' : pro_upload_path,
    #                         'description' : pro_description,
    #                         'metadata' : {k:v for k,v in zip(pro_metadata_keys, pro_metadata_values)}
    #                     }
                        
                        
    #                     # Add ProData to session state
    #                     if not st.session_state['pro_data_new'] is None:
    #                         # Returns a list of dicts
    #                         pro_data_new = st.session_state['pro_data_new']
    #                         pro_data_new_names = [e['name'] for e in pro_data_new]  
                            
    #                         if pro_data_name in pro_data_new_names:
    #                             st.error("ProData Name already exists.")
    #                         else:
    #                             pro_data_new.append(pro_data_entry)
    #                             st.session_state['pro_data_new'] = pro_data_new
    #                     else:
    #                         # Initialize ProData as list of dicts
    #                         st.session_state['pro_data_new'] = [pro_data_entry]
                                                    
    #     with col4:
    #         if not st.session_state['pro_data_new'] is None:
    #             names = [e['name'] for e in st.session_state['pro_data_new']]
                
    #             st.write('ProData added: ' + ', '.join(names))
        
    with st.container(horizontal=True, horizontal_alignment='right'):

        if st.button('Cancel', key='cancel_create_project'):
            st.rerun()

        if st.button('Confirm', type ='primary', key='ok_create_dataset'):
            
            # Get project_ids for selected project names
            project_ids = reference_project_names_df.loc[
                reference_project_names_df['name'].isin(project_names_select),'id'].tolist()
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Replace all None values with empty string
            metadata_df = metadata_df.loc[metadata_df['key'] != '', :]
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
                    st.session_state['error_cache'] = f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces'
                    break
                if k in uiconfig.METADATA_RESERVED_KEYS:
                    st.session_state['error_cache'] = f'Metadata Key **{k}**: Reserved keyword, please choose another key'
                    break
            else:            
                # Validate username / Better use case
                if name == '':
                    st.session_state['error_cache'] = 'Dataset Name is empty'
                elif not extensions.validate_charset(name):
                    st.session_state['error_cache'] = 'Dataset Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces'
                elif name.lower() in reference_fq_dataset_names:
                    st.session_state['error_cache'] = 'Dataset Name already exists in Group'
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

    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None


#region Update Dataset
@st.dialog('Update Dataset', width="medium", on_dismiss=reset_selected_project_names)
def update_dataset(selected_fq_dataset: pd.DataFrame,
                   selected_fq_metadata: pd.DataFrame,
                   selected_fq_attachments: pd.DataFrame,
                   selected_fq_pro_data: pd.DataFrame,
                    reference_fq_dataset_names: pd.Series,
                    reference_project_names_df: pd.DataFrame):
    """Update dataset

    Args:
        selected_fq_dataset: Selected dataset to update
        selected_fq_metadata: Selected metadata for dataset to update
        selected_fq_attachments: Selected attachments for dataset to update
        selected_fq_pro_data: Selected datasets ProData entries
        reference_fq_dataset_names: Existing fq_datasets names 
        reference_project_names_df: Existing projects names
    """
    
    fq_dataset_input = selected_fq_dataset.copy()
        
    read_long_map = {
        'R1' : 'Read 1',
        'R2' : 'Read 2',
        'I1' : 'Index 1',
        'I2' : 'Index 2',
    }
    
    #read_file_file_map = {}
    
    fq_dataset_id = fq_dataset_input['id']
    fq_dataset_name_old = fq_dataset_input['name']
    fq_dataset_description_old = fq_dataset_input['description']
    fq_dataset_project_names = fq_dataset_input['project_names']

    # # Map fq file ids to read types
    # if extensions.df_not_empty(fq_dataset_input['fq_file_r1']):
    #     read_file_file_map['R1'] = fq_dataset_input['fq_file_r1']
    # if extensions.df_not_empty(fq_dataset_input['fq_file_r2']):
    #     read_file_file_map['R2'] = fq_dataset_input['fq_file_r2']
    # if extensions.df_not_empty(fq_dataset_input['fq_file_i1']):        
    #     read_file_file_map['I1'] = fq_dataset_input['fq_file_i1']
    # if extensions.df_not_empty(fq_dataset_input['fq_file_i2']):
    #     read_file_file_map['I2'] = fq_dataset_input['fq_file_i2']

    # Remove current name from reference names
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names[
        reference_fq_dataset_names != fq_dataset_name_old.lower()]
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()
    
    project_names_select = st.session_state['dataset_select_project_names']

    # # Get fq for all read types
    # for k, v in read_file_file_map.items():
    #     read_file_file_map[k] = datamanager.get_fq_file_detail(st.session_state["jwt_auth_header"], v)

    # Define Tabs
    #tab_names = [read_long_map[rt] for rt in read_file_file_map.keys()]
    tab_names_format = ["Features",
                        "Projects",
                        "Attachments"]
    
    # #tab_names_format.extend([f"{tn}" for tn in tab_names])
    # fq_file_names = [None] * len(read_file_file_map)
    
    # Add Metadata and Attachments Tabs
    tabs = st_yled.tabs(tab_names_format, font_size=14, font_weight=500)
        
    # region Metadata Tab        
    with tabs[0]:
        
        st_yled.markdown('Edit Dataset Attributes and Metadata', font_size=12, color='#808495')

        name = st_yled.text_input("Project Name",
                                max_chars=150,
                                width = 400,
                                border_style='none',
                                border_width='0px',
                                help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
                                value = fq_dataset_name_old,
                                key = 'update_dataset_name_input')

        st.write("")

        description = st_yled.text_area("Dataset Description",
                                        help = 'Description of the dataset.',
                                        value = fq_dataset_description_old,
                                        width = 512,
                                    border_style='none',
                                    border_width='0px',
                                    key = 'update_dataset_description_input')
            
        st.write("")

        st_yled.markdown('Metadata', font_size=14, font_weight=500)
            
        with st_yled.container(key='dataset-metadata-info'):
            st_yled.markdown("Dataset metadata must be provided as key-value pairs.", font_size=12, color='#808495')
            st_yled.markdown("Metadata facilitate grouping and filtering of datasets by pre-defined features.", font_size=12, color='#808495')
            st_yled.markdown("Select a Project to inherit Metadata Keys.", font_size=12, color='#808495')

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

            if selected_fq_metadata.shape[0] == 0:
                selected_fq_metadata = pd.DataFrame({'key' : [''], 'value' : ['']})
            else:
                selected_fq_metadata = selected_fq_metadata.astype(str)
            
            metadata_df = st.data_editor(
                selected_fq_metadata,
                hide_index=True,
                column_config = {
                    'key' : st.column_config.TextColumn('Key'),
                    'value' : st.column_config.TextColumn('Value')
                },
                num_rows ='dynamic',
                key = 'update_dataset_metadata_df',
                width = 400
            )
            

        # region Projects Tab
    with tabs[1]:
        
        project_options = sorted(reference_project_names_df['name'])
        st_yled.markdown('Attach the Dataset to one or more Projects', font_size=12, color='#808495')
        
        projects_default = fq_dataset_project_names
        
        st.multiselect("Select Projects",
                    project_options,
                    projects_default,
                    help = 'Attach the Dataset to one or more Projects',
                    on_change=update_selected_project_names,
                    key='multiselect_dataset_project_names',
                    width=400)

        st.write("")
        st.write("")
    
    # region Attachment Tab
    with tabs[2]:
        
        with st.container(key='dataset-attachments-info'):
            
            st_yled.markdown('Upload or Remove Dataset File Attachments', font_size=12, color='#808495')

            st.write("")

            # Define Max Heigth of attachment select
            # Limit Max Height of Dataframe
            if selected_fq_attachments.shape[0] > 7:
                max_df_height = 290
            else:
                max_df_height = 'content'
            
            if selected_fq_attachments.shape[0] == 0:
                
                st_yled.info(':material/notifications: No attachments available. Start by uploading new files below.',
                             border_width="2.0px",
                             border_color="#808495",
                             border_style="solid",
                             color="#808495",
                             key='info-no-samples',
                             width=400)

            else:
                attach_select = st.dataframe(selected_fq_attachments,
                                        hide_index = True,
                                        width = 400,
                                        column_config = {
                                            'id' : None,
                                            'name' : st.column_config.TextColumn('Name'),
                                            'description' : None,
                                            'fq_dataset_id' : None},
                                        key='update_attachment_df',
                                        selection_mode='multi-row',
                                        on_select = 'rerun',
                                        height = max_df_height)

                if len(attach_select.selection['rows']) > 0:
                    delete_disabled = False
                else:
                    delete_disabled = True

                with st_yled.container(horizontal=True, horizontal_alignment='right', width=400):

                    with st_yled.expander('Delete',
                                        icon=":material/delete:",
                                        width=104,
                                        border_width="2.0px",
                                        font_weight="500",
                                        background_color="#f0f2f6",
                                        border_style="solid",
                                        border_color="#1d959b",
                                        color="#1d959b",
                                        key='delete_attachment_expander'):

                        if st.button('Confirm', key='delete_attachments', disabled=delete_disabled, type='primary', width='stretch'):
                            
                            attach_ixes = attach_select.selection['rows']
                            attach_ids = selected_fq_attachments.loc[attach_ixes,'id'].tolist()
                            
                            for attach_id in attach_ids:
                                datamanager.delete_fq_attachment(attach_id)
                            else:
                                st.cache_data.clear()
                                # Reset attachment select for project id
                                st.session_state[f'download_fq_attachments_select_{fq_dataset_id}'] = None
                                st.rerun()

        st.write("")
        st.write("")                        

        uploaded_files = st.file_uploader("**Upload attachments for the Dataset**",
                                        help = "Upload attachments for the Dataset. Attachments can be any file type.",
                                        accept_multiple_files = True,
                                        width=400)

    
    # region ProData
    
    # with tabs[3]:
        
    #     with st.container(border=True, height=495):
            
    #         # List all attachments            
    #         update_include_archived = st.checkbox('Include archived',
    #                                             key='pro_data_show_archived_versions_update',
    #                                             value = False)
            
    #         if not update_include_archived:
    #             selected_fq_pro_data = selected_fq_pro_data.loc[
    #                     selected_fq_pro_data['valid_to'].isna(),:]

    #         # Define Max Heigth of attachment select
    #         # Limit Max Height of Dataframe
    #         if selected_fq_pro_data.shape[0] > 7:
    #             max_df_height = 350
    #         else:
    #             max_df_height = 'content'
            
    #         pro_data_select = st.dataframe(selected_fq_pro_data,
    #                                     hide_index = True,
    #                                     use_container_width = True,
    #                                     column_config = {
    #                                         'id' : st.column_config.TextColumn('ID'),
    #                                         'name' : st.column_config.TextColumn('Name'),
    #                                         'data_type' : st.column_config.TextColumn('Type'),
    #                                         'description' : None,
    #                                         'version' : st.column_config.TextColumn('Version'),
    #                                         'owner_username' : None,
    #                                         'valid_to' : None
    #                                     },
    #                                     key='update_pro_data_df',
    #                                     selection_mode='multi-row',
    #                                     on_select = 'rerun',
    #                                     height = max_df_height)

    #     col, _ = st.columns([4,8])

    #     with col:
    #         with st.expander('Delete ProData', icon=":material/delete_forever:"):
    #             if st.button('Confirm', key='delete_pro_data', width='stretch'):
                    
    #                 pro_data_ixes = pro_data_select.selection['rows']
    #                 pro_data_ids = selected_fq_pro_data.loc[pro_data_ixes,'id'].tolist()
                    
    #                 for pro_data_id in pro_data_ids:
    #                     datamanager.delete_pro_data(pro_data_id)
    #                 else:
    #                     st.cache_data.clear()
    #                     # Reset selection config for pro data
    #                     st.session_state[f'download_pro_data_select_{fq_dataset_id}'] = None
    #                     st.rerun()


#     for ix, rt in enumerate(read_file_file_map.keys()):
        
#         # region Read Tab
#         with tabs[4+ix]:
            
#             col1, col2 = st.columns([1, 1])
            
#             with col1:
                
#                 with st.container(border=True, height=460):
                    
#                     st.subheader('FASTQ Stats')
                    
#                     # Get id of the fq file for read
#                     fq_file_read = read_file_file_map[rt]
                    
#                     fq_file_id = fq_file_read.id
#                     fq_file_name_old = fq_file_read.name
#                     phred_values = fq_file_read.qc_phred
#                     qc_phred_mean = round(fq_file_read.qc_phred_mean,2)
                                        
#                     fq_file_created = fq_file_read.created.strftime('%Y-%m-%d %H:%M')
                    
#                     fq_file_df = pd.DataFrame({
#                         'Created' : [fq_file_created],
#                         'QC Passed' : [fq_file_read.qc_passed],
#                         'Upload Path' : [fq_file_read.upload_path],
# #                        'Bucket' : [fq_file_read.bucket],
# #                        'Key' : [fq_file_read.key],
#                         'Read Length' : [fq_file_read.read_length],
#                         'Num Reads' : [fq_file_read.num_reads],
#                         'Mean Phred Score' : [qc_phred_mean],
#                         'Size (MB)' : [fq_file_read.size_mb],
#                         'MD5 Checksum' : [fq_file_read.md5_checksum],
#                     })
                                        
#                     fq_file_df = fq_file_df.T
#                     fq_file_df.index.name = 'FASTQ File'
#                     fq_file_df.columns = [fq_file_id]
                    
#                     fq_file_names[ix] = st.text_input("FASTQ File Name", value=fq_file_name_old, key=f'fq_name_{ix}')
                    
#                     st.write(fq_file_df)
            
#             with col2:
                
#                 with st.container(border=True, height=460):
                    
#                     st.subheader('Per Base Phred Score')
                    
#                     st.write('')
#                     st.write('')
#                     st.write('')
                    
#                     phred_base_pos = [i for i in range(1, len(phred_values)+1)]
#                     phres_val = [phred_values[str(k-1)] for k in phred_base_pos]
#                     phred_df = pd.DataFrame({'Base Position' : phred_base_pos, 'Phred Score' : phres_val})
                    
#                     st.line_chart(phred_df, x='Base Position', y='Phred Score')

#             # # Define updated fastq files
#             fq_file_read.name = fq_file_names[ix]
#             read_file_file_map[rt] = fq_file_read


    with st.container(horizontal=True, horizontal_alignment='right'):

        if st.button('Cancel', key='cancel_create_project'):
            st.rerun()
    
        # region Confirm Button     
        if st.button('Confirm', key='confirm_ds_update', type = 'primary'):
            
            # Prep Metadata
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Replace all None values with empty string
            metadata_df = metadata_df.loc[metadata_df['key'] != '', :]
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
                 st.session_state['error_cache'] = "Please enter a Dataset Name."
            elif name.lower() in reference_fq_dataset_names:
                st.session_state['error_cache'] = "Dataset Name already exists. Please choose another name."
            elif not extensions.validate_charset(name):
                st.session_state['error_cache'] = 'Dataset Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.'
            #else:
                # Loop over fastq file Pydantic Models
                # There is not constraint on the fastq file name, can be duplicated
                # for fq_file in read_file_file_map.values():
                #     fq_file_name = fq_file.name
                #     if not extensions.validate_charset(fq_file_name):
                #         st.error('Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                #         break
                #     if fq_file_name == '':
                #         st.error("Please enter a name for FASTQ file")
                #         break
                # If names of all fastq files are valid, continue metadata check
            else:              
                # 3) Third check for metadata
                for k, v in zip(keys, values):
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.session_state['error_cache'] = f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces.'
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.session_state['error_cache'] = f'Metadata key **{k}**: Reserved keyword, please choose another key'
                        break
                        
                    # Check if attachment names are valid
                    #selected_fq_attachments
                else: 
                    # Update FqFiles
                    # for v in read_file_file_map.values():
                    #     datamanager.update_fq_file(v)
                    # else:
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

    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None


# # region Update Many Datasets
# @st.dialog('Update Datasets', width='large')
# def update_many_datasets(selected_fq_dataset: pd.DataFrame,
#                          selected_fq_metadata: pd.DataFrame,
#                         reference_project_names_df: pd.DataFrame):
        
#     # Add Metadata and Attachments Tabs
#     tabs = st.tabs([":blue-background[**Projects**]"])
    
#     with tabs[0]:
        
#         with st.container(border=True):
            
#             st.subheader('Projects')

#             project_options = sorted(reference_project_names_df['name'])
#             st.write('Attach the selected Datasets to one or more Projects')
                        
#             project_names_select = st.multiselect("Select Projects",
#                     project_options,
#                     help = 'Attach the dataset to project(s).')
        
#         coldel, _ = st.columns([4,8])
        
#         with coldel:
#             with st.expander('Delete all Datasets', icon=":material/delete_forever:"):
#                 if st.button('Confirm', key='delete_fq_dataset_many'):
                
#                     # Dataset will automatically be deleted through cascade
#                     with st.spinner('Deleting Datasets...'):
                        
#                         _ = [datamanager.delete_fq_dataset(fq_id) for fq_id in selected_fq_dataset['id']]
                    
#                     st.cache_data.clear()
#                     st.rerun()

#     _, col1d = st.columns([9,3])
    
#     with col1d:
        
#         # region Confirm Button     
#         if st.button('Confirm', key='confirm_ds_update_many', type = 'primary', use_container_width=True):
            
#             # Get project ids for selected project names
#             project_ids = reference_project_names_df.loc[
#                 reference_project_names_df['name'].isin(project_names_select),'id'].tolist()
            
#             # Get metadata keys for selected projects returns list of dicts
#             project_dataset_metadata_keys = reference_project_names_df.loc[
#                 reference_project_names_df['name'].isin(project_names_select),'dataset_metadata_keys'].tolist()
            
#             project_dataset_metadata_keys = [list(m.keys()) for m in project_dataset_metadata_keys]
#             project_dataset_metadata_keys = itertools.chain.from_iterable(project_dataset_metadata_keys)

#             # Update selected FqDatasets with new project ids
#             for ix, (_, fq_dataset) in enumerate(selected_fq_dataset.iterrows()):
                
#                 metadata = selected_fq_metadata.iloc[ix,:]
#                 metadata = metadata.dropna().reset_index()
#                 metadata.columns = ['key', 'value']
#                 metadata_dict = {k:v for k,v in zip(metadata['key'],metadata['value'])}

#                 # Update with new metadata keys
#                 for k in project_dataset_metadata_keys:
#                     if not k in metadata_dict.keys():
#                         metadata_dict[k] = ''
                
#                 # Attach new project metadata keys to metadata
#                 fq_dataset_id = fq_dataset['id']                
#                 name = fq_dataset['name']
#                 description = fq_dataset['description']
#                 project_ids_old = fq_dataset['project']
#                 project_ids_update = list(set(project_ids + project_ids_old))
                
#                 datamanager.update_fq_dataset(fq_dataset_id,
#                                               name,
#                                               description,
#                                               metadata_dict,
#                                               project_ids_update)
            
#             st.cache_data.clear()
#             st.rerun()
            

    
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
    
    st_yled.markdown("""Export Selection as .csv file

Choose from the options:
- Datasets and Metadata
- Dataset FASTQ Statistics
- Dataset associated Processed Data
            """, color='#808495', font_size=12)
            
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

                st.write("")
                st.write("")

                with st_yled.container(horizontal=True, horizontal_alignment='right'):

                    if st.button('Cancel', key='cancel_create_project'):
                        st.rerun()

                    st.download_button('Download .csv',
                                    fq_files.to_csv(index=False).encode("utf-8"),
                                    'fastq_files.csv',
                                    'text/csv',
                                type='primary')
            
        elif export_selection == 'Datasets':
            
            # Get fq_attachments
            # TODO: Speedup requesting view
            fq_attachments = datamanager.get_fq_dataset_attachments(st.session_state["jwt_auth_header"])
            # Cast attachments to a list
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
            
            st.write("")
            st.write("")

            with st_yled.container(horizontal=True, horizontal_alignment='right'):

                if st.button('Cancel', key='cancel_create_project'):
                    st.rerun()

                st.download_button('Download .csv',
                                fq_dataset_view.to_csv(index=False).encode("utf-8"),
                                'datasets.csv',
                                'text/csv',
                                type='primary')

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
                
                pro_data, pro_metadata = datamanager.get_pro_data_meta_overview(st.session_state["jwt_auth_header"],
                                                                                include_archived=export_include_archived)
                
                pro_data_meta = pd.concat([pro_data, pro_metadata], axis=1)
                
                pro_data_meta_merge = pro_data_meta.merge(fq_datasets_meta,
                                                          left_on='fq_dataset',
                                                        right_on='id',
                                                        suffixes=('', '_fq_dataset'))
                
                pro_data_meta_merge = pro_data_meta_merge.drop(columns=['id_fq_dataset', 'name_fq_dataset'])
                pro_data_meta_merge = pro_data_meta_merge.rename(columns={'owner_username' : 'creator',
                                                                        'fq_dataset' : 'dataset_id',
                                                                        'fq_dataset_name' : 'dataset_name',
                                                                        'project' : 'project_ids',
                                                                        })
                
            pro_data = datamanager.get_pro_data_owner_group(st.session_state["jwt_auth_header"])
            
            st.write("")
            st.write("")

            with st_yled.container(horizontal=True, horizontal_alignment='right'):

                if st.button('Cancel', key='cancel_create_project'):
                    st.rerun()

                st.download_button('Download .csv',
                                pro_data_meta_merge.to_csv(index=False).encode("utf-8"),
                                'processed_data.csv',
                                'text/csv',
                                type='primary')
        
        else:
            st.error('Invalid Export Selection')

#region Delete Datasets
@st.dialog('Delete Datasets', width='medium', on_dismiss='rerun')
def delete_datasets(dataset_select_df: pd.DataFrame):
    """
    Dialog for confirming deletion of selected datasets.
    
    Args:
        project_select_df: DataFrame containing the projects to be deleted
    """

    # Check if project_select_df is series 
    fq_dataset_ids = dataset_select_df['id']
    if isinstance(fq_dataset_ids, int):
        fq_dataset_ids = [fq_dataset_ids]
    else:
        fq_dataset_ids = fq_dataset_ids.tolist()
    
    num_datasets = len(fq_dataset_ids)
    
    if num_datasets == 1:
        st.warning(f"Are you sure you want to delete the selected dataset?")
    else:
        st.warning(f"Are you sure you want to delete {num_datasets} datasets?")
    
    st.error("⚠️ This action cannot be undone!")
    st.write("")
    
    with st.container(horizontal=True, horizontal_alignment='right'):
        
        if st.button('Cancel', key='cancel_delete_datasets'):
            st.rerun()
        
        if st.button('Delete', type='primary', key='confirm_delete_datasets'):
            
            for did in fq_dataset_ids:
                datamanager.delete_fq_dataset(did)
            
            st.cache_data.clear()
            st.rerun()

#region UI Main Fragment
@st.fragment
def uimain(fq_datasets_show, my_projects, reference_project_names_df, reference_dataset_names):
    """Main UI rendering function for datasets page"""

    # Show Toast Cache
    if st.session_state['toast_cache']:
        st.toast(st.session_state['toast_cache'])
        st.session_state['toast_cache'] = None

    # Define Main Container
    with st_yled.container(key='work-ui'):

        st.space(32)

        with st_yled.container(horizontal=True,
                                vertical_alignment='center',
                                horizontal_alignment='distribute',
                                key='datasets-header-container'):

            with st_yled.container(key='datasets-header-left-container',
                                    horizontal=True,
                                    vertical_alignment='center',
                                    horizontal_alignment='left',
                                    gap='small'):

                with st_yled.container(key='datasets-header-title-container',
                                        horizontal=True,
                                        vertical_alignment='center',
                                        horizontal_alignment='left',
                                        gap='small',
                                        width=144):

                    # Create hash for button key
                    if not 'dataset_split_but_hash' in st.session_state:
                        st.session_state['dataset_split_but_hash'] = str(uuid.uuid4())

                    with st.container(key='datasets-header-split-button-container'):

                        split_but = split_button(label='Create',
                                                options=['Update', 'Export', 'Delete'],
                                                icon=':material/add:',
                                                key=f'dataset_split_button-{st.session_state["dataset_split_but_hash"]}')

                    if split_but == 'Create':
                        st.session_state['dataset_split_but_hash'] = str(uuid.uuid4())
                        create_dataset(reference_dataset_names, reference_project_names_df)

                    elif split_but == 'Update':
                        st.session_state['dataset_split_but_hash'] = str(uuid.uuid4())
                        
                        if st.session_state['selected_dataset_enable_edit']:
                            update_dataset(st.session_state['selected_fq_dataset'],
                                         st.session_state['selected_fq_metadata'],
                                         st.session_state['selected_fq_attachments'],
                                         st.session_state['selected_fq_pro_data'],
                                         reference_dataset_names,
                                         reference_project_names_df)
                        
                        else:
                            st.session_state['toast_cache'] = 'Select one or more Datasets to Update'
                            st.rerun()

                    elif split_but == 'Export':
                        st.session_state['dataset_split_but_hash'] = str(uuid.uuid4())
                        export_datasets(st.session_state['selected_dataset_export'])
                        
                        
                    elif split_but == 'Delete':
                        
                        st.session_state['dataset_split_but_hash'] = str(uuid.uuid4())
                        if st.session_state['selected_dataset_enable_delete']:
                            delete_datasets(st.session_state['selected_fq_dataset'])
                        else:
                            st.session_state['toast_cache'] = 'Select one or more Datasets to Delete'
                            st.rerun()


                search_value_fq_datasets = st_yled.text_input("Search Datasets",
                                    help='Search for Datasets',
                                    placeholder='Search Datasets',
                                    key='search_datasets',
                                    label_visibility='collapsed',
                                    border_width=2,
                                    width=256)

                # Search across all columns
                mask = fq_datasets_show.astype(str).apply(lambda x: x.str.contains(search_value_fq_datasets, case=False)).any(axis=1)
                fq_datasets_show = fq_datasets_show[mask]

                # Project filter
                fq_dataset_project_filter = extensions.project_filter_from_df(fq_datasets_show)
                fq_dataset_project_filter = [proj for proj in fq_dataset_project_filter if proj in my_projects['name'].tolist()]
                fq_dataset_project_filter.insert(0, 'No Project')

                # projects_filter = st.multiselect('Filter Projects',
                #                     options=fq_dataset_project_filter,
                #                     help='Filter Projects',
                #                     placeholder='Filter Projects',
                #                     label_visibility='collapsed',
                #                     key='datasets_projects_filter')

                # # Apply project filter
                # if projects_filter:
                #     if 'No Project' in projects_filter:
                #         fq_datasets_show = fq_datasets_show[
                #             (fq_datasets_show['project_names'].apply(lambda x: len(x) == 0)) |
                #             (fq_datasets_show['project_names'].apply(lambda x: any(p in projects_filter for p in x)))
                #         ]
                #     else:
                #         fq_datasets_show = fq_datasets_show[
                #             fq_datasets_show['project_names'].apply(lambda x: any(p in projects_filter for p in x))
                #         ]

                # Store metadata of remaining datasets for filtering
                metadata_select = fq_datasets_show[fq_metadata.columns]
                metadata_select = metadata_select.dropna(axis=1, how='all')

                filter_bg_color = styles.SECONDARY_BACKGROUND_COLOR_DEFAULT
                color = styles.PRIMARY_COLOR

                with st_yled.popover(':material/filter_alt:',
                                key='dataset-metadata-filter-popover',
                                help='Filter Metadata',
                                background_color=filter_bg_color,
                                color=color,
                                font_weight='500',
                                border_style='none',
                                border_width=0,
                                width='content'):

                    with st_yled.container(horizontal=True,
                                            vertical_alignment='center',
                                            horizontal_alignment='left',
                                            gap='small',
                                            key='dataset-metadata-filter-container'):

                        st_yled.markdown('Apply Filter', color=styles.PRIMARY_COLOR, font_size=14)
                        st_yled.button('Reset', icon=':material/filter_alt_off:', on_click=reset_meta_filter_hash)

                    st.multiselect('Filter Projects',
                                    options=fq_dataset_project_filter,
                                    placeholder='',
                                    key=f'fq_dataset_project_filter_{st.session_state["fq_dataset_meta_filter_hash"]}')

                    metadata_options = metadata_select.columns

                    for k in metadata_options:
                        options = sorted(metadata_select[k].dropna().unique().tolist())
                        options = [o for o in options if o != '']
                        st.multiselect(label=f'Filter {k}',
                                        options=options,
                                        key=f'fq_dataset_meta_filter_{st.session_state["fq_dataset_meta_filter_hash"]}_{k}',
                                        placeholder="")

            with st_yled.container(key='datasets-header-right-container',
                                    horizontal=True,
                                    vertical_alignment='center',
                                    horizontal_alignment='right',
                                    gap='small',
                                    width=250):

                st.session_state['show_metadata'] = st_yled.toggle("Show Metadata",
                                                                    color='#808495',
                                                                    font_size=12,
                                                                    value=st.session_state['show_metadata'],
                                                                    key='datasets-show-metadata-toggle')

                if st.session_state.show_details:
                    st.button(':material/unfold_less:',
                                help='Collapse Details Pane',
                                key='datasets-collapse-details',
                                type='tertiary',
                                width='content',
                                on_click=extensions.switch_show_details)
                else:
                    st.button(':material/unfold_more:',
                            help='Expand Details Pane',
                            key='datasets-collapse-details',
                            type='tertiary',
                            width='content',
                            on_click=extensions.switch_show_details)

                if st_yled.button(':material/refresh:',
                            help='Refresh Datasets',
                            key='datasets-refresh',
                            type='tertiary',
                            font_weight='500',
                            font_size='16px',
                            width='content'):

                    on_click = extensions.refresh_page()

        # Define Column Configurations
        col_config_user = {
            'id': st.column_config.NumberColumn('ID', width='small'),
            'name': st.column_config.TextColumn('Name', help='Dataset Name'),
            'project': None,
            'project_names': st.column_config.ListColumn('Projects', help='Projects the Dataset is associated with'),
            'owner_group_name': None,
            'qc_passed': st.column_config.Column('QC Passed', help='Quality Control Passed', width='small'),
            'paired_end': st.column_config.Column('Paired End', help='Paired End Dataset', width='small'),
            'index_read': st.column_config.Column('Index Read', help='Index Read Available', width='small'),
            'created': st.column_config.DateColumn('Created', help='Creation Date'),
            'description': None,
            'owner_username': None,
            'fq_file_r1': None,
            'fq_file_r2': None,
            'fq_file_i1': None,
            'fq_file_i2': None,
            'id_str': None,
            'fq_dataset_id': None,
        }

        col_config_meta = {
            'id': st.column_config.NumberColumn('ID', width='small'),
            'name': st.column_config.TextColumn('Name', help='Dataset Name'),
            'project_names': None,
            'owner_group_name': None,
            'id_str': None
        }

        # Filter by projects filter
        projects_filter = st.session_state[f"fq_dataset_project_filter_{st.session_state['fq_dataset_meta_filter_hash']}"]
        
        if projects_filter:
            if 'No Project' in projects_filter:

                print("No Project Filter")

                fq_datasets_show = fq_datasets_show.loc[
                    (fq_datasets_show['project_names'].apply(lambda x: len(x) == 0)) |
                    (fq_datasets_show['project_names'].apply(lambda x: any(p in projects_filter for p in x)))
                ]
            else:
                fq_datasets_show = fq_datasets_show.loc[
                    fq_datasets_show['project_names'].apply(lambda x: any(p in projects_filter for p in x))
                ]

        # Filter by metadata filter
        fq_datasets_show = extensions.filter_df_by_metadata_filter(fq_datasets_show,
                                                                   filter_session_prefix=f'fq_dataset_meta_filter_{st.session_state["fq_dataset_meta_filter_hash"]}_')

        # Remove those meta cols which are all None
        fq_meta_cols_all_none = fq_datasets_show.loc[:, fq_metadata.columns].isna().all()
        fq_meta_cols_all_none = fq_meta_cols_all_none[fq_meta_cols_all_none].index
        fq_meta_cols_show = list(filter(lambda x: x not in fq_meta_cols_all_none, fq_metadata.columns))

        # Dynamically adjust height of dataframe
        if st.session_state['show_details']:
            if len(fq_datasets_show) < 10:
                fq_df_height = 'content'
            else:
                fq_df_height = 370
        elif len(fq_datasets_show) < 14:
            fq_df_height = 'content'
        else:
            fq_df_height = 500

        # Remove all columns which are all None
        fq_datasets_show = fq_datasets_show.drop(columns=fq_meta_cols_all_none)

        # Define which columns to show, depending on show_metadata toggle
        if st.session_state.show_metadata:
            show_cols = ['id', 'name', 'project_names', 'owner_group_name'] + fq_meta_cols_show
            fq_metadata_col_config = {k: k for k in fq_meta_cols_show}
            col_config_meta.update(fq_metadata_col_config)
            col_config = col_config_meta
        else:
            show_cols = fq_datasets.columns.tolist()
            col_config = col_config_user

        # For formatting, replace None with empty string
        fq_datasets_show = fq_datasets_show.fillna('')
        fq_datasets_show = fq_datasets_show.sort_values(by='id')

        if fq_datasets_show.shape[0] == 0:
            st_yled.info(':material/notifications: No Datasets found. Create new Dataset or adjust filter criteria',
                        border_width="2.0px",
                        border_color="#808495",
                        border_style="solid",
                        color="#808495",
                        key='info-no-samples',
                        width=600)
            # Return early to avoid errors with empty dataframe
            return
        else:
            fq_select = st.dataframe(fq_datasets_show[show_cols],
                                column_config=col_config,
                                selection_mode=['single-cell', 'multi-row'],
                                hide_index=True,
                                on_select='rerun',
                                width='stretch',
                                key='fq_datasets_select_df',
                                height=fq_df_height)

            # Define selected rows from 'rows' and 'cells'
            rows_from_rows = fq_select.selection['rows']
            row_from_cells = [cell[0] for cell in fq_select.selection['cells']]

            if len(rows_from_rows) > 0:
                selection = rows_from_rows
            else:
                selection = row_from_cells

            # Define selected dataset(s)
            if len(selection) == 1:
                
                # Subset projects and metadata to feed into update/details
                # Get index from selection
                select_row = selection[0]
                
                # Get original index from projects overview before subset
                selected_fq_dataset_ix = fq_datasets_show.iloc[[select_row], :].index[0]
                
                fq_dataset_detail = fq_datasets.loc[selected_fq_dataset_ix, :]
                fq_metadata_detail = fq_metadata.loc[selected_fq_dataset_ix, :]
                
                fq_metadata_detail = fq_metadata_detail.dropna().reset_index()
                fq_metadata_detail.columns = ['key', 'value']
                
                update_one = True

                if st.session_state['show_details']:
                    show_project_details = True
                else:
                    show_project_details = False


                fq_dataset_detail_id = fq_dataset_detail['id']
                
                select_fq_dataset_attachments = datamanager.get_fq_dataset_attachments(
                    st.session_state["jwt_auth_header"],
                    fq_dataset_id=fq_dataset_detail_id
                )
                
                select_fq_dataset_pro_data = datamanager.get_fq_dataset_pro_data(
                    st.session_state["jwt_auth_header"],
                    fq_dataset_id=fq_dataset_detail_id
                )
                
                # Would need to only combine with the metadata exactly for the selected dataset
                export_cols = fq_dataset_detail.index.tolist() + fq_metadata_detail['key'].tolist()
                
                fq_export_select = fq_datasets_show.loc[[selected_fq_dataset_ix], :]
                fq_export_select = fq_export_select[export_cols]
                
                st.session_state['dataset_select_id'] = fq_dataset_detail_id
                st.session_state['selected_fq_dataset'] = fq_dataset_detail
                st.session_state['selected_fq_metadata'] = fq_metadata_detail
                st.session_state['selected_fq_attachments'] = select_fq_dataset_attachments
                st.session_state['selected_fq_pro_data'] = select_fq_dataset_pro_data
                st.session_state['selected_dataset_enable_edit'] = True
                st.session_state['selected_dataset_enable_delete'] = True
                st.session_state['selected_dataset_export'] = fq_export_select
                
                
            elif len(selection) > 1:
                select_row = selection
                
                # Get original index from projects overview before subset
                selected_fq_dataset_ix = fq_datasets_show.iloc[select_row, :].index
                
                # Get fq datasets and associated metadata
                fq_dataset_detail = fq_datasets.loc[selected_fq_dataset_ix, :]
                fq_metadata_detail_many = fq_metadata.loc[selected_fq_dataset_ix, :]
                
                show_project_details = False
                
                # Remove all columns which are all None
                fq_metadata_detail_many = fq_metadata_detail_many.dropna(axis=1, how='all')
            
                fq_export_select = pd.concat([fq_dataset_detail, fq_metadata_detail_many], axis=1)
                
                st.session_state['dataset_select_id'] = None

                st.session_state['selected_fq_dataset'] = fq_dataset_detail
                st.session_state['selected_fq_metadata'] = None
                st.session_state['selected_fq_attachments'] = None
                st.session_state['selected_fq_pro_data'] = None

                st.session_state['selected_dataset_enable_edit'] = False
                st.session_state['selected_dataset_enable_delete'] = True

                st.session_state['selected_dataset_export'] = fq_export_select

            else:
                show_project_details = False
                
                fq_dataset_detail = None
                fq_metadata_detail = None
                
                fq_dataset_update = None
                fq_metadata_update = None
                
                fq_export_select = fq_datasets_show
                
                st.session_state['dataset_select_id'] = None
                st.session_state['selected_fq_dataset'] = None
                st.session_state['selected_fq_metadata'] = None
                st.session_state['selected_fq_attachments'] = None
                st.session_state['selected_fq_pro_data'] = None
                st.session_state['selected_dataset_enable_edit'] = False
                st.session_state['selected_dataset_enable_delete'] = False

                st.session_state['selected_dataset_export'] = fq_export_select


            if show_project_details:

                st_yled.space(72)
                
                segment_control_options = ['Features', 'Projects', 'Attachments', 'ProData']
                segment_default = segment_control_options[st.session_state['fq_details_segment_ix']]
                
                dataset_detail_selection = st.segmented_control(
                        'Dataset Detail Selection',
                        segment_control_options,
                        key='dataset_detail_selection',
                        default=segment_default,
                        label_visibility='collapsed',
                        on_change=update_segment_default,
                        args=(segment_control_options,)
                    )
                
                # Detail views will be rendered here by the existing code below
                # (Features, Projects, Attachments, ProData sections)
                if dataset_detail_selection == 'Features':
                    
                    with st_yled.container(key='project-features-detail-container',
                                            horizontal=True,):

                        with st_yled.container(key='project-features-detail-columns-container',
                                            width=400,
                                            background_color=styles.DATAFRAME_HEADER_BG_COLOR):

                            fq_dataset_id = fq_dataset_detail['id']
                            fq_dataset_name = fq_dataset_detail['name']
                            fq_dataset_description = fq_dataset_detail['description']
                            fq_dataset_created = fq_dataset_detail['created'].strftime('%Y-%m-%d %H:%M')
                            
                            fq_file_r1_id = fq_dataset_detail.pop('fq_file_r1')
                            fq_file_r2_id = fq_dataset_detail.pop('fq_file_r2')
                            fq_file_i1_id = fq_dataset_detail.pop('fq_file_i1')
                            fq_file_i2_id = fq_dataset_detail.pop('fq_file_i2')
                            
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


                            with st_yled.container(horizontal=True):

                                if st.button('Read 1',
                                            disabled = read1_but_disabled,
                                            help = 'Read 1 FASTQ Details'):
                                    detail_fq_file(fq_file_r1_id)
                                
                                if st.button('Read 2',
                                    disabled = read2_but_disabled,
                                    help = 'Read 2 FASTQ Details'):
                                    
                                    detail_fq_file(fq_file_r2_id)

                                if not index1_but_disabled:
                                    if st.button('Index 1', help = 'Index Read 1 FASTQ Details'):
                                        detail_fq_file(fq_file_i1_id)
                                
                                if not index2_but_disabled:

                                    if st.button('Index 2',
                                        disabled = index2_but_disabled,
                                        help = 'Index Read 2 FASTQ Details'):
                                        
                                        detail_fq_file(fq_file_i2_id)

                            with st_yled.container(horizontal=True,
                                                background_color='#FFFFFF',
                                                width='content',
                                                key='dataset-features-detail-id'):
                                
                                st.markdown('Dataset ID', width='content')
                                st.markdown(f'{fq_dataset_id}', width='content')

                            
                            with st_yled.container(horizontal=True,
                                                background_color='#FFFFFF',
                                                width='content',
                                                key='dataset-features-detail-name'):
                                
                                st.markdown('Dataset Name', width='content')
                                st.markdown(f'{fq_dataset_name}', width='content')


                            with st_yled.container(horizontal=True,
                                                background_color='#FFFFFF',
                                                width='content',
                                                key='dataset-features-detail-created'):
                                
                                st.markdown('Created', width='content')
                                st.markdown(f'{fq_dataset_created}', width='content')


                            with st_yled.container(background_color='#FFFFFF',
                                                width='content',
                                                key='dataset-features-detail-description'):
                                
                                st.markdown('Description', width='content')
                                st.markdown(f'{fq_dataset_description}', width='content')


                        with st_yled.container(key='project-features-detail-metadata-container',
                                                width=300,
                                                border=True):
                                
                            st_yled.markdown('Metadata', font_weight=500)
                            
                            if fq_metadata_detail.shape[0] == 0:
                                st_yled.info(':material/notifications: No metadata set. Define in Update Project',
                                            border_width="2.0px",
                                            border_color="#808495",
                                            border_style="solid",
                                            color="#808495",
                                            key='info-no-samples-metadata',
                                            width=400)
                            else:
                                st.dataframe(fq_metadata_detail,
                                            use_container_width = True,
                                            hide_index = True,
                                            column_config = {
                                                'key' : st.column_config.Column('Key'),
                                                'value' : st.column_config.Column('Value'),
                                            },
                                            key='metadata_details_df')

                if dataset_detail_selection == 'Projects':
                    
                    with st.container(border = True, width=550):
                        
                        st_yled.markdown("Overview of Projects assigned to the Dataset", font_size=12, color='#808495')
                        st.write("")
                        
                        # Get prject information here: my_projects    
                            
                        project_ids = fq_dataset_detail['project']
                        dataset_projects_detail = my_projects.loc[my_projects['id'].isin(project_ids),['id', 'name', 'description']]
                        
                        # Get ID, Name and Description of all projects
                        if dataset_projects_detail.shape[0] == 0:
                            st_yled.info(':material/notifications: Dataset is not assigned to any Project',
                                        border_width="2.0px",
                                        border_color="#808495",
                                        border_style="solid",
                                        color="#808495",
                                        key='info-no-samples-datasets',
                                        width=480)
                    
                        else:

                            # Limit Max Height of Dataframe
                            if dataset_projects_detail.shape[0] > 7:
                                max_df_height = 315
                            else:
                                max_df_height = 'content'
                            
                            st.dataframe(dataset_projects_detail,
                                            hide_index = True,
                                            column_config = {
                                                'id' : st.column_config.TextColumn('ID', width='small'),
                                                'name' : st.column_config.TextColumn('Name'),
                                                'description' : st.column_config.TextColumn('Description')
                                            },
                                            key='fq_dataset_projects_df',
                                            height = max_df_height)
                    
                if dataset_detail_selection == 'Attachments':
                    
                    with st.container(border = True, width=450):
                        
                        select_dataset_id = st.session_state['dataset_select_id']
                        
                        # Value is none if not run
                        download_fq_attach_key_name = f'download_fq_attachments_select_{select_dataset_id}'
                        
                        if download_fq_attach_key_name in st.session_state:
                            fq_attach_select = st.session_state[download_fq_attach_key_name]
                        else:
                            fq_attach_select = None

                        with st_yled.container(horizontal=True, horizontal_alignment='right'):
                            
                            st_yled.markdown("Overview of File Attachments", font_size=12, color='#808495')

                            # Provide download button if attachment was selected
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
                                st.button('Download',
                                        disabled = True,
                                        help = 'Select an attachment to download',
                                        key='download_attachment')
                        
                        if select_fq_dataset_attachments.shape[0] == 0:
                            
                            st_yled.info(':material/notifications: No Attachments for the Project. Add Attachments in Update Project',
                                        border_width="2.0px",
                                        border_color="#808495",
                                        border_style="solid",
                                        color="#808495",
                                        key='info-no-attachments',
                                        width=400)

                        else:

                            # Limit Max Height of Dataframe
                            if select_fq_dataset_attachments.shape[0] > 7:
                                max_df_height = 315
                            else:
                                max_df_height = 'content'
                            
                            st.dataframe(select_fq_dataset_attachments,
                                        hide_index = True,
                                        column_config = {
                                            'id' : None,
                                            'name' : st.column_config.TextColumn('Name'),
                                            'description' : None,
                                            'fq_dataset_id' : None},
                                        on_select = update_attachment_select,
                                        selection_mode='single-row',
                                        key='fq_attachment_details_df',
                                        height = max_df_height)

                if dataset_detail_selection == 'ProData':
                    
                    with st.container(border = True, width=450):
                        
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
                        
                        with st_yled.container(horizontal=True, horizontal_alignment='right'):
                        
                            st_yled.markdown("Overview of Processed Data", font_size=12, color='#808495')
                        
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
                        

                        if select_fq_dataset_pro_data.shape[0] == 0:
                            
                            st_yled.info(':material/notifications: No Processed Data for the Dataset',
                                        border_width="2.0px",
                                        border_color="#808495",
                                        border_style="solid",
                                        color="#808495",
                                        key='info-no-prodata',
                                        width=400)
                        else:
                            # Limit Max Height of Dataframe
                            if select_fq_dataset_pro_data.shape[0] > 7:
                                max_df_height = 260
                            else:
                                max_df_height = 'content'
                            
                            st.dataframe(select_fq_dataset_pro_data,
                                        hide_index = True,
                                        use_container_width = True,
                                        column_config = {
                                            'id' : st.column_config.TextColumn('ID'),
                                            'name' : st.column_config.TextColumn('Name'),
                                            'data_type' : st.column_config.TextColumn('Type'),
                                            'description' : None,
                                            'version' : st.column_config.TextColumn('Version'),
                                            'owner_username' : None,
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

fq_dataset_project_filter = extensions.project_filter_from_df(fq_datasets)
fq_dataset_project_filter = [proj for proj in fq_dataset_project_filter if proj in my_project_names.tolist()]
fq_dataset_project_filter.insert(0, 'No Project')

# Reference project names 
reference_project_names_df = project_owner_group[['id', 'name', 'dataset_metadata_keys']]
# Subset dataset names those that are in the owner group
reference_dataset_names = fq_datasets.loc[
    fq_datasets['owner_group_name'] == st.session_state['owner_group'],'name'
    ]

# Add id string for search
fq_datasets['id_str'] = fq_datasets['id'].astype(str)

# Add metadata
fq_datasets_show = pd.concat([fq_datasets, fq_metadata], axis=1)

# Render UI
uimain(fq_datasets_show, my_projects, reference_project_names_df, reference_dataset_names)

