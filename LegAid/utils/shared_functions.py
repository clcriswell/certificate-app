"""Shared helper functions for LegAid."""


def example_helper():
    """Example helper function."""
    pass


def reset_certcreate_session():
    """Clear CertCreate-related session state keys."""
    import streamlit as st

    keys = [
        "pdf_text",
        "source_type",
        "parsed_entries",
        "cert_rows",
        "uniform_template",
        "event_date_raw",
        "formatted_event_date",
        "use_uniform",
        "guidance",
        "manual_certs",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.started = False
    st.session_state.start_mode = None
