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

tutorial_json = {
    "start": {
        "title": "Welcome to ReadStore",
        "slug": "start",
        "content_paragraphs_md": [
            "Your solution for managing NGS and Omics data.",
            "Keep your projects organized and integrated with your bioinformatics workflows.",
            "*Take a short tour through the main features!*"
        ],
        "content_small_md": [],
        "image_url": "static/tutorial/img_01_welcome_readstore.webp",
        "prev_link_page": "",
        "next_link_page": "data-structure",
    },
    "data-structure": {
        "slug": "data-structure",
        "title": "Data Structure",
        "content_paragraphs_md": [
            "FASTQ files and processed data (e.g. count matrices, BAM, ...) are stored in Datasets.",
            "Datasets can be grouped in projects.",
            '''Structured metadata can be added in form of key-value pairs (e.g. {replicate: 1}). This is useful for grouping datasets for downstream analysis.'''
        ],
        "content_small_md": [],
        "image_url": "static/tutorial/img_02_datastructure.png",
        "prev_link_page": "start",
        "next_link_page": "file-upload",
    },
    "file-upload": {
        "slug": "file-upload",
        "title": "File Upload",
        "content_paragraphs_md": [
            "A first step is uploading FASTQ files into ReadStore.",
            "Upload files via Command Line Interface, or import directly on from the **Upload Page**. During the upload, a QC step is run which can take some time."
        ],
        "content_small_md": [
            "More on ReadStore Command Line Interface TODO: ADD LINK",
            "More on Import from a Template File TODO: ADD LINK"
        ],
        "image_url": "static/tutorial/img_03_tutorial_import_dataset.png",
        "prev_link_page": "data-structure",
        "next_link_page": "upload-check-in",           
    },
    "upload-check-in": {
        "slug": "upload-check-in",
        "title": "Upload Check In",
        "content_paragraphs_md": [
            "FASTQ files are automatically grouped into Datasets by their file name. Change the grouping by typing a another name in the Dataset field.",
            "Click **Check In** to confirm single Dataset. Use **Check In All** in the drop down menu to check in all datasets at once.",
        ],
        "content_small_md": [],
        "image_url": "static/tutorial/img_04_tutorial_dataset_check_in.png",
        "prev_link_page": "file-upload",
        "next_link_page": "check-in-form",
    },
    "check-in-form": {
        "slug": "check-in-form",
        "title": "Complete Check In",
        "content_paragraphs_md": [
            "In the upload form you can adapt the Dataset name or associate with an existing Dataset or Project.",
            "Set metadata like replicate information and check FASTQ statistics for each read.",
            "Click **Confirm** to complete Check In."
        ],
        "content_small_md": [],
        "image_url": "static/tutorial/img_05_tutorial_check_in_dataset.png",
        "prev_link_page": "upload-check-in",
        "next_link_page": "datasets", 
    },
    "datasets": {
        "slug": "datasets",
        "title": "Create and edit Datasets",
        "content_paragraphs_md": [
            "The Dataset page lists all datasets and allows creating new Datasets and updating descriptions or metadata.",
            "Click on a Dataset to get a detail view below the table.",
        ],
        "content_small_md": ["More on metadata key-value pairs TODO: ADD LINK"],
        "image_url": "static/tutorial/img_06_datasets_overview.png",
        "prev_link_page": "check-in-form",
        "next_link_page": "pro-data",
    },
    "pro-data": {
        "slug": "pro-data",
        "title": "Processed Data (ProData)",
        "content_paragraphs_md": [
            "Processed data are intermediary files from computational biology workflows, for instance gene count tables. These files are essential for data analysis and can be stored together with Datasets.",
            "Each Dataset can have several ProData entries attached. Entries can be versioned and point to a file on disk.",
        ],
        "content_small_md": [
            "More on working with ProData TODO: ADD LINK"
        ],
        "image_url": "static/tutorial/img_07_pro_data.png",
        "prev_link_page": "datasets",
        "next_link_page": "projects",
    },
    "projects": {
        "slug": "projects",
        "title": "Projects",
        "content_paragraphs_md": [
            "Datasets can be grouped into one or more projects. For each project you can set metadata and descriptions or attach files.",
            "Through the API, all project assets can be readily loaded for analysis.",
        ],
        "content_small_md": [
        ],
        "image_url": "static/tutorial/img_08_projects.png",
        "prev_link_page": "pro-data",
        "next_link_page": "api",
    },
    "api": {
        "slug": "api",
        "title": "ReadStore API",
        "content_paragraphs_md": [
            "Access the ReadStore database from your code, terminal or script to automatically load data into your workflows and analysis.",
            "Use the ReadStore Command Line Interface (CLI) to upload files and manage your data from the terminal. Use the Python or R SDK to access data from your scripts or notebooks.",
        ],
        "content_small_md": [
            "ReadStore CLI on [GitHub](https://github.com/EvobyteDigitalBiology/readstore-cli)",
            "ReadStore Python SDK [GitHub](https://github.com/EvobyteDigitalBiology/pyreadstore)",
            "ReadStore R SDK [GitHub](https://github.com/EvobyteDigitalBiology/r-readstore)",
        ],
        "image_url": "static/tutorial/img_09_api.webp",
        "prev_link_page": "projects",
        "next_link_page": "",
    },
}

st.space(80)

qparams = st.query_params

if "page" in qparams:
    page_key = qparams["page"]
else:
    page_key = "start"

page_json = tutorial_json[page_key] if page_key in tutorial_json else tutorial_json["start"]


with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="center", gap='large'):

    with st_yled.container(background_color='#1D959B20',
                           border_style='solid',
                           border_width=1,
                           border_color=styles.PRIMARY_COLOR,
                           height="stretch",
                           horizontal_alignment="center",
                           vertical_alignment="center",
                           padding=32,
                           width=540):

        st.image(page_json["image_url"])


    with st.container(height="stretch",
                           width=400):

        st.subheader(page_json["title"])

        for paragraph in page_json["content_paragraphs_md"]:
            st.markdown(paragraph)

        st.write("")

        for small_paragraph in page_json["content_small_md"]:
            st_yled.markdown(small_paragraph, font_size=12, color='#808495')

st.write("")
st.write("")

with st.container(horizontal=True, width='stretch', gap='large', horizontal_alignment="center"):

    if page_json["prev_link_page"] != "":
        st.page_link("app_pages/getting_started.py", icon=':material/keyboard_double_arrow_left:', label="First", query_params = {"page": "start"}, width=75)
    else:
        st.page_link("app_pages/getting_started.py", icon=':material/keyboard_double_arrow_left:', label="First", disabled=True, width=75)

    if page_json["prev_link_page"] != "":
        st.page_link("app_pages/getting_started.py", icon=':material/arrow_back:', label="Previous", query_params = {"page": page_json["prev_link_page"]}, width=100)
    else:
        st.page_link("app_pages/getting_started.py", icon=':material/arrow_back:', label="Previous", disabled=True, width=100)

    if page_json["next_link_page"] != "":
        st.page_link("app_pages/getting_started.py", icon=':material/arrow_forward:', label="Next", query_params = {"page": page_json["next_link_page"]}, width=100)
    else:
        st.page_link("app_pages/getting_started.py", icon=':material/arrow_forward:', label="Next", disabled=True, width=100)

    if page_json["next_link_page"] != "":
        st.page_link("app_pages/getting_started.py", icon=':material/keyboard_double_arrow_right:', label="Last", query_params = {"page": "api"}, width=75)
    else:
        st.page_link("app_pages/getting_started.py", icon=':material/keyboard_double_arrow_right:', label="Last", disabled=True, width=75)