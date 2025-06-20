import streamlit as st
import asyncio
import os
from utils.navigation import render_sidebar, render_logo
from modules.research_assistant import build_your_assistant
from modules.report_view import generate_html_report

st.set_page_config(page_title="Research Assistant", layout="wide")
render_sidebar()
render_logo()

# Load API keys from secrets into environment variables
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "SERPAPI_API_KEY" in st.secrets:
    os.environ["SERPAPI_API_KEY"] = st.secrets["SERPAPI_API_KEY"]
if "TWITTER_BEARER_TOKEN" in st.secrets:
    os.environ["TWITTER_BEARER_TOKEN"] = st.secrets["TWITTER_BEARER_TOKEN"]

st.title("\ud83d\udd0d Next-Gen Research Assistant")

query = st.text_input("Enter your research question")

if st.button("Run Research") and query:
    with st.spinner("Researching, analyzing, and synthesizing..."):
        assistant = build_your_assistant()
        result = asyncio.run(assistant.run(query))
        st.success("Research complete.")
        st.components.v1.html(generate_html_report(result), height=700, scrolling=True)
        with st.expander("\ud83d\udd0e View Answer Text"):
            st.write(result["answer"])
