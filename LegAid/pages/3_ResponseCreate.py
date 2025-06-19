import streamlit as st
from utils.navigation import render_sidebar, render_logo



st.set_page_config(
    layout="centered",
    initial_sidebar_state="collapsed",
    page_title="ResponseCreate",
    page_icon=None,
)
render_sidebar()
render_logo()

st.markdown("<h1>ResponseCreate</h1>", unsafe_allow_html=True)


def render_constituent_response():
    st.write("Draft replies to constituent inquiries.")

    st.text_area("Constituent Question", height=100)
    st.button("Generate Response")


if __name__ == "__main__":
    render_constituent_response()
