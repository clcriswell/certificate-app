"""Voice profile generation and updates using OpenAI."""
from __future__ import annotations

from datetime import datetime
import json
import os
import openai


def generate_profile_from_text(text: str, name: str) -> dict:
    """Generate a writing voice profile from sample text."""
    if not text:
        raise ValueError("No text provided for profile generation")

    sys_prompt = (
        "You are VoiceMapper, an AI that analyzes a person's writing style and "
        "summarizes it. Produce a JSON object with keys 'name', 'profile_text', "
        "'created_at'. The profile_text should describe tone, vocabulary and "
        "style in 2-3 sentences. Use ISO datetime format."
    )
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"NAME: {name}\nTEXT:\n{text}"},
    ]
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o", messages=messages, temperature=0.2
    )
    try:
        data = json.loads(resp.choices[0].message.content.strip())
    except Exception:
        data = {
            "name": name,
            "profile_text": resp.choices[0].message.content.strip(),
            "created_at": datetime.utcnow().isoformat(),
        }
    data.setdefault("name", name)
    data.setdefault("created_at", datetime.utcnow().isoformat())
    data.setdefault("samples", [text])
    return data


def update_profile(profile: dict, new_text: str) -> dict:
    """Append a new writing sample to the profile's samples array."""
    samples = profile.get("samples", [])
    samples.append(new_text)
    profile["samples"] = samples
    return profile
