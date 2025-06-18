import streamlit as st
from pathlib import Path
import base64

st.set_page_config(page_title="Legislative Tools", page_icon="📜", layout="wide")

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

st.write("Select a tool from the sidebar to begin.")
