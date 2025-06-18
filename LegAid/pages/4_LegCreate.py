import streamlit as st
from utils.shared_functions import example_helper


st.set_page_config(layout="centered")
st.title("📚 LegCreate")


def render_knowledge_center():
    st.write("Access legislative resources and references.")

    st.text_input("Search Resources")
    st.button("Search")


if __name__ == "__main__":
    render_knowledge_center()
