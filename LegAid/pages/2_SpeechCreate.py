"""Speech Creator page integrated with LegAid."""

from __future__ import annotations

import json
import io
import os
import difflib
from datetime import datetime
from pathlib import Path
import sys

import streamlit as st
from docx import Document

from utils.navigation import render_sidebar, render_logo

# Ensure repository root is importable for speech_creator package
sys.path.append(str(Path(__file__).resolve().parents[2]))

from speech_creator.file_utils import extract_text
from speech_creator.voice_profile import generate_profile_from_text, update_profile
from speech_creator.github_io import load_file, save_file, list_files
from speech_creator.prompt_builder import make_speech_prompt

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

import openai

client = openai.OpenAI()
MODEL = "gpt-4o"

st.set_page_config(page_title="SpeechCreate", layout="wide")
render_sidebar()
render_logo()

st.title("🗣️ Speech Creator")

if "profile" not in st.session_state:
    st.session_state.profile = None
if "speech_draft" not in st.session_state:
    st.session_state.speech_draft = ""
if "orig_draft" not in st.session_state:
    st.session_state.orig_draft = ""
if "final_text" not in st.session_state:
    st.session_state.final_text = ""


def _slugify(name: str) -> str:
    return Path(name.lower().replace(" ", "_")).stem


with st.expander("Voice Integrated Profile", expanded=True):
    profiles = [Path(p).name for p in list_files("profiles")]
    selected = st.selectbox("Load Existing Profile", ["" ] + profiles)
    if selected:
        data = load_file(f"profiles/{selected}")
        if data:
            st.session_state.profile = json.loads(data)

    uploaded = st.file_uploader(
        "Upload Writing Samples", type=["txt", "pdf", "docx"], accept_multiple_files=True
    )
    profile_name = st.text_input("Profile Name", "My Voice")
    if st.button("Generate Profile"):
        texts = [extract_text(f) for f in uploaded or []]
        all_text = "\n".join(texts)
        if not all_text:
            st.error("Please upload at least one file")
        else:
            with st.spinner("Analyzing writing style..."):
                st.session_state.profile = generate_profile_from_text(all_text, profile_name)
            st.success("Profile generated")

    if st.session_state.profile:
        profile_json = json.dumps(st.session_state.profile, indent=2)
        edited = st.text_area("Voice Profile", value=profile_json, height=200)
        try:
            st.session_state.profile = json.loads(edited)
        except Exception:
            st.warning("Invalid JSON; using previous profile")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Profile to GitHub"):
                slug = _slugify(st.session_state.profile.get("name", "profile"))
                save_file(
                    f"profiles/{slug}.json",
                    json.dumps(st.session_state.profile, indent=2),
                    f"Save profile {slug}",
                )
                st.success("Profile saved")
        with col2:
            st.download_button(
                "Download Profile", json.dumps(st.session_state.profile, indent=2), "profile.json"
            )

with st.form("speech_form"):
    st.subheader("Occasion Details")
    event_type = st.text_input("Event Type")
    purpose = st.text_input("Purpose")
    audience = st.text_input("Audience")
    emotions = st.text_input("Desired Emotions")
    timing = st.text_input("Timing / Length")
    recognitions = st.text_input("Recognitions / Thanks")
    tone = st.text_input("Tone (formal, casual, etc.)")
    context_background = st.text_area("Background Context")
    special_considerations = st.text_area("Special Considerations")
    submitted = st.form_submit_button("Create Speech")

if submitted:
    form_data = {
        "event_type": event_type,
        "purpose": purpose,
        "audience": audience,
        "emotions": emotions,
        "timing": timing,
        "recognitions": recognitions,
        "tone": tone,
        "context_background": context_background,
        "special_considerations": special_considerations,
    }
    research_notes = None
    try:
        from modules import research_assistant

        if hasattr(research_assistant, "gather_info"):
            research_notes = research_assistant.gather_info(event_type)
    except Exception:
        research_notes = None

    with st.spinner("Generating draft..."):
        messages = make_speech_prompt(
            st.session_state.profile or {}, form_data, research_notes
        )
        response = client.chat.completions.create(
            model=MODEL, messages=messages, max_tokens=2000
        )
        draft = response.choices[0].message.content.strip()
        st.session_state.speech_draft = draft
        st.session_state.orig_draft = draft

if st.session_state.speech_draft:
    draft_text = st.text_area("Speech Draft", value=st.session_state.speech_draft, height=300)
    if st.button("Complete"):
        final_text = draft_text
        diff = "\n".join(
            difflib.unified_diff(
                st.session_state.orig_draft.splitlines(),
                final_text.splitlines(),
                lineterm="",
            )
        )
        if st.session_state.profile:
            st.session_state.profile = update_profile(st.session_state.profile, final_text)
        slug = datetime.now().strftime("%Y-%m-%d_%H%M")
        save_file(f"speeches/{slug}.txt", final_text, f"Add speech {slug}")

        doc = Document()
        doc.add_paragraph(final_text)
        buf = io.BytesIO()
        doc.save(buf)
        st.download_button("Download DOCX", buf.getvalue(), file_name=f"{slug}.docx")

        st.session_state.final_text = final_text
        with st.expander("Changes from original draft"):
            st.text_area("Diff", diff, height=200)
        st.success("Speech saved and files generated")

    if st.session_state.final_text and st.button("Create Talking Points"):
        sum_messages = [
            {"role": "system", "content": "Summarize the following speech into bullet points."},
            {"role": "user", "content": st.session_state.final_text},
        ]
        resp = client.chat.completions.create(
            model=MODEL, messages=sum_messages, temperature=0.7, max_tokens=2000
        )
        points = resp.choices[0].message.content.strip()
        slug = datetime.now().strftime("%Y-%m-%d_%H%M")
        st.download_button("Download Talking Points", points, file_name=f"{slug}_points.txt")
        save_file(f"speeches/{slug}_points.txt", points, f"Add points {slug}")
