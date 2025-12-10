# readstore-basic/frontend/streamlit/app.py

"""
Streamlit App Main Page
"""

import streamlit as st
from PIL import Image
import requests.auth as requests_auth
import os

import extensions
import uiconfig
import datamanager

__author__ = "Jonathan Alles"
__email__ = "Jonathan.Alles@evo-byte.com"
__copyright__ = "Copyright 2024"

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
                       title="Staging",
                       icon=":material/data_check:",
                       url_path = "staging")

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
                        icon=":material/settings:",
                        url_path = "settings")

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
            pages = [admin_page, settings_page, logout_page]
        elif 'appuser' in user_groups:
            
            if not 'owner_group' in st.session_state:
                st.session_state['owner_group'] = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].tolist()[0]
        
            pages = [project_page, dataset_page, pro_data_page]
        
            if 'staging' in user_groups:
                pages = pages + [staging_page]
            
            pages = pages + [settings_page, logout_page]

    else:
        if not 'owner_group' in st.session_state:
            st.session_state['owner_group'] = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].tolist()[0]
        
        # No login enabled - show all pages
        pages = [project_page, dataset_page, pro_data_page, staging_page]
    
    pg = st.navigation(pages)

else:
    # Show login page only if login is enabled
    if uiconfig.ENABLE_LOGIN:
        pg = st.navigation([login_page])
    else:
        st.error('Authentication failed. Please check your configuration.')
        st.stop()

pg.run()

footer = """<style>
.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
text-align: center;
font-size: 12.8px;
margin-bottom: 0.25rem;
}
</style>
<div class="footer">
<p style="margin-bottom: 0rem;">ReadStore Basic insert_version (c) 2024-2025</p>
</div>
"""

footer = footer.replace("insert_version", uiconfig.__version__)

st.markdown(footer,unsafe_allow_html=True)