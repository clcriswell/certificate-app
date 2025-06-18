import streamlit as st
from utils.shared_functions import example_helper


def render_speech_writer():
    st.markdown("## 📝 **Speech Writer**")
    st.write("Compose speeches with AI assistance.")

    st.text_area("Speech Topic", height=100)
    st.button("Draft Speech")


if __name__ == "__main__":
    render_speech_writer()
