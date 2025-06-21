import os
import sys
from pathlib import Path
import streamlit as st
from utils.navigation import render_sidebar, render_logo

# Ensure repository root is on Python path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from modules.task_agent_client import send_task
from modules.parallel_agent import start_agent

st.set_page_config(page_title="Task Agent", layout="wide")
render_sidebar()
render_logo()

st.title("🚀 Parallel Task Agent")

if st.button("Start Agent"):
    if start_agent():
        st.success("Agent started")
    else:
        st.info("Agent already running")

description = st.text_area("Task Description")
repo_url = st.text_input("Repository URL", "https://github.com/")

if st.button("Submit Task"):
    if not description or not repo_url:
        st.error("Please provide both a description and repository URL")
    else:
        try:
            send_task(description, repo_url)
            st.success("Task submitted")
        except Exception as e:
            st.error(f"Failed to submit task: {e}")
