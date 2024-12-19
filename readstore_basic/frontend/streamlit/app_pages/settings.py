# readstore-basic/frontend/streamlit/app_pages/settings.py

import time

import streamlit as st

import extensions
import datamanager
import styles
import live
import datetime
import numpy as np
                
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
    
    repeat_new_pwd = st.text_input('Repeat New Password',
                            type='password',
                            help = 'Name must only contain 0-9 a-z A-Z. @ - _characters')
    
    if st.button('Confirm', type='primary'):
        
        if old_pwd == new_pwd:
            st.error('Passwords are identical')        
        elif not extensions.validate_charset(new_pwd):
            st.error('Password: Only 0-9 a-z A-Z. @ - _ characters allowed')
        elif len(new_pwd) < 8:
            st.error('Password: Minimum 8 characters')
        elif new_pwd != repeat_new_pwd:
            st.error('New Passwords do not match')
        else:
            try:
                if datamanager.user_reset_password(old_pwd, new_pwd):
                    st.success('Password Reset Successful')
                    st.rerun()
                else:
                    st.error('Old Password Incorrect')
            except Exception as e:
                st.error(str(e))

@st.dialog('Enter License Key', width='medium')
def enter_license_key():
    
    license_key = st.text_input('Enter License Key',
                            help = 'Key Format: XXXXX-XXXXX-XXXXX-XXXXX')
    
    if st.button('Confirm', type='primary'):
        valid, res, seats = live.vl(license_key)
        if valid:
            if res < datetime.datetime.now().date():
                st.error('License Key Expired')
            else:
                st.success('License Key Valid')
                res = datamanager.create_license_key(st.session_state["jwt_auth_header"], 
                                                license_key,
                                                seats,
                                                res)
                
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
        else:
            st.error('License Key Invalid')

@st.dialog('License Key', width='medium')
def show_key(key):
    st.text_input('License Key', key, disabled=False, label_visibility='collapsed')
    
    
user_data = datamanager.get_my_user(st.session_state["jwt_auth_header"])
user_groups = datamanager.get_user_groups(st.session_state["jwt_auth_header"])['name'].tolist()

latest_license_key = datamanager.get_license_key(st.session_state["jwt_auth_header"])

if not datamanager.valid_license(st.session_state["jwt_auth_header"]):
        st.warning('License Key invalid or expired. Please get in touch with support.')
    
col1, _ = st.columns([4,8])

with col1:
    
    st.write('**Username**', user_data.username)
        
    # Build page for appuser
    if 'appuser' in user_groups:

        token = user_data.appuser['token']

        st.write('**Email**', user_data.email)

        if 'staging' in user_groups:
            st.checkbox('Staging', value=True, key='staging', disabled=True, help='User has Staging Permissions (e.g. for FASTQ Upload)')
        else:
            st.checkbox('Staging', value=False, key='staging', disabled=True, help='Staging Permissions disabled (e.g. for FASTQ Upload)')

        with st.popover('Token', icon=":material/token:", use_container_width=True):
            with st.container(border=True):
                st.write(token)
            if st.button("Reset", type='primary'):
                datamanager.user_regenerate_token()
                st.cache_data.clear()
                st.rerun()
    
    if 'admin' in user_groups:
        
        with st.popover('License Key', icon=":material/key:", use_container_width=True):
                    
            if len(latest_license_key) == 0:
                st.warning('No License Key Found. Enter New Key.')
            elif len(latest_license_key) > 1:
                st.warning('Multiple Active License Keys Found. Please contact Support.')
            else:
                license_key = latest_license_key['key'].values[0]
                
                expiration = latest_license_key['expiration_date'].values[0]
                expiration = np.datetime_as_string(expiration, unit='D')
                seats = str(latest_license_key['seats'].values[0])
                
                st.write('**Expiration Date**', expiration)
                st.write('**Seats / Users**', seats)
            
                if st.button('Show License Key'):
                    show_key(license_key)
            
            if st.button('Enter New Key'):
                enter_license_key()


    if st.button('Reset Password', use_container_width=True):
        reset_password()