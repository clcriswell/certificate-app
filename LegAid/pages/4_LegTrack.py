import streamlit as st
from pathlib import Path
from utils.shared_functions import example_helper
from utils.navigation import render_sidebar, render_logo


st.set_page_config(layout="centered", initial_sidebar_state="expanded")
render_sidebar()
render_logo()
st.title("📚 LegTrack")


def render_knowledge_center():
    st.write("Access legislative resources and references.")

    st.text_input("Search Resources")
    st.button("Search")


if __name__ == "__main__":
    render_knowledge_center()
