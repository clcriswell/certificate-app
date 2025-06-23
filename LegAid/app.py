import streamlit as st
from pathlib import Path
import base64
from utils.navigation import render_sidebar

st.set_page_config(
    page_title="Legislative Tools",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_sidebar()

logo_path = Path(__file__).parent / "Assets" / "MainLogo.png"
with open(logo_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style='text-align:center; padding:2rem 0;'>
        <img src='data:image/png;base64,{encoded}' width='600' alt='Application logo'>
        <h4 style='margin-top:0; color: gray;'>Tools for Legislative Productivity</h4>
    </div>
    """,
    unsafe_allow_html=True,
)

col2, col3, col4 = st.columns(3)

with col2:
    if st.button("CertCreate"):
        st.switch_page("pages/1_CertCreate.py")

with col3:
    if st.button("SpeechCreate"):
        st.switch_page("pages/2_SpeechCreate.py")

with col4:
    if st.button("ResponseCreate"):
        st.switch_page("pages/3_ResponseCreate.py")




