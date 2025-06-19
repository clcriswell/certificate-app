import streamlit as st
from pathlib import Path
import base64
from .shared_functions import reset_certcreate_session

# Preload the application logo for reuse
_logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
with open(_logo_path, "rb") as _f:
    _encoded_logo = base64.b64encode(_f.read()).decode()



def render_sidebar():
    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none;}</style>",
        unsafe_allow_html=True,
    )
    logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    with st.sidebar:
        st.page_link("app.py", label="LegAid", icon=None)
        if st.button("CertCreate", use_container_width=True):
            reset_certcreate_session()
            st.switch_page("pages/1_CertCreate.py")

        st.page_link("pages/2_SpeechCreate.py", label="SpeechCreate", icon=None)

        st.page_link("pages/3_ResponseCreate.py", label="ResponseCreate", icon=None)

        st.page_link("pages/4_LegTrack.py", label="LegTrack", icon=None)

        st.page_link("pages/5_MailCreate.py", label="MailCreate", icon=None)



def render_logo():
    logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"<a href='../app.py'><img src='data:image/png;base64,{encoded}' width='160' style='position:absolute;top:10px;right:10px;z-index:1000;'></a>",
        unsafe_allow_html=True,
    )
