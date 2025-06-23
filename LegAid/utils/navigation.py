import streamlit as st
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
            
        st.page_link("pages/2_SpeechCreate.py", label="SpeechCreate", icon=None)

        st.page_link("pages/3_ResponseCreate.py", label="ResponseCreate", icon=None)

        st.page_link("pages/4_LegTrack.py", label="LegTrack", icon=None)

        st.page_link("pages/5_MailCreate.py", label="MailCreate", icon=None)

        st.page_link("pages/6_ResearchAssistant.py", label="Research Assistant", icon=None)

        st.page_link("pages/7_ChatMode.py", label="Chat Mode", icon=None)

        st.page_link("pages/8_TaskAgent.py", label="Task Agent", icon=None)



def render_logo():
    """Render the application logo responsively in the top-right corner."""
    st.markdown(
        f'''
        <style>
        .logo-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
        }}

        .logo-container img {{
            width: 200px;
        }}

        @media only screen and (max-width: 768px) {{
            .logo-container img {{
                width: 120px; /* reduce logo size on smaller screens */
            }}
            .logo-container {{
                top: 5px;
                right: 5px;
            }}
        }}
        </style>

        <div class="logo-container">
            <a href="/" target="_self">
                <img src="data:image/png;base64,{_encoded_logo}" />
            </a>
        </div>
        ''',
        unsafe_allow_html=True
    )

