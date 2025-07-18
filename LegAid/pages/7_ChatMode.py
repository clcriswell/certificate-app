import os
import streamlit as st
import sys
from pathlib import Path
from utils.navigation import render_sidebar, render_logo

# Ensure the repository root is on the Python path so ``modules`` can be
# imported when this script is executed directly with Streamlit.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from modules.chat_mode import ChatBot

st.set_page_config(page_title="Chat Mode", layout="wide")
render_sidebar()
render_logo()

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

st.title("💬 Chat Mode")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

bot = ChatBot()

for msg in st.session_state.chat_history:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    reply, history = bot.reply(prompt, st.session_state.chat_history)
    st.session_state.chat_history = history
    st.chat_message("assistant").write(reply)
