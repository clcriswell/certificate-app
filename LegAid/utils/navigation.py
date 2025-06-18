import streamlit as st
from pathlib import Path
import base64


def render_sidebar(on_certcreate=None):
    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none;}</style>",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.page_link("app.py", label="LegAid")
        if on_certcreate:
            st.button("CertCreate", on_click=on_certcreate)
        else:
            st.page_link("pages/1_CertCreate.py", label="CertCreate")
        st.page_link("pages/2_SpeechCreate.py", label="SpeechCreate")
        st.page_link("pages/3_ResponseCreate.py", label="ResponseCreate")
        st.page_link("pages/4_LegTrack.py", label="LegTrack")
        st.page_link("pages/5_MailCreate.py", label="MailCreate")


def render_logo():
    logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"<a href='../app.py'><img src='data:image/png;base64,{encoded}' width='80' style='position:absolute;top:10px;right:10px;z-index:1000;'></a>",
        unsafe_allow_html=True,
    )
