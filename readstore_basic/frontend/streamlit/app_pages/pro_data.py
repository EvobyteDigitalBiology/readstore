# readstore-basic/frontend/streamlit/app_pages/pro_data.py
import string

import streamlit as st
import pandas as pd
import numpy as np
import os

import extensions
import datamanager
import styles
import uiconfig

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

colh1, colh2 = st.columns([11,1], vertical_alignment='top')

# Add username info top right
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

# Session state for showing archived processed data
if not 'pro_data_show_archived_versions' in st.session_state:
    st.session_state['pro_data_show_archived_versions'] = False

if not 'pro_metadata_select' in st.session_state:
    st.session_state['pro_metadata_select'] = pd.DataFrame()

if not 'pro_details_segment_ix' in st.session_state:
    st.session_state['pro_details_segment_ix'] = 0

if not 'show_pro_data_archived' in st.session_state:
    st.session_state['show_pro_data_archived'] = False


#region FUNCTIONS

def switch_show_archived_details():
    if not 'show_pro_data_archived' in st.session_state:
        st.session_state.show_pro_data_archived = True
    else: 
        st.session_state.show_pro_data_archived = not st.session_state.show_pro_data_archived


def update_segment_default(segment_control_options):
    
    # detail_selection can be none
    detail_selection = st.session_state['pro_detail_selection']
    
    # Update the index of the segment control if the selection is not None
    if detail_selection:    
        ix = segment_control_options.index(detail_selection)
        st.session_state['pro_details_segment_ix'] = ix


#region Create ProData
@st.dialog('Create ProData Entry', width='large')
def create_pro_data(ref_dataset_projects_df: pd.DataFrame,
                    ref_name_dataset_df: pd.DataFrame):
    """Create empty dataset

    Args:
        ref_dataset_projects_df: Reference dataframe with project dataset mapping
        ref_name_dataset_df: Reference dataframe with ProData name and dataset mapping
    """

    ref_dataset_projects_df = ref_dataset_projects_df.copy()
    ref_name_dataset_df = ref_name_dataset_df.drop_duplicates()
        
    # pass
    name = st.text_input("Pro Data Name",
                        key='pro_data_name',
                        help = 'Name must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')

    data_type = st.text_input("Data Type",
                        key='pro_data_type',
                        help = 'Data Type must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')
    
    data_path = st.text_input("ProData Path",
                            key='pro_data_path',
                            help = 'Path to the data file, which must be a valid and accessible by the app.')
    
    # Define Tabs
    tab1, tab2 = st.tabs([":blue-background[**Dataset**]",
                        ":blue-background[**Features**]"])

    with tab1:
        
        with st.container(height=395, border=False):
            
            project_options = ref_dataset_projects_df['project_name'].dropna().unique()
            project_options = sorted(project_options)
            project_options.insert(0, 'No Project')
            
            st.write('Select Dataset for ProData Entry')
            
            ds_col_1, _, ds_col_2 = st.columns([5.5,1,5.5])
            
            with ds_col_1:
                
                # Select project to attach dataset to
                project_names_select = st.multiselect("Subset by Projects",
                        project_options,
                        help = 'Attach the dataset to project(s).')

            with ds_col_2:
                
                # Select dataset
                dataset_search = st.text_input("Search Datasets by Name or ID")
            
            if project_names_select:
                if 'No Project' in project_names_select:
                    # Rename Project Name to No Project
                    ref_dataset_projects_df.loc[
                        ref_dataset_projects_df['project_name'].isna(), 'project_name'] = 'No Project'    
                    
                ref_dataset_projects_df = ref_dataset_projects_df.loc[
                    ref_dataset_projects_df['project_name'].isin(project_names_select),:]
            
            ref_dataset_projects_df = ref_dataset_projects_df[
                (ref_dataset_projects_df['dataset_name'].str.contains(dataset_search, case=False) | 
                ref_dataset_projects_df['dataset_id'].astype(str).str.contains(dataset_search, case=False))
            ]
            
            dataset_options = ref_dataset_projects_df['dataset_name'].dropna().unique()
            
            dataset_select = st.selectbox('Select Dataset',
                                          options=dataset_options,
                                          key='pro_data_dataset',
                                          index=None)
            
            if dataset_select:    
                dataset_id = ref_dataset_projects_df.loc[
                    ref_dataset_projects_df['dataset_name'] == dataset_select,'dataset_id'].values[0]
            else:
                dataset_id = None
                
    with tab2:
        
        description = st.text_area("Enter ProData Description",
                                        help = 'Description of ProData',
                                        height = 68)
            
        with st.container(border=True, height=280):
        
            col1c, col2c = st.columns([11,1], vertical_alignment='top')
            
            with col1c:
            
                tab1c = st.tabs([":blue-background[**Metadata**]"])[0]

                with tab1c:
                
                    st.write('Key-value pairs to describe and group ProData metadata')
                    
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
            
            with col2c:
                with st.popover(':material/help:'):
                    st.write("Key-value pairs to store and group dataset metadata. For example 'species' : 'human'")
                    
                          
    _ , col_conf = st.columns([9,3])    
            
    with col_conf:
        
        if st.button('Confirm', type ='primary', key='ok_create_pro_data', use_container_width=True):
            
            ref_name_check = ref_name_dataset_df[
                (ref_name_dataset_df['fq_dataset'] == dataset_id) & 
                (ref_name_dataset_df['name'] == name)]
            
            if name == '':
                st.error("Please enter a ProData Name.")
            elif not extensions.validate_charset(name):
                st.error('ProData Name: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
            elif data_type == '':
                st.error("Please enter a ProData Data Type.")
            elif not extensions.validate_charset(data_type):
                st.error('ProData Data Type: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
            elif data_path == '':
                st.error("Enter an upload path")
            elif not os.path.isfile(data_path):
                st.error("Upload path for ProData File not found")
            elif dataset_id is None:
                st.error("Please select a dataset to attach ProData entry to.")
            # Test dataset_id name combination exists
            elif not ref_name_check.empty:
                st.error("ProData Name already exists for selected Dataset. Use **Update** ProData instead.")
            else:
                # Remove na values from metadata key column
                metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
                # Replace all None values with empty string
                metadata_df = metadata_df.fillna('')
                
                # Validate ProData Metadata
                pro_metadata_keys = metadata_df['key'].tolist()
                pro_metadata_values = metadata_df['value'].tolist()
                pro_metadata_keys = [k.lower() for k in pro_metadata_keys]                  
                
                for k, v in zip(pro_metadata_keys, pro_metadata_values):                        
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.error(f'Metadata Key **{k}**: Reserved keyword, please choose another key')
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


#region Update ProData

# continue HERE: Update Rules for ProData

@st.dialog('Update ProData Entry', width='large')
def update_pro_data(pro_data_update: pd.Series,
                    pro_data_metadata_update: pd.DataFrame):
    """Update ProData entry
    
    Create a ProData entry with higher version for the selected ProData Entry
    Data Type, Description, Metadata and Upload Path can be updated

    Args:
        pro_data_update: Series with ProData entry to update
        pro_data_metadata_update: DataFrame with metadata keys and values to update
    """

    pro_data_id = pro_data_update['id']
    dataset_id = pro_data_update['fq_dataset']
    
    # pass
    name = st.text_input("Pro Data Name",
                        key='pro_data_name',
                        value=pro_data_update['name'],
                        disabled=True)

    data_type = st.text_input("Data Type",
                        key='pro_data_type',
                        value=pro_data_update['data_type'],
                        help = 'Data Type must only contain [0-9][a-z][A-Z][.-_@] (no spaces).')
    
    data_path = st.text_input("ProData Path",
                            key='pro_data_path',
                            value=pro_data_update['upload_path'],
                            help = 'Path to the data file, which must be a valid and accessible by the app.')
    
    # Define Tabs
    tab1, tab2 = st.tabs([":blue-background[**Dataset**]",
                        ":blue-background[**Features**]"])

    with tab1:
        
        with st.container(height=330, border=False):
            
            st.write('Select Dataset for ProData Entry')
            
            ds_col_1, _, ds_col_2 = st.columns([5.5,1,5.5])
            
            with ds_col_1:
                
                # Select project to attach dataset to
                _ = st.multiselect("Subset by Projects",
                                    [],
                                    disabled=True)

            with ds_col_2:
                
                # Select dataset
                dataset_search = st.text_input("Search Datasets by Name or ID", disabled=True)
            
            dataset_select = st.selectbox('Select Dataset',
                                          options=[pro_data_update['fq_dataset_name']],
                                          index = 0,
                                          disabled=True)
            
        coldel, _ = st.columns([4,8])
        
        with coldel:
            with st.expander('Delete ProData Entry', icon=":material/delete_forever:"):
                if st.button('Confirm', key='delete_pro_data'):
                    
                    datamanager.delete_pro_data(pro_data_id)
                    
                    st.cache_data.clear()
                    st.rerun()
              
    with tab2:
        
        description = st.text_area("Enter ProData Description",
                                        help = 'Description of ProData',
                                        height = 68)
            
        with st.container(border=True, height=280):
        
            col1c, col2c = st.columns([11,1], vertical_alignment='top')
            
            with col1c:
            
                tab1c = st.tabs([":blue-background[**Metadata**]"])[0]

                with tab1c:
                
                    st.write('Key-value pairs to describe and group ProData metadata')
                    
                    pro_data_metadata_update = pro_data_metadata_update.astype(str)
                    metadata_df = st.data_editor(
                        pro_data_metadata_update,
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
                    
                          
    _ , col_conf = st.columns([9,3])    
            
    with col_conf:
        
        if st.button('Confirm', type ='primary', key='ok_update_pro_data', use_container_width=True):
            
            if data_type == '':
                st.error("Please enter a ProData Data Type.")
            elif not extensions.validate_charset(data_type):
                st.error('ProData Data Type: Only [0-9][a-z][A-Z][.-_@] characters allowed, no spaces.')
            elif data_path == '':
                st.error("Enter an upload path")
            elif not os.path.isfile(data_path):
                st.error("Upload path for ProData File not found")
            else:
                # Remove na values from metadata key column
                metadata_df = metadata_df.loc[~metadata_df['key'].isna(),:]
                # Replace all None values with empty string
                metadata_df = metadata_df.fillna('')
                
                # Validate ProData Metadata
                pro_metadata_keys = metadata_df['key'].tolist()
                pro_metadata_values = metadata_df['value'].tolist()
                pro_metadata_keys = [k.lower() for k in pro_metadata_keys]                  
                
                for k, v in zip(pro_metadata_keys, pro_metadata_values):                        
                    if not set(k) <= set(string.digits + string.ascii_lowercase + '_-.'):
                        st.error(f'Key {k}: Only [0-9][a-z][.-_] characters allowed, no spaces')
                        break
                    if k in uiconfig.METADATA_RESERVED_KEYS:
                        st.error(f'Metadata Key **{k}**: Reserved keyword, please choose another key')
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
    
# region Update Many Pro Data
@st.dialog('Update ProData', width='large')
def update_many_pro_data(pro_data_select_df: pd.DataFrame):
    """Delete selected ProData entries

    Args:
        pro_data_select_df: DataFrame with selected ProData entries
    """
    
    # Show delete button if project is owned by user's owner_group
    col1expander,_ = st.columns([6,6])
    with col1expander:
        with st.expander('Delete all ProData Entries', icon=":material/delete_forever:"):
            if st.button('Confirm', key='delete_pro_data_many'):
                pro_data_ids = pro_data_select_df['id']
                
                _ = [datamanager.delete_pro_data(pid) for pid in pro_data_ids]
                
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
    
#region DATA

# Get overfiew of all fastq datasets

# Get all fq_datasets and combined
pro_data_overview, pro_data_metadata = datamanager.get_pro_data_meta_overview(st.session_state["jwt_auth_header"],
                                                                              include_archived=st.session_state['show_pro_data_archived'])
project_datasets = datamanager.get_project_datasets_overview(st.session_state["jwt_auth_header"])

# Subset fq_datasets and collapse projects

pro_data_project_filter = extensions.project_filter_from_df(pro_data_overview)
pro_data_project_filter = [proj for proj in pro_data_project_filter if proj in project_datasets['project_name'].tolist()]
pro_data_project_filter.insert(0, 'No Project')

# Add id string for search
pro_data_overview['id_str'] = pro_data_overview['id'].astype(str)

col1, col2, col3, col4, col5, col6 = st.columns([3,3,1.75,2.2,1.3,0.75], vertical_alignment='center')

with col1:
    
    search_value = st.text_input("Search ProData",
                                help = 'Search for Processed Data entries',
                                placeholder='Search ProData',
                                key = 'search_pro_data',
                                label_visibility = 'collapsed')

with col2:
    
    projects_filter = st.multiselect('Filter Projects',
                                    options = pro_data_project_filter,
                                    help = 'Filter Projects',
                                    placeholder = 'Filter Projects',
                                    label_visibility = 'collapsed')

with col4:
    
    st.toggle("Metadata",
              key='show_pro_metadata')


# Dynamic list of checkboxes with distinct values
with col5:
    
    # Dataframe to hold metadata filter for datasets
    metadata_select = st.session_state['pro_metadata_select']
    
    # Drop columns which are all N/A
    metadata_select = metadata_select.dropna(axis=1, how='all')
    
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
                            key = f'pro_data_meta_filter_{k}',
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
    'id_str' : None
}

pro_data_show = pd.concat([pro_data_overview, pro_data_metadata], axis=1)

# Search filter
pro_data_show = pro_data_show[
    (pro_data_show['name'].str.contains(search_value, case=False) | 
     pro_data_show['id_str'].str.contains(search_value, case=False) |
     pro_data_show['data_type'].str.contains(search_value, case=False) |
     pro_data_show['fq_dataset_name'].str.contains(search_value, case=False)
     )]

# Project filter
if projects_filter:
    if 'No Project' in projects_filter:
        projects_filter.remove('No Project')
        pro_data_show = pro_data_show.loc[
            pro_data_show['project_names'].apply(lambda x: any([p in x for p in projects_filter]) or len(x) == 0),:
            ]
    else:
        pro_data_show = pro_data_show.loc[
            pro_data_show['project_names'].apply(lambda x: any([p in x for p in projects_filter])),:
            ]

# Store metadata of those datasets remain after filtering for dataset_id/name and project
# This is used to build a filter for metadata columns
st.session_state['pro_metadata_select'] = pro_data_show[pro_data_metadata.columns]

# Filter out meta columns from selected view which are all None
pro_data_show = extensions.filter_df_by_metadata_filter(pro_data_show,
                                                        filter_session_prefix = 'pro_data_meta_filter_')

# Remove those meta cols from pro_data_show which are all None
pro_meta_cols_all_none = pro_data_show.loc[:,pro_data_metadata.columns].isna().all() # Pro data columns only NA
pro_meta_cols_all_none = pro_meta_cols_all_none[pro_meta_cols_all_none].index
pro_data_meta_show = list(filter(lambda x: x not in pro_meta_cols_all_none, pro_data_metadata.columns))

# Show metadata
# Add metadata
if st.session_state.show_pro_metadata:
    # How selected datasets metadata only for subset
    show_cols = ['id', 'name', ] + pro_data_meta_show
    
    pro_data_col_config = {k : k for k in pro_data_metadata.columns}
    
    col_config_meta.update(pro_data_col_config)
    col_config = col_config_meta
else:
    show_cols = pro_data_overview.columns.tolist()
    col_config = col_config_user

# Dynamically adjust height of dataframe
if st.session_state['show_details']:
    if (len(pro_data_show) < 10):
        df_height = None
    else:
        df_height = 370 # 7 Rows
elif (len(pro_data_show) < 14):
    df_height = None
else:
    # Full Height for 14 rows
    df_height = 500

# For formatting, replace None with empty string
pro_data_show = pro_data_show.fillna('')

pro_data_select = st.dataframe(pro_data_show[show_cols],
                                column_config = col_config,
                                selection_mode='multi-row',
                                hide_index = True,
                                on_select = 'rerun',
                                use_container_width=True,
                                key='pro_data_select_df',
                                height=df_height)


if len(pro_data_select.selection['rows']) == 1:
    
    # Subset projects and metadata to feed into update/details
    # Get index from selection
    select_row = pro_data_select.selection['rows'][0]
    
    # Get original index from projects overview before subset
    selected_ix = pro_data_show.iloc[[select_row],:].index[0] # Refers to original index
    
    pro_data_detail = pro_data_overview.loc[selected_ix,:]
    pro_data_metadata_detail = pro_data_metadata.loc[selected_ix,:] # Returns a series 
    
    pro_data_metadata_detail = pro_data_metadata_detail.dropna().reset_index()
    
    pro_data_metadata_detail.columns = ['key', 'value']
    
    pro_data_update = pro_data_detail.copy()
    pro_data_metadata_update = pro_data_metadata_detail.copy()
    
    pro_data_detail_id = pro_data_detail['id']
    
    if st.session_state['show_details']:
        show_details = True
    else:
        show_details = False
    
    update_disabled = False
    update_one = True
    
    # Would need to only combine with the metadata exactly for the selected dataset
    export_cols = pro_data_detail.index.tolist() + pro_data_metadata_detail['key'].tolist()
    
    # Combinate fq_dataset_detais
    # Remove all metadata columns which arennot in fq_metadata_detail keys
    export_select = pro_data_show.loc[[selected_ix],:]
    export_select = export_select[export_cols]
    
    
elif len(pro_data_select.selection['rows']) > 1:

    select_row = pro_data_select.selection['rows']
    
    # Get original index from projects overview before subset
    selected_ix = pro_data_show.iloc[select_row,:].index # Refers to original index
    
    # Would need to only combine with the metadata exactly for the selected dataset
    
    # Get fq datasets and associated metadata assays
    pro_data_detail = pro_data_overview.loc[selected_ix,:]
    pro_data_metadata_detail_many = pro_data_metadata.loc[selected_ix,:] # Returns a series 
    
    # TODO: Is this necessary?
    pro_data_dataset_update = pro_data_detail.copy()
    
    show_details = False
    update_disabled = False
    update_one = False
    
    # Remove all columns which are all None
    pro_data_metadata_detail_many = pro_data_metadata_detail_many.dropna(axis=1, how='all')
    
    export_select = pd.concat([pro_data_detail, pro_data_metadata_detail_many], axis=1)
    
else:
    show_details = False
    update_disabled = True
    update_one = False
    
    select_row = None
    selected_fq_dataset_ix = None

    pro_data_detail = None
    pro_data_metadata_detail = None
    
    pro_data_dataset_update = None
    pro_data_metadata_update = None
    
    export_select = pro_data_show
    

col_low_1, col_low_2, col_low_3, _, col_low_4, col_low_5 = st.columns([1.75,1.75, 1.75, 1.0 ,2.75,3],
                                                          vertical_alignment = 'center')

with col_low_1:
    
    if st.button('Create',
                 key='create_pro_date',
                 use_container_width=True,
                 help = 'Create new empty Dataset',
                 type='primary'):
        
        ref_name_dataset_df = pro_data_overview[['name', 'fq_dataset']]
        
        create_pro_data(project_datasets,
                        ref_name_dataset_df)

with col_low_2:    
    
    if st.button('Update',
                 key='update_dataset',
                 use_container_width=True,
                 disabled = update_disabled,
                 help = 'Update the selected Dataset'):
        
        if update_one:
            update_pro_data(pro_data_update,
                            pro_data_metadata_update)

        else:            
            update_many_pro_data(
                pro_data_dataset_update
            )
        
with col_low_3:
    
    if st.button('Export',
                 key='export_datasets',
                 use_container_width=True,
                 help = 'Export and download Dataset overview'):
        
        # Prepare input for export
        export_datasets(export_select)

with col_low_4:
   
    pro_archived = st.toggle("Archived",
                            key='show_archived',
                            value=st.session_state['show_pro_data_archived'],
                            on_change = switch_show_archived_details,
                            help='Show Archived ProData versions')

with col_low_5:    
   
    on = st.toggle("Details",
                  key='show_details_pro_data',
                  value=st.session_state['show_details'],
                  on_change = extensions.switch_show_details,
                  help='Show Details for selected ProData entry')
    
if show_details:
    
    st.divider()
    
    segment_control_options = ['Features', 'Projects']
    segment_default = segment_control_options[st.session_state['pro_details_segment_ix']]
    
    pro_detail_selection = st.segmented_control(
            'ProData Detail Selection',
            segment_control_options,
            key='pro_detail_selection',
            default=segment_default,
            label_visibility = 'collapsed',
            on_change = update_segment_default,
            args = (segment_control_options,)
        )
    
    
    if pro_detail_selection == 'Features':
        
        
        col1d1, col2d1 = st.columns([7,5])
        
        with col1d1:
            
            with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
                
                col1atta, col2atta = st.columns([3,9])
                
                detail_format = pro_data_detail.copy()
                upload_path = detail_format['upload_path']
                pro_data_name = detail_format['name']
                
                with col1atta:
                    st.write('**Details**')
                
                with col2atta:
                    if st.button('Upload Path'):
                        show_upload_path(pro_data_name, upload_path)
                
                                
                pro_data_id = detail_format.pop('id')
                
                pro_data_detail_format = detail_format[['name',
                                                          'description',
                                                          'data_type',
                                                          'fq_dataset',
                                                          'fq_dataset_name',
                                                          'version',
                                                          'created',
                                                          'owner_username']]
                
                pro_data_detail_format['created'] = pro_data_detail_format['created'].strftime('%Y-%m-%d %H:%M')
                
                pro_data_detail_format = pro_data_detail_format.reset_index()
                pro_data_detail_format.columns = ['ProData ID', pro_data_id]
                
                pro_data_detail_format['ProData ID'] = [
                    'Name',
                    'Description',
                    'Data Type',
                    'Dataset ID',
                    'Dataset',
                    'Version',
                    'Created',
                    'Creator'
                ]
                    
                st.dataframe(pro_data_detail_format,
                            use_container_width = True,
                            hide_index = True,
                            key='project_details_df')
                
        with col2d1:
            
            with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
                
                st.write('**Metadata**')
                
                st.dataframe(pro_data_metadata_detail,
                            use_container_width = True,
                            hide_index = True,
                            column_config = {
                                'key' : st.column_config.Column('Key'),
                                'value' : st.column_config.Column('Value'),
                            },
                            key='pro_data_metadata_details_df')
                
    if pro_detail_selection == 'Projects':
        
        with st.container(border = True, height = uiconfig.DETAIL_VIEW_HEIGHT):
            
            st.write('**Projects**')
            
            # Get prject information here: my_projects    
                 
            project_ids = pro_data_detail['project']
            
            dataset_projects_detail = project_datasets.loc[project_datasets['project_id'].isin(project_ids),
                                                           ['project_id', 'project_name', 'project_description']]
            
            # Limit Max Height of Dataframe
            if dataset_projects_detail.shape[0] > 7:
                max_df_height = 315
            else:
                max_df_height = None
            
            st.dataframe(dataset_projects_detail,
                        use_container_width = True,
                        hide_index = True,
                        column_config = {
                            'project_id' : st.column_config.TextColumn('ID', width='small'),
                            'project_name' : st.column_config.TextColumn('Name'),
                            'project_description' : st.column_config.TextColumn('Description')
                        },
                        height = max_df_height)