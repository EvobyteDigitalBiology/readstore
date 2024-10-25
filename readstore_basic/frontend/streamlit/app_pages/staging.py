# readstore-basic/frontend/streamlit/app_pages/staging.py

from typing import List
import time
import uuid
import string
import json
import itertools

import streamlit as st
import pandas as pd

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

@st.dialog('Check In Dataset', width='large')
def checkin_df(fq_file_df: pd.DataFrame,
               projects_owner_group: pd.DataFrame,
               reference_fq_dataset_names: pd.Series):
    
    reference_fq_dataset_names = reference_fq_dataset_names.str.lower()
    reference_fq_dataset_names = reference_fq_dataset_names.tolist()
    
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
        
        name = st.text_input("Dataset Name",
                             value=name_old,
                             key='dataset_name',
                             help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')
        
        tab_names = [read_long_map[rt] for rt in read_types]
        tab_names_format = [":blue-background[**Projects**]",
                            ":blue-background[**Features**]",
                             ":blue-background[**Attachments**]"]
        tab_names_format.extend([f":blue-background[**{tn}**]" for tn in tab_names])
        
        # Add Metadata and Attachments Tabs
        tabs = st.tabs(tab_names_format)
        fq_file_names = ['NA'] * len(read_types)
        
        # region Project Tab
        
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
        
        for ix, rt in enumerate(read_types):
            
            # region Read Tab
            with tabs[3+ix]:
                
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
                # TODO Automate
                # 1) First check for dataset name
                if name == '':
                    st.error("Please enter a Dataset name.")
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
                            st.error("Please enter a name for FASTQ entry")
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
                            
                            del st.session_state['fq_data_staging']
                            st.cache_data.clear()
                            st.rerun()
        

def delete_fastq_files(fq_file_ids: List[int]):
    for fq_file_id in fq_file_ids:
        datamanager.delete_fq_file(fq_file_id)
    
    del st.session_state['fq_data_staging']
    st.cache_data.clear()
    st.rerun()  
        
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
    #     with col1f:
    #     st.success("No FASTQ Files to Check In.", icon=":material/check:")
    
    # with col2f:
    #     with st.container(border=True):
    #         st.write('Jobs in QC Queue:', str(num_jobs))

    # col1f, col2f, col3f = st.columns([8.25, 3, 0.75], vertical_alignment='center')

    col1s, col2s, col3s, col4s = st.columns([6, 4, 1.25, 0.75], vertical_alignment='center')
    
    with col1s:
        st.info(f"{len(fq_files_staging)} FASTQ files waiting for Check In.")
    
    with col2s:
        with st.container(border=True):
             st.write(str(num_jobs), ' Jobs in QC Queue')
    
    with col3s:
        with st.popover(':material/help:'):
            
            st.markdown("ReadStore groups **Dataset**s based on the filename of each **FASTQ** file.\n")
            st.markdown("The **Read** type is also infered. [Read1/R1, Read2/R2, Index1/I1, Index2/I2]\n")
                        
            st.markdown("Click *Check In* to validate and register the **Dataset**s \n")
            
            st.markdown("If the infered **Datasets** are not correct, you can change the name in the Dataset columns below.\n")
            st.markdown("Also the **Read** type can be changed by clicking the column blow.\n")
            
    with col4s:
        if st.button(':material/refresh:', key='refresh_projects', help='Refresh Page'):
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
                checkin_df(fq_file_df,
                        projects_owner_group,
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
    col1f, col2f, col3f = st.columns([7.25, 4, 0.75], vertical_alignment='center')
    
    with col1f:
        st.success("No FASTQ Files to Check In.", icon=":material/check:")
    
    with col2f:
        with st.container(border=True):
            st.write(str(num_jobs), ' Jobs in QC Queue')
        
    with col3f:
        if st.button(':material/refresh:', key='refresh_projects', help='Refresh Page'):
            if 'fq_data_staging' in st.session_state:
                del st.session_state['fq_data_staging']
            extensions.refresh_page()
