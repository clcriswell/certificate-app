import streamlit as st
from utils.shared_functions import example_helper
from utils.navigation import render_sidebar, render_logo

st.set_page_config(layout="centered", initial_sidebar_state="expanded")
render_sidebar()
render_logo()
st.title("📮 MailCreate")


def render_mail_creator():
    st.write("Draft formal mail pieces.")
    st.text_area("Mail Content", height=100)
    st.button("Generate Mail")


if __name__ == "__main__":
    render_mail_creator()
