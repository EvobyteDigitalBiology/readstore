# readstore-basic/frontend/streamlit/app_pages/dataset.py

from typing import List
import time
import uuid
import string
import json
import copy
import webbrowser
import itertools

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


#region Update Dataset

@st.dialog('Update Dataset', width='large')
def update_dataset(selected_fq_dataset: pd.DataFrame,
                   selected_fq_metadata: pd.DataFrame,
                   selected_fq_attachments: pd.DataFrame,
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
                        ":blue-background[**Attachments**]"]
    tab_names_format.extend([f":blue-background[**{tn}**]" for tn in tab_names])
    fq_file_names = [None] * len(read_file_file_map)
    
    # Add Metadata and Attachments Tabs
    tabs = st.tabs(tab_names_format)
    
    # region Projects Tab
    with tabs[0]:
        
        with st.container(border=True, height=395):
            
            st.subheader('Projects')

            project_options = sorted(reference_project_names_df['name'])
            st.write('Attach the Dataset to Group Projects.')
            
            projects_default = fq_dataset_project_names
            
            project_names_select = st.multiselect("Select Projects",
                    project_options,
                    projects_default,
                    help = 'Attach the dataset to project(s).')

        coldel, _ = st.columns([4,8])
        
        with coldel:
            with st.expander('Delete Dataset', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_fq_dataset'):
                    
                    # Delete Fq Files attached to Dataset
                    # Dataset will automatically be deleted through cascade
                    for v in read_file_file_map.values():
                        datamanager.delete_fq_file(v.id)
                    
                    st.cache_data.clear()
                    st.rerun()
            
    # region Metadata Tab        
    with tabs[1]:
        
        with st.container(border=True, height=460):
            
            st.subheader('Dataset Description')
            
            description = st.text_area("Enter Dataset Description",
                                        help = 'Description of the FASTQ Dataset.',
                                        value = fq_dataset_description_old)
            
            st.subheader('Metadata',
                help = "Key-value pairs to store and group dataset metadata. For example 'species' : 'human'")
            
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
    
    
    # region Attachment Tab
    with tabs[2]:
        
        with st.container(border=True, height=460):
            
            # List all attachments
            
            st.subheader('Attachments')
            
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
                                    on_select = 'rerun')
            
            st.write('Upload attachments for the dataset.')
            
            uploaded_files = st.file_uploader("Choose Files to Upload",
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
                            st.rerun()
            
    for ix, rt in enumerate(read_file_file_map.keys()):
        
        # region Read Tab
        with tabs[3+ix]:
            
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
                            st.error(f'Metadata key {k}: Reserved keyword, please choose another key')
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

#region Export Project

@st.dialog('Export Datasets')            
def export_datasets(fq_dataset_view: pd.DataFrame):
    
    st.write('Save Datasets and Metadata or Dataset FASTQ stats as .csv file')
    
    export_fq = st.toggle('Export FASTQ Files',
                            help='Export FASTQ Files associated with each Dataset')
    
    if export_fq:
        
        fq_files = []
        
        with st.spinner('Exporting Datasets...'):
            
            for _, fq in fq_dataset_view.iterrows():
                
                fq_id = fq['id']
                fq_name = fq['name']
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
                                
                for fq_file in dataset_fq_files:
                    fq_file_detail = datamanager.get_fq_file_detail(st.session_state["jwt_auth_header"], fq_file)
                    df = pd.DataFrame(fq_file_detail.dict(), index=[0])
                    df['dataset_id'] = fq_id
                    df['dataset_name'] = fq_name
                    df['creator'] = fq['owner_username'] # TODO: this would not work if stager is not creator of dataset
                    
                    fq_files.append(df)
        
        fq_files = pd.concat(fq_files, axis=0)
        fq_files = fq_files.drop(columns=['qc_phred', 'staging', 'pipeline_version', 'updated', 'valid_from', 'valid_to', 'owner', 'bucket', 'key'])
        
        fq_files = fq_files[['dataset_id', 'dataset_name','id', 'name', 'read_type', 'qc_passed','read_length', 'num_reads', 'size_mb', 'qc_phred_mean', 'created', 'creator', 'upload_path', 'md5_checksum']]
        
        fq_files = fq_files.rename(columns={'upload_path' : 'upload_path',
                                            'id' : 'fastq_id',
                                            'name' : 'fastq_name'})
        
        st.download_button('Download .csv',
                        fq_files.to_csv(index=False).encode("utf-8"),
                        'fastq_files.csv',
                        'text/csv')
        
    else:
        # project_names to projects
        fq_dataset_view = fq_dataset_view.drop(columns=['fq_file_r1',
                                                        'fq_file_r2',
                                                        'fq_file_i1',
                                                        'fq_file_i2',
                                                        'id_str',
                                                        'fq_dataset_id',
                                                        'owner_group_name'])
        
        fq_dataset_view = fq_dataset_view.rename(columns={'project' : 'project_ids',
                                                        'project_names' : 'project_names',
                                                        'owner_username' : 'creator'})
        
        st.download_button('Download .csv',
                        fq_dataset_view.to_csv(index=False).encode("utf-8"),
                        'datasets.csv',
                        'text/csv')


        
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

# Get attachments for all datasets
fq_attachments = datamanager.get_fq_dataset_attachments(st.session_state["jwt_auth_header"])
fq_attachments_list = fq_attachments.groupby('fq_dataset_id')['name'].apply(list)
fq_attachments_list = fq_attachments_list.reset_index()
fq_attachments_list.columns = ['fq_dataset_id', 'attachments']
fq_datasets = fq_datasets.merge(fq_attachments_list, left_on = 'id', right_on='fq_dataset_id', how='left')
fq_datasets['attachments'] = fq_datasets['attachments'].apply(lambda x: [] if x is np.nan else x)


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

col1, col2, col3, col4, col5 = st.columns([3,3,2.5,2.75,0.75], vertical_alignment='center')


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

with col5:
    if st.button(':material/refresh:', key='refresh_projects', help='Refresh Page'):
        on_click = extensions.refresh_page()


col_config_user = {
    'id': st.column_config.TextColumn('ID'),
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
    'attachments' : None
}

col_config_meta = {
    'id': st.column_config.TextColumn('ID'),
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
        
# Filter out meta columns from selected view which are all None

# Remove those meta cols from projects_show which are all None
fq_meta_cols_all_none = fq_datasets_show.loc[:,fq_metadata.columns].isna().all()
fq_meta_cols_all_none = fq_meta_cols_all_none[fq_meta_cols_all_none].index

fq_datasets_show = fq_datasets_show.drop(columns=fq_meta_cols_all_none)

# Add metadata
if st.session_state.show_fq_metadata:
    # How selected datasets metadata only for subset
    fq_meta_cols_show = list(filter(lambda x: x not in fq_meta_cols_all_none, fq_metadata.columns))
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
                        selection_mode='single-row',
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
    
    select_fq_dataset_attachments = datamanager.get_fq_dataset_attachments(
        st.session_state["jwt_auth_header"],
        fq_dataset_id = int(fq_dataset_detail['id'])
    )
        
    if st.session_state['show_details']:
        show_project_details = True
    else:
        show_project_details = False
    
    
else:
    show_project_details = False
    update_disabled = True
    
    select_row = None
    selected_fq_dataset_ix = None

    fq_dataset_detail = None
    fq_metadata_detail = None
    
    fq_dataset_update = None
    fq_metadata_update = None

col5a, col5b,_, col6a = st.columns([1.75, 1.75,5.5,3], vertical_alignment = 'center')

with col5a:    
    
    if st.button('Update',
                 type ='primary',
                 key='update_dataset',
                 use_container_width=True,
#                 disabled = update_disabled,
                 help = 'Update the selected Dataset'):
        
        update_dataset(fq_dataset_update,
                       fq_metadata_update,
                       select_fq_dataset_attachments,
                       reference_dataset_names,
                       reference_project_names_df)

with col5b:
    
    if st.button('Export',
                 key='export_datasets',
                 use_container_width=True,
                 help = 'Export and download Dataset overview'):
        
        export_datasets(fq_datasets_show)

with col6a:    
   
   on = st.toggle("Details",
                  key='show_details_dataset',
                  value=st.session_state['show_details'],
                  on_change = extensions.switch_show_details,
                  help='Show Details for selected Dataset')

if show_project_details:
    
    st.divider()
    
    tab1d, tab2d, tab3d = st.tabs([':blue-background[**Features**]', ':blue-background[**Projects**]', ':blue-background[**Attachments**]'])
    
    with tab1d:
    
        col1d1, col2d1 = st.columns([7,5])
    
        with col1d1:
            
            with st.container(border = True, height = 300):
                
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
            with st.container(border = True, height = 300):
                
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
        
        with st.container(border = True, height = 300):
            
            st.write('**Projects**')
            
            # Get prject information here: my_projects    
                 
            project_ids = fq_dataset_detail['project']
            dataset_projects_detail = my_projects.loc[my_projects['id'].isin(project_ids),['id', 'name', 'description']]
            
            # Get ID, Name and Description of all projects
            
            st.dataframe(dataset_projects_detail,
                            use_container_width = True,
                            hide_index = True,
                            column_config = {
                                'id' : st.column_config.TextColumn('ID', width='small'),
                                'name' : st.column_config.TextColumn('Name'),
                                'description' : st.column_config.TextColumn('Description')
                            },
                            key='fq_dataset_projects_df')
            
    with tab3d:
    
        with st.container(border = True, height = 300):
        
            st.write('**Attachments**')
            
            attach_select = st.dataframe(select_fq_dataset_attachments,
                                        hide_index = True,
                                        use_container_width = True,
                                        column_config = {
                                            'id' : None,
                                            'name' : st.column_config.TextColumn('Name'),
                                            'description' : None,
                                            'fq_dataset_id' : None},
                                        on_select = 'rerun',
                                        selection_mode='single-row',
                                        key='attachment_details_df')
            
            if len(attach_select.selection['rows']) == 1:
                select_ix = attach_select.selection['rows'][0]
                select_attachment = select_fq_dataset_attachments.loc[select_ix,:]
                select_attachment_id = int(select_attachment['id'])
                select_attachment_name = select_attachment['name']
                
                st.download_button('Download',
                                data=datamanager.get_fq_attachment_file_download(select_attachment_id),
                                file_name = select_attachment_name,
                                key='download_attachment')
            else:
                disable_download = True
                select_attachment_id = 0

                st.button('Download', disabled = True, help = 'Select an attachment to download.', key='download_attachment')