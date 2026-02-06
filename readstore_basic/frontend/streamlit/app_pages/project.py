# readstore-basic/frontend/streamlit/app_pages/project.py

import time
import string

import streamlit as st
import pandas as pd
import numpy as np

import st_yled
from st_yled import split_button

import extensions
import datamanager
import exceptions
import styles

import uuid

from uidataclasses import OwnerGroup
from uidataclasses import Project

import uiconfig

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

st_yled.init()

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

# Applying the custom CSS in the app
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

# region session_sate

# Reset session state for selecting datasets for projects
if 'available' in st.session_state:
    del st.session_state['available']
if 'selected' in st.session_state:
    del st.session_state['selected']
if 'available_input' in st.session_state:
    del st.session_state['available_input']

# TODO Check Necessary
# if 'available_collab' in st.session_state:
#     del st.session_state['available_collab']
# if 'selected_collab' in st.session_state:
#     del st.session_state['selected_collab']

# State for selected project
if not 'project_select_id' in st.session_state:
    st.session_state['project_select_id'] = None

# if not 'metadata_select' in st.session_state:
#     st.session_state['metadata_select'] = pd.DataFrame()

# Selected Details View
if not 'details_segment_ix' in st.session_state:
    st.session_state['details_segment_ix'] = 0

if not 'selected_project' in st.session_state:
    st.session_state['selected_project'] = None

if not 'selected_project_enable_edit' in st.session_state:
    st.session_state['selected_project_enable_edit'] = False

if not 'selected_project_metadata' in st.session_state:
    st.session_state['selected_project_metadata'] = None

if not 'selected_project_ref_fq_datasets' in st.session_state:
    st.session_state['selected_project_ref_fq_datasets'] = None

if not 'selected_project_export' in st.session_state:
    st.session_state['selected_project_export'] = None

if not 'selected_project_enable_delete' in st.session_state:
    st.session_state['selected_project_enable_delete'] = False

if not 'project_meta_filter_hash' in st.session_state:
    st.session_state['project_meta_filter_hash'] = str(uuid.uuid4())

if not 'project_meta_filter_applied' in st.session_state:
    st.session_state['project_meta_filter_applied'] = False

if not 'toast_cache' in st.session_state:
    st.session_state['toast_cache'] = None

if not 'error_cache' in st.session_state:
    st.session_state['error_cache'] = None

if not 'show_details' in st.session_state:
    st.session_state['show_details'] = True

if not 'show_metadata' in st.session_state:
    st.session_state['show_metadata'] = False

def reset_meta_filter_hash():
    """ Reset project metadata filter hash to force re-rendering of metadata filter UI """

    st.session_state['project_meta_filter_hash'] = str(uuid.uuid4())


def update_attachment_select():
    """ Update which attachments are selected for download for a project """

    if st.session_state['project_select_id']:
        pid = st.session_state['project_select_id']
        st.session_state[f'download_attachments_select_{pid}'] = st.session_state['attachment_details_df']

def update_segment_default(segment_control_options):
    """ Update the default segment based on the current project detail selection """
    
    project_detail_selection = st.session_state['project_detail_selection']
    
    if project_detail_selection:
        ix = segment_control_options.index(project_detail_selection)
        st.session_state['details_segment_ix'] = ix
    
# Assign and remove datasets to project
def add_selected_datasets(fq_datasets, selected_rows):
    """ Update which datasets are selected for addition to project """

    if len(selected_rows) == 0:
        return
    else:    
        # Get ID of selected dataset
        select_dataset_r = fq_datasets.iloc[selected_rows,:]
        # Append to selected datasets
        st.session_state['selected'] = pd.concat([
            st.session_state['selected'],
            select_dataset_r
        ], axis=0)

        # Filter out prev selected ID
        st.session_state['available'] = st.session_state['available'].loc[
            ~st.session_state['available']['id'].isin(select_dataset_r['id']),:]

    
def remove_selected_datasets(fq_datasets, selected_rows):
    """ Update which datasets are selected for addition to project """

    if len(selected_rows) == 0:
        return
    else:    
        # Get ID of selected dataset
        select_dataset_r = fq_datasets.iloc[selected_rows,:]
        # Append to selected datasets
        st.session_state['available'] = pd.concat([
            st.session_state['available'],
            select_dataset_r
        ], axis=0)

        # Filter out prev selected ID
        st.session_state['selected'] = st.session_state['selected'].loc[
            ~st.session_state['selected']['id'].isin(select_dataset_r['id']),:]

# region Create Project

@st.dialog('Create Project', width="medium", on_dismiss='rerun')
def create_project(reference_project_names: pd.Series,
                   reference_fq_datasets: pd.DataFrame):
    """
    Create a new Project (dialog)

    Args:
        reference_project_names (pd.Series): Series of existing project names to validate uniqueness
        reference_fq_datasets (pd.DataFrame): DataFrame of available datasets which can be attached to a project
    """

    reference_project_names = reference_project_names.str.lower()
    reference_project_names = reference_project_names.tolist()
    
    reference_fq_datasets = reference_fq_datasets.sort_values(by='name')
    
    tab1, tab2, tab3 = st_yled.tabs(["Features", "Datasets", "Attachments"], font_size=14, font_weight=500)
    
    with tab1:
        st_yled.markdown('Set Project Attributes and Metadata', font_size=12, color='#808495')
        
        st.write("")
        
        # Fragment to render input field for project details
        @st.fragment
        def feature_ui():

            name = st_yled.text_input("Project Name",
                                    max_chars=150,
                                    help = 'Name must only contain [0-9][a-z][A-Z][.-_@ ]',
                                    width = 400,
                                    border_style='none',
                                    border_width='0px',
                                    key = 'create_project_name_input')
            
            st.write("")

            description = st_yled.text_area("Project Description",
                                    help = 'Description of the project.',
                                    width = 512,
                                    border_style='none',
                                    border_width='0px',
                                    key = 'create_project_description_input')
            
            st.write("")

            st_yled.markdown('Metadata', font_size=14, font_weight=500)

            with st_yled.container(key='project-metadata-info'):
                st_yled.markdown("Project metadata must be provided as key-value pairs.", font_size=12, color='#808495')
                st_yled.markdown("Metadata facilitate grouping and filtering of projects by pre-defined features.", font_size=12, color='#808495')

            metadata_df = st.data_editor(
                            pd.DataFrame({'key' : [''], 'value' : ['']}),
                            hide_index=True,
                            column_config = {
                                'key' : st.column_config.TextColumn('Key'),
                                'value' : st.column_config.TextColumn('Value')
                            },
                            num_rows ='dynamic',
                            key = 'create_metadata_df',
                            width = 400,
                        )

            st.write("")

            st_yled.markdown('Dataset Metadata Keys', font_size=14, font_weight=500)

            with st_yled.container(key='project-metadata-keys-info'):
            
                st_yled.markdown("Dataset Metadata Keys help to create a metadata mask for attached datasets.", font_size=12, color='#808495')
                st_yled.markdown("Datasets associated with a project will automatically get the key defined here as metadata keys. ", font_size=12, color='#808495')

            # Value column is hidden so that value is set to None for each created key
            dataset_meta_keys_df = st.data_editor(
                pd.DataFrame({'key' : [''], 'value' : ['']}),
                hide_index=True,
                column_config = {
                    'key' : st.column_config.Column('Key'),
                    'value' : None
                },
                num_rows ='dynamic',
                key = 'create_dataset_metadata_keys_df',
                width = 256,
            )

            return name, description, metadata_df, dataset_meta_keys_df

        name, description, metadata_df, dataset_meta_keys_df = feature_ui()

    with tab2:
        
        if 'available' not in st.session_state:
            st.session_state['available'] = reference_fq_datasets[['id', 'name']]
        if 'selected' not in st.session_state:
            st.session_state['selected'] = pd.DataFrame(columns=['id', 'name'])

        @st.fragment
        def select_form_fq_datasets():
             
            # Columns for explanation and popover
            col1a, col2a = st.columns([11,1])
            
            with col1a:
                st_yled.markdown("Select **Datasets** to attach to the Project", font_size=12, color='#808495')

            with col2a:
                with st.popover(':material/help:'):
                    
                    st.write('Attach **Datasets** to the project.')
                    st.write('Click on item checkbox in **Available Dataset** table to select')
                    st.write('Click on item checkbox in **Attached Dataset** table to de-select')
                    
            # Columns for available and selected datasets
            col1, col2, col3 = st.columns([5.5,1,5.5])
            
            # First col to select available datasets
            with col1:
                
                with st.container(height=475, key=''):
                    
                    st.write('Available Datasets')
                                
                    datasets_available = st.session_state['available']
                    
                    search_value_fq_ds = st.text_input("Search Datasets",
                                    help = 'Search in available Datasets',
                                    placeholder='Search Available Datasets',
                                    key = 'create_search_fq_datasets',
                                    label_visibility = 'collapsed')
                    
                    datasets_available['id_str'] = datasets_available['id'].astype(str)
                    
                    fq_datasets_show = datasets_available.loc[
                        (datasets_available['name'].str.contains(search_value_fq_ds, case=False) | 
                         datasets_available['id_str'].str.contains(search_value_fq_ds, case=False)),:
                    ]
                    
                    fq_avail_df = st.dataframe(fq_datasets_show,
                                                width='stretch',
                                                hide_index = True,
                                                column_config = {
                                                    'id' : st.column_config.TextColumn('ID'),
                                                    'name' : st.column_config.TextColumn('Name'),
                                                    'owner_group_name' : None,
                                                    'id_str' : None
                                                },
                                                key='create_collab_datasets_df',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')

            # Column with selected datasets
            with col3:
                with st.container(border = True, height=475):              
                    
                    st.write('Attached Datasets')
                    
                    datasets_selected = st.session_state['selected']
                    
                    search_value_fq_ds_select = st.text_input("Search Datasets",
                                                            help = 'Search in Attached Datasets',
                                                            placeholder='Search Attached Datasets',
                                                            key = 'create_search_attached_fq_datasets',
                                                            label_visibility = 'collapsed')
                    
                    datasets_selected['id_str'] = datasets_selected['id'].astype(str)
                    
                    fq_datasets_select_show = datasets_selected.loc[
                            (datasets_selected['name'].str.contains(search_value_fq_ds_select, case=False) | 
                             datasets_selected['id_str'].str.contains(search_value_fq_ds_select, case=False)),:
                        ]
                    
                    fq_select_df = st.dataframe(fq_datasets_select_show,
                                                width='stretch',
                                                hide_index = True,
                                                column_config = {
                                                    'id' : st.column_config.TextColumn('ID'),
                                                    'name' : st.column_config.TextColumn('Name'),
                                                    'owner_group_name' : None,
                                                    'id_str' : None
                                                },
                                                key='create_collab_datasets_select_df',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')
            
            with col2:
                
                # Spacer Container
                st.container(height = 100, border = False)
                st.button(':material/arrow_forward:', width='stretch', type='primary', on_click=add_selected_datasets, args = (fq_datasets_show, fq_avail_df.selection['rows']))
                st.button(':material/arrow_back:', width='stretch', type='primary', on_click=remove_selected_datasets, args = (fq_datasets_select_show, fq_select_df.selection['rows']))

        select_form_fq_datasets()
    
    with tab3:
        
        with st_yled.container(key='project-attachments-info'):

            st_yled.markdown('Attach Files to the Project', font_size=12, color='#808495')
            
            st.write("")
            st.write("")
            
            uploaded_files = st.file_uploader(
                "Choose Files to Upload",
                help = "Upload attachments for the Project. Attachments can be any file type.",
                accept_multiple_files=True,
                width = 400
            )
        
            st.write("")
            st.write("")

    with st.container(horizontal=True, horizontal_alignment='right'):

        if st.button('Cancel', key='cancel_create_project'):
            st.rerun()

        if st.button('Confirm', type ='primary', key='ok_create_project'):
            
            name = name.strip()

            selected_datasets = st.session_state['selected']
            selected_datasets_ids = selected_datasets['id'].tolist()
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Replace all None values with empty string
            metadata_df = metadata_df.loc[metadata_df['key'] != '', :]

            metadata_df = metadata_df.fillna('')
            
            keys = metadata_df['key'].tolist()
            keys = [k.lower() for k in keys]
            values = metadata_df['value'].tolist()
            values = [v.strip() for v in values]
            
            # Remove all empty keys and na key
            dataset_meta_keys_df = dataset_meta_keys_df.loc[~dataset_meta_keys_df['key'].isna(),:]
            dataset_meta_keys_df = dataset_meta_keys_df.loc[dataset_meta_keys_df['key'] != '', :]

            key_templates = dataset_meta_keys_df['key'].tolist()
            key_templates = [k.lower() for k in key_templates if not k is None]

            # Validate uploaded files
            file_names = [file.name for file in uploaded_files]
            file_bytes = [file.getvalue() for file in uploaded_files]
            
            # Validate metadata key formats
            # Check if metadata keys are in reserved keywords
            for k, v in zip(keys, values):
                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                    st.session_state['error_cache'] = f'Key **{k}**: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                    break
                if k in uiconfig.METADATA_RESERVED_KEYS:
                    st.session_state['error_cache'] = f'Metadata Key **{k}**: Reserved keyword, please choose another key'
                    break
            else:
                # Validate dataset key formats
                for k in key_templates:
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.session_state['error_cache'] = f'Key **{k}**: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.session_state['error_cache'] = f'Metadata key **{k}**: Reserved keyword, please choose another key'
                        break
                
                # If no error occured validate name
                else:            
                    # Validate username / Better use case
                    if name == '':
                        st.session_state['error_cache'] = 'Project Name is empty'
                    elif name == 'No Project':
                        st.session_state['error_cache'] = 'No Project is a reserved keyword.'
                    # elif not extensions.validate_charset(name):
                    #     st.session_state['error_cache'] = f'Project Name: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                    elif name.lower() in reference_project_names:
                        st.session_state['error_cache'] = 'Project Name already exists in Group'
                    else:
                        metadata = {k:v for k,v in zip(keys,values)}
                        dataset_meta_keys = {k:None for k in key_templates}

                        project_id = datamanager.create_project(st.session_state["jwt_auth_header"],
                                                                name,
                                                                description,
                                                                metadata,
                                                                dataset_meta_keys)
                        
                        for file_name, file_byte in zip(file_names, file_bytes):
                            datamanager.create_project_attachment(file_name,
                                                                file_byte,
                                                                project_id)
                    
                        # Attach Datasets
                        for dataset_id in selected_datasets_ids:
                            datamanager.update_fq_dataset_project(dataset_id, add_project_id=project_id)
                            
                        st.cache_data.clear()
                        st.rerun()
                
    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None


#region Update Project
@st.dialog('Update Project', width="medium", on_dismiss="rerun")
def update_project(project_select_df: pd.DataFrame,
                   metadata_select_df: pd.DataFrame,
                   reference_project_names: pd.Series,
                   reference_fq_datasets: pd.DataFrame):
    """
        Update an existing Project (dialog)

        Args:
            project_select_df (pd.DataFrame): DataFrame of selected project to update
            metadata_select_df (pd.DataFrame): DataFrame of existing metadata for the selected project
            reference_project_names (pd.Series): Series of existing project names to validate uniqueness
            reference_fq_datasets (pd.DataFrame): DataFrame of available datasets which can be attached to a project
    """

    project_id = int(project_select_df['id_project'])
    name_old = project_select_df['name_project']
    description_old = project_select_df['description']
    collaborators = project_select_df['collaborators']
    dataset_metadata_keys = project_select_df['dataset_metadata_keys']
    dataset_metadata_keys = list(dataset_metadata_keys.keys())
    
    reference_project_names = reference_project_names[reference_project_names != name_old]
    reference_project_names = reference_project_names.str.lower()
    reference_project_names = reference_project_names.tolist()
    
    # Get existing attachments for project
    select_project_attachments = datamanager.get_project_attachments(st.session_state["jwt_auth_header"],
                                                                     project_id)
    
    attachment_ref_names = select_project_attachments['name'].tolist()
    
    reference_fq_datasets = reference_fq_datasets.sort_values(by='name')
    
    tab1, tab2, tab3 = st_yled.tabs(["Features", "Datasets", "Attachments"], font_size=14, font_weight=500)
    
    #region TAB1 Data  
    with tab1:
        st_yled.markdown('Edit Project Attributes and Metadata', font_size=12, color='#808495')
        
        def feature_ui(name_old, description_old, metadata_select_df, dataset_metadata_keys):

            name = st_yled.text_input("Project Name",
                                max_chars=150,
                                width = 400,
                                border_style='none',
                                border_width='0px',
                                help = 'Name must only contain [0-9][a-z][A-Z][.-_@ ]',
                                value = name_old,
                                key = 'update_project_name_input')
            
            st.write("")

            description = st_yled.text_area("Project Description",
                                        help = 'Description of the project.',
                                        value = description_old,
                                        width = 512,
                                    border_style='none',
                                    border_width='0px',
                                    key = 'update_project_description_input')
            
            st.write("")

            st_yled.markdown('Metadata', font_size=14, font_weight=500)
            
            with st_yled.container(key='project-metadata-info'):
                st_yled.markdown("Project metadata must be provided as key-value pairs.", font_size=12, color='#808495')
                st_yled.markdown("Metadata facilitate grouping and filtering of projects by pre-defined features.", font_size=12, color='#808495')

            # Add empty row for new metadata
            if metadata_select_df.shape[0] == 0:
                metadata_select_df = pd.DataFrame({'key' : [''], 'value' : ['']})
            else:
                metadata_select_df = metadata_select_df.astype(str)
            
            metadata_df = st.data_editor(
                metadata_select_df,
                hide_index=True,
                column_config = {
                    'key' : st.column_config.TextColumn('Key', width='medium'),
                    'value' : st.column_config.TextColumn('Value', width='medium')
                },
                num_rows ='dynamic',
                key = 'create_metadata_df',
                width = 400,
            )

            st.write("")
            st_yled.markdown('Dataset Metadata Keys', font_size=14, font_weight=500)

            with st_yled.container(key='project-metadata-keys-info'):
                
                st_yled.markdown("Dataset Metadata Keys help to create a metadata mask for attached datasets.", font_size=12, color='#808495')
                st_yled.markdown("Datasets associated with a project will automatically get the key defined here as metadata keys. ", font_size=12, color='#808495')

            if len(dataset_metadata_keys) == 0:
                dataset_metadata_keys = ['']

            # Value column is hidden so that value is set to None for each created key
            dataset_meta_keys_df = st.data_editor(
                pd.DataFrame({
                    'key' : dataset_metadata_keys,
                    'value' : None},
                            dtype=str),
                hide_index=True,
                column_config = {
                    'key' : st.column_config.TextColumn('Key', width='medium'),
                    'value' : None
                },
                num_rows ='dynamic',
                key = 'create_dataset_metadata_keys_df',
                width = 256,
            )

            return name, description, metadata_df, dataset_meta_keys_df

        name, description, metadata_df, dataset_meta_keys_df = feature_ui(name_old,
                                                                         description_old,
                                                                         metadata_select_df,
                                                                         dataset_metadata_keys) 
        


    #region TAB2 Datasets  
    with tab2:
        
        # Subset datasets which are already attached to project
        fq_datasets_attached = reference_fq_datasets.loc[
            reference_fq_datasets['project'].apply(lambda x: any((e == project_id) for e in x)),:
        ]
        # Remove attached datasets from available datasets
        fq_datasets_avail = reference_fq_datasets.loc[
            ~reference_fq_datasets['id'].isin(fq_datasets_attached['id']),:
        ]
        
        if 'available' not in st.session_state:
            st.session_state['available'] = fq_datasets_avail[['id', 'name']]
            st.session_state['available_input'] = fq_datasets_avail['id'].tolist()
            
        if 'selected' not in st.session_state:
            st.session_state['selected'] = fq_datasets_attached[['id', 'name']]
            st.session_state['selected_input'] = fq_datasets_attached['id'].tolist()

        @st.fragment
        def update_select_form_fq_datasets():               
            
            # Content
            col1a, col2a = st.columns([11,1], vertical_alignment='top')
            
            with col1a:
                st_yled.markdown("Select **Datasets** to attach to the Project", font_size=12, color='#808495')
            
            with col2a:
                with st.popover(':material/help:'):
                    
                    st.write('Attach **Datasets** to the project.')
                    st.write('Click on item checkbox in **Available Datasets** table to select')
                    st.write('Click on item checkbox in **Attached Datasets** table to de-select')
                    st.write('Use the arrow buttons to move datasets')
                    st.write('Click **Confirm** to attach datasets')
                    
            col1, col2, col3 = st.columns([5.5,1,5.5])
            
            # First col to select available datasets
            with col1:
                
                with st.container(border = True, height=540):
                    
                    st.write('Available Datasets')
                                
                    datasets_available = st.session_state['available']
                    
                    search_value_fq_ds = st.text_input("Search Datasets",
                                    help = 'Search in available Datasets',
                                    placeholder='Search Available Datasets',
                                    key = 'update_search_fq_datasets',
                                    label_visibility = 'collapsed')
                    
                    datasets_available['id_str'] = datasets_available['id'].astype(str)
                    
                    fq_datasets_show = datasets_available.loc[
                        (datasets_available['name'].str.contains(search_value_fq_ds, case=False) | 
                         datasets_available['id_str'].str.contains(search_value_fq_ds, case=False)),:
                    ]
                    
                    fq_avail_df = st.dataframe(fq_datasets_show,
                                                width='stretch',
                                                hide_index = True,
                                                column_config = {
                                                    'id' : st.column_config.TextColumn('ID', width='small'),
                                                    'name' : st.column_config.Column('Name'),
                                                    'owner_group_name' : None,
                                                    'id_str' : None
                                                },
                                                key='update_collab_datasets_df',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')

            # Column with selected datasets
            with col3:
                with st.container(border = True, height=540):              
                    
                    st.write('Attached Datasets')
                    
                    datasets_selected = st.session_state['selected']
                    
                    search_value_fq_ds_select = st.text_input("Search Datasets",
                                                            help = 'Search in Attached Datasets',
                                                            placeholder='Search Attached Datasets',
                                                            key = 'update_search_attached_fq_datasets',
                                                            label_visibility = 'collapsed')
                    
                    datasets_selected['id_str'] = datasets_selected['id'].astype(str)
                    
                    fq_datasets_select_show = datasets_selected.loc[
                            (datasets_selected['name'].str.contains(search_value_fq_ds_select, case=False) | 
                             datasets_selected['id_str'].str.contains(search_value_fq_ds_select, case=False)),:
                        ]
                    
                    fq_select_df = st.dataframe(fq_datasets_select_show,
                                                width='stretch',
                                                hide_index = True,
                                                column_config = {
                                                    'id' : st.column_config.TextColumn('ID', width='small'),
                                                    'name' : st.column_config.TextColumn('Name'),
                                                    'owner_group_name' : None,
                                                    'id_str' : None
                                                },
                                                key='update_collab_datasets_select_df',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')

                with col2:
                
                    # Spacer Container
                    st.container(height = 100, border = False)
                    st.button(':material/arrow_forward:', width='stretch', type='primary', on_click=add_selected_datasets, args = (fq_datasets_show, fq_avail_df.selection['rows']))
                    st.button(':material/arrow_back:', width='stretch', type='primary', on_click=remove_selected_datasets, args = (fq_datasets_select_show, fq_select_df.selection['rows']))
            

        update_select_form_fq_datasets()
    
    #region TAB3 Attachments
    with tab3:
        
        with st_yled.container(key='project-attachments-info'):

            st_yled.markdown('Upload or Remove Project File Attachments', font_size=12, color='#808495')

            st.write("")

            # Define Max Heigth of attachment select
            # Limit Max Height of Dataframe
            if select_project_attachments.shape[0] > 7:
                max_df_height = 320
            else:
                max_df_height = 'content'
            
            if select_project_attachments.shape[0] == 0:
                
                st_yled.info(':material/notifications: No attachments available. Start by uploading new files below.',
                             border_width="2.0px",
                             border_color="#808495",
                             border_style="solid",
                             color="#808495",
                             key='info-no-samples',
                             width=400)
            else:

                select_attach_update = st.dataframe(
                    select_project_attachments,
                    hide_index = True,
                    width = 400,
                    column_config = {
                        'id' : None,
                        'name' : st.column_config.Column('Filename'),
                        'description' : None,
                        'project_id' : None},
                    on_select = 'rerun',
                    selection_mode='multi-row',
                    key = 'select_attachment_update',
                    height = max_df_height)
                
                if len(select_attach_update.selection['rows']) > 0:
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
                            
                            attach_ixes = select_attach_update.selection['rows']
                            attach_ids = select_project_attachments.loc[attach_ixes,'id'].tolist()
                            
                            for attach_id in attach_ids:
                                datamanager.delete_project_attachment(attach_id)
                            else:
                                st.cache_data.clear()
                                
                                # Reset attachment select for project id
                                st.session_state[f'download_attachments_select_{project_id}'] = None
                                st.rerun()

            st.write("")
            st.write("")
    
            uploaded_files = st.file_uploader(
                "Upload Project Attachments",
                accept_multiple_files=True,
                width = 400
            )

        st.write("")

        
    with st.container(horizontal=True, horizontal_alignment='right'):

        if st.button('Cancel', key='cancel_update_project'):
            st.rerun()

        #region Confirm
        if st.button('Confirm', type ='primary', key='ok_update_project'):
            
            # Needs to be compared to the original selected
            if 'selected' in st.session_state:
                selected_datasets = st.session_state['selected']
                selected_datasets_ids = selected_datasets['id'].tolist()
                selected_datasets_ids_input = st.session_state['selected_input']
                selected_datasets_ids_new = list(set(selected_datasets_ids) - set(selected_datasets_ids_input))     
            else: # Case that project is shared TODO Should be decprecated
                selected_datasets_ids_new = [] #TODO Should be decprecated
            
            if 'available' in st.session_state:
                available_datasets = st.session_state['available']
                available_datasets_ids = available_datasets['id'].tolist()
                available_datasets_ids_input = st.session_state['available_input']
                available_datasets_ids_new = list(set(available_datasets_ids) - set(available_datasets_ids_input))
            else:  #TODO Should be decprecated
                available_datasets_ids_new = [] #TODO Should be decprecated
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Remove all empty strings in key column
            metadata_df = metadata_df.loc[metadata_df['key'] != '', :]
            # Replace all None values with empty string
            metadata_df = metadata_df.fillna('')
            
            keys = metadata_df['key'].tolist()
            keys = [k.lower() for k in keys]
            values = metadata_df['value'].tolist()
            values = [v.strip() for v in values]
            
            name = name.strip()

            # Remove all empty keys and na key
            dataset_meta_keys_df = dataset_meta_keys_df.loc[~dataset_meta_keys_df['key'].isna(),:]
            dataset_meta_keys_df = dataset_meta_keys_df.loc[dataset_meta_keys_df['key'] != '', :]

            key_templates = dataset_meta_keys_df['key'].tolist()
            key_templates = [k.lower() for k in key_templates if not k is None]

            # Attachment Data
            file_names = [file.name for file in uploaded_files]
            file_bytes = [file.getvalue() for file in uploaded_files]
            
            # Validate metadata key formats
            for k, v in zip(keys, values):
                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                    st.session_state['error_cache'] = f'Key {k}: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                    break
                if k in uiconfig.METADATA_RESERVED_KEYS:
                    st.session_state['error_cache'] = f'Metadata key {k}: Reserved keyword, please choose another key'
                    break
            else:
                # Validate dataset key formats
                for k in key_templates:
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.session_state['error_cache'] = f'Key {k}: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.session_state['error_cache'] = f'Metadata key {k}: Reserved keyword, please choose another key'
                        break
                
                # If no error occured validate name
                else:
                    # Validate username / Better use case
                    if name == '':
                        st.session_state['error_cache'] = 'Project Name is empty'
                    elif name == 'No Project':
                        st.session_state['error_cache'] = 'No Project is a reserved keyword.'
                    elif not extensions.validate_charset(name):
                        st.session_state['error_cache'] = 'Project Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces'
                    elif name.lower() in reference_project_names:
                        st.session_state['error_cache'] = 'Project Name already exists in Group'
                    else:
                        metadata = {k:v for k,v in zip(keys,metadata_df['value'])}
                        dataset_meta_keys = {k:None for k in key_templates}
                        
                        datamanager.update_project(st.session_state["jwt_auth_header"],
                                                    project_id,
                                                    name,
                                                    description,
                                                    metadata,
                                                    dataset_meta_keys,
                                                    collaborators)
                        
                        # If no error occured validate name            
                        for file_name, file_byte in zip(file_names, file_bytes):
                            if file_name in attachment_ref_names:
                                st.warning(f'Attachment {file_name} already exists. Skip')
                            else:
                                datamanager.create_project_attachment(file_name,
                                                                    file_byte,
                                                                    project_id)
                        
                        # Attach Datasets
                        for dataset_id in selected_datasets_ids_new:
                            datamanager.update_fq_dataset_project(dataset_id, add_project_id=project_id)
                        # Remove Datasets unselected
                        for dataset_id in available_datasets_ids_new:
                            datamanager.update_fq_dataset_project(dataset_id, remove_project_id=project_id)
                        
                        st.cache_data.clear()
                        st.rerun()
    
    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None
              

#region Export Project
@st.dialog('Export Projects', on_dismiss='rerun')            
def export_project(project_view: pd.DataFrame):
    """
        Export selected Projects as .csv file

        Args:
            project_view (pd.DataFrame): DataFrame of selected projects to export
    """

    num_projects = project_view.shape[0]

    st.write(f'Export {num_projects} Projects and Metadata as .csv file')
    
    # Combine attachments to lists
    project_attachments = datamanager.get_project_attachments(st.session_state["jwt_auth_header"])
    
    # Map in attachment names to projects
    project_attachments_list = project_attachments.groupby('project_id')['name'].apply(list)
    projects = project_view.merge(project_attachments_list, left_on = 'id_project', right_on='project_id', how='left')
    projects['name'] = projects['name'].apply(lambda x: [] if x is np.nan else x)
    
    projects_export = projects.drop(columns=['dataset_metadata_keys',
                                            'collaborators',
                                            'id_str',
                                            'name_og'])
    
    projects_export = projects_export.rename(columns={'id_project' : 'id',
                                                    'name_project' : 'name',
                                                    'owner_username' : 'creator',
                                                    'name' : 'attachments'})

    st.write("")    
    st.write("")    

    with st_yled.container(horizontal=True, horizontal_alignment='right'):

        if st.button('Cancel', key='cancel_create_project'):
            st.rerun()

        st_yled.download_button('Download .csv',
                                projects_export.to_csv(index=False).encode("utf-8"),
                                'projects.csv',
                                'text/csv',
                                type='primary')



#region Delete Projects
@st.dialog('Delete Projects', width='medium', on_dismiss='rerun')
def delete_projects(project_select_df: pd.DataFrame):
    """
    Dialog for confirming deletion of selected projects.
    
    Args:
        project_select_df: DataFrame containing the projects to be deleted
    """

    # Check if project_select_df is series 
    project_ids = project_select_df['id_project']
    if isinstance(project_ids, int):
        project_ids = [project_ids]
    else:
        project_ids = project_ids.tolist()

    num_projects = len(project_ids)
    
    if num_projects == 1:
        st.warning(f"Are you sure you want to delete the selected project?")
    else:
        st.warning(f"Are you sure you want to delete {num_projects} projects?")
    
    st.error("⚠️ This action cannot be undone!")
    st.write("")
    
    with st.container(horizontal=True, horizontal_alignment='right'):
        
        if st.button('Cancel', key='cancel_delete_projects'):
            st.rerun()
        
        if st.button('Delete', type='primary', key='confirm_delete_projects'):
            
            for pid in project_ids:
                datamanager.delete_project(pid)
            
            st.cache_data.clear()
            st.rerun()



#endregion

#region UI
@st.fragment
def uimain(projects_show, my_owner_group_name, fq_dataset_og, fq_dataset_collab):

    # Show Toast Cache
    if st.session_state['toast_cache']:
        st.toast(st.session_state['toast_cache'])
        st.session_state['toast_cache'] = None

    # Define Main Container
    with st_yled.container(key='work-ui'):

        st.space(32)

        with st_yled.container(horizontal=True,
                                vertical_alignment='center',
                                horizontal_alignment ='distribute',
                                key='projects-header-container'):

            with st_yled.container(key='projects-header-left-container',
                                    horizontal=True,
                                    vertical_alignment='center',
                                    horizontal_alignment ='left',
                                    gap='small'):

                with st_yled.container(key='projects-header-title-container',
                                        horizontal=True,
                                        vertical_alignment='center',
                                        horizontal_alignment ='left',
                                        gap='small',
                                        width=144):

                    # Create hash for button key
                    if not 'project_split_but_hash' in st.session_state:
                        st.session_state['project_split_but_hash'] = str(uuid.uuid4())

                    with st.container(key='projects-header-split-button-container'):

                        split_but = split_button(label='Create',
                                                options=['Update', 'Export', 'Delete'],
                                                icon=':material/add:',
                                                key=f'project_split_button-{st.session_state['project_split_but_hash']}')

                    if split_but == 'Create':
                        st.session_state['project_split_but_hash'] = str(uuid.uuid4())
                        
                        create_project(reference_og_project_names,
                                        fq_dataset_og)

                    elif split_but == 'Update':
                        
                        st.session_state['project_split_but_hash'] = str(uuid.uuid4())

                        if st.session_state['selected_project_enable_edit']:
                            update_project(st.session_state['selected_project'],
                                            st.session_state['selected_project_metadata'],
                                            reference_og_project_names,
                                            st.session_state['selected_project_ref_fq_datasets'])
                        else:
                            st.session_state['toast_cache'] = 'Select one Project to Update'
                            st.rerun()


                    elif split_but == 'Export':
                        st.session_state['project_split_but_hash'] = str(uuid.uuid4())
                        export_project(st.session_state['selected_project_export'])

                    elif split_but == 'Delete':
                        
                        st.session_state['project_split_but_hash'] = str(uuid.uuid4())

                        if st.session_state['selected_project_enable_delete']:
                            delete_projects(st.session_state['selected_project'])
                        else:
                            st.session_state['toast_cache'] = 'Select one or more Projects to Delete'
                            st.rerun()

                search_value_projects = st_yled.text_input("Search Projects",
                                    help = 'Search for Projects',
                                    placeholder='Search Projects',
                                    key = 'search_projects',
                                    label_visibility = 'collapsed',
                                    border_width=2,
                                    width = 256)

                mask = projects_show.astype(str).apply(lambda x: x.str.contains(search_value_projects, case=False)).any(axis=1)
                projects_show = projects_show[mask]

                # Filter out meta columns from selected view which are all None
                # TODO: Needed?
                # st.session_state['metadata_select'] = projects_show[metadata.columns]
                # metadata_select = st.session_state['metadata_select']
                
                metadata_select = projects_show[metadata.columns]
                metadata_select = metadata_select.dropna(axis=1, how='all')
                
                # if st.session_state['project_meta_filter_applied']:
                #     filter_bg_color = styles.PRIMARY_COLOR
                #     color = "#FFFFFF"
                # else:
                # TODO: Alternative for marking active filter
                filter_bg_color = styles.SECONDARY_BACKGROUND_COLOR_DEFAULT
                color = styles.PRIMARY_COLOR

                with st_yled.popover(':material/filter_alt:',
                                key='project-metadata-filter-popover',  
                                help='Filter Metadata',
                                background_color=filter_bg_color,
                                color=color,
                                font_weight='500',
                                border_style='none',
                                border_width=0,
                                width='content'):
                    
                    with st_yled.container(horizontal=True,
                                            vertical_alignment='center',
                                            horizontal_alignment ='left',
                                            gap='small',
                                            key='project-metadata-filter-container'):
                        
                        st_yled.markdown('Apply Metadata Filter', color=styles.PRIMARY_COLOR, font_size=14, key='project-metadata-filter-title')
                        st_yled.button('Reset', icon=':material/filter_alt_off:', on_click=reset_meta_filter_hash)
                    
                    metadata_options = metadata_select.columns

                    if len(metadata_options) == 0:
                        st_yled.info('No Metadata available for filtering')
                    else:
                        # all_selections = []
                        for k in metadata_options:
                            
                            options = metadata_select[k].dropna().unique().tolist()
                            
                            st.multiselect(label = f'Filter {k}',
                                            options = options,
                                            key = f'project_meta_filter_{st.session_state["project_meta_filter_hash"]}_{k}',
                                            placeholder = "")
                            
                        #     all_selections.extend(st.session_state[f'project_meta_filter_{st.session_state["project_meta_filter_hash"]}_{k}'])
                        # else:
                        #     if len(all_selections) > 0:
                        #         if not st.session_state['project_meta_filter_applied']:
                        #             st.session_state['project_meta_filter_applied'] = True
                        #             #st.rerun()
                        #     else:
                        #         # Case that all filters are cleared
                        #         if st.session_state['project_meta_filter_applied']:
                        #             st.session_state['project_meta_filter_applied'] = False
                        #             #st.rerun()

            with st_yled.container(key='projects-header-right-container',
                                    horizontal=True,
                                    vertical_alignment='center',
                                    horizontal_alignment ='right',
                                    gap='small',
                                    width=250):

                st.session_state['show_metadata'] = st_yled.toggle("Show Metadata",
                                                                    color='#808495',
                                                                    font_size=12,
                                                                    value=st.session_state['show_metadata'],
                                                                    key='projects-show-metadata-toggle',)
                
                if st.session_state.show_details:
                    st.button(':material/unfold_less:',
                                help='Collapse Details Pane',
                                key='projects-collapse-details',
                                type='tertiary',
                                width='content',
                                on_click=extensions.switch_show_details)

                else:
                    st.button(':material/unfold_more:',
                            help='Expand Details Pane',
                            key='projects-collapse-details',
                            type='tertiary',
                            width='content',
                            on_click=extensions.switch_show_details)                


                if st_yled.button(':material/refresh:',
                            help='Refresh Projects',
                            key='projects-refresh',
                            type='tertiary',
                            font_weight='500',
                            font_size='16px',
                            width='content'):
                
                    on_click = extensions.refresh_page()

        # Define Column Configurations
        col_config_user = {
                'id_project' : st.column_config.NumberColumn('ID', width='small'),
                'name_project' : st.column_config.TextColumn('Name'),
                'description' : st.column_config.TextColumn('Description'),
                'name_og' : None,
                'created' : st.column_config.DateColumn('Created'),
                'archived' : None,
                'owner_username' : None,
                'collaborators' : None,
                'dataset_metadata_keys' : None,
                'id_str' : None,
        #        'name' : None,
            }

        col_config_meta = {
                'id_project' : st.column_config.NumberColumn('ID', width='small'),
                'name_project' : st.column_config.TextColumn('Name'),
                'name_og' : None,
                'id_str' : None
            }

        # Search by metadata filter
        projects_show = extensions.filter_df_by_metadata_filter(projects_show,
                                                                filter_session_prefix=f'project_meta_filter_{st.session_state["project_meta_filter_hash"]}_')

        # Remove those meta cols from projects_show which are all None
        meta_cols_all_none = projects_show.loc[:,metadata.columns].isna().all()
        meta_cols_all_none = meta_cols_all_none[meta_cols_all_none].index
        meta_cols_show = list(filter(lambda x: x not in meta_cols_all_none, metadata.columns))

        # Dynamically adjust height of dataframe
        if st.session_state['show_details']:
            if (len(projects_show) < 11):
                project_df_height = 'content'
            else:
                project_df_height = 368 # 11 rows
        else:
            if (len(projects_show) < 22):
                project_df_height = 'content'
            else:
                project_df_height = 720

        
        # Remove all columns which are all None
        projects_show = projects_show.drop(columns=meta_cols_all_none)

        # Define which columns to show, depending on show_metadata toggle
        if st.session_state.show_metadata:
            # How selected projects show only metadata for subset
            # Show all meatadata columns which are not all None
            show_cols = ['id_project', 'name_project', 'name_og'] + meta_cols_show
            
            # Highlight somehow
            metadata_col_config = {k : k for k in meta_cols_show}

            col_config_meta.update(metadata_col_config)
            col_config = col_config_meta
            
        else:    
            show_cols = projects.columns.tolist()
            col_config = col_config_user
            
        # For formatting, replace None with empty string
        projects_show = projects_show.fillna('')
        projects_show = projects_show.sort_values(by='id_project')

        if projects_show.shape[0] == 0:

            st_yled.info(':material/notifications: No Projects found. Create a new Project or remove Filters to see all Projects.',
                         border_width="2.0px",
                         border_color="#808495",
                         border_style="solid",
                         color="#808495",
                         key='info-no-projects',
                         width=600)
        
        else:
            # TODO Change naming here
            projects_select = st.dataframe(projects_show[show_cols],
                                column_config = col_config,
                                selection_mode=['single-cell', 'multi-row'],
                                hide_index = True,
                                on_select = 'rerun',
                                width='stretch',
                                key='projects_select_df',
                                height = project_df_height)
                
            # Define selected rows from 'rows' and 'cells'
            rows_from_rows = projects_select.selection['rows']
            row_from_cells = [cell[0] for cell in projects_select.selection['cells']]

            if len(rows_from_rows) > 0:
                selection = rows_from_rows
            else:
                selection = row_from_cells

            if len(selection) == 1:
                
                # Subset projects and metadata to feed into update/details
                # Get index from selection
                select_row = selection[0]
                
                # Get original index from projects overview before subset
                selected_project_ix = projects_show.iloc[[select_row],:].index[0]
                
                selected_project = projects.loc[selected_project_ix,:]
                # metadata as series to directly show as dataframe
                selected_metadata = metadata.loc[selected_project_ix,:]
                selected_metadata = selected_metadata.dropna().reset_index()
                selected_metadata.columns = ['key', 'value']
                
                # Check if the selected project is shared by user from different group
                # Available datasets for attachment to project
                # TODO: Not necessary
                if selected_project['name_og'] == my_owner_group_name:
                    update_ref_fq_datasets = fq_dataset_og
                else:
                    update_ref_fq_datasets = fq_dataset_collab
                
                update_one = True 
                
                if st.session_state['show_details']:
                    show_project_details = True
                else:
                    show_project_details = False
                
                select_project_id = selected_project['id_project']
                select_project_attached_fq_datasets = update_ref_fq_datasets.loc[
                    update_ref_fq_datasets['project'].apply(lambda x: any((e == select_project_id) for e in x)),:
                ]
                
                # Get attachments for selected project from backend
                select_project_attachments = datamanager.get_project_attachments(st.session_state["jwt_auth_header"],
                                                                                select_project_id)
                
                project_export_select = projects_show.loc[[selected_project_ix],:]
                
                # For download attachments
                st.session_state['selected_project'] = selected_project
                st.session_state['project_select_id'] = select_project_id
                st.session_state['selected_project_enable_edit'] = True
                st.session_state['selected_project_metadata'] = selected_metadata
                st.session_state['selected_project_ref_fq_datasets'] = update_ref_fq_datasets
                st.session_state['selected_project_export'] = project_export_select
                st.session_state['selected_project_enable_delete'] = True


            elif len(selection) > 1:
                
                select_row = selection
                
                # Get original index from projects overview before subset
                selected_project_ix = projects_show.iloc[select_row,:].index # Refers to original index
                selected_project = projects.loc[selected_project_ix,:]
                selected_metadata = metadata.loc[selected_project_ix,:]
                
                update_one = False
                
                show_project_details = False
                
                # For download attachments
                st.session_state['selected_project'] = selected_project
                st.session_state['project_select_id'] = None
                st.session_state['selected_project_enable_edit'] = False
                st.session_state['selected_project_metadata'] = None
                st.session_state['selected_project_ref_fq_datasets'] = None
                st.session_state['selected_project_export'] = selected_project
                st.session_state['selected_project_enable_delete'] = True   


            else:
                show_project_details = False
                #is_shared = True
                select_row = None
                selected_project = None
                selected_metadata = None
                
                st.session_state['project_select_id'] = None
                st.session_state['selected_project'] = None
                st.session_state['selected_project_enable_edit'] = False
                st.session_state['selected_project_metadata'] = None
                st.session_state['selected_project_ref_fq_datasets'] = None
                st.session_state['selected_project_export'] = projects_show
                st.session_state['selected_project_enable_delete'] = False


            # col5a, col6a, col7a, col7b, _, col8a = st.columns([1.75,1.75,1.75, 1.75, 2,3], vertical_alignment='center')

            # with col5a:
                
            #     if st.button('Create', type ='primary', key='create_project', width='stretch', help = 'Create a new Project'):
            #         create_project(reference_og_project_names,
            #                     fq_dataset_og)

            # with col6a:
                
            #     if st.button('Update', key='update_project', disabled = update_disabled, width='stretch', help = 'Update the selected Project'):
                    
            #         if update_one:
            #             update_project(selected_project,
            #                         selected_metadata,
            #                         reference_og_project_names,
            #                         update_ref_fq_datasets)

            #         else:
            #             update_many_projects(selected_project)
                    
            # with col7a:
            #     if st.button('Export', key='export_projects', width='stretch', help = 'Export and download Project overview'):
                    
            #         export_project(project_export_select)

            # with col8a:  
            
            #     on = st.toggle("Details",
            #                     key='show_details_project',
            #                     value=st.session_state['show_details'],
            #                     on_change = extensions.switch_show_details,
            #                     help='Show Details for selected Project')

            if show_project_details:
                
                st_yled.space(72)
                
                # detail_tab_names = [":blue-background[**Features**]",
                #                     ":blue-background[**Datasets**]",
                #                     ":blue-background[**Attachments**]"]
                # # Show Collaborators Tab only if project is owned by user's owner_group

                # detail_tabs = st.tabs(detail_tab_names)

                # Try tabs

                segment_control_options = ['Features', 'Datasets', 'Attachments']
                segment_default = segment_control_options[st.session_state['details_segment_ix']]
                
                project_detail_selection = st_yled.segmented_control(
                        'Project Detail Selection',
                        segment_control_options,
                        key='project_detail_selection',
                        default=segment_default,
                        label_visibility = 'collapsed',
                        on_change = update_segment_default,
                        args = (segment_control_options,),
                        font_weight=500
                    )
                
                #region Detail Features
                if project_detail_selection == 'Features':
                    
                    with st_yled.container(key='project-features-detail-container',
                                        horizontal=True,):

                        with st_yled.container(key='project-features-detail-columns-container',
                                            width=400,
                                            background_color=styles.DATAFRAME_HEADER_BG_COLOR):

                            project_id = selected_project['id_project']
                            project_name = selected_project['name_project']
                            project_description = selected_project['description']
                            project_created = selected_project['created'].strftime('%Y-%m-%d %H:%M')

                            with st_yled.container(horizontal=True,
                                                background_color='#FFFFFF',
                                                width='content',
                                                key='project-features-detail-id'):
                                
                                st.markdown('Project ID', width='content')
                                st.markdown(f'{project_id}', width='content')


                            with st_yled.container(horizontal=True,
                                                background_color='#FFFFFF',
                                                width='content',
                                                key='project-features-detail-name'):
                                
                                st.markdown('Project Name', width='content')
                                st.markdown(f'{project_name}', width='content')
                            
                            with st_yled.container(horizontal=True,
                                                background_color='#FFFFFF',
                                                width='content',
                                                key='project-features-detail-created'):
                                
                                st.markdown('Created', width='content')
                                st.markdown(f'{project_created}', width='content')

                            
                            with st_yled.container(background_color='#FFFFFF',
                                                width='content',
                                                key='project-features-detail-description'):
                                
                                st.markdown('Description', width='content')
                                st.markdown(f'{project_description}', width='content')
                            

                            # project_detail = selected_project.copy()
                            # project_detail_og = project_detail['name_og']
                            
                            # project_detail['created'] = project_detail['created'].strftime('%Y-%m-%d %H:%M')
                            # project_id = project_detail.pop('id_project')
                            # project_id = project_detail.pop('id_str')
                            # project_detail.pop('collaborators')
                            # project_detail.pop('dataset_metadata_keys')
                            # #project_detail.pop('name')                
                            # project_detail.pop('name_og')
                            
                            # project_detail = project_detail.reset_index()
                            # project_detail.columns = ['Project ID', project_id]
                            
                            # project_detail['Project ID'] = [
                            #     'Name',
                            #     'Description',
                            #     'Created',
                            #     'Creator'
                            # ]
                            
                            # st.dataframe(project_detail,
                            #             use_container_width = True,
                            #             hide_index = True,
                            #             key='projects_details_df')
                            
                        
                        with st_yled.container(key='project-features-detail-metadata-container',
                                            width=300,
                                            border=True):
                            
                            st_yled.markdown('Metadata', font_weight=500)
                            
                            if selected_metadata.shape[0] == 0:
                                st_yled.info(':material/notifications: No metadata set. Define in Update Project',
                                            border_width="2.0px",
                                            border_color="#808495",
                                            border_style="solid",
                                            color="#808495",
                                            key='info-no-samples-metadata',
                                            width=400)
                            else:
                                st.dataframe(selected_metadata,
                                            width = 'stretch',
                                            hide_index = True,
                                            column_config = {
                                                'key' : st.column_config.Column('Key'),
                                                'value' : st.column_config.Column('Value'),
                                            },
                                            key='metadata_details_df')
                
                #region Detail Datasets
                if project_detail_selection == 'Datasets':
                    
                    with st.container(border = True,
                                    width=550):

                        st_yled.markdown("Overview of Datasets assigned to the Project", font_size=12, color='#808495')
                        st.write("")

                        if select_project_attached_fq_datasets.shape[0] == 0:
                            
                            st_yled.info(':material/notifications: No Datasets attached to the Project. Attach Datasets in Update Project',
                                        border_width="2.0px",
                                        border_color="#808495",
                                        border_style="solid",
                                        color="#808495",
                                        key='info-no-samples-datasets',
                                        width=480)
                        else:
                            # Limit Max Height of Dataframe
                            if select_project_attached_fq_datasets.shape[0] > 7:
                                max_df_height = 315
                            else:
                                max_df_height = 'content'
                    
                            st.dataframe(select_project_attached_fq_datasets[['id','name', 'description']],
                                        hide_index = True,
                                        column_config = {
                                            'id' : st.column_config.TextColumn('ID', width='small'),
                                            'name' : st.column_config.TextColumn('Name'),
                                            'description' : st.column_config.TextColumn('Description', width = 'medium'),
                                        },
                                        key='select_project_fq_datasets_df',
                                        height = max_df_height)
                    
                #region Detail Attachments   
                if project_detail_selection == 'Attachments':
                    
                    with st.container(border = True,
                                        width=450):
                        
                        select_project_id = st.session_state['project_select_id']
                                    
                        # Value is none if not run
                        download_attach_key_name = f'download_attachments_select_{select_project_id}'
                        
                        if download_attach_key_name in st.session_state:
                            attach_select = st.session_state[download_attach_key_name]
                        else:
                            attach_select = None
                        
                        with st_yled.container(horizontal=True, horizontal_alignment='right'):
                            
                            st_yled.markdown("Overview of File Attachments", font_size=12, color='#808495')

                            if attach_select and len(attach_select.selection['rows']) == 1:
                                
                                select_ix = attach_select.selection['rows'][0]
                                select_attachment = select_project_attachments.iloc[select_ix,:]
                                select_attachment_id = int(select_attachment['id'])
                                select_attachment_name = select_attachment['name']
                                
                                st.download_button('Download',
                                                data=datamanager.get_project_attachment_file_download(select_attachment_id),
                                                file_name = select_attachment_name,
                                                key='download_attachment')
                            else:
                                disable_download = True
                                select_attachment_id = 0

                                st.button('Download', disabled = True, help = 'Select attachment to download')

                        if select_project_attachments.shape[0] == 0:
                            
                            st_yled.info(':material/notifications: No Attachments for the Project. Add Attachments in Update Project',
                                        border_width="2.0px",
                                        border_color="#808495",
                                        border_style="solid",
                                        color="#808495",
                                        key='info-no-attachments',
                                        width=400)
                        else:

                            # Limit Max Height of Dataframe
                            if select_project_attachments.shape[0] > 7:
                                max_df_height = 315
                            else:
                                max_df_height = 'content'
                                        
                            st.dataframe(select_project_attachments,
                                            hide_index = True,
                                            column_config = {
                                                'id' : None,
                                                'name' : st.column_config.Column('Filename'),
                                                'description' : None,
                                                'project_id' : None
                                            },
                                            on_select = update_attachment_select,
                                            selection_mode='single-row',
                                            key='attachment_details_df',
                                            height = max_df_height)
                            

#region Data

# Data
reference_og_project_names = datamanager.get_project_owner_group(st.session_state["jwt_auth_header"])['name']
# Get projects and metadata for both owner group and collaborator
projects, metadata = datamanager.get_project_metadata_overview(st.session_state["jwt_auth_header"])

# Map in attachment names
# project_attachments = datamanager.get_project_attachments(st.session_state["jwt_auth_header"])
# # Combine attachments to lists

# # Map in attachment names to projects
# project_attachments_list = project_attachments.groupby('project_id')['name'].apply(list)
# projects = projects.merge(project_attachments_list, left_on = 'id_project', right_on='project_id', how='left')
# projects['name'] = projects['name'].apply(lambda x: [] if x is np.nan else x)

my_owner_group_name = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].values[0]

# Ignore metadata for fastq
fq_dataset_og = datamanager.get_fq_dataset_owner_group(st.session_state["jwt_auth_header"])
fq_dataset_collab = datamanager.get_fq_dataset_collab(st.session_state["jwt_auth_header"])

# Add id string for search
projects['id_str'] = projects['id_project'].astype(str)

# Add metadata
projects_show = pd.concat([projects,metadata], axis=1)

# Render UI
uimain(projects_show, my_owner_group_name, fq_dataset_og, fq_dataset_collab)