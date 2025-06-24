"""Prompt building utilities for speech generation."""
from __future__ import annotations

from typing import Dict, List, Optional
import json


def make_speech_prompt(profile: Dict, form: Dict, research: Optional[str] = None) -> List[Dict[str, str]]:
    """Create a message list for ChatGPT speech generation."""
    profile_text = profile.get("profile_text", "")
    occasion = json.dumps(form, indent=2)
    sys_msg = (
        "You are an experienced speechwriter. Craft a heartfelt speech using the "
        "speaker's voice and the provided occasion details."
    )
    user_content = (
        f"VOICE PROFILE:\n{profile_text}\n\n"
        f"OCCASION DETAILS:\n{occasion}"
    )
    if research:
        user_content += f"\n\nRESEARCH NOTES:\n{research}"
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user_content},
    ]
