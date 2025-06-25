import streamlit as st
import asyncio
import os
from pathlib import Path
import sys
from utils.navigation import render_sidebar, render_logo

# Ensure the repository root is on the Python path so ``modules`` can be
# imported when this script is executed directly with Streamlit.
sys.path.append(str(Path(__file__).resolve().parents[2]))

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

# Use the literal Unicode character instead of a surrogate pair so
# Streamlit can encode the string without errors.
st.title("🔍 Next-Gen Research Assistant")

query = st.text_input("Enter your research question")

if st.button("Run Research") and query:
    with st.spinner("Researching, analyzing, and synthesizing..."):
        try:
            assistant = build_your_assistant()
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(assistant.run(query))
            finally:
                loop.close()
        except RuntimeError as e:
            st.warning(f"Research assistant unavailable: {e}")
            result = None
        if result:
            st.success("Research complete.")
            st.components.v1.html(generate_html_report(result), height=700, scrolling=True)
            with st.expander("🔎 View Answer Text"):
                st.write(result["answer"])
