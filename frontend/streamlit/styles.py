# readstore-basic/frontend/streamlit/styles.py

import streamlit as st



# footer = """<style>
# .footer {
# position: fixed;
# left: 0;
# bottom: 0;
# width: 100%;
# background-color: white;
# color: black;
# text-align: center;
# }
# </style>
# <div class="footer">
# <p><strong>EVO</strong>BYTE Digital Biology</br>evo-case-2 version insert_version</p>
# </div>
# """

# footer = footer.replace("insert_version", uiconfig.__version__)

# st.markdown(footer,unsafe_allow_html=True)

# Remove streamlit buttons
# hide_default_format = """
#        <style>
#        #MainMenu {visibility: hidden; }
#        footer {visibility: hidden;}
#        </style>
#        """
# st.markdown(hide_default_format, unsafe_allow_html=True)


# Adjust button height
def adjust_button_height(height_px: int = 25):
    
    st.markdown(
        # Double brake to escape the string
        f"""
        <style>
            /* Custom CSS to change button height */
            [data-testid="stBaseButton-secondary"] {{
                height: {height_px}px !important; /* Change this to your desired height */
                min-height: {height_px}px !important; /* Change this to your desired height */
            }}
            [data-testid="stBaseButton-primary"] {{
                height: {height_px}px !important; /* Change this to your desired height */
                min-height: {height_px}px !important; /* Change this to your desired height */
            }}
        </style>
        """,
        unsafe_allow_html=True)