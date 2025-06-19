"""Shared helper functions for LegAid."""

from __future__ import annotations

import re
from datetime import datetime
from dateutil import parser as date_parser


def example_helper():
    """Example helper function."""
    pass


def normalize_date_strings(text: str) -> str:
    """Return text with common date formats normalized.

    Examples like "JUNE 14TH" or "14th of June" will be converted to
    "June 14". Dates that include a year will be formatted as
    ``YYYY-MM-DD``.
    """

    month = (
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
        r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    )

    patterns = [
        rf"{month}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s*\d{{2,4}})?(?:\s+[A-Za-z]+)*",
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?",
        rf"\d{{1,2}}(?:st|nd|rd|th)?\s+of\s+{month}\.?(?:,?\s*\d{{2,4}})?",
        r"\d{4}-\d{2}-\d{2}",
    ]
    date_regex = re.compile("|".join(patterns), flags=re.IGNORECASE)

    def repl(match: re.Match) -> str:
        raw = match.group(0)
        try:
            dt = date_parser.parse(raw, fuzzy=True, default=datetime(1900, 1, 1))
        except Exception:
            return raw
        has_year = dt.year != 1900
        return dt.strftime("%Y-%m-%d") if has_year else dt.strftime("%B %d")

    return date_regex.sub(repl, text)


def reset_certcreate_session():
    """Clear CertCreate-related session state keys."""
    import streamlit as st

    keys = [
        "pdf_text",
        "source_type",
        "parsed_entries",
        "cert_rows",
        "uniform_template",
        "event_date_raw",
        "formatted_event_date",
        "use_uniform",
        "guidance",
        "manual_certs",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.started = False
    st.session_state.start_mode = None


def enforce_first_person(text: str) -> str:
    """Return text with first-person pronouns instead of plural forms."""

    replacements = [
        (r"\bwe are\b", "I am"),
        (r"\bwe're\b", "I'm"),
        (r"\bwe have\b", "I have"),
        (r"\bwe've\b", "I've"),
        (r"\bwe\b", "I"),
        (r"\bour\b", "my"),
        (r"\bours\b", "mine"),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, flags=re.IGNORECASE)
    return text
