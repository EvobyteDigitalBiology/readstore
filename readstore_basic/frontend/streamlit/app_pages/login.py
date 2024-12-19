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


col2a, col2, _ = st.columns([4, 4, 4], vertical_alignment="center")

with col2:
    
    st.image(os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/BannerLargeLightBlueBackground.png"), use_container_width = True)
    
    login_form = st.form("Login")

    username = login_form.text_input("**Username**").lower()
    password = login_form.text_input("**Password**", type="password")

    if login_form.form_submit_button("Login", type='primary'):
        
        # Run JWT authentication after login submit

        if uiconfig.AUTH_METHOD == uiconfig.AUTH_METHOD.JWT:
            try:
                access_token, refresh_token = extensions.get_jwt_token(username, password)

                st.session_state["access_token"] = access_token
                st.session_state["refresh_token"] = refresh_token
                st.session_state["jwt_auth_header"] = {"Authorization": "JWT " + access_token}
                
                st.write()
                
                extensions.validate_endpoints(uiconfig.ENDPOINT_CONFIG,
                                headers = st.session_state["jwt_auth_header"])
                
                extensions.start_token_refresh_thread()
                
                st.rerun()
                
            except exceptions.UIAppError:
                st.error("Username/password is incorrect")