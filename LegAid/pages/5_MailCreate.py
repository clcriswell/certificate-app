import streamlit as st
from utils.navigation import render_sidebar, render_logo


st.set_page_config(
    layout="centered",
    initial_sidebar_state="auto",
    page_title="MailCreate",
    page_icon=None,
)
render_sidebar()
render_logo()

st.markdown("<h1>MailCreate</h1>", unsafe_allow_html=True)


def render_mail_creator():
    st.write("Draft formal mail pieces.")
    st.text_area("Mail Content", height=100)
    st.button("Generate Mail")


if __name__ == "__main__":
    render_mail_creator()
