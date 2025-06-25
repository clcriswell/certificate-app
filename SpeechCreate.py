import json
import io
import difflib
from datetime import datetime
from pathlib import Path
import os

import streamlit as st
import openai
import logging
from docx import Document

from speech_creator.file_utils import extract_text
from speech_creator.voice_profile import generate_profile_from_text, update_profile
from speech_creator.github_io import load_file, save_file, list_files
from speech_creator.prompt_builder import make_speech_prompt

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
        handlers=[
            logging.FileHandler("speech.log"),
            logging.StreamHandler(),
        ],
    )
logger = logging.getLogger(__name__)

client = openai.OpenAI()
MODEL = "gpt-4o"

st.set_page_config(page_title="Speech Creator", layout="wide")
st.title("🗣️ Speech Creator")

for key, default in {
    "profile": None,
    "speech_draft": "",
    "orig_draft": "",
    "final_text": "",
    "step": 0,
}.items():
    st.session_state.setdefault(key, default)


def _slugify(name: str) -> str:
    return Path(name.lower().replace(" ", "_")).stem


def goto_step(new_step: int, desc: str = "") -> None:
    """Set the session step and log the transition."""
    logger.info("Transition to step %d %s", new_step, f"- {desc}" if desc else "")
    st.session_state.step = new_step


def back_button():
    if st.button("Back"):
        goto_step(max(st.session_state.step - 1, 0), "Back pressed")


step = st.session_state.step

if step == 0:
    st.header("Select Voice Profile")
    profiles = [Path(p).name for p in list_files("profiles")]
    selected = st.radio("Existing Voice Profiles", profiles, key="selected_profile")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Next", disabled=not selected):
            data = load_file(f"profiles/{selected}")
            if data:
                st.session_state.profile = json.loads(data)
                goto_step(2, f"Loaded profile {selected}")
    with col2:
        if st.button("Add New"):
            goto_step(1, "Add new profile")

elif step == 1:
    st.header("Create Voice Profile")
    uploaded = st.file_uploader(
        "Upload Writing Samples",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
        key="upload",
    )
    profile_name = st.text_input("Profile Name", key="profile_name")
    if st.button("Generate Profile"):
        texts = [extract_text(f) for f in uploaded or []]
        all_text = "\n".join(texts)
        if not all_text:
            st.error("Please upload at least one file")
        else:
            logger.info("Generating profile '%s' from %d files", profile_name, len(uploaded or []))
            with st.spinner("Analyzing writing style..."):
                st.session_state.profile = generate_profile_from_text(
                    all_text, profile_name
                )
            st.success("Profile generated")
            logger.info("Profile generation completed")
    if st.session_state.profile:
        profile_json = json.dumps(st.session_state.profile, indent=2)
        st.text_area(
            "Voice Profile", value=profile_json, height=200, key="profile_json"
        )
        if st.button("Save Profile"):
            slug = _slugify(st.session_state.profile.get("name", "profile"))
            save_file(
                f"profiles/{slug}.json",
                json.dumps(st.session_state.profile, indent=2),
                f"Save profile {slug}",
            )
            st.success("Profile saved")
            goto_step(2, f"Profile saved {slug}")
    back_button()

elif step == 2:
    st.header("Event Title and Description")
    st.text_area(
        "Event Title and Description",
        key="event_desc",
        help="Tell us about the event (Name and Any details)",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Next"):
            goto_step(3, "Event details provided")

elif step == 3:
    st.header("Speech Length")
    st.radio(
        "How long will the speech be?",
        ["5 Minutes", "10 Minutes", "15 Minutes", "30 minutes"],
        key="time",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Next"):
            goto_step(4, "Selected speech length")

elif step == 4:
    st.header("Tone")
    st.multiselect(
        "What tone do you want the speech to be in?",
        [
            "Inspirational",
            "Celebratory",
            "Solemn",
            "Persuasive",
            "Informative",
            "Urgent",
            "Humorous",
        ],
        key="tone",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Next"):
            goto_step(5, "Selected tone")

elif step == 5:
    st.header("Audience")
    st.multiselect(
        "Tell us about the Audience.",
        [
            "Local community members",
            "Industry professionals/peers",
            "Government officials & policymakers",
            "Students",
            "Educators",
            "Fundraiser",
            "Media and press representatives",
            "Business Leaders",
        ],
        key="audience",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Next"):
            goto_step(6, "Selected audience")

elif step == 6:
    st.header("Special Recognitions")
    st.text_area(
        "Special Recognitions",
        key="recognitions",
        help="Is there anybody we should mention?",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Next"):
            goto_step(7, "Added recognitions")

elif step == 7:
    st.header("Specific Instructions")
    st.text_area(
        "Specific Instructions",
        key="instructions",
        help="Is there anything else that we need to include?",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Create Speech"):
            logger.info("Starting speech generation")
            form_data = {
                "event_type": st.session_state.get("event_desc", ""),
                "purpose": "",
                "audience": ", ".join(st.session_state.get("audience", [])),
                "emotions": "",
                "timing": st.session_state.get("time", ""),
                "recognitions": st.session_state.get("recognitions", ""),
                "tone": ", ".join(st.session_state.get("tone", [])),
                "context_background": "",
                "special_considerations": st.session_state.get("instructions", ""),
            }
            research_notes = None
            try:
                from modules import research_assistant

                if hasattr(research_assistant, "gather_info"):
                    logger.info("Gathering research notes")
                    research_notes = research_assistant.gather_info(
                        form_data["event_type"]
                    )
            except RuntimeError as e:
                st.warning(f"Research assistant unavailable: {e}")
                research_notes = None
            except Exception:
                logging.exception("Research assistant failed")
                st.warning("Failed to gather research notes.")
                research_notes = None

            with st.spinner(
                "We\u2019re burning the midnight oil on this one, your speech is coming right up!"
            ):
                messages = make_speech_prompt(
                    st.session_state.profile or {}, form_data, research_notes
                )
                logger.info("Calling OpenAI for draft")
                response = client.chat.completions.create(
                    model=MODEL, messages=messages, max_tokens=2000
                )
                draft = response.choices[0].message.content.strip()
                st.session_state.speech_draft = draft
                st.session_state.orig_draft = draft
                logger.info("Draft generated")
            goto_step(8, "Speech draft ready")

elif step == 8:
    st.header("Speech Preview")
    draft_text = st.text_area(
        "Make any revisions now, or click accept",
        value=st.session_state.speech_draft,
        height=300,
        key="draft_edit",
    )
    col1, col2 = st.columns(2)
    with col1:
        back_button()
    with col2:
        if st.button("Accept"):
            final_text = draft_text
            diff = "\n".join(
                difflib.unified_diff(
                    st.session_state.orig_draft.splitlines(),
                    final_text.splitlines(),
                    lineterm="",
                )
            )
            if st.session_state.profile:
                st.session_state.profile = update_profile(
                    st.session_state.profile, final_text
                )
            slug = datetime.now().strftime("%Y-%m-%d_%H%M")
            logger.info("Saving speech %s", slug)
            save_file(f"speeches/{slug}.txt", final_text, f"Add speech {slug}")
            doc = Document()
            doc.add_paragraph(final_text)
            buf = io.BytesIO()
            doc.save(buf)
            st.session_state.final_text = final_text
            st.session_state.docx_data = buf.getvalue()
            st.session_state.slug = slug
            st.session_state.diff = diff
            goto_step(9, f"Saved speech {slug}")

elif step == 9:
    st.success("Speech saved")
    st.download_button(
        "Download DOCX",
        st.session_state.docx_data,
        file_name=f"{st.session_state.slug}.docx",
    )
    if st.button("Create Talking Points"):
        logger.info("Generating talking points for %s", st.session_state.slug)
        sum_messages = [
            {
                "role": "system",
                "content": "Summarize the following speech into bullet points.",
            },
            {"role": "user", "content": st.session_state.final_text},
        ]
        resp = client.chat.completions.create(
            model=MODEL, messages=sum_messages, temperature=0.7, max_tokens=2000
        )
        points = resp.choices[0].message.content.strip()
        st.download_button(
            "Download Talking Points",
            points,
            file_name=f"{st.session_state.slug}_points.txt",
        )
        save_file(
            f"speeches/{st.session_state.slug}_points.txt",
            points,
            f"Add points {st.session_state.slug}",
        )
        logger.info("Talking points saved for %s", st.session_state.slug)
