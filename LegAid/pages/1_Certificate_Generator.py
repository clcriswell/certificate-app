import streamlit as st
from utils.shared_functions import example_helper


def render_certificate_generator():
    st.markdown("## 📄 **Certificate Generator**")
    st.write("This module will create official certificates.")

    col1, col2 = st.columns(2)
    col1.text_input("Recipient Name")
    col2.date_input("Date")
    st.text_area("Certificate Notes", height=100)
    st.button("Generate")


if __name__ == "__main__":
    render_certificate_generator()
