timport streamlit as st
from pathlib import Path
import base64

from .shared_functions import reset_certcreate_session

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
        a[data-testid="stPageLink"], [data-testid='stSidebar'] button {
            display:block;
            padding:0.75rem 1.25rem;
            margin:0 0 0.25rem;
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

    # JavaScript to toggle the sidebar based on screen width
    st.markdown(
        """
        <script>
        function adjustSidebar() {
            const hideBtn = window.parent.document.querySelector('button[title="Hide sidebar"]');
            const showBtn = window.parent.document.querySelector('button[title="Show sidebar"]');
            const sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
            const expanded = sidebar?.getAttribute('aria-expanded');
            if (window.innerWidth <= 768 && expanded === 'true' && hideBtn) {
                hideBtn.click();
            } else if (window.innerWidth > 768 && expanded === 'false' && showBtn) {
                showBtn.click();
            }
        }
        window.addEventListener('load', adjustSidebar);
        window.parent.document.addEventListener('click', function(e) {
            if (e.target.closest('a[data-testid="stPageLink"], #nav_certcreate')) {
                setTimeout(adjustSidebar, 0);
            }
        });
        adjustSidebar();
        </script>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.page_link("app.py", label="LegAid", icon=None)

        st.page_link("pages/1_CertCreate.py", label="CertCreate", icon=None)
        
        if st.page_link("pages/1_CertCreate.py", key="nav_certcreate"):
            reset_certcreate_session()
            st.switch_page("pages/1_CertCreate.py")
            
        st.page_link("pages/2_SpeechCreate.py", label="CSpeech", icon=None)

        st.page_link("pages/3_ResponseCreate.py", label="ResponseCreate", icon=None)

        st.page_link("pages/4_LegTrack.py", label="LegTrack", icon=None)

        st.page_link("pages/5_MailCreate.py", label="MailCreate", icon=None)

        st.page_link("pages/6_ResearchAssistant.py", label="Research Assistant", icon=None)

        st.page_link("pages/7_ChatMode.py", label="Chat Mode", icon=None)

        st.page_link("pages/8_TaskAgent.py", label="Task Agent", icon=None)



def render_logo():
    """Render the application logo in the top-right corner."""
    st.markdown(
        f"<a href='../app.py'><img src='data:image/png;base64,{_encoded_logo}' width='160' style='position:absolute;top:10px;right:10px;z-index:1000;'></a>",
        unsafe_allow_html=True,
    )

