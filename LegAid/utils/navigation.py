import streamlit as st
from pathlib import Path
import base64

# Preload the application logo for reuse
_logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
with open(_logo_path, "rb") as _f:
    _encoded_logo = base64.b64encode(_f.read()).decode()

# Small inline logo HTML used in page headers
SMALL_LOGO_HTML = (
    f"<img src='data:image/png;base64,{_encoded_logo}' width='20' "
    "style='vertical-align:middle;margin-right:4px;'>"
)


def render_sidebar(on_certcreate=None):
    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none;}</style>",
        unsafe_allow_html=True,
    )
    logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    logo_small = f"<img src='data:image/png;base64,{encoded}' width='20' style='vertical-align:middle;margin-right:4px;'>"
    with st.sidebar:
        st.page_link("app.py", label="LegAid")
        if on_certcreate:
            st.button("CertCreate", on_click=on_certcreate)
        else:
            st.markdown(logo_small, unsafe_allow_html=True)
            st.page_link("pages/1_CertCreate.py", label="CertCreate")
        st.markdown(logo_small, unsafe_allow_html=True)
        st.page_link("pages/2_SpeechCreate.py", label="SpeechCreate")
        st.markdown(logo_small, unsafe_allow_html=True)
        st.page_link("pages/3_ResponseCreate.py", label="ResponseCreate")
        st.markdown(logo_small, unsafe_allow_html=True)
        st.page_link("pages/4_LegTrack.py", label="LegTrack")
        st.markdown(logo_small, unsafe_allow_html=True)
        st.page_link("pages/5_MailCreate.py", label="MailCreate")


def render_logo():
    logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"<a href='../app.py'><img src='data:image/png;base64,{encoded}' width='80' style='position:absolute;top:10px;right:10px;z-index:1000;'></a>",
        unsafe_allow_html=True,
    )
