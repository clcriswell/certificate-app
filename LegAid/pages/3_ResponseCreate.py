import streamlit as st
from utils.shared_functions import example_helper
from utils.navigation import render_sidebar, SMALL_LOGO_HTML


st.set_page_config(layout="centered", initial_sidebar_state="expanded")
render_sidebar()
st.markdown(f"<h1>{SMALL_LOGO_HTML} ResponseCreate</h1>", unsafe_allow_html=True)


def render_constituent_response():
    st.write("Draft replies to constituent inquiries.")

    st.text_area("Constituent Question", height=100)
    st.button("Generate Response")


if __name__ == "__main__":
    render_constituent_response()
