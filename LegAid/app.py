import streamlit as st
from pathlib import Path
import base64
from utils.navigation import render_sidebar

st.set_page_config(
    page_title="Legislative Tools",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)
render_sidebar()

logo_path = Path(__file__).parent / "Assets" / "MainLogo.png"
with open(logo_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode()
logo_small = f"<img src='data:image/png;base64,{encoded}' width='20' style='vertical-align:middle;margin-right:4px;'>"

st.markdown(
    f"""
    <div style='text-align:center; padding:2rem 0;'>
        <img src='data:image/png;base64,{encoded}' width='600' alt='Application logo'>
        <h4 style='margin-top:0; color: gray;'>Tools for Legislative Productivity</h4>
    </div>
    <style>
    a[data-testid="stPageLink"] {{
        display:inline-block;
        padding:0.5rem 1rem;
        background:#eee;
        border:1px solid #ccc;
        border-radius:4px;
        margin:0 0.2rem;
        text-decoration:none;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(logo_small, unsafe_allow_html=True)
    st.page_link("pages/1_CertCreate.py", label="CertCreate", icon=None)
with col2:
    st.markdown(logo_small, unsafe_allow_html=True)
    st.page_link("pages/2_SpeechCreate.py", label="SpeechCreate", icon=None)
with col3:
    st.markdown(logo_small, unsafe_allow_html=True)
    st.page_link("pages/3_ResponseCreate.py", label="ResponseCreate", icon=None)
with col4:
    st.markdown(logo_small, unsafe_allow_html=True)
    st.page_link("pages/4_LegTrack.py", label="LegTrack", icon=None)
with col5:
    st.markdown(logo_small, unsafe_allow_html=True)
    st.page_link("pages/5_MailCreate.py", label="MailCreate", icon=None)

