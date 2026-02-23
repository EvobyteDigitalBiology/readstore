# readstore-basic/frontend/streamlit/app_pages/pro_data.py
import string
import uuid

import streamlit as st
import pandas as pd
import numpy as np
import os
import st_yled
from st_yled import split_button

import extensions
import datamanager
import styles
import uiconfig

st_yled.init()

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# Session state for showing archived processed data
if not 'pro_data_show_archived_versions' in st.session_state:
    st.session_state['pro_data_show_archived_versions'] = False

if not 'pro_details_segment_ix' in st.session_state:
    st.session_state['pro_details_segment_ix'] = 0

if not 'pro_data_meta_filter_hash' in st.session_state:
    st.session_state['pro_data_meta_filter_hash'] = str(uuid.uuid4())

if not 'pro_data_split_but_hash' in st.session_state:
    st.session_state['pro_data_split_but_hash'] = str(uuid.uuid4())

if not 'show_details' in st.session_state:
    st.session_state['show_details'] = True

if not 'show_metadata' in st.session_state:
    st.session_state['show_metadata'] = False

if not 'show_pro_data_archived' in st.session_state:
    st.session_state['show_pro_data_archived'] = False

if not 'toast_cache' in st.session_state:
    st.session_state['toast_cache'] = None

if not 'error_cache' in st.session_state:
    st.session_state['error_cache'] = None

if not 'selected_pro_data' in st.session_state:
    st.session_state['selected_pro_data'] = None

if not 'selected_pro_data_metadata' in st.session_state:
    st.session_state['selected_pro_data_metadata'] = None

if not 'selected_pro_data_enable_edit' in st.session_state:
    st.session_state['selected_pro_data_enable_edit'] = False

if not 'selected_pro_data_enable_delete' in st.session_state:
    st.session_state['selected_pro_data_enable_delete'] = True

if not 'selected_pro_data_export' in st.session_state:
    st.session_state['selected_pro_data_export'] = None

if not 'pro_data_select_project_names' in st.session_state:
    st.session_state['pro_data_select_project_names'] = []

#region FUNCTIONS

def reset_meta_filter_hash():
    """Reset pro_data metadata filter hash to force re-rendering of metadata filter UI"""
    st.session_state['pro_data_meta_filter_hash'] = str(uuid.uuid4())

def switch_show_archived_details():
    if not 'show_pro_data_archived' in st.session_state:
        st.session_state.show_pro_data_archived = True
    else: 
        st.session_state.show_pro_data_archived = not st.session_state.show_pro_data_archived

def update_selected_project_names():
    st.session_state['pro_data_select_project_names'] = st.session_state['multiselect_pro_data_project_names']

def update_show_archived_versions():
    st.session_state['pro_data_show_archived_versions'] = not st.session_state['pro-data-show-archived-toggle']

def reset_selected_project_names():
    st.session_state['pro_data_select_project_names'] = []

def update_segment_default(segment_control_options):
    
    # detail_selection can be none
    detail_selection = st.session_state['pro_detail_selection']
    
    # Update the index of the segment control if the selection is not None
    if detail_selection:    
        ix = segment_control_options.index(detail_selection)
        st.session_state['pro_details_segment_ix'] = ix


#region Create ProData
@st.dialog('Create ProData Entry', width='medium', on_dismiss=reset_selected_project_names)
def create_pro_data(ref_dataset_projects_df: pd.DataFrame,
                    ref_name_dataset_df: pd.DataFrame,
                    data_types: list):
    """Create empty dataset

    Args:
        ref_dataset_projects_df: Reference dataframe with project dataset mapping
        ref_name_dataset_df: Reference dataframe with ProData name and dataset mapping
    """

    ref_dataset_projects_df = ref_dataset_projects_df.copy()
    ref_name_dataset_df = ref_name_dataset_df.drop_duplicates()

    project_names_select = st.session_state['pro_data_select_project_names']
    
    # Define Tabs
    tab1, tab2 = st_yled.tabs(["Features", "Dataset"], font_size=14, font_weight=500)

    with tab1:
        
        st_yled.markdown('Set Processed Data for a Dataset', font_size=12, color='#808495')

        # pass
        name = st_yled.text_input("ProData Name",
                            max_chars=150,
                            help = 'Name must only contain [0-9][a-z][A-Z][.-_@ ]',
                            width = 400,
                            border_style='none',
                            border_width='0px',
                            key='pro_data_name')
        st.write("")

        data_path = st_yled.text_input("ProData Path",
                                max_chars=1000,
                                help = 'Path to the data file, which must be a valid and accessible by the app.',
                                width = 512,
                                border_style='none',
                                border_width='0px',
                                key='pro_data_path')
        st.write("")

        # TODO Make dropdown of existing data types?
    
        data_type = st_yled.selectbox("ProData Data Type",
                            options=data_types,
                            index=None,
                            help = 'Select or type a Data Type. Data Type must only contain [0-9][a-z][A-Z][.-_@] (no spaces).',
                            width = 240,
                            border_style='none',
                            placeholder='Select or type in a Data Type',
                            border_width='0px',
                            key='pro_data_type',
                            accept_new_options=True)
        st.write("")
        
        description = st_yled.text_area("ProData Description",
                                        help = 'Description of ProData.',
                                        width = 512,
                                        border_style='none',
                                        border_width='0px',
                                        key = 'create_pro_data_description_input')
        
        st.write("")
        
        st_yled.markdown('Metadata', font_size=14, font_weight=500)
        
        with st_yled.container(key='pro-data-metadata-info'):
            st_yled.markdown("Processed Data metadata must be provided as key-value pairs.", font_size=12, color='#808495')
            st_yled.markdown("Metadata facilitate grouping and filtering of ProData entries by pre-defined features.", font_size=12, color='#808495')
        
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

    with tab2:
        
        with st_yled.container(key='project-attachments-info'):
            
            st_yled.markdown('Attach Processed Data to a Dataset', font_size=12, color='#808495')

            project_options = ref_dataset_projects_df['project_name'].dropna().unique()
            project_options = sorted(project_options)
            project_options.insert(0, 'No Project')
            
            # Select project to attach dataset to
            st.multiselect("Filter Datasets by Project",
                    project_options,
                    help = 'Attach the dataset to project(s)',
                    placeholder='',
                    key='multiselect_pro_data_project_names',
                    on_change=update_selected_project_names,
                    width = 360)
            
            if project_names_select:
                if 'No Project' in project_names_select:
                    # Rename Project Name to No Project
                    ref_dataset_projects_df.loc[
                        ref_dataset_projects_df['project_name'].isna(), 'project_name'] = 'No Project'    
                    
                ref_dataset_projects_df = ref_dataset_projects_df.loc[
                    ref_dataset_projects_df['project_name'].isin(project_names_select),:]
            
            dataset_id_options = ref_dataset_projects_df['dataset_id'].dropna().unique()
            dataset_name_options = ref_dataset_projects_df['dataset_name'].dropna().unique()

            # Concatenate dataset id and name for selection
            dataset_options = []
            for did, d_name in zip(dataset_id_options, dataset_name_options):
                dataset_options.append(f"ID{did} {d_name}")
            
            dataset_select = st.selectbox('Select Dataset',
                                          options=dataset_options,
                                          placeholder='',
                                          key='pro_data_dataset',
                                          index=None,
                                        width = 420)
            
            if dataset_select:
                
                # TODO: Handle Case Where dataset name contains spaces -> split only on first space to get id and name
                select_name = ' '.join(dataset_select.split(' ')[1:])

                dataset_id = ref_dataset_projects_df.loc[
                    ref_dataset_projects_df['dataset_name'] == select_name,'dataset_id'].values[0]
            else:
                dataset_id = None

        st.write("")
        st.write("")

    with st.container(horizontal=True, horizontal_alignment='right'):
        
        if st.button('Cancel', key='cancel_create_pro_data'):
            reset_selected_project_names()
            st.rerun()

        if st.button('Confirm', type='primary', key='ok_create_pro_data'):
            
            ref_name_check = ref_name_dataset_df[
                (ref_name_dataset_df['fq_dataset'] == dataset_id) & 
                (ref_name_dataset_df['name'] == name)]
            
            name = name.strip()

            if name == '':
                st.session_state['error_cache'] = "Please enter a ProData Name."
            elif not extensions.validate_charset(name):
                st.session_state['error_cache'] = 'ProData Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.'
            elif data_type == '' or data_type is None:
                st.session_state['error_cache'] = "Please enter a ProData Data Type."
            elif not extensions.validate_charset(data_type):
                st.session_state['error_cache'] = 'ProData Data Type: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.'
            elif data_path == '':
                st.session_state['error_cache'] = "Please enter an file path"
            elif not os.path.isfile(data_path):
                st.session_state['error_cache'] = "Entered path for ProData File not found"
            elif dataset_id is None:
                st.session_state['error_cache'] = "Please select a dataset to attach ProData entry to."
            # Test dataset_id name combination exists
            elif not ref_name_check.empty:
                st.session_state['error_cache'] = "ProData Name already exists for selected Dataset. Use **Update** ProData instead."
            else:
                # Remove na values from metadata key column
                metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
                # Replace all None values with empty string
                metadata_df = metadata_df.loc[metadata_df['key'] != '', :]
                metadata_df = metadata_df.fillna('')
                
                # Validate ProData Metadata
                pro_metadata_keys = metadata_df['key'].tolist()
                pro_metadata_values = metadata_df['value'].tolist()
                pro_metadata_keys = [k.lower() for k in pro_metadata_keys]
                pro_metadata_values = [v.strip() for v in pro_metadata_values]
                
                for k, v in zip(pro_metadata_keys, pro_metadata_values):                        
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.session_state['error_cache'] = f'Key {k}: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.session_state['error_cache'] = f'Metadata Key **{k}**: Reserved keyword, please choose another key'
                        break
                else:
                    metadata = {k:v for k,v in zip(pro_metadata_keys, pro_metadata_values)}
                    
                    datamanager.create_pro_data(st.session_state["jwt_auth_header"],
                                                name = name,
                                                data_type = data_type,
                                                description = description,
                                                upload_path = data_path,
                                                metadata = metadata,
                                                fq_dataset = dataset_id)

                    reset_selected_project_names()
                    st.cache_data.clear()
                    st.rerun()


    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None

#region Update ProData

# continue HERE: Update Rules for ProData

@st.dialog('Update ProData Version', width='medium', on_dismiss=reset_selected_project_names)
def update_pro_data(pro_data_update: pd.Series,
                    pro_data_metadata_update: pd.DataFrame,
                    data_types: list):
    """Update ProData entry
    
    Create a ProData entry with higher version for the selected ProData Entry
    Data Type, Description, Metadata and Upload Path can be updated

    Args:
        pro_data_update: Series with ProData entry to update
        pro_data_metadata_update: DataFrame with metadata keys and values to update
    """

    pro_data_id = pro_data_update['id']
    dataset_id = pro_data_update['fq_dataset']
    data_type = pro_data_update['data_type']
    
    st_yled.markdown('Update the version of the ProData entry.', font_size=12, color='#808495')
    st_yled.markdown('Description and Metadata can be updated.', font_size=12, color='#808495')

    name = st_yled.text_input("ProData Name",
                            max_chars=150,
                            width = 400,
                            border_style='none',
                            value=pro_data_update['name'],
                            border_width='0px',
                            key='pro_data_name',
                            disabled=True)

    st.write("")

    data_path = st_yled.text_input("ProData Path",
                                max_chars=1000,
                                help = 'Path to the data file, which must be a valid and accessible by the app.',
                                width = 512,
                                border_style='none',
                                border_width='0px',
                                value=pro_data_update['upload_path'],
                                key='pro_data_path',
                                disabled=True)

    st.write("")
    
    description = st.text_area("ProData Description",
                                    help = 'Description of ProData',
                                    width = 512)
    
    
    st_yled.markdown('Metadata', font_size=14, font_weight=500)
        
    with st_yled.container(key='pro-data-metadata-info'):
        st_yled.markdown("Processed Data metadata must be provided as key-value pairs.", font_size=12, color='#808495')
        st_yled.markdown("Metadata facilitate grouping and filtering of ProData entries by pre-defined features.", font_size=12, color='#808495')
    
    if pro_data_metadata_update.empty:
        pro_data_metadata_update = pd.DataFrame({'key' : [''], 'value' : ['']})
    else:
        pro_data_metadata_update = pro_data_metadata_update.astype(str)

    metadata_df = st.data_editor(
        pro_data_metadata_update,
        width = 400,
        hide_index=True,
        column_config = {
            'key' : st.column_config.TextColumn('Key'),
            'value' : st.column_config.TextColumn('Value')
        },
        num_rows ='dynamic',
        key = 'create_metadata_df'
    )

    st.write("")
    st.write("")
      
    with st.container(horizontal=True, horizontal_alignment='right'):
        
        if st.button('Cancel', key='cancel_update_pro_data'):
            reset_selected_project_names()
            st.rerun()

        if st.button('Confirm', type ='primary', key='ok_update_pro_data'):
            
            # Remove na values from metadata key column
            metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
            # Replace all None values with empty string
            metadata_df = metadata_df.loc[metadata_df['key'] != '', :]
            metadata_df = metadata_df.fillna('')
            
            # Validate ProData Metadata
            pro_metadata_keys = metadata_df['key'].tolist()
            pro_metadata_values = metadata_df['value'].tolist()
            pro_metadata_keys = [k.lower() for k in pro_metadata_keys]
            pro_metadata_values = [v.strip() for v in pro_metadata_values]
            
            name = name.strip()
            
            for k, v in zip(pro_metadata_keys, pro_metadata_values):                        
                if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                    st.session_state['error_cache'] = f'Key **{k}**: Only [0-9][a-z][.-_] allowed. no whitespaces.'
                    break
                if k in uiconfig.METADATA_RESERVED_KEYS:
                    st.session_state['error_cache'] = f'Metadata Key **{k}**: Reserved keyword, please choose another key'
                    break
            else:
                metadata = {k:v for k,v in zip(pro_metadata_keys, pro_metadata_values)}
                
                datamanager.create_pro_data(st.session_state["jwt_auth_header"],
                                            name = name,
                                            data_type = data_type,
                                            description = description,
                                            upload_path = data_path,
                                            metadata = metadata,
                                            fq_dataset = dataset_id)

                st.cache_data.clear()
                st.rerun()
    
    if st.session_state['error_cache']:
        st.error(st.session_state['error_cache'])
        st.session_state['error_cache'] = None

#region Delete ProData
@st.dialog('Delete ProData', width='medium', on_dismiss='rerun')
def delete_pro_data(pro_data_select_df: pd.DataFrame):
    """Delete selected ProData entries

    Args:
        pro_data_select_df: DataFrame with selected ProData entries
    """
    
    pro_data_ids = pro_data_select_df['id']
    
    if isinstance(pro_data_ids, int):
        pro_data_ids = [pro_data_ids]
    elif isinstance(pro_data_ids, np.int64):
        pro_data_ids = [int(pro_data_ids)]
    else:
        pro_data_ids = pro_data_ids.tolist()

    num_pro_data = len(pro_data_ids)
    
    if num_pro_data == 1:
        st.warning(f"Are you sure you want to delete the selected ProData entry?")
    else:
        st.warning(f"Are you sure you want to delete {num_pro_data} ProData entries?")
    
    st.error("⚠️ This action cannot be undone!")
    st.write("")
    
    with st.container(horizontal=True, horizontal_alignment='right'):
        
        if st.button('Cancel', key='cancel_delete_pro_data'):
            st.rerun()
        
        if st.button('Delete', type='primary', key='confirm_delete_pro_data'):
            for pid in pro_data_ids:
                datamanager.delete_pro_data(pid)
            
            st.cache_data.clear()
            st.rerun()


#region Export ProData
@st.dialog('Export ProData')            
def export_datasets(pro_data_view: pd.DataFrame):
    
    st.write('Save ProData and Metadata as .csv file')
    
    # export_include_archived = st.checkbox('Include archived',
    #                                         value = False)
            
    # if not export_include_archived:
    #     pro_data_view = pro_data_view.loc[
    #             pro_data_view['valid_to'].isna(),:]
    
    pro_data_view = pro_data_view.drop(columns=['id_str'])
    pro_data_view = pro_data_view.rename(columns={'owner_username' : 'creator',
                                                'fq_dataset' : 'dataset_id',
                                                'fq_dataset_name' : 'dataset_name',
                                                'project' : 'project_ids',
                                                })

    st.download_button('Download .csv',
                            pro_data_view.to_csv(index=False).encode("utf-8"),
                            'processed_data.csv',
                            'text/csv')

#region Show Upload Path
@st.dialog('Upload Path')
def show_upload_path(pro_data_name: str,
                    upload_path: str):
    
    st.text_input(f'ProData Entry: {pro_data_name}', value=upload_path)
    

#region UI Main Fragment
@st.fragment
def uimain(pro_data_show,
            pro_data_metadata,
            project_datasets,
            ref_name_dataset_df,
            data_types):
    """Main UI rendering function for pro_data page"""

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
                                key='prodata-header-container'):

            with st_yled.container(key='prodata-header-left-container',
                                    horizontal=True,
                                    vertical_alignment='center',
                                    horizontal_alignment='left',
                                    gap='small'):

                with st_yled.container(key='prodata-header-title-container',
                                        horizontal=True,
                                        vertical_alignment='center',
                                        horizontal_alignment='left',
                                        gap='small',
                                        width=144):

                    # Create hash for button key
                    if not 'pro_data_split_but_hash' in st.session_state:
                        st.session_state['pro_data_split_but_hash'] = str(uuid.uuid4())

                    with st.container(key='prodata-header-split-button-container'):

                        split_but = split_button(label='Create',
                                                options=['Update', 'Export', 'Delete'],
                                                icon=':material/add:',
                                                key=f'prodata_split_button-{st.session_state["pro_data_split_but_hash"]}')

                    if split_but == 'Create':
                        st.session_state['pro_data_split_but_hash'] = str(uuid.uuid4())
                        create_pro_data(project_datasets, ref_name_dataset_df, data_types)

                    elif split_but == 'Update':
                        st.session_state['pro_data_split_but_hash'] = str(uuid.uuid4())
                        
                        # Get selection from dataframe
                        if st.session_state['selected_pro_data_enable_edit']:
                        
                            update_pro_data(st.session_state['selected_pro_data'],
                                            st.session_state['selected_pro_data_metadata'],
                                            data_types)
                        else:
                            st.session_state['toast_cache'] = 'Select one or more ProData entries to Update'
                            st.rerun()

                    elif split_but == 'Export':
                        st.session_state['pro_data_split_but_hash'] = str(uuid.uuid4())
                        
                        # Get selection or all data
                        if 'pro_data_select_df' in st.session_state and hasattr(st.session_state['pro_data_select_df'], 'selection'):
                            selection = st.session_state['pro_data_select_df'].selection
                            
                            if selection and 'rows' in selection and len(selection['rows']) > 0:
                                select_row = selection['rows']
                                selected_ix = pro_data_show.iloc[select_row,:].index
                                export_select = pro_data_show.loc[selected_ix,:]
                            else:
                                export_select = pro_data_show
                        else:
                            export_select = pro_data_show
                        
                        export_datasets(export_select)

                    elif split_but == 'Delete':
                        st.session_state['pro_data_split_but_hash'] = str(uuid.uuid4())

                        if st.session_state['selected_pro_data_enable_delete']:
                            delete_pro_data(st.session_state['selected_pro_data'])

                        else:
                            st.session_state['toast_cache'] = 'Select one or more ProData entries to Delete'
                            st.rerun()


                search_value = st_yled.text_input("Search ProData",
                                            help = 'Search Processed Data',
                                            placeholder='Search ProData',
                                            key = 'search_pro_data',
                                            label_visibility = 'collapsed',
                                            border_width=2,
                                            width=256)

                # Search across all columns
                mask = pro_data_show.astype(str).apply(lambda x: x.str.contains(search_value, case=False)).any(axis=1)
                pro_data_show = pro_data_show[mask]

                # Generate a list of projects for filtering // Example ['No Project', 'master_blaster']
                pro_data_project_filter = extensions.project_filter_from_df(pro_data_show)
                pro_data_project_filter = [proj for proj in pro_data_project_filter if proj in project_datasets['project_name'].tolist()]
                pro_data_project_filter.insert(0, 'No Project')

                # with st_yled.container(key='prodata-header-filter-container',
                #                         horizontal=True,
                #                         vertical_alignment='center',
                #                         horizontal_alignment='left',
                #                         gap='small',
                #                         width=288):

                #     projects_filter = st.multiselect('Filter Projects',
                #                                     options = pro_data_project_filter,
                #                                     help = 'Filter Projects',
                #                                     placeholder = 'Filter Projects',
                #                                     label_visibility = 'collapsed')

                # Store metadata of remaining datasets for filtering
                metadata_select = pro_data_show[pro_data_metadata.columns]
                metadata_select = metadata_select.dropna(axis=1, how='all')

                filter_bg_color = styles.SECONDARY_BACKGROUND_COLOR_DEFAULT
                color = styles.PRIMARY_COLOR

                with st_yled.popover(':material/filter_alt:',
                                key='prodata-metadata-filter-popover',
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
                                    options=pro_data_project_filter,
                                    placeholder='',
                                    key=f'pro_data_project_filter_{st.session_state["pro_data_meta_filter_hash"]}')
                    
                    for k in metadata_select.columns:
                        
                        options = sorted(metadata_select[k].dropna().unique().tolist())
                        options = [o for o in options if o != '']
                        
                        st.multiselect(label = f'Filter {k}',
                                        options = options,
                                        key = f'pro_data_meta_filter_{st.session_state["pro_data_meta_filter_hash"]}_{k}',
                                        placeholder="")

            # Table Header Buttons Right Aligned
            with st_yled.container(key='prodata-header-right-container',
                                    horizontal=True,
                                    vertical_alignment='center',
                                    horizontal_alignment='right',
                                    gap='small'):

                with st_yled.container(key='prodata-header-toggles-container',
                                        horizontal=True,
                                        vertical_alignment='center',
                                        horizontal_alignment='right',
                                        gap='small'):

                    st.session_state['show_metadata'] = st_yled.toggle("Show Metadata",
                                                                    color='#808495',
                                                                    font_size=12,
                                                                    value=st.session_state['show_metadata'],
                                                                    key='datasets-show-metadata-toggle')

                    if st_yled.toggle("Show Archived",
                                    color='#808495',
                                    font_size=12,
                                    on_change=update_show_archived_versions,
                                    value=st.session_state['pro_data_show_archived_versions'],
                                    key='pro-data-show-archived-toggle'):

                        # Cuase rerun to load lineage data if toggle changes
                        if st.session_state['pro_data_show_archived_versions'] == False:
                            st.session_state['pro_data_show_archived_versions'] = True
                            st.rerun()

                    else:
                        if st.session_state['pro_data_show_archived_versions'] == True:
                            st.session_state['pro_data_show_archived_versions'] = False
                            st.rerun()

                    if st.session_state.show_details:
                        st.button(':material/unfold_less:',
                                    help='Collapse Details Pane',
                                    key='prodata-collapse-details',
                                    type='tertiary',
                                    width='content',
                                    on_click=extensions.switch_show_details)
                    else:
                        st.button(':material/unfold_more:',
                                help='Expand Details Pane',
                                key='prodata-collapse-details',
                                type='tertiary',
                                width='content',
                                on_click=extensions.switch_show_details)
                        
                    if st_yled.button(':material/refresh:',
                            help='Refresh Datasets',
                            key='prodata-refresh',
                            type='tertiary',
                            font_weight='500',
                            font_size='16px',
                            width='content'):

                        on_click = extensions.refresh_page()

                    # pro_archived = st.toggle("Archived",
                    #                         key='show_archived',
                    #                         value=st.session_state['show_pro_data_archived'],
                    #                         on_change = switch_show_archived_details,
                    #                         help='Show Archived ProData versions')


        # Column configuration for user view
        col_config_user = {
            'id': st.column_config.NumberColumn('ID'),
            'name' : st.column_config.TextColumn('Name', help='ProData Name'),
            'description' : None,
            'data_type' : st.column_config.TextColumn('Data Type', help='Data Type'),
            'fq_dataset' : None,
            'fq_dataset_name' : st.column_config.TextColumn('Dataset', help='Dataset ProData is associated with'),
            'project' : None,
            'project_names' : st.column_config.ListColumn('Projects', help='Projects the Dataset is associated with'),
            'version': st.column_config.NumberColumn('Version', help='Version of the Dataset'),
            'created' : st.column_config.DateColumn('Created', help='Creation Date'),
            'valid_to': None,    
            'owner_username' : None,
            'upload_path' : None,
            'id_str' : None,
        }

        col_config_meta = {
            'id': st.column_config.NumberColumn('ID'),
            'name' : st.column_config.TextColumn('Name', help='ProData Name'),
            'fq_dataset_name': st.column_config.TextColumn('Dataset', help='Parent Dataset'),
            'id_str' : None
        }

        projects_filter = st.session_state.get(f'pro_data_project_filter_{st.session_state["pro_data_meta_filter_hash"]}', None)
        
        # Project filter
        if projects_filter:
            if 'No Project' in projects_filter:
                projects_filter_copy = [p for p in projects_filter if p != 'No Project']
                if projects_filter_copy:
                    pro_data_show = pro_data_show.loc[
                        pro_data_show['project_names'].apply(lambda x: any([p in x for p in projects_filter_copy]) or len(x) == 0),:]
                else:
                    pro_data_show = pro_data_show.loc[pro_data_show['project_names'].apply(lambda x: len(x) == 0),:]
            else:
                pro_data_show = pro_data_show.loc[
                    pro_data_show['project_names'].apply(lambda x: any([p in x for p in projects_filter])),:]

        # Filter by metadata
        pro_data_show = extensions.filter_df_by_metadata_filter(pro_data_show,
                                                                filter_session_prefix = f'pro_data_meta_filter_{st.session_state["pro_data_meta_filter_hash"]}_')

        # Remove meta cols that are all None
        pro_meta_cols_all_none = pro_data_show.loc[:,pro_data_metadata.columns].isna().all()
        pro_meta_cols_all_none = pro_meta_cols_all_none[pro_meta_cols_all_none].index
        pro_data_meta_show = list(filter(lambda x: x not in pro_meta_cols_all_none, pro_data_metadata.columns))

        # Show metadata columns if toggled
        if st.session_state.show_metadata:
            show_cols = ['id', 'name', 'fq_dataset_name'] + pro_data_meta_show
            pro_data_col_config = {k : k for k in pro_data_metadata.columns}
            col_config_meta.update(pro_data_col_config)
            col_config = col_config_meta
        else:
            show_cols = pro_data_overview.columns.tolist()
            col_config = col_config_user

        # Dynamically adjust height
        if st.session_state['show_details']:
            if (len(pro_data_show) < 10):
                df_height = 'content'
            else:
                df_height = 370
        elif (len(pro_data_show) < 14):
            df_height = 'content'
        else:
            df_height = 500

        # Replace None with empty string for display
        pro_data_show_display = pro_data_show.fillna('')

        # Check if there are any ProData entries
        if pro_data_show_display.empty:

            with st_yled.container(key='info-no-prodata'):
                st_yled.info(':material/notifications: No Processed Data found. Create new ProData or adjust filter criteria.',
                        border_width="2.0px",
                        border_color="#808495",
                        border_style="solid",
                        color="#808495",
                        key='info-no-samples',
                        width=600)
        else:

            pro_data_select = st.dataframe(pro_data_show_display[show_cols],
                                            column_config = col_config,
                                            selection_mode=['single-cell', 'multi-row'],
                                            hide_index = True,
                                            on_select = 'rerun',
                                            width='stretch',
                                            key='pro_data_select_df',
                                            height=df_height)

            # Define selected rows from 'rows' and 'cells'
            rows_from_rows = pro_data_select.selection['rows']
            row_from_cells = [cell[0] for cell in pro_data_select.selection['cells']]

            if len(rows_from_rows) > 0:
                selection = rows_from_rows
            else:
                selection = row_from_cells

            # Define selected dataset(s)
            if (len(selection) == 1) and (selection[0] < pro_data_show.shape[0]): # Check if selection is within the displayed dataframe
                
                select_row = selection[0]   
                selected_ix = pro_data_show.iloc[[select_row],:].index[0]
                    
                pro_data_detail = pro_data_overview.loc[selected_ix,:]
                pro_data_metadata_detail = pro_data_metadata.loc[selected_ix,:].dropna().reset_index()
                pro_data_metadata_detail.columns = ['key', 'value']

                update_one = True

                if st.session_state['show_details']:
                    show_project_details = True
                else:
                    show_project_details = False

                # Would need to only combine with the metadata exactly for the selected dataset
                export_cols = pro_data_detail.index.tolist() + pro_data_metadata_detail['key'].tolist()
                
                pro_data_export_select = pro_data_show.loc[[selected_ix], :]
                pro_data_export_select = pro_data_export_select[export_cols]

                st.session_state['selected_pro_data'] = pro_data_detail
                st.session_state['selected_pro_data_metadata'] = pro_data_metadata_detail
                st.session_state['selected_pro_data_enable_edit'] = True
                st.session_state['selected_pro_data_enable_delete'] = True
                st.session_state['selected_pro_data_export'] = pro_data_export_select

            elif len(selection) > 1:
                
                select_row = selection
                select_row = [r for r in select_row if r < pro_data_show.shape[0]]

                selected_ix = pro_data_show.iloc[select_row,:].index

                pro_data_detail = pro_data_overview.loc[selected_ix,:]
                pro_data_metadata_detail = pro_data_metadata.loc[selected_ix,:].dropna().reset_index()
                
                pro_data_export_select = pd.concat([pro_data_detail, pro_data_metadata_detail], axis=1)
                
                show_project_details = False

                st.session_state['selected_pro_data'] = pro_data_detail
                st.session_state['selected_pro_data_metadata'] = pro_data_metadata_detail
                st.session_state['selected_pro_data_enable_edit'] = False
                st.session_state['selected_pro_data_enable_delete'] = True
                st.session_state['selected_pro_data_export'] = pro_data_export_select

            else:
                show_project_details = False

                pro_data_export_select = pro_data_show

                st.session_state['selected_pro_data'] = None
                st.session_state['selected_pro_data_metadata'] = None
                st.session_state['selected_pro_data_enable_edit'] = False
                st.session_state['selected_pro_data_enable_delete'] = False
                st.session_state['selected_pro_data_export'] = pro_data_export_select



            if show_project_details:
                
                st_yled.space(48)

                # segment_control_options = ['Features', 'Projects']
                # segment_default = segment_control_options[st.session_state['pro_details_segment_ix']]

                # pro_detail_selection = st.segmented_control(
                #         'ProData Detail Selection',
                #         segment_control_options,
                #         key='pro_detail_selection',
                #         default=segment_default,
                #         label_visibility = 'collapsed',
                #         on_change = update_segment_default,
                #         args = (segment_control_options,))

                # if pro_detail_selection == 'Features':
                    
                with st_yled.container(key='project-features-detail-container',
                                        horizontal=True,):

                    with st_yled.container(key='project-features-detail-columns-container',
                                        width=400,
                                        background_color=styles.DATAFRAME_HEADER_BG_COLOR):
                    
                        upload_path = pro_data_detail['upload_path']
                        name = pro_data_detail['name']
                        pro_data_id = pro_data_detail['id']
                        data_type = pro_data_detail['data_type']
                        version = pro_data_detail['version']
                        created = pro_data_detail['created'].strftime('%Y-%m-%d %H:%M')
                        dataset = pro_data_detail['fq_dataset_name']

                        with st_yled.container(key='features-detail-path-container'):
                            st_yled.markdown('ProData File Path', font_size=12, color='#808495')
                            st_yled.code(upload_path)

                        styles.feature_badge('ID', pro_data_id, 'prodata-features-detail-id')
                        styles.feature_badge('Name', name, 'prodata-features-detail-name')
                        styles.feature_badge('Data Type', data_type, 'prodata-features-detail-data-type')
                        styles.feature_badge('Version', version, 'prodata-features-detail-version')
                        styles.feature_badge('Dataset', dataset, 'prodata-features-detail-dataset')
                        styles.feature_badge('Created', created, 'prodata-features-detail-created')
                        
                        
                    with st_yled.container(key='project-features-detail-metadata-container',
                                            width=300,
                                            border=True):
                            
                        st_yled.markdown('Metadata', font_weight=500)
                        
                        if pro_data_metadata_detail.shape[0] == 0:
                            st_yled.info(':material/notifications: No metadata set. Define in Update Project',
                                        border_width="2.0px",
                                        border_color="#808495",
                                        border_style="solid",
                                        color="#808495",
                                        key='info-no-samples-metadata',
                                        width=400)
                        else:
                            st.dataframe(pro_data_metadata_detail,
                                        width = 'stretch',
                                        hide_index = True,
                                        column_config = {
                                            'key' : st.column_config.Column('Key'),
                                            'value' : st.column_config.Column('Value'),
                                        },
                                        key='metadata_details_df')
                            
                # if pro_detail_selection == 'Projects':
                    
                #     with st_yled.container(key='prodata-details-projects', border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
                        
                #         st.write('**Projects**')
                        
                #         project_ids = pro_data_detail['project']
                        
                #         dataset_projects_detail = project_datasets.loc[project_datasets['project_id'].isin(project_ids),
                #                                                         ['project_id', 'project_name', 'project_description']]
                        
                #         if dataset_projects_detail.shape[0] > 7:
                #             max_df_height = 315
                #         else:
                #             max_df_height = 'content'
                        
                #         st.dataframe(dataset_projects_detail,
                #                     use_container_width = True,
                #                     hide_index = True,
                #                     column_config = {
                #                         'project_id' : st.column_config.TextColumn('ID', width='small'),
                #                         'project_name' : st.column_config.TextColumn('Name'),
                #                         'project_description' : st.column_config.TextColumn('Description')
                #                     },
                #                     height = max_df_height)

            st.space(48)

#region DATA

# Get overfiew of all fastq datasets

# Get all fq_datasets and combined
pro_data_overview, pro_data_metadata = datamanager.get_pro_data_meta_overview(st.session_state["jwt_auth_header"],
                                                                              include_archived=st.session_state['pro_data_show_archived_versions'])
project_datasets = datamanager.get_project_datasets_overview(st.session_state["jwt_auth_header"])

# Subset fq_datasets and collapse projects

# Add id string for search
pro_data_overview['id_str'] = pro_data_overview['id'].astype(str)
data_types = sorted(pro_data_overview['data_type'].unique().tolist())

# Reference data for create/update dialogs
ref_name_dataset_df = pro_data_overview[['name', 'fq_dataset']]

# Prepare data for UI
pro_data_show = pd.concat([pro_data_overview, pro_data_metadata], axis=1)

# Call UI fragment
uimain(pro_data_show, pro_data_metadata, project_datasets, ref_name_dataset_df, data_types)