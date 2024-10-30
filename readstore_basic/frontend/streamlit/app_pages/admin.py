# readstore-basic/frontend/streamlit/app_pages/admin.py

from typing import List
import time

import streamlit as st
import pandas as pd

import extensions
import datamanager
import exceptions
from uidataclasses import OwnerGroup
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



# Methods

# region Create User

# USERS
@st.dialog('Create User')
def create_user(reference_user_names: pd.Series,
                 reference_owner_group_names: pd.Series):
    
    # Compare lower case
    reference_user_names = reference_user_names.str.lower()
    reference_user_names = reference_user_names.tolist()
    number_users = len(reference_user_names)
    
    # Check for general issues
    if len(reference_owner_group_names) == 0:
        st.error('No Groups Found. Create in Groups tab first.')
        confirm_disabled = True
    else:
        confirm_disabled = False
    
    username = st.text_input("Enter Username",
                               max_chars=150,
                               help = 'Name must only contain 0-9 a-z A-Z . @ - _characters')
    
    email = st.text_input("Enter Email",
                               max_chars=150,
                               help = 'Name must only contain 0-9 a-z A-Z. @ - _characters')
    
    password = st.text_input("Enter Password (min 8 characters)",
                               help = 'Name must only contain 0-9 a-z A-Z. @ - _characters',
                               type = 'password')
    
    # owner_group_name = st.selectbox("Select Group",
    #                            options = reference_owner_group_names,
    #                            help = 'A Group shares Datasets and Projects')
    
    owner_group_name = uiconfig.DEFAULT_OWNER_GROUP
    
    staging = st.checkbox("Staging Permissions",
                          help = "Enables FASTQ File Upload via CLI",)
    
    _ , col2c = st.columns([9,3], vertical_alignment='center')
    
    with col2c:
        if st.button('Confirm', type ='primary', key='ok_create_user', disabled = confirm_disabled, use_container_width=True):
            
            valid_license = datamanager.valid_license(st.session_state['jwt_auth_header'])
            number_seats = datamanager.get_license_seats(st.session_state['jwt_auth_header'])
            
            # Make username and password case sensitive
            username = username.lower()
            email = email.lower()
            
            # Validate username / Better use case
            if username == '':
                st.error('Username is empty')
            elif not extensions.validate_charset(username):
                st.error('Username: Only 0-9 a-z A-Z. @ - _ characters allowed')
            elif username.lower() in reference_user_names:
                # Check if group_name exists
                st.error('Username exists')
            elif not extensions.validate_charset(password):
                st.error('Password: Only 0-9 a-z A-Z. @ - _ characters allowed')
            elif len(password) < 8:
                st.error('Password: Minimum 8 characters')
            elif email != '' and not extensions.validate_charset(email):
                st.error('Email: Only 0-9 a-z A-Z. @ - _ characters allowed')
            elif email != '' and not extensions.validate_email(email):
                st.error('Email: Invalid Email Format')
            elif not valid_license:
                st.error('License Key Invalid')
            elif number_users > number_seats: # Take account for admin user
                st.error('License Key Seats Full and Maximum Users Reached')
            else:
                datamanager.create_user(st.session_state['jwt_auth_header'],
                                        username,
                                        email,
                                        password,
                                        owner_group_name,
                                        staging)            
                st.cache_data.clear()
                st.rerun()

# region Update User

@st.dialog('Update User')
def update_user(row_ix: int,
                 appusers_df: pd.DataFrame,
                 reference_user_names: pd.Series,
                 reference_owner_group_names: pd.Series):
    
    
    appusers_df_select = appusers_df.iloc[row_ix,:]
    
    # Get values
    pk_id = int(appusers_df_select['id_user'])
    username_old = appusers_df_select['username']
    email_old = appusers_df_select['email']
    #og_name_old = appusers_df_select['name']
    is_active_old = appusers_df_select['is_active']
    staging_old = appusers_df_select['staging']
    token = appusers_df_select['token']
    
    # Remove self from ref user names
    reference_user_names = reference_user_names[reference_user_names!=username_old]
    reference_user_names = reference_user_names.str.lower()
    reference_user_names = reference_user_names.tolist()

    username = st.text_input("Enter Username",
                               max_chars=150,
                               help = 'Name must only contain 0-9 a-z A-Z . @ - _characters',
                               value = username_old)
    
    email = st.text_input("Enter Email",
                               max_chars=150,
                               help = 'Name must only contain 0-9 a-z A-Z. @ - _characters',
                               value = email_old)
    
    owner_group_name = uiconfig.DEFAULT_OWNER_GROUP
    
    staging = st.checkbox("Staging Permissions",
                          help = "Enables FASTQ File Upload via CLI",
                          value = staging_old)
    
    is_active = st.checkbox("User Is Active",
                          help = "Deactive User Account",
                          value = is_active_old)
    
    _, col2c = st.columns([9,3])
    
    with col2c:
        if st.button('Confirm', type ='primary', key='ok_update_user', use_container_width=True):
            
            username = username.lower()
            email = email.lower()
            
            # Validate username / Better use case
            if username == '':
                st.error('Username is empty')
            elif not extensions.validate_charset(username):
                st.error('Username: Only 0-9 a-z A-Z. @ - _ characters allowed')
            elif username.lower() in reference_user_names:
                # Check if group_name exists
                st.error('Username exists')
            elif email != '' and not extensions.validate_charset(email):
                st.error('Email: Only 0-9 a-z A-Z. @ - _ characters allowed')
            elif email != '' and not extensions.validate_email(email):
                st.error('Email: Invalid Email Format')
            
            else:
                datamanager.update_user(st.session_state['jwt_auth_header'],
                                        pk_id,
                                        username,
                                        email,
                                        None,
                                        owner_group_name,
                                        staging,
                                        is_active,
                                        token)            
                st.cache_data.clear()
                st.rerun()

# region Delete User
    
@st.dialog('Delete User(s)')
def delete_users(row_ixes: List[int], 
                  appusers_df: pd.DataFrame):
    
    # Get id from row index
    appusers_ids = appusers_df.iloc[row_ixes,:]['id_user'].tolist()
    
    appusers_delete = appusers_df.loc[
        appusers_df['id_user'].isin(appusers_ids),['id_user','username','name']
    ]
    
    st.write("Listed Users will be deleted")
    
    st.dataframe(appusers_delete,
                 hide_index = True,
                 column_config = {
                     'id_user' : st.column_config.Column('ID'),
                     'username' : st.column_config.Column('Username'),
                    'name' : None
                }, 
                 use_container_width = True)
    
    # Check which owner groups has users attached
    
    
    # Helper variable to check if all datasets to delete were processed to trigger rerun
    found_attached = False
        
    # Check if user is owner of a fq_dataset or fq_file, if true, skip delete and issue warning
    for appuser_id, appuser_name in zip(appusers_delete['id_user'], appusers_delete['username']):
        
        # Check if user is owner of fq_dataset or fq_file
        appuser_fq_datasets = datamanager.get_fq_dataset(headers=st.session_state['jwt_auth_header'],
                                                         owner=appuser_id)
        appuser_fq_file = datamanager.get_fq_file_owner(headers=st.session_state['jwt_auth_header'],
                                                  owner=appuser_id)
        
        num_fq_datasets = len(appuser_fq_datasets)
        num_fq_files = len(appuser_fq_file)
        
        if num_fq_datasets > 0 or num_fq_files > 0:

            st.warning(f'User {appuser_name}: {num_fq_datasets} Datasets and {num_fq_files} FASTQ Files Found for User.')
            found_attached = True

    if found_attached:
        st.warning(f'Are you sure you want to delete associated Datasets and FASTQ Files for selected Users?')
    
    _, col2c = st.columns([9,3])
    
    with col2c:
        if st.button('Confirm', type ='primary', key='ok_delete_user', use_container_width=True):
            
            # Check if user is owner of a fq_dataset or fq_file, if true, skip delete and issue warning
            for appuser_id, appuser_name in zip(appusers_delete['id_user'], appusers_delete['username']):
                
                # Check if user is owner of fq_dataset or fq_file
                appuser_fq_datasets = datamanager.get_fq_dataset(headers=st.session_state['jwt_auth_header'],
                                                                 owner=appuser_id)
                appuser_fq_file = datamanager.get_fq_file_owner(headers=st.session_state['jwt_auth_header'],
                                                          owner=appuser_id)
                
                for fq_file_id in appuser_fq_file['id']:
                    datamanager.delete_fq_file(fq_file_id)
                else:
                    datamanager.delete_user(appuser_id)
            else:
                st.cache_data.clear()
                st.rerun()


@st.dialog('Reset Password')
def reset_password(row_ix: int,
                   appusers_df: pd.DataFrame):
    
    appusers_df_select = appusers_df.iloc[row_ix,:]
    
    st.write("Set new Password for User Account")
    
    password = st.text_input("Enter Password (min 8 characters)",
                            help = 'Password must only contain 0-9 a-z A-Z. @ - _characters',
                            type = 'password')
    
    _, col2c = st.columns([9,3])
    
    # TODO: Only allowed for own user
    with col2c:
        if st.button('Confirm', type ='primary', key='ok_reset_pwd', use_container_width=True):
            # Validate pwd
            if not extensions.validate_charset(password):
                st.error('Password: Only 0-9 a-z A-Z. @ - _ characters allowed')
            elif len(password) < 8:
                st.error('Password: Minimum 8 characters')
            else:
                datamanager.update_user(st.session_state['jwt_auth_header'],
                                        int(appusers_df_select['id_user']),
                                        appusers_df_select['username'],
                                        appusers_df_select['email'],
                                        password,
                                        appusers_df_select['name'],
                                        appusers_df_select['staging'],
                                        appusers_df_select['is_active'],
                                        appusers_df_select['token'])            
                st.cache_data.clear()
                st.rerun()
    
  
# Data

owner_groups = datamanager.get_owner_group(headers=st.session_state['jwt_auth_header'])
users = datamanager.get_user(headers=st.session_state['jwt_auth_header'])

reference_user_names = users['username']
reference_group_names = owner_groups['name'].copy() # Ref group for valdiating input

owner_group_user = datamanager.get_owner_group_owner(headers=st.session_state['jwt_auth_header'])
appusers_overview = datamanager.get_appuser_overview(headers=st.session_state['jwt_auth_header'])
appusers_og_names = appusers_overview['name'].unique().tolist()

# Add ID as string for search function
owner_group_user['id_og_str'] = owner_group_user['id_og'].astype(str)
owner_groups['id_str'] = owner_groups['id'].astype(str)

appusers_overview['id_user_str'] = appusers_overview['id_user'].astype(str)

# UI

# Navbar
#tab1, tab2 = st.tabs([":blue-background[**Users**]", ":blue-background[**Groups**]"])

tab1 = st.tabs([":blue-background[**Users**]"])[0]

with tab1:
            
    col1, col2, _, col3 = st.columns([3,3,5,1])
    
    with col1:
        
        search_value_users = st.text_input("Search Users",
                            help = 'Search for Users',
                            placeholder='Search Users',
                            key = 'search_users',
                            label_visibility = 'collapsed')
    
    # with col2:
        
    #     og_filter = st.multiselect('Filter Groups',
    #                                options = appusers_og_names,
    #                                help = 'Filter for Groups',
    #                                placeholder = 'Filter Groups',
    #                                label_visibility = 'collapsed')
    
    
    with col3:
    
        if st.button(':material/refresh:', key='refresh_projects', help='Refresh Page'):
            on_click = extensions.refresh_page()
        
    col_config_user = {
            'id_user' : st.column_config.Column('ID'),
            'username' : st.column_config.TextColumn('Username'),
            'owner_group' : None,
            'name' : None,
            'email' : st.column_config.TextColumn('Mail'),
            'is_active' : st.column_config.Column('Active', help = "Account Active or Disabled"),
            'token' : st.column_config.Column('Token', help = 'Token for CLI/SDK Access'),
            'staging' : st.column_config.Column('Staging', help = 'Enables FASTQ File Upload via CLI'),
            'date_joined' : st.column_config.DateColumn('Created'),
            'id_user_str' : None
        }
    
    # Search Filter
    appusers_overview = appusers_overview.loc[
        (appusers_overview['username'].str.contains(search_value_users, case=False) |
         appusers_overview['id_user_str'].str.contains(search_value_users, case=False)),:
    ]
    
    # #  Group Filter
    # if len(og_filter) > 0:    
    #     appusers_overview = appusers_overview.loc[
    #         appusers_overview['name'].isin(og_filter),:
    #     ]
    
    # Dynamically adjust height of dataframe
    if len(appusers_overview) < 14:
        appuser_df_height = None
    else:
        appuser_df_height = 500
    
    
    appusers_select = st.dataframe(appusers_overview,
                        column_config = col_config_user,
                        selection_mode='multi-row',
                        hide_index = True,
                        on_select = 'rerun',
                        height = appuser_df_height)
            
    col4a, col5a, col6a, col7a, _ = st.columns([1.75,1.75,1.75,2.5, 4.25])
    
    if len(appusers_select.selection['rows']) == 1:
        update_disabled = False
        delete_disabled = False
        reset_pwd_disabled = False
        selection_user = appusers_select.selection['rows']
    elif len(appusers_select.selection['rows']) > 1:
        update_disabled = True
        delete_disabled = False
        reset_pwd_disabled = True
        selection_user = appusers_select.selection['rows']
    else:
        update_disabled = True
        delete_disabled = True
        reset_pwd_disabled = True
        selection_user = []
    
    with col4a:
        if st.button('Create', type ='primary', key='create_user', use_container_width=True, help = 'Create a new User'):
            create_user(reference_user_names=reference_user_names,
                        reference_owner_group_names=reference_group_names)
            
    with col5a:    
        if st.button('Update', key='update_user', disabled = update_disabled, use_container_width=True, help = 'Update selected User'):
            update_user(row_ix=selection_user[0],
                        appusers_df = appusers_overview,
                        reference_user_names=reference_user_names,
                        reference_owner_group_names=reference_group_names)
    
    with col6a:    
        if st.button('Delete', key='delete_user', disabled = delete_disabled, use_container_width=True, help = 'Delete selected User(s)'):
            delete_users(row_ixes=selection_user,
                          appusers_df=appusers_overview)
    
    with col7a:    
        if st.button('Reset Password', key='reset_password', disabled = reset_pwd_disabled, use_container_width=True, help = 'New Password for selected User'):
            reset_password(row_ix=selection_user[0],
                            appusers_df=appusers_overview)
