# readstore-basic/frontend/streamlit/app_pages/logout.py

"""
Streamlit App Logout Page

Reset the authentication status to False and rerun the app.
"""

import streamlit as st

import extensions


st.cache_data.clear()
st.session_state.clear()
st.rerun()