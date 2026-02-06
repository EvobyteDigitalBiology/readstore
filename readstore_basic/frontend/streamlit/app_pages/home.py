# readstore-basic/frontend/streamlit/app_pages/settings.py

import time


import st_yled
import streamlit as st

import extensions
import datamanager
import styles
import datetime
import numpy as np
import pandas as pd

from uidataclasses import UserDataStats
import uiconfig

if not extensions.user_auth_status():
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

st_yled.init()


def quickstart_card(title: str,
                    description: str,
                    link: str,
                    target: str = "_self",
                    width: int = 256):
    
    st.html("""
            <style>
                .intro-card {
                    background-color: #F0F2F6;
                    border-radius: 8px;
                    padding: 16px;
                }
                .intro-card:hover {
                    background-color: #eef0f5;
                    box-shadow: 0 2px 2px rgba(0, 0, 0, 0.1);
                }
                .intro-card-link,
                .intro-card-link:hover,
                .intro-card-link:visited {
                    color: inherit;
                    text-decoration: none;
                }   
            </style>
            """
            )

    st.html(
        f"""
        <a class="intro-card-link" href="{link}" target="{target}">
            <div class="intro-card">
                <div style="margin-bottom: 16px; font-weight: 500;">
                    <span>{title}</span>
                </div>
                <div>
                    <span style="color: #31333FA0; font-weight: 500;">{description}</span>
                </div>
            </div>
        </a>
        """,
        width=width
    )


def main_ui(user_data_stats: UserDataStats, user_recent_activity: pd.DataFrame):

    # Define Main Container
    with st_yled.container(key='work-ui', width=600):

        st.space(80)

        with st_yled.container(horizontal=True, key="home-main-container"):

            with st_yled.container(key="home-left"):

                st_yled.subheader("Workspace", font_size=20)

                num_projects = user_data_stats.num_projects
                num_datasets = user_data_stats.num_fq_datasets
                num_fastqs = user_data_stats.num_fq_files
                stored_reads = user_data_stats.total_num_reads
                num_pro_data = user_data_stats.num_pro_data

                if stored_reads >= 1e12:
                    stored_reads = f"{stored_reads/1e12:.1f}TN"
                elif stored_reads >= 1e9:
                    stored_reads = f"{stored_reads/1e9:.1f}BN"
                elif stored_reads >= 1e6:
                    stored_reads = f"{stored_reads/1e6:.1f}M"
                elif stored_reads >= 1e3:
                    stored_reads = f"{stored_reads/1e3:.1f}K"
                else:
                    stored_reads = f"{stored_reads}"

                st.space(24)

                with st.container(key="metrics-container", horizontal=True):

                    st_yled.metric(
                        label="Projects",
                        value=f"{num_projects}",
                        color='#1d959b',
                        width = 120
                    )

                    st_yled.metric(
                        label="Datasets",
                        value=f"{num_datasets}",
                        color='#1d959b',
                        width = 120
                    )

                    st_yled.metric(
                        label="Pro Datasets",
                        value=f"{num_pro_data}",
                        color='#1d959b',
                        width = 120
                    )

                    st_yled.metric(
                        label="FASTQ Files",
                        value=f"{num_fastqs}",
                        color='#1d959b',
                        width = 120
                    )

                    st_yled.metric(
                        label="Stored Reads",
                        value=f"{stored_reads}",
                        color='#1d959b',
                        width = 120
                    )

                st.space(48)

                # Show quickstart ONLY if login is disabled
                if not uiconfig.ENABLE_LOGIN:


                    st_yled.subheader("Quickstart", font_size=20)

                    st.space(24)

                    with st.container(gap='medium', horizontal=True):
                        
                        quickstart_card(
                            title="Getting started",
                            description="ReadStore Tutorial",
                            link="/getting_started?page=start",
                            width=256
                        )

                        quickstart_card(
                            title="Using the Command Line Interface",
                            description="Connect from Terminal and Bash shell",
                            link="/api#connecting-from-terminal-shell",
                            width=400
                        ) 

                    with st.container(gap='medium', horizontal=True):
                        
                        quickstart_card(
                            title="Using the Python SDK",
                            description="Access ReadStore from Python scripts and notebooks",
                            link="/api#python-api",
                            width=400
                        )

                        quickstart_card(
                            title="Using the R SDK",
                            description="Access ReadStore from R code",
                            link="/api#r-api",
                            width=256
                        )

                    with st.container(gap='medium', horizontal=True):
                        
                        quickstart_card(
                            title="Upload FASTQ Files",
                            description="How to upload FASTQ files to ReadStore",
                            link="/getting_started?page=file-upload",
                            width=256
                        )

                        quickstart_card(
                            title="What are Processed Data?",
                            description="Add analysis files to your Datasets",
                            link="/getting_started?page=pro-data",
                            width=256
                        )

            with st_yled.container(key="home-right", width=240):

                max_activities = min(4, len(user_recent_activity))

                st_yled.subheader("Recent Activities", font_size=20)

                st.space(24)
                
                for ix in range(max_activities):
                    
                    activity = user_recent_activity.iloc[ix]
                    
                    item_name = activity['name']
                    item_id = activity['id']
                    item_type = activity['type']
                    action = activity['action']
                    updated = activity['updated'].strftime("%Y-%m-%d")

                    if action == 'created':
                        action_name = 'Added'
                    else:
                        action_name = 'Updated'

                    if item_type == 'dataset':
                        item_tag = "Dataset"
                    elif item_type == 'project':
                        item_tag = "Project"
                    elif item_type == 'pro_data':
                        item_tag = "Processed Data"
                    
                    with st_yled.container(border_color='#1d959b',
                                           border_width="2px",
                                           border_style="solid",
                                           key = "home-activity-container-" + str(ix)):

                        st_yled.markdown(item_tag,
                                         key="home-activity-item-type-" + str(ix),
                                         font_size=12,
                                         color='#FFFFFF',
                                         font_weight=600,
                                         width='content')

                        st_yled.text(item_name)

                        st_yled.markdown(action_name + " " + updated, font_size=12, color='#808495')


# region DATA

user_data_stats = datamanager.get_user_data_stats(st.session_state["jwt_auth_header"])
user_recent_activity = datamanager.get_recent_activity(st.session_state["jwt_auth_header"])

main_ui(user_data_stats, user_recent_activity)