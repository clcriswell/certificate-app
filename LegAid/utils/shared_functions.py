"""Shared helper functions for LegAid."""

from __future__ import annotations

import re
from datetime import datetime
from dateutil import parser as date_parser


def example_helper():
    """Example helper function."""
    pass


def extract_json_block(content: str) -> str:
    """Return the JSON payload embedded in an LLM response.

    Many model responses include code fences or short explanations
    before the actual JSON. This helper strips common wrappers and
    returns the first balanced JSON object or array it can find.

    Raises:
        ValueError: If no JSON content can be located or the JSON block
            appears to be truncated.
    """

    if not content:
        raise ValueError("No content provided to extract JSON from.")

    text = content.strip()
    if not text:
        raise ValueError("No content provided to extract JSON from.")

    lower = text.lower()
    for marker in ("```json", "```"):
        idx = lower.find(marker)
        if idx != -1:
            start = idx + len(marker)
            end = lower.find("```", start)
            segment = text[start:end if end != -1 else None].strip()
            if segment:
                text = segment
                lower = text.lower()
                break

    def _first_json_start(value: str) -> int | None:
        positions = [pos for pos in (value.find("{"), value.find("[")) if pos != -1]
        if not positions:
            return None
        return min(positions)

    start_index = _first_json_start(text)
    if start_index is None:
        raise ValueError("No JSON object or array found in response.")

    def _slice_balanced(value: str, idx: int) -> str:
        stack: list[str] = []
        in_string = False
        escape = False
        result: list[str] = []

        for ch in value[idx:]:
            result.append(ch)

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
            elif ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack:
                    raise ValueError("Unexpected closing bracket while parsing JSON.")
                opener = stack.pop()
                if opener == "{" and ch != "}":
                    raise ValueError("Mismatched JSON braces in response.")
                if opener == "[" and ch != "]":
                    raise ValueError("Mismatched JSON brackets in response.")
                if not stack:
                    return "".join(result)

        raise ValueError("JSON content appears to be truncated in the response.")

    return _slice_balanced(text, start_index).strip()


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
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text
