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

# stAppViewBlockContainer / Define format for Login Page

_, col1, _ = st.columns([3, 6, 3])

# stTextInputRootElement

with col1:  
    st.image(os.path.join(uiconfig.STATIC_PATH_PREFIX, "static/BannerLarge.png"), caption = "", use_column_width = True)

_, col2, _ = st.columns([4, 4, 4])


with col2:
    
    login_form = st.form("Login")
    login_form.subheader("Login")


username = login_form.text_input("Username").lower()
password = login_form.text_input("Password", type="password")

if login_form.form_submit_button("Login"):
    
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


footer = """<style>
.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p><strong>EVO</strong>BYTE Digital Biology</br>ReadStore Version insert_version</p>
</div>
"""

footer = footer.replace("insert_version", uiconfig.__version__)

st.markdown(footer,unsafe_allow_html=True)