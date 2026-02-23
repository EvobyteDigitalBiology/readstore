# readstore-basic/frontend/streamlit/app.py

"""
Streamlit App Main Page
"""


import os

import streamlit as st
import st_yled

from PIL import Image
import requests.auth as requests_auth

import extensions
import uiconfig
import styles
import datamanager

__author__ = "Jonathan Alles"
__email__ = "Jonathan.Alles@evo-byte.com"
__copyright__ = "Copyright 2024-2026"

st_yled.init()


im = Image.open(os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/favicon.ico"))
st.set_page_config(layout="wide", page_title="ReadStore", page_icon=im)

st.logo(
        "static/BannerStackedLightBlueBackground2.png",
        size='large',
        link = 'https://www.evo-byte.com/readstore'
)

st.html('static/styles.css')


# Handle authentication based on login configuration
if not uiconfig.ENABLE_LOGIN:
    # Automatic login with default user
    if not extensions.user_auth_status():
        secret_default_user_key_path = os.path.join(uiconfig.CONFIG_DIR, 'secret_default_user_key')
        
        if os.path.exists(secret_default_user_key_path) and os.access(secret_default_user_key_path, os.R_OK):
            try:
                with open(secret_default_user_key_path, 'r') as f:
                    default_password = f.read().strip()
                
                # Perform automatic login
                extensions.perform_login('default', default_password)
            except Exception as e:
                st.error(f'ERROR: Failed to read default user key: {e}')
                st.stop()
        else:
            st.error('ERROR: Default user key file not found or not readable')
            st.stop()

auth_status = extensions.user_auth_status()

# PAGES
home_page = st.Page("app_pages/home.py",
                     title="Home",
                     icon=":material/home:",
                     url_path = "home",
                     default=True)

login_page = st.Page("app_pages/login.py",
                     title="Login",
                     icon=":material/login:",
                     url_path = "login")

logout_page = st.Page("app_pages/logout.py",
                      title="Logout",
                      icon=":material/logout:",
                      url_path = "logout")

admin_page = st.Page("app_pages/admin.py",
                      title="Admin",
                      icon=":material/admin_panel_settings:",
                      url_path = "admin")

project_page = st.Page("app_pages/project.py",
                       title="Projects",
                       icon=":material/apps:",
                       url_path = "project")

staging_page = st.Page("app_pages/staging.py",
                       title="Upload",
                       icon=":material/data_check:",
                       url_path = "upload")

dataset_page = st.Page("app_pages/dataset.py",
                        title="Datasets",
                        icon=":material/list:",
                        url_path = "dataset")

pro_data_page = st.Page("app_pages/pro_data.py",
                        title="ProData",
                        icon=":material/insert_drive_file:",
                        url_path = "pro_data")

settings_page = st.Page("app_pages/settings.py",
                        title="Settings",
                        url_path = "settings")

api_page = st.Page("app_pages/api.py",
                    title="API & CLI",
                    url_path = "api")

getting_started_page = st.Page("app_pages/getting_started.py",
                                title="Getting Started",
                                url_path = "getting_started")


# Define context dependent pages, only shown if the user is authenticated
if auth_status:
    
    # Switch to control if details are shown
    if not 'show_details' in st.session_state:
        st.session_state['show_details'] = True
    if not 'username' in st.session_state:
        st.session_state['username'] = datamanager.get_my_user(st.session_state["jwt_auth_header"]).username
    
    # Check if all file paths are valid
    if not 'valid_filepath' in st.session_state:
        # Check if the file path in the database are valid
        fq_files_invalid_path = datamanager.get_fq_file_invalid_upload_paths(st.session_state["jwt_auth_header"])
        pro_data_invalid_path = datamanager.get_pro_data_invalid_upload_paths(st.session_state["jwt_auth_header"])

        if len(fq_files_invalid_path) > 0:
            st.error('FASTQ upload paths not found:')
            st.error(fq_files_invalid_path.to_dict())
        if len(pro_data_invalid_path) > 0:
            st.error('ProData upload paths not found:')
            st.error(pro_data_invalid_path.to_dict())            
        else:
            st.session_state['valid_filepath'] = True
    
    if uiconfig.ENABLE_LOGIN:

        # Define group to select pages to display
        user_groups = datamanager.get_user_groups(st.session_state["jwt_auth_header"])['name'].tolist()

        if 'admin' in user_groups:
            pages = [admin_page, settings_page, logout_page, api_page, getting_started_page]
        elif 'appuser' in user_groups:
            
            if not 'owner_group' in st.session_state:
                st.session_state['owner_group'] = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].tolist()[0]
        
            pages = [home_page, project_page, dataset_page, pro_data_page]
        
            if 'staging' in user_groups:
                pages = pages + [staging_page]
            
            pages = pages + [settings_page, logout_page, api_page, getting_started_page]

    else:
        if not 'owner_group' in st.session_state:
            st.session_state['owner_group'] = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].tolist()[0]
        
        # No login enabled - show all pages
        pages = [home_page, project_page, dataset_page, pro_data_page, staging_page, settings_page, api_page, getting_started_page]
    
    pg = st.navigation(pages)

    # region HEADER
    sticky_header_bg = st_yled.container(
        key="sticky-header-bg",
        background_color="#eef0f5",
    )

    with sticky_header_bg:
        st.write("")

    sticky_header = st.container(
        key="sticky-header",
        horizontal=True,
        vertical_alignment="center",
        width="stretch",
    )

    with sticky_header:
        
        with st.container(horizontal=True, horizontal_alignment="left"):
            st.write("")
            
        with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", width=512, key="sticky-header-links"):
            
            st_yled.page_link(getting_started_page, label="Getting Started")
            st_yled.page_link(api_page, label="API & CLI")
            st_yled.link_button("Docs", url="https://evobytedigitalbiology.github.io/readstore/",
                                type="secondary",
                                border_style="none",
                                color="#808495",
                                font_size="16.0px",
                                background_color='#eef0f5',
                                width="content")

            with st_yled.popover("U", key="avatar-popover"):
                
                st_yled.markdown("**User** " + st.session_state['username'],width="content", font_size="12px", key="avatar-username")
                st.write("")
                
                st_yled.page_link(settings_page, label="Settings", width="stretch")

else:
    # Show login page only if login is enabled
    if uiconfig.ENABLE_LOGIN:
        pg = st.navigation([login_page])
    else:
        st.error('Authentication failed. Please check your configuration.')
        st.stop()

pg.run()


# region SIDEBAR FOOTER

version_info_md = f"""
**ReadStore Basic**

v{uiconfig.__version__} (c) 2024-2026
"""

with st.sidebar.container(key="sidebar-footer-container", width='stretch'):
    
    with st.container(key="sidebar-footer-letter-container",
                      horizontal=True,
                      vertical_alignment="center",
                        gap = "medium",
                        width='stretch'):

        st_yled.markdown(version_info_md,
                        font_size="12px",
                        color='#31333F99',
                        width='stretch')


