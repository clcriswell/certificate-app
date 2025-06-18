import streamlit as st
from utils.shared_functions import example_helper


st.set_page_config(layout="centered")
st.title("📬 ResponseCreate")


def render_constituent_response():
    st.write("Draft replies to constituent inquiries.")

    st.text_area("Constituent Question", height=100)
    st.button("Generate Response")


if __name__ == "__main__":
    render_constituent_response()
