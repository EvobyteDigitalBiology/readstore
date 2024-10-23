# readstore-basic/frontend/streamlit/app_pages/settings.py

import time

import streamlit as st

import extensions
import datamanager
import styles

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# Change Button Height
styles.adjust_button_height(25)

@st.dialog('Reset Password', width='medium')
def reset_password():
    st.write('Reset Password')
    
    old_pwd = st.text_input('Enter Old Password',
                            type='password',
                            help = 'Name must only contain 0-9 a-z A-Z. @ - _characters')
    
    new_pwd = st.text_input('Enter New Password (min 8 characters)',
                            type='password',
                            help = 'Name must only contain 0-9 a-z A-Z. @ - _characters')
    
    if st.button('Confirm', type='primary'):
        
        if old_pwd == new_pwd:
            st.error('Passwords are identical')        
        elif not extensions.validate_charset(new_pwd):
            st.error('Password: Only 0-9 a-z A-Z. @ - _ characters allowed')
        elif len(new_pwd) < 8:
                st.error('Password: Minimum 8 characters')
        else:
            try:
                if datamanager.user_reset_password(old_pwd, new_pwd):
                    st.success('Password Reset Successful')
                    st.rerun()
                else:
                    st.error('Old Password Incorrect')
            except Exception as e:
                st.error(str(e))
        
user_data = datamanager.get_my_user(st.session_state["jwt_auth_header"])
user_groups = datamanager.get_user_groups(st.session_state["jwt_auth_header"])['name'].tolist()

col1, _ = st.columns([4,8])

with col1:
    st.write('**Username**', user_data.username)
        
    # Build page for appuser
    if 'appuser' in user_groups:

        token = user_data.appuser['token']

        st.write('**Email**', user_data.email)
        #st.write('**Group**', st.session_state['owner_group'])

        if 'staging' in user_groups:
            st.checkbox('Staging', value=True, key='staging', disabled=True)
        else:
            st.checkbox('Staging', value=False, key='staging', disabled=True)   

        with st.popover('Token', use_container_width=True):
            with st.container(border=True):
                st.write(token)
            if st.button("Reset", type='primary'):
                datamanager.user_regenerate_token()
                st.cache_data.clear()
                st.rerun()
        
                
    if st.button('Reset Password', use_container_width=True):
        reset_password()