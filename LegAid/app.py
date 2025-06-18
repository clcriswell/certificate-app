import streamlit as st
from pathlib import Path
import base64

st.set_page_config(
    page_title="Legislative Tools",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

st.write("Select a tool below to begin.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link("LegAid/pages/1_CertCreate.py", label="CertCreate")
with col2:
    st.page_link("LegAid/pages/2_SpeechCreate.py", label="SpeechCreate")
with col3:
    st.page_link("LegAid/pages/3_ResponseCreate.py", label="ResponseCreate")
with col4:
    st.page_link("LegAid/pages/4_LegCreate.py", label="LegCreate")
