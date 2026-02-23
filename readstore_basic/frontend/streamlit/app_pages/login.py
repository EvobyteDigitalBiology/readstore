# readstore-basic/frontend/streamlit/app_pages/login.py


"""
Streamlit App Login Page

Simple Login Form
Auth via HTTP Basic Auth

"""

import os

import streamlit as st

import uiconfig
import extensions
import exceptions

# VALIDATION SESSION STATE
# Remove cached data to prevent unauthorized access
if not extensions.user_auth_status():
    st.cache_data.clear()

# Remove sidebar
st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
    [data-testid="stSidebar"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

st.space(128)

login_cont = st.container(horizontal_alignment="center")

with login_cont:
    
    #
    st.html("""
        <div style="gap: 0px;">
        <span style="color: #2A4159; font-size: 28px; font-weight: 700;">READ</span><span style="color: #2A4159; font-size: 28px;">STORE</span>
        </div>
        """,
        width='content')

    login_form = st.form("Login", width=312)

    username = login_form.text_input("**Username**").lower()
    password = login_form.text_input("**Password**", type="password")

    if login_form.form_submit_button("Login", type='primary'):
        
        # Run JWT authentication after login submit

        if uiconfig.AUTH_METHOD == uiconfig.AUTH_METHOD.JWT:
            try:
                extensions.perform_login(username, password)
                st.rerun()
                
            except exceptions.UIAppError as e:
                st.error(e.message, width=312)