# readstore-basic/frontend/streamlit/app_pages/project.py

import time
import string

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

# Applying the custom CSS in the app
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

# Reset session state for selecting datasets for projects
if 'available' in st.session_state:
    del st.session_state['available']
if 'selected' in st.session_state:
    del st.session_state['selected']
if 'selected_input' in st.session_state:
    del st.session_state['selected_input']
if 'available_input' in st.session_state:
    del st.session_state['available_input']
if 'available_collab' in st.session_state:
    del st.session_state['available_collab']
if 'selected_collab' in st.session_state:
    del st.session_state['selected_collab']

# Methods

# Assign and remove datasets to project
def add_selected_datasets(fq_datasets, selected_rows):
                
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

# # USERS
@st.dialog('Create Project', width='large')
def create_project(reference_project_names: pd.Series,
                   reference_fq_datasets: pd.DataFrame):
    
    reference_project_names = reference_project_names.str.lower()
    reference_project_names = reference_project_names.tolist()
    
    reference_fq_datasets = reference_fq_datasets.sort_values(by='name')
    
    tab1, tab2, tab3 = st.tabs([":blue-background[**Features**]", ":blue-background[**Datasets**]", ":blue-background[**Attachments**]"])
    
    with tab1:
        st.write(' ')
        
        name = st.text_input("Enter Project Name",
                                max_chars=150,
                                help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')
        
        description = st.text_area("Enter Project Description",
                                help = 'Description of the project.',)
        
        
        col1c, col2c = st.columns([11,1], vertical_alignment='top')
            
        with col1c:
            
            tab1c, tab2c = st.tabs([":blue-background[**Metadata**]", ":blue-background[**Dataset Keys**]"])
                
            with tab1c:
                
                st.write('Key-value pairs to describe and group project metadata')
                
                metadata_df = st.data_editor(
                    pd.DataFrame(columns=['key', 'value']),
                    use_container_width=True,
                    hide_index=True,
                    column_config = {
                        'key' : st.column_config.TextColumn('Key'),
                        'value' : st.column_config.TextColumn('Value')
                    },
                    num_rows ='dynamic',
                    key = 'create_metadata_df'
                )

            with tab2c:
                
                st.write('Metadata keys for datasets attached to the project')

                # Value column is hidden so that value is set to None for each created key
                dataset_meta_keys_df = st.data_editor(
                    pd.DataFrame(columns=['key', 'value']),
                    use_container_width=True,
                    hide_index=True,
                    column_config = {
                        'key' : st.column_config.Column('Key'),
                        'value' : None
                    },
                    num_rows ='dynamic',
                    key = 'create_dataset_metadata_keys_df'
                )
        
        with col2c:
            with st.popover(':material/help:'):
                
                st.write('Define Project and Dataset Metadata')
                st.write('**Project Metadata** are key-value pairs to describe project attributes, e.g. "assay":"RNA-Seq"')
                st.write("""**Dataset Keys** are templates for attached datasets' metadata""")
                st.write('Dataset Metadata are autmatically prefilled with Dataset Keys')
                st.write('')
        
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
                st.write('Select **Datasets** to attach to project')
            
            with col2a:
                with st.popover(':material/help:'):
                    
                    st.write('Attach **Datasets** to the project.')
                    st.write('Click on item checkbox in **Available Dataset** table to select')
                    st.write('Click on item checkbox in **Attached Dataset** table to de-select')
                    
            # Columns for available and selected datasets
            col1, col2, col3 = st.columns([5.5,1,5.5])
            
            # First col to select available datasets
            with col1:
                
                with st.container(border = True):
                    
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
                                                use_container_width=True,
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
                with st.container(border = True):              
                    
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
                                                use_container_width=True,
                                                hide_index = True,
                                                column_config = {
                                                    'id' : st.column_config.TextColumn('ID'),
                                                    'name' : st.column_config.TextColumn('Name'),
                                                    'owner_group_name' : None,
                                                },
                                                key='create_collab_datasets_select_df',
                                                on_select = 'rerun',
                                                selection_mode='multi-row')
            
            with col2:
                
                # Spacer Container
                st.container(height = 100, border = False)
                st.button(':material/arrow_forward:', use_container_width=True, type='primary', on_click=add_selected_datasets, args = (fq_datasets_show, fq_avail_df.selection['rows']))
                st.button(':material/arrow_back:', use_container_width=True, type='primary', on_click=remove_selected_datasets, args = (fq_datasets_select_show, fq_select_df.selection['rows']))

            
        select_form_fq_datasets()
    
    
    with tab3:
        
        st.write(' ')
        
        st.write('Attach files to the project.')
        
        uploaded_files = st.file_uploader(
            "Choose Files to Upload",
            help = "Upload attachments for the dataset. Attachments can be any file type.",
            accept_multiple_files=True
        )
        
        st.write(' ')
    
    _ , col_conf = st.columns([9,3])
    
    with col_conf:
        if st.button('Confirm', type ='primary', key='ok_create_project', use_container_width=True):
            
            selected_datasets = st.session_state['selected']
            selected_datasets_ids = selected_datasets['id'].tolist()
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Replace all None values with empty string
            metadata_df = metadata_df.fillna('')
                        
            keys = metadata_df['key'].tolist()
            keys = [k.lower() for k in keys]
            values = metadata_df['value'].tolist()
            
            key_templates = dataset_meta_keys_df['key'].tolist()
            key_templates = [k.lower() for k in key_templates]
            
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
                    st.error(f'Metadata Key {k}: Reserved keyword, please choose another key')
                    break
            else:
                # Validate dataset key formats
                for k in key_templates:
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.error(f'Metadata key {k}: Reserved keyword, please choose another key')
                        break
                
                # If no error occured validate name
                else:            
                    # Validate username / Better use case
                    if name == '':
                        st.error('Project Name is empty')
                    elif name == 'No Project':
                        st.error('No Project is a reserved keyword.')
                    elif not extensions.validate_charset(name):
                        st.error('Project Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces')
                    elif name.lower() in reference_project_names:
                        st.error('Project Name already exists in Group')
                    else:
                        metadata = {k:v for k,v in zip(keys,metadata_df['value'])}
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
                        
#region Update Project
@st.dialog('Update Project', width='large')
def update_project(project_select_df: pd.DataFrame,
                   metadata_select_df: pd.DataFrame,
                   reference_project_names: pd.Series,
                   reference_fq_datasets: pd.DataFrame
                   ):
    
    project_id = int(project_select_df['id_project'])
    name_old = project_select_df['name_project']
    description_old = project_select_df['description']
    collaborators = project_select_df['collaborators']
    dataset_metadata_keys = project_select_df['dataset_metadata_keys']
    dataset_metadata_keys = list(dataset_metadata_keys.keys())
    
    reference_project_names = reference_project_names[reference_project_names != name_old]
    reference_project_names = reference_project_names.str.lower()
    reference_project_names = reference_project_names.tolist()
    
    select_project_attachments = datamanager.get_project_attachments(st.session_state["jwt_auth_header"], project_id)
    attachment_ref_names = select_project_attachments['name'].tolist()
    
    reference_fq_datasets = reference_fq_datasets.sort_values(by='name')
    
    tab1, tab2, tab3 = st.tabs([":blue-background[**Features**]", ":blue-background[**Datasets**]", ":blue-background[**Attachments**]"])
    
    #region TAB1 Data  
    with tab1:
        st.write(' ')
        
        name = st.text_input("Enter Project Name",
                                max_chars=150,
                                help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
                                value = name_old)
        
        description = st.text_area("Enter Project Description",
                                help = 'Description of the project.',
                                value = description_old)
        
        col1c, col2c = st.columns([11,1], vertical_alignment='top')
            
        with col1c:
            
            tab1c, tab2c = st.tabs([":blue-background[**Metadata**]", ":blue-background[**Dataset Keys**]"])
                
            with tab1c:
                
                st.write('Key-value pairs to describe and group project metadata')
                
                metadata_select_df = metadata_select_df.astype(str)
                
                metadata_df = st.data_editor(
                    metadata_select_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config = {
                        'key' : st.column_config.TextColumn('Key', width='medium'),
                        'value' : st.column_config.TextColumn('Value', width='medium')
                    },
                    num_rows ='dynamic',
                    key = 'create_metadata_df'
                )

            with tab2c:
                
                st.write('Metadata keys for datasets attached to the project')

                # Value column is hidden so that value is set to None for each created key
                dataset_meta_keys_df = st.data_editor(
                    pd.DataFrame({
                        'key' : dataset_metadata_keys,
                        'value' : None},
                                 dtype=str),
                    use_container_width=True,
                    hide_index=True,
                    column_config = {
                        'key' : st.column_config.TextColumn('Key', width='medium'),
                        'value' : None
                    },
                    num_rows ='dynamic',
                    key = 'create_dataset_metadata_keys_df'
                )
        
        with col2c:
            with st.popover(':material/help:'):
                
                st.write('Define Project and Dataset Metadata')
                st.write('**Project Metadata** are key-value pairs to describe project attributes, e.g. "assay":"RNA-Seq"')
                st.write("""**Dataset Keys** are templates for attached datasets' metadata""")
                st.write('Dataset Metadata are autmatically prefilled with Dataset Keys')
                st.write('')
        
        # Show delete button if project is owned by user's owner_group
        col1expander,_ = st.columns([3,9])
        with col1expander:
            with st.expander('Delete Project', icon=":material/delete_forever:",
                            ):
                if st.button('Confirm', key='delete_project'):
                    
                    datamanager.delete_project(project_id)
                    
                    st.cache_data.clear()
                    st.rerun()

        
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
            col1a, col2a = st.columns([11,1])
            
            with col1a:
                st.write('Attach **Datasets** to the project.')
            
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
                
                with st.container(border = True):
                    
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
                                                use_container_width=True,
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
                with st.container(border = True):              
                    
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
                                                use_container_width=True,
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
                    st.button(':material/arrow_forward:', use_container_width=True, type='primary', on_click=add_selected_datasets, args = (fq_datasets_show, fq_avail_df.selection['rows']))
                    st.button(':material/arrow_back:', use_container_width=True, type='primary', on_click=remove_selected_datasets, args = (fq_datasets_select_show, fq_select_df.selection['rows']))
            

        update_select_form_fq_datasets()
    
    #region TAB3 Attachments
    with tab3:
        select_attach_update = st.dataframe(
            select_project_attachments,
            hide_index = True,
            use_container_width=True,
            column_config = {
                'id' : None,
                'name' : st.column_config.Column('Name'),
                'description' : None,
                'project_id' : None},
            on_select = 'rerun',
            selection_mode='multi-row',
            key = 'select_attachment_update')
        
        if len(select_attach_update.selection['rows']) > 0:
            delete_disabled = False
        else:
            delete_disabled = True
    
        st.write(' ')
    
        uploaded_files = st.file_uploader(
            "Choose Files to Upload", accept_multiple_files=True
        )
        
        st.write(' ')
    
        col1attach, _ = st.columns([4,8])
    
        with col1attach:
            with st.expander('Delete Attachment(s)', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_attachments', disabled=delete_disabled):
                    
                    attach_ixes = select_attach_update.selection['rows']
                    attach_ids = select_project_attachments.loc[attach_ixes,'id'].tolist()
                    
                    for attach_id in attach_ids:
                        datamanager.delete_project_attachment(attach_id)
                    else:
                        st.cache_data.clear()
                        st.rerun()
    
    _ , col_conf = st.columns([9,3])
    with col_conf:
        #region Confirm
        if st.button('Confirm', type ='primary', key='ok_update_project', use_container_width=True):
            
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
            # Replace all None values with empty string
            metadata_df = metadata_df.fillna('')
            
            keys = metadata_df['key'].tolist()
            keys = [k.lower() for k in keys]
            values = metadata_df['value'].tolist()
                    
            key_templates = dataset_meta_keys_df['key'].tolist()
            key_templates = [k.lower() for k in key_templates]
            
            # Attachment Data
            file_names = [file.name for file in uploaded_files]
            file_bytes = [file.getvalue() for file in uploaded_files]
            
            # Validate metadata key formats
            for k, v in zip(keys, values):
                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                    st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                    break
                if k in uiconfig.METADATA_RESERVED_KEYS:
                    st.error(f'Metadata key {k}: Reserved keyword, please choose another key')
                    break
            else:
                # Validate dataset key formats
                for k in key_templates:
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.error(f'Metadata key {k}: Reserved keyword, please choose another key')
                        break
                
                # If no error occured validate name
                else:
                    # Validate username / Better use case
                    if name == '':
                        st.error('Name is empty')
                    elif name == 'No Project':
                        st.error('No Project is a reserved keyword.')
                    elif not extensions.validate_charset(name):
                        st.error('Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces')
                    elif name.lower() in reference_project_names:
                        st.error('Name already exists in Group')
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
              

#region Export Project
@st.dialog('Export Projects')            
def export_project(project_view: pd.DataFrame):
    
    st.write('Save Projects and Metadata as .csv file')
    
    project_view_export = project_view.drop(columns=['dataset_metadata_keys',
                                                     'collaborators',
                                                     'id_str',
                                                     'name_og'])
    
    project_view_export = project_view_export.rename(columns={'id_project' : 'id',
                                                    'name_project' : 'name',
                                                    'owner_username' : 'creator',
                                                    'name' : 'attachments'})
    
    st.download_button('Download .csv',
                       project_view_export.to_csv(index=False).encode("utf-8"),
                       'projects.csv',
                       'text/csv')
    
#region Data

    
# Data

reference_og_project_names = datamanager.get_project_owner_group(st.session_state["jwt_auth_header"])['name']
# Get projects and metadata for both owner group and collaborator
projects, metadata = datamanager.get_project_metadata_overview(st.session_state["jwt_auth_header"])

# Map in attachment names
project_attachments = datamanager.get_project_attachments(st.session_state["jwt_auth_header"])
# Combine attachments to lists

# Map in attachment names to projects
project_attachments_list = project_attachments.groupby('project_id')['name'].apply(list)
projects = projects.merge(project_attachments_list, left_on = 'id_project', right_on='project_id', how='left')
projects['name'] = projects['name'].apply(lambda x: [] if x is np.nan else x)

reference_owner_group_names = sorted(projects['name_og'].unique().tolist())
my_owner_group_name = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].values[0]

# Ignore metadata for fastq
fq_dataset_og = datamanager.get_fq_dataset_owner_group(st.session_state["jwt_auth_header"])
fq_dataset_collab = datamanager.get_fq_dataset_collab(st.session_state["jwt_auth_header"])

# Add id string for search
projects['id_str'] = projects['id_project'].astype(str)

#endregion

#region UI

# Navbar
col1, col2, col3, col4, col5 = st.columns([3,3,2.5,2.75,0.75], vertical_alignment='center')

with col1:

    search_value_projects = st.text_input("Search Projects",
                        help = 'Search for Projects',
                        placeholder='Search Projects',
                        key = 'search_projects',
                        label_visibility = 'collapsed')

with col4:
    st.toggle("Metadata", key='show_metadata', help='Switch to Projects Metadata View')

with col5:
    if st.button(':material/refresh:', key='refresh_projects', help='Refresh Page'):
        on_click = extensions.refresh_page()
    

col_config_user = {
        'id_project' : st.column_config.TextColumn('ID', width='small'),
        'name_project' : st.column_config.TextColumn('Name'),
        'description' : st.column_config.TextColumn('Description'),
        'name_og' : None,
        'created' : st.column_config.DateColumn('Created'),
        'archived' : None,
        'owner_username' : None,
        'collaborators' : None,
        'dataset_metadata_keys' : None,
        'id_str' : None,
        'name' : None,
    }

col_config_meta = {
        'id_project' : st.column_config.TextColumn('ID', width='small'),
        'name_project' : st.column_config.TextColumn('Name'),
        'name_og' : None,
        'id_str' : None
    }

# Add metadata
projects_show = pd.concat([projects,metadata], axis=1)

# Search Filter
projects_show = projects_show.loc[
    (projects_show['name_project'].str.contains(search_value_projects, case=False) |
     projects_show['id_str'].str.contains(search_value_projects, case=False)),:
]


# Dynamically adjust height of dataframe
if st.session_state['show_details']:
    if (len(projects_show) < 10):
        project_df_height = None
    else:
        project_df_height = 370 # 7 Rows
elif (len(projects_show) < 14):
    project_df_height = None
else:
    # Full Height for 14 rows
    project_df_height = 500

# Filter out meta columns from selected view which are all None

# Remove those meta cols from projects_show which are all None
meta_cols_all_none = projects_show.loc[:,metadata.columns].isna().all()
meta_cols_all_none = meta_cols_all_none[meta_cols_all_none].index

# Remove all columns which are all None
projects_show = projects_show.drop(columns=meta_cols_all_none)

# Define which columns to show, depending on show_metadata toggle
if st.session_state.show_metadata:
    # How selected projects show only metadata for subset
    # Show all meatadata columns which are not all None
    meta_cols_show = list(filter(lambda x: x not in meta_cols_all_none, metadata.columns))
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

# TODO Change naming here
projects_select = st.dataframe(projects_show[show_cols],
                    column_config = col_config,
                    selection_mode='single-row',
                    hide_index = True,
                    on_select = 'rerun',
                    use_container_width=True,
                    key='projects_select_df',
                    height = project_df_height)
        
if len(projects_select.selection['rows']) == 1:
    
    # Subset projects and metadata to feed into update/details
    # Get index from selection
    select_row = projects_select.selection['rows'][0]
    
    # Get original index from projects overview before subset
    selected_project_ix = projects_show.iloc[[select_row],:].index[0]
    
    selected_project = projects.loc[selected_project_ix,:]
    # metadata as series to directly show as dataframe
    selected_metadata = metadata.loc[selected_project_ix,:]
    selected_metadata = selected_metadata.dropna().reset_index()
    selected_metadata.columns = ['key', 'value']
    
    # Check if the selected project is shared by user from different group
    if selected_project['name_og'] == my_owner_group_name:
        #is_shared = False
        update_ref_fq_datasets = fq_dataset_og
        update_disabled = False
    else:
        #is_shared = True
        update_ref_fq_datasets = fq_dataset_collab
        update_disabled = True
    
    if st.session_state['show_details']:
        show_project_details = True
    else:
        show_project_details = False
    
    select_project_id = selected_project['id_project']
    select_project_attached_fq_datasets = update_ref_fq_datasets.loc[
        update_ref_fq_datasets['project'].apply(lambda x: any((e == select_project_id) for e in x)),:
    ]
    
    select_project_attachments = project_attachments.loc[
        project_attachments['project_id'] == select_project_id,:
    ]
    
else:
    update_disabled = True
    show_project_details = False
    #is_shared = True
    select_row = None
    selected_project = None
    selected_metadata = None

col5a, col6a, col7a, col7b, _, col8a = st.columns([1.75,1.75,1.75, 1.75, 2,3], vertical_alignment='center')

with col5a:
    
    if st.button('Create', type ='primary', key='create_project', use_container_width=True, help = 'Create a new Project'):
        create_project(reference_og_project_names,
                       fq_dataset_og)

with col6a:
    
    if st.button('Update', key='update_project', disabled = update_disabled, use_container_width=True, help = 'Update the selected Project'):
        update_project(selected_project,
                       selected_metadata,
                       reference_og_project_names,
                       update_ref_fq_datasets)

with col7a:
    if st.button('Export', key='export_projects', use_container_width=True, help = 'Export and download Project overview'):
        
        export_project(projects_show)

with col8a:  
   
   on = st.toggle("Details",
                  key='show_details_project',
                  value=st.session_state['show_details'],
                  on_change = extensions.switch_show_details,
                  help='Show Details for selected Project')


if show_project_details:
    
    st.divider()
    
    detail_tab_names = [":blue-background[**Features**]",
                        ":blue-background[**Datasets**]",
                        ":blue-background[**Attachments**]"]
    # Show Collaborators Tab only if project is owned by user's owner_group

    detail_tabs = st.tabs(detail_tab_names)

    #region Detail Features
    with detail_tabs[0]:
    
        col1d, col2d = st.columns([7,5])
        
        with col1d:
            with st.container(border = True, height = 300):
                
                project_detail = selected_project.copy()
                project_detail_og = project_detail['name_og']
                
                project_detail['created'] = project_detail['created'].strftime('%Y-%m-%d %H:%M')
                project_id = project_detail.pop('id_project')
                project_id = project_detail.pop('id_str')
                project_detail.pop('collaborators')
                project_detail.pop('dataset_metadata_keys')
                project_detail.pop('name')                
                project_detail.pop('name_og')
                
                project_detail = project_detail.reset_index()
                project_detail.columns = ['Project ID', project_id]
                
                project_detail['Project ID'] = [
                    'Name',
                    'Description',
                    'Created',
                    'Creator'
                ]
                
                st.write('**Details**')
                st.dataframe(project_detail,
                            use_container_width = True,
                            hide_index = True,
                            key='projects_details_df')
                
                st.write(' ')
            
        with col2d:
            with st.container(border = True, height = 300):
                
                st.write('**Metadata**')
                
                st.dataframe(selected_metadata,
                            use_container_width = True,
                            hide_index = True,
                            column_config = {
                                'key' : st.column_config.Column('Key'),
                                'value' : st.column_config.Column('Value'),
                            },
                            key='metadata_details_df')
    
    #region Detail Datasets
    with detail_tabs[1]:
        
        with st.container(border = True, height = 300):
                
            st.write('**Datasets**')
            
            st.dataframe(select_project_attached_fq_datasets[['id','name', 'description']],
                        use_container_width = True,
                        hide_index = True,
                        column_config = {
                            'id' : st.column_config.TextColumn('ID', width='small'),
                            'name' : st.column_config.TextColumn('Name'),
                            'description' : st.column_config.TextColumn('Description', width = 'medium'),
                        },
                        key='select_project_fq_datasets_df')
    
    #region Detail Attachments   
    with detail_tabs[2]:
        
        with st.container(border = True, height = 300):
        
            st.write('**Attachments**')
            attach_select = st.dataframe(select_project_attachments,
                                        hide_index = True,
                                        use_container_width = True,
                                        column_config = {
                                            'id' : None,
                                            'name' : st.column_config.Column('Name'),
                                            'description' : None,
                                            'project_id' : None
                                        },
                                        on_select = 'rerun',
                                        selection_mode='single-row',
                                        key='attachment_details_df')
            
            if len(attach_select.selection['rows']) == 1:
                select_ix = attach_select.selection['rows'][0]
                select_attachment = select_project_attachments.loc[select_ix,:]
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