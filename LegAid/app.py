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

# Load and encode logo image
logo_path = Path(__file__).parent / "Assets" / "MainLogo.png"
with open(logo_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode()

# Render the centered logo and title
st.markdown(
    f"""
    <div style='text-align:center; padding:2rem 0;'>
        <img src='data:image/png;base64,{encoded}' width='600' alt='Application logo'>
        <h4 style='margin-top:0; color: gray;'>Tools for Legislative Productivity</h4>
    </div>
    """,
    unsafe_allow_html=True,
)

# Inject CSS for button styling and positioning below the logo
st.markdown("""
<style>
.centered-btn-container {
    margin-top: 1rem; /* spacing above buttons */
    display: flex;
    justify-content: center;
    gap: 10px; /* spacing between buttons */
}

.centered-btn-container button {
    background-color: #5b8dee;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-size: 16px;
}

.centered-btn-container button:hover {
    background-color: #4a7bd1;
}
</style>
""", unsafe_allow_html=True)

# Place buttons directly below the logo/title block
st.markdown("""
<div class='centered-btn-container'>
    <a href='1_CertCreate'><button>Certificates</button></a>
    <a href='2_SpeechCreate'><button>Speeches</button></a>
    <a href='3_ResponseCreate'><button>Responses</button></a>
</div>
""", unsafe_allow_html=True)





