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
    
    # Define group to select pages to display
    user_groups = datamanager.get_user_groups(st.session_state["jwt_auth_header"])['name'].tolist()

    if not datamanager.valid_license(st.session_state["jwt_auth_header"]):
        st.error('No valid license found. Please enter a valid license key in the Admin Settings.')
        pages = [settings_page, logout_page]
    elif 'admin' in user_groups:
        pages = [admin_page, settings_page, logout_page]
    elif 'appuser' in user_groups:
        
        if not 'owner_group' in st.session_state:
            st.session_state['owner_group'] = datamanager.get_my_owner_group(st.session_state["jwt_auth_header"])['name'].tolist()[0]
    
        pages = [project_page, dataset_page]
    
        if 'staging' in user_groups:
            pages = pages + [staging_page]
        
        pages = pages + [settings_page, logout_page]

    pg = st.navigation(pages)
else:
    pg = st.navigation([login_page])

pg.run()


footer = """<style>
.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: #1D959B;
text-align: center;
}
</style>
<div class="footer">
<p>ReadStore Basic insert_version (c) 2024</p>
</div>
"""

footer = footer.replace("insert_version", uiconfig.__version__)

st.markdown(footer,unsafe_allow_html=True)