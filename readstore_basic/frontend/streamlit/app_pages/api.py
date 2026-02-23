# readstore-basic/frontend/streamlit/app_pages/settings.py

import time

import st_yled
import streamlit as st

import extensions
import datamanager
import styles
import datetime
import numpy as np

from uidataclasses import User

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

st_yled.init()

# region UI

def uimain():

    
    # Define Main Container
    with st_yled.container(key='work-ui', width=600):

        st.space(32)
        
        with st_yled.container(key="api-instructions-container", width=512):

            # Region Connect Terminal
            st_yled.subheader("Connecting from Terminal / Shell", font_size=20)

            st.write("")

            st.markdown("""
Interact with ReadStore from Bash scripts or terminal using the **ReadStore CLI**.
Upload FASTQ files or integrate data access into your pipelines.
""")        

            st_yled.markdown("Read the [CLI docs](https://evobytedigitalbiology.github.io/readstore/readme/)", color='#808495')
            st_yled.markdown("ReadStore CLI on [GitHub](https://github.com/evobytedigitalbiology/readstore-cli)", color='#808495')
            
            with st_yled.expander("Installing the ReadStore CLI",
                                  key="installing-cli-expander",
                                  background_color='#eef0f5',
                                  border_color='#eef0f5'):

                st.write("")

                st.markdown("Install from PyPI using pip")
                st.code("pip install readstore-cli", language='bash')

                st.write("")

                st.markdown("Check successful install. This command should print current version")
                st.code("""
readstore -v

ReadStore CLI Version: 1.3.0""", language='bash')
                
                st.write("")

                st.markdown("Configure the CLI. You can find your token and username in >*Settings*")
                st.code("""
readstore configure

Configuring ReadStore CLI
ReadStore Username: default
ReadStore Token: TOKEN123
Default Output Format (json, text, csv): json""", language='bash')
                
                st_yled.markdown("""
Output Format defined how the CLI returns data.
‘text’ is recommended for readability, while json and csv are best for structured processing.
""", color="#808495")
            
            st.write("")
            st.write("")

            st_yled.markdown("Example: Upload FASTQ Files", font_weight=500)
            st_yled.markdown("After QC step, the files are available for Check-in on >*Upload*")
            st.code("readstore upload tumor_rep1_r1.fastq.gz tumor_rep1_r2.fastq.gz", language='bash')

            st.space(32)

            # Region Connect Python
            st_yled.subheader("Python API", font_size=20)

            st.write("")

            st.markdown("""
Interact with ReadStore from Python code using the **ReadStore Python SDK**.
Load, analyze and store your data in Notebooks or Python pipelines.
""")        

            st_yled.markdown("Read the [Python SDK docs](https://evobytedigitalbiology.github.io/readstore/readme/)", color='#808495')
            st_yled.markdown("ReadStore Python SDK on [GitHub](https://github.com/EvobyteDigitalBiology/pyreadstore)", color='#808495')
            
            with st_yled.expander("Installing the pyreadstore API",
                                  key="installing-python-sdk-expander",
                                  background_color='#eef0f5',
                                  border_color='#eef0f5'):

                st.write("")

                st.markdown("Install from PyPI using pip")
                st.code("pip install pyreadstore", language='bash')

                st.write("")

                st.markdown("Validate the install by importing from Python")
                st.code("""import pyreadstore""", language='python')
                
                st.write("")

                st.markdown("Create a Client instance to setup credentials. More in the docs.")
                st.code("""rs_client = pyreadstore.Client()""", language='python')
                
            
            st.write("")
            st.write("")

            st_yled.markdown("Example: List datasets in Python", font_weight=500)
            st.code("datasets = rs_client.list()", language='python')

            st.space(32)

            # Region Connect Python
            st_yled.subheader("R API", font_size=20)

            st.write("")

            st.markdown("""
Interact with ReadStore from R code or R Studio using the **ReadStore R SDK**.
""")        

            st_yled.markdown("Read the [R SDK docs](https://evobytedigitalbiology.github.io/readstore/readme/)", color='#808495')
            st_yled.markdown("ReadStore R SDK on [GitHub](https://github.com/EvobyteDigitalBiology/r-readstore)", color='#808495')
            
            with st_yled.expander("Installing the r-readstore API",
                                  key="installing-r-sdk-expander",
                                  background_color='#eef0f5',
                                  border_color='#eef0f5'):

                st.write("")

                st.markdown("Install from GitHub using devtools")
                st.code("devtools::install_github('https://github.com/EvobyteDigitalBiology/r-readstore', subdir='readstore')", language='r')

                st.write("")

                st.markdown("Validate the install by importing from R")
                st.code("""library(readstore)""", language='r')
                
                st.write("")

                st.markdown("Create a Client instance to setup credentials. More in the docs.")
                st.code("""client <- get_client()""", language='r')
                
            
            st.write("")
            st.write("")

            st_yled.markdown("Example: Load a dataset by ID", font_weight=500)
            st.code("dataset_25 <- get_dataset(client, dataset_id = 25)", language='r')

            st.space(96)

# region DATA
uimain()