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


def show_updated(ix):
    
    change = st.session_state[f"fq_sd_{ix}"]
    edited = change['edited_rows']
    st.session_state['update_field_state'] = (ix, edited)

def update_staging_mode():
    
    dataset_select_name = st.session_state['select_preexist_dataset']
    
    if not dataset_select_name is None:
        st.session_state['preexist_dataset_name'] = dataset_select_name
    else:
        del st.session_state['preexist_dataset_name']
    
    
# Print Info about User
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

# region Check In
@st.dialog('Check In Dataset', width='large')
def checkin_df(fq_file_df: pd.DataFrame,
               projects_owner_group: pd.DataFrame,
               fq_datasets_empty: pd.DataFrame,
               reference_fq_dataset_names: pd.Series):
    
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()
    
    empty_dataset_names = fq_datasets_empty['name'].tolist()
    
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
        st.error("Please set Read type (R1, R2, I1, I2) of ALL FASTQ files.")
    elif fq_file_df['read_type'].duplicated().any():
        st.error("Read types must be unique for each dataset. Do not use duplicate R1 or R2 entries.")
    else:
        name_old = fq_file_df['dataset'].iloc[0]
        
        # Dynamically get dataset from backend
        col_n_1, col_n_2 = st.columns([9, 3], vertical_alignment='bottom')
        
        update_view = False
        
        with col_n_1:
            if 'preexist_dataset_name' in st.session_state:
                display_name = st.session_state['preexist_dataset_name']
                create_mode = False
            else:
                display_name = name_old
                create_mode = True
            
            name = st.text_input("Dataset Name",
                                value=display_name,
                                key='dataset_name',
                                help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')
        
        with col_n_2:
            
            if len(empty_dataset_names) > 0:
            
                with st.popover('Select Existing', use_container_width=True):
                    existing_dataset_select = st.selectbox('Select Existing',
                                                        options=empty_dataset_names,
                                                        index=None,
                                                        label_visibility = 'collapsed',
                                                        key = 'select_preexist_dataset',
                                                        on_change = update_staging_mode)        
        
        # region Project Tab
        tab_names = [read_long_map[rt] for rt in read_types]
        fq_file_names = ['NA'] * len(read_types)
        
        if create_mode:
            
            tab_names_format = [":blue-background[**Projects**]",
                                ":blue-background[**Features**]",
                                ":blue-background[**Attachments**]"]
            tab_names_format.extend([f":blue-background[**{tn}**]" for tn in tab_names])
            reads_offset = 3
            
            # Add Metadata and Attachments Tabs
            tabs = st.tabs(tab_names_format)
            
            with tabs[0]:
                
                with st.container(border=True, height=460):
                    
                    st.subheader('Projects')
                    
                    st.write('Attach the dataset to one or more projects')
                    
                    project_names_select = st.multiselect("Select Projects",
                            sorted(projects_owner_group['name'].unique()),
                            help = 'Attach the dataset to project(s).')
            
            # region Metadata Tab
            with tabs[1]:
                
                with st.container(border=True, height=460):
                    
                    # Get metadata keys for selected projects
                    # Metadata keys are stored as dicts in dataframe
                    # Extract keys and flatten
                    metadata_keys = projects_owner_group.loc[
                        projects_owner_group['name'].isin(project_names_select),'dataset_metadata_keys'].to_list()
                    metadata_keys = [list(m.keys()) for m in metadata_keys]
                    metadata_keys = itertools.chain.from_iterable(metadata_keys)
                    metadata_keys = sorted(list(set(metadata_keys)))
                    
                    metadata_df_template = pd.DataFrame({
                        'key' : metadata_keys,
                        'value' : ''
                    })
                    
                    st.subheader('Dataset Description')
                    
                    description = st.text_area("Enter Dataset Description",
                                    help = 'Description of the FASTQ Dataset.',)

                    st.subheader('Metadata',
                        help = "Key-value pairs to store and group dataset metadata. For example 'species' : 'human'")

                    metadata_df_template = metadata_df_template.astype(str)
                    metadata_df = st.data_editor(
                        metadata_df_template,
                        use_container_width=True,
                        hide_index=True,
                        column_config = {
                            'key' : st.column_config.TextColumn('Key'),
                            'value' : st.column_config.TextColumn('Value')
                        },
                        num_rows ='dynamic',
                        key = 'create_metadata_df'
                    )

            # region Projects Tab
            with tabs[2]:
                
                with st.container(border=True, height=460):
                    
                    st.subheader('Attachments')
                    
                    st.write('Upload attachments for the dataset')
                    
                    uploaded_files = st.file_uploader("Choose Files to Upload",
                        help = "Upload attachments for the dataset. Attachments can be any file type",
                        accept_multiple_files = True)
        
        else:
            tab_names_format = [f":blue-background[**{tn}**]" for tn in tab_names]
            tabs = st.tabs(tab_names_format)
            reads_offset = 0
            
        for ix, rt in enumerate(read_types):
            
            # region Read Tab
            with tabs[reads_offset+ix]:
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    
                    with st.container(border=True, height=460):
                        
                        st.subheader('FASTQ Stats')
                        
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
                        
                        fq_file_id.index = ['FASTQ File']
                        
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
                                        
                        fq_file_names[ix] = st.text_input("FASTQ File Name", value=fq_file_name_old, key=f'fq_name_{ix}')
                        
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
        _, col = st.columns([9,3])    
        with col:
            if st.button('Confirm', key='confirm_checkin', type = 'primary', use_container_width=True):
                
                checkin_complete = False
                
                if create_mode:
                    
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
                    if name == '':
                        st.error("Please enter a Dataset Name.")
                    elif name.lower() in reference_fq_dataset_names:
                        st.error("Dataset name already exists in Group. Please choose another name.")
                    elif not extensions.validate_charset(name):
                        st.error('Dataset Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                    else:
                        # 2) Second check for fq file names
                        for v in read_fq_map.values():
                            if not extensions.validate_charset(v['name']):
                                st.error('FASTQ Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                                break
                            if v['name'] == '':
                                st.error("Please enter a FASTQ File Name")
                                break
                        else:
                            # 3) Third check for metadata
                            for k, v in zip(keys, values):
                                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                                    st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces.')
                                    break
                                if k in uiconfig.METADATA_RESERVED_KEYS:
                                    st.error(f'Metadata key {k}: Reserved keyword, please choose another key')
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
                                    name = name,
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
                            st.error('FASTQ Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
                            break
                        if v['name'] == '':
                            st.error("Please enter a FASTQ File Name")
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
                    st.cache_data.clear()
                    st.rerun()
                
        
# region Batch Check In
@st.dialog('Batch Check In Datasets', width='large')
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
    
    na_in_read_types_warning = False
    duplicated_read_types_warning = False
    dataset_exists_warning = False
    empty_dataset_name_warning = False
    invalid_dataset_chars_warning = False
    invalid_fq_file_name_warning = False
    empty_fq_file_name_warning = False
    
    for dataset, fq_files in fq_files_staging_datasets:
        
        read_types = fq_files['read_type'].unique()
        read_types = sorted(read_types)
        
        # Check if NA is in read types
        if 'NA' in read_types:
            if not na_in_read_types_warning:
                st.warning('Datasets Excluded: NA in read types')
                na_in_read_types_warning = True
            continue # consider warning
        
        # Check if read types are unique
        elif fq_files['read_type'].duplicated().any():
            if not duplicated_read_types_warning:
                st.warning('Datasets Excluded: Duplicated read types')
                duplicated_read_types_warning = True
            continue
        
        # Check if dataset name is no yet used and adreres to naming conventions
        elif dataset.lower() in reference_fq_dataset_names:
            
            # Check if dataset is empty
            if not dataset.lower() in empty_dataset_names:                       
                if not dataset_exists_warning:
                    st.warning('Datasets Excluded: Dataset with identical name exists')
                    dataset_exists_warning = True
                continue
        
        # Empty dataset name
        elif dataset == '':
            if not empty_dataset_name_warning:
                st.warning('Datasets Excluded: Dataset Name Empty')
                empty_dataset_name_warning = True    
            continue
        
        # Check if characters in dataset are valid
        elif not extensions.validate_charset(dataset):
            if not invalid_dataset_chars_warning:
                st.warning('Datasets Excluded: Invalid Dataset Name')
                invalid_dataset_chars_warning = True
            continue
        
        # Check if fq file names are valid
        elif not all([extensions.validate_charset(fq) for fq in fq_files['name']]):
            if not invalid_fq_file_name_warning:
                st.warning('Datasets Excluded: Invalid Fastq File Name')
                invalid_fq_file_name_warning = True
            continue
        
        elif not all([fq != '' for fq in fq_files['name']]):
            if not empty_fq_file_name_warning:
                st.warning('Datasets Excluded: Empty Fastq File Name')
                empty_fq_file_name_warning = True
            continue
        
        # Check if fq file names are not empty
        valid_datasets[dataset] = fq_files
    
    num_valid_datasets = len(valid_datasets)
    valid_dataset_names_df = pd.DataFrame({'name' : list(valid_datasets.keys())})
    
    st.write(f"Valid Datasets for Check In **{num_valid_datasets}/{total_input_datasets}**")
    
    if num_valid_datasets > 0:
        
        # Overview of valid datasets

        if 'available_staging' not in st.session_state:
            st.session_state['available_staging'] = valid_dataset_names_df
            #st.session_state['available_staging_input'] = fq_datasets_avail['id'].tolist()
            
        if 'selected_staging' not in st.session_state:
            st.session_state['selected_staging'] = pd.DataFrame(columns=['name'])
            #st.session_state['selected_staging_input'] = pd.DataFrame(columns=['name'])

        @st.fragment
        def update_select_form_fq_datasets():               
            
            col1, col2, col3 = st.columns([5.5,1,5.5])
            
            # First col to select available datasets
            with col1:
                
                with st.container(border = True):
                    
                    st.write('Available Datasets')
                                
                    datasets_available = st.session_state['available_staging']
                    
                    search_value_fq_ds = st.text_input("Search Datasets",
                                    help = 'Search in available Datasets',
                                    placeholder='Search Available Datasets',
                                    key = 'update_search_fq_datasets_staging',
                                    label_visibility = 'collapsed')
                                    
                    fq_datasets_show = datasets_available.loc[
                        datasets_available['name'].str.contains(search_value_fq_ds, case=False) 
                    ]
                    
                    fq_avail_df = st.dataframe(fq_datasets_show,
                                                use_container_width=True,
                                                hide_index = True,
                                                column_config = {
                                                    'name' : st.column_config.Column('Name'),
                                                },
                                                key='update_datasets_df_staging',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')

            # Column with selected datasets
            with col3:
                with st.container(border = True):              
                    
                    st.write('Selected Datasets')
                    
                    datasets_selected = st.session_state['selected_staging']
                    
                    search_value_fq_ds_select = st.text_input("Search Datasets",
                                                            help = 'Search in Selected Datasets',
                                                            placeholder='Search Selected Datasets',
                                                            key = 'update_search_attached_fq_datasets_staging',
                                                            label_visibility = 'collapsed')
                                    
                    fq_datasets_select_show = datasets_selected.loc[
                            datasets_selected['name'].str.contains(search_value_fq_ds_select, case=False) 
                        ]
                    
                    fq_select_df = st.dataframe(fq_datasets_select_show,
                                                use_container_width=True,
                                                hide_index = True,
                                                column_config = {
                                                    'name' : st.column_config.TextColumn('Name'),
                                                },
                                                key='update_datasets_select_df_staging',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')

                with col2:
                    
                    # CONTINUE HERE
                    
                    # Spacer Container
                    st.container(height = 100, border = False)
                    st.button(':material/arrow_forward:', use_container_width=True, type='primary', on_click=add_selected_datasets, args = (fq_datasets_show, fq_avail_df.selection['rows']))
                    st.button(':material/arrow_back:', use_container_width=True, type='primary', on_click=remove_selected_datasets, args = (fq_datasets_select_show, fq_select_df.selection['rows']))
            

        update_select_form_fq_datasets()
                
        st.write('Attach datasets to one or more projects')
                    
        project_names_select = st.multiselect("Select Projects",
                sorted(projects_owner_group['name'].unique()),
                help = 'Attach the dataset to project(s).')
                
        # region Check In Button  
        _, col = st.columns([9,3])    
        with col:
            if st.button('Confirm', key='confirm_bulk_checkin', type = 'primary', use_container_width=True):
                
                selected_datasets = st.session_state['selected_staging']
                selected_datasets = selected_datasets['name'].tolist()
                                
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
                del st.session_state['available_staging']
                del st.session_state['selected_staging']
                st.cache_data.clear()
                st.rerun()
    
    
def delete_fastq_files(fq_file_ids: List[int]):
    for fq_file_id in fq_file_ids:
        datamanager.delete_fq_file(fq_file_id)
    
    del st.session_state['fq_data_staging']
    st.cache_data.clear()
    st.rerun()  

@st.dialog('Delete All Staged FASTQ Files', width='medium')
def bulk_delete_fq_files(fq_file_ids: List[int]):
    num_files = len(fq_file_ids)
    st.warning(f'Confirm deletion of {num_files} staged FASTQ Files.')
    
    if st.button('Confirm Delete', key='confirm_delete', type='primary'):
        delete_fastq_files(fq_file_ids)

#region Import FASTQ from file

@st.dialog('Import FASTQ from File', width='large')
def import_from_file():

    # Upload File
    
    upload_template = st.file_uploader("**Upload Template File**",
                                        help = "Upload a template file to import FASTQ files.",
                                        type = ['.csv', '.xlsx'],
                                        accept_multiple_files = False)
           
    if upload_template:
        if upload_template.name.endswith('.csv'):
            try:
                upload_template = pd.read_csv(upload_template, header=0)
            except pd.errors.EmptyDataError:
                st.error('No data found in template file .csv file')
                return
        elif upload_template.name.endswith('.xlsx'):
            try:
                upload_template = pd.read_excel(upload_template, header=0)
            except pd.errors.EmptyDataError:
                st.error('No data found in template file .excel file')
                return
        else:
            st.error('Please upload a valid CSV or Excel file.')
            return
        
        if not upload_template.shape[1] == 3:
            st.error('Invalid number of columns in template file. Please use FASTQFileName, ReadType, UploadPath')
            return
        if upload_template.shape[0] == 0:
            st.error('No FASTQ files found in template file')
            return
        
        # Check if sufficient space in queue    

        # Get number of fq files in queue
        num_queue_jobs = datamanager.get_fq_queue_jobs(st.session_state["jwt_auth_header"])
        max_jobs_queue = uiconfig.BACKEND_MAX_QUEUE_SIZE
        max_allowed_jobs = max_jobs_queue - num_queue_jobs
        
        if upload_template.shape[0] > max_allowed_jobs:
            st.error(f'Not enough space in jobs queue. Maximum allowed files for upload: {max_jobs_queue}')
            st.error(f'Currently running jobs: {num_queue_jobs}')
            return
                
        # Check column names
        if not all(upload_template.columns == ['FASTQFileName', 'ReadType', 'UploadPath']):
            st.error('Invalid column names in template file. Please use FASTQFileName, ReadType, UploadPath')
        if not upload_template['ReadType'].isin(['R1', 'R2', 'I1', 'I2']).all():
            st.error('Invalid ReadType in template file. Please use only R1, R2, I1, I2')
        else:
            # Validate FASTQ File Names
            for fq_name in upload_template['FASTQFileName']:
                
                if (fq_name == '') or (pd.isna(fq_name)):
                    st.error('Empty FASTQ name found')
                    break
                elif not extensions.validate_charset(fq_name):
                    st.error('Error in FASTQ name found. Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces')
                    break
            else:
                with st.container(border=True):
                    st.write('**FASTQ Files to Import**')

                    st.dataframe(upload_template,
                                use_container_width=True,
                                column_config = {
                                    'FASTQFileName' : st.column_config.TextColumn('FASTQ File Name'),
                                    'ReadType' : st.column_config.TextColumn('Read Type'),
                                    'UploadPath' : st.column_config.TextColumn('Upload Path')
                                })

    cols = st.columns([4,5,3])
    
    with cols[0]:
        with st.popover('Download Templates'):
            
            excel_template_path = os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/readstore_upload_template.xlsx")
            csv_template_path = os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/readstore_upload_template.csv")
            
            excel_template = open(excel_template_path, 'rb').read()
            csv_template = open(csv_template_path, 'rb').read()

            st.download_button('Download Excel Template',
                               excel_template,
                               'readstore_template.xlsx',
                               help='Download a template Excel file to import FASTQ files.',
                               use_container_width=True)
            st.download_button('Download .csv Template',
                               csv_template,
                               'readstore_template.csv',
                               help='Download a template CSV file to import FASTQ files.',
                               use_container_width=True)
    
    with cols[2]:
        if st.button('Confirm', key='confirm_import_fastq', type='primary', use_container_width=True):
            
            if not upload_template is None:
                for ix, row in upload_template.iterrows():
                    res = datamanager.submit_fq_queue_job(
                            st.session_state["jwt_auth_header"],
                            row['FASTQFileName'],
                            row['UploadPath'],
                            row['ReadType']
                    )
                    
                    if res.status_code != 200:
                        st.warning(f"Error with file {row['FASTQFileName']} \n {res.json()['detail']} \n Quit Import")
                        break
                else:        
                    st.cache_data.clear()
                    st.rerun()

@st.dialog('Help')
def staging_help():
    
    st.markdown("ReadStore groups **Dataset**s based on the filename of each **FASTQ** file.\n")
    st.markdown("The **Read** type is also infered. [Read1/R1, Read2/R2, Index1/I1, Index2/I2]\n")
                
    st.markdown("Click *Check In* to validate and register the **Dataset**s \n")
    
    st.markdown("If the infered **Datasets** are not correct, you can change the name in the Dataset columns below.\n")
    st.markdown("Also the **Read** type can be changed by clicking the column blow.\n")
    
    st.link_button('Manual in ReadStore Blog', 'https://evo-byte.com/readstore-tutorial-uploading-staging-fastq-files/')


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
fq_dataset_empty = datamanager.get_fq_dataset_empty(st.session_state["jwt_auth_header"])

projects_owner_group = datamanager.get_project_owner_group(st.session_state["jwt_auth_header"])[['id', 'name', 'dataset_metadata_keys']]

# Get number of running jobs in QC queue
num_jobs = datamanager.get_fq_queue_jobs(st.session_state["jwt_auth_header"])

#region UI
    
col_config = {
        'id' : None,
        'dataset' : st.column_config.TextColumn('Dataset', help="Each Dataset Combines Read Files for Sample"),
        'name' : st.column_config.TextColumn('FASTQ', help="Name of FASTQ File"),
        'read_type' : st.column_config.SelectboxColumn('Read', width ="small", options = ['R1', 'R2', 'I1', 'I2'], help = "Read or Index Type (R1, R2, I1, I2)", required =True),
        'created' : st.column_config.DateColumn('Created', width ='small', disabled = True),
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

if fq_files_staging.shape[0] > 0:

    col1s, col2s, col3s, col4s = st.columns([4.5, 4.5, 2.25, 0.75], vertical_alignment='center')
    
    with col1s:
        st.info(f"{len(fq_files_staging)} FASTQ files waiting for Check In.")
    
    with col2s:
        with st.container(border=True):
             st.write(str(num_jobs), ' Jobs in QC Queue')
    
    with col3s:
        with st.popover('More', use_container_width=True):
            
            if st.button('Import From File', use_container_width=True, type='primary'):
                import_from_file()
            
            if st.button('Batch Check In', use_container_width=True, type='primary'):
                bulk_checkin_df(fq_files_staging,
                                projects_owner_group,
                                fq_dataset_empty,
                                fq_dataset_names_owner_group)
                
            if st.button(':material/delete_forever: Delete All', use_container_width=True, type='primary'):
                fq_file_ids_stage = fq_files_staging['id'].tolist()
                bulk_delete_fq_files(fq_file_ids_stage)
            
            if st.button(':material/help: Help', use_container_width=True, type='primary'):
                staging_help()
            
    with col4s:
        if st.button(':material/refresh:',
                     key='refresh_projects',
                     help='Refresh Page',
                     type='tertiary',
                    use_container_width = True):
            if 'fq_data_staging' in st.session_state:
                del st.session_state['fq_data_staging']
            extensions.refresh_page()
    
    coln, _ = st.columns([10, 2])
    
    with coln:
        search_value_fastq = st.text_input("Search FASTQ",
                                help = 'Search FASTQ Files and Datasets',
                                placeholder='Search FASTQ',
                                key = 'search_fastq',
                                label_visibility = 'collapsed')
    
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
    
    for ix, fq_file_df in enumerate(fq_files_staging_split_show):
        
        st.divider()
            
        col1, col2 = st.columns([1.5, 10.5], vertical_alignment='center')
        
        with col1:
            if st.button("Check In", key=f"checkin_{ix}", type = 'primary', help='Validate and Register Dataset'):
                
                if 'preexist_dataset_name' in st.session_state:
                    del st.session_state['preexist_dataset_name']
                
                checkin_df(fq_file_df,
                        projects_owner_group,
                        fq_dataset_empty,
                        fq_dataset_names_owner_group)
            
            with st.popover(':material/delete_forever:', help="Delete FASTQ Files"):
                    if st.button('Confirm Delete', key=f"delete_ok_{ix}", use_container_width=True):
                        
                        fq_file_ids = fq_file_df['id'].tolist()
                        delete_fastq_files(fq_file_ids)
        with col2:
            if 'update_field_state' in st.session_state:
                field_ix, edited = st.session_state['update_field_state']
                if field_ix == ix:
                    df_ix = list(edited.keys())[0]
                    col = list(edited[df_ix].keys())[0]
                    val = edited[df_ix][col]
                    
                    fq_file_df[col].iloc[df_ix] = val
                    do_rerun = True
                          
                    del st.session_state['update_field_state']
            
            df_set = st.data_editor(fq_file_df,
                            hide_index=True,
                            key=f"fq_sd_{ix}",
                            column_config=col_config,
                            on_change=show_updated,
                            args=(ix,))
                        
            # List of (displayed) datasets
            fq_files_staging_update.append(df_set)

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
        
        st.divider()
        
        # If there are more fastq files to show, display a button to show more
        if len(fq_files_staging_split_left) > 0:
            
            _, col_more, _ = st.columns([5, 2, 5])
            with col_more:    
                if st.button('More', key='more_fq_data_staging', help='Show More FASTQ Files', use_container_width=True, type='primary'):
                    st.session_state['num_fq_data_staging_staging'] = num_fq_data_staging_staging + 10                    
                    st.rerun()

else:
    col1f, col2f, col3f, col4f = st.columns([4.5, 4.5, 2.25, 0.75], vertical_alignment='center')
    
    with col1f:
        st.success("No FASTQ Files to Check In.", icon=":material/check:")
    
    with col2f:
        with st.container(border=True):
            st.write(str(num_jobs), ' Jobs in QC Queue')
    
    with col3f:
        with st.popover('More', use_container_width=True):
            
            if st.button('Import From File', use_container_width=True, type='primary'):
                import_from_file()
            
            st.button('Batch Check In', use_container_width=True, type='primary', disabled=True)
            
            st.button(':material/delete_forever: Delete All', use_container_width=True, type='primary', disabled=True)
            
            if st.button(':material/help: Help', use_container_width=True, type='primary'):
                staging_help()
            
    with col4f:
        if st.button(':material/refresh:',
                     key='refresh_projects',
                     help='Refresh Page',
                     type='tertiary',
                     use_container_width = True):
            if 'fq_data_staging' in st.session_state:
                del st.session_state['fq_data_staging']
            extensions.refresh_page()
