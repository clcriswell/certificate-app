import streamlit as st
from pathlib import Path
import base64

# Preload the application logo for reuse
_logo_path = Path(__file__).resolve().parent.parent / "Assets" / "MainLogo.png"
with open(_logo_path, "rb") as _f:
    _encoded_logo = base64.b64encode(_f.read()).decode()



def render_sidebar():
    """Render sidebar with mobile auto-close and navigation links."""
    st.markdown(
        "<style>[data-testid='stSidebarNav']{display:none;}</style>",
        unsafe_allow_html=True,
    )

    # Style the navigation links and CertCreate button consistently
    st.markdown(
        """
        <style>
        a[data-testid="stPageLink"],
        button#nav_certcreate {
            display:inline-block;
            padding:0.75rem 1.25rem;
            margin:0 0.1rem;
            background:#004cbd;
            color:#fff !important;
            border-radius:4px;
            text-decoration:none;
            font-weight:600;
            border:none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # JavaScript to collapse the sidebar on small screens
    st.markdown(
        """
        <script>
        function closeSidebarIfMobile() {
            const btn = window.parent.document.querySelector('button[title="Hide sidebar"]');
            const sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
            if (window.innerWidth <= 768 && btn && sidebar?.getAttribute('aria-expanded') === 'true') {
                btn.click();
            }
        }
        window.addEventListener('load', closeSidebarIfMobile);
        window.parent.document.addEventListener('click', function(e) {
            if (e.target.closest('a[data-testid="stPageLink"], #nav_certcreate')) {
                setTimeout(closeSidebarIfMobile, 0);
            }
        });
        </script>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.page_link("app.py", label="LegAid", icon=None)

        if st.button("CertCreate", key="nav_certcreate"):
            st.session_state["certcreate_reset"] = True
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
