"""Prompt building utilities for speech generation."""
from __future__ import annotations

from typing import Dict, List, Optional
import json


def make_speech_prompt(profile: Dict, form: Dict, research: Optional[str] = None) -> List[Dict[str, str]]:
    """Create a message list for ChatGPT speech generation."""
    profile_text = profile.get("profile_text", "")
    occasion = json.dumps(form, indent=2)
    sys_msg = (
        "You are a veteran speechwriter and communications strategist.\n"
        "Your task is to craft a speech channeling the speaker\u2019s voice and the provided occasion details. \n"
        "The goal is a *fully human*, emotionally resonant speech that sounds as if it were written personally by the speaker.  \n"
        "Nothing in the language may feel AI\u2011generated or generic. Avoid clich\u00e9s, filler, and robotic symmetry.\n"
        "\n"
        "CORE MESSAGE : \n"
        "\u2022 Key theme in 3\u20136 words (the mantra) \n"
        "\u2022 Problem statement (one vivid sentence)\n"
        "\u2022 Vision statement (one vivid sentence)\n"
        "\u2022 Call\u2011to\u2011action\n"
        "\n"
        "STRUCTURE (follow this arc):\n"
        "\n"
        "1. **Opening\u2014Establish Connection**  \n"
        "   \u2013 Vivid personal anecdote or local reference unique to the speaker  \n"
        "   \u2013 A note of gratitude or acknowledgment  \n"
        "2. **Define the Moment\u2014What\u2019s at Stake**  \n"
        "   \u2013 Frame the shared challenge in plain language; explain \u201cWhy now?\u201d  \n"
        "3. **Share Vision\u2014Where We\u2019re Going**  \n"
        "   \u2013 Offer a hopeful, values\u2011based picture of the future; repeat the mantra  \n"
        "4. **Offer Plan or Proof\u2014What\u2019s Being Done**  \n"
        "   \u2013 Cite 2\u20133 concrete actions, policies, or results (no dense jargon)  \n"
        "5. **Call to Action\u2014Invite Everyone In**  \n"
        "   \u2013 Close with an inspiring, 8\u201312\u2011word, headline\u2011ready line that ties back to the opening story  \n"
        "\n"
        "REQUIREMENTS FOR AUTHENTICITY & IMPACT: \n"
        "\n"
        "Avoid Statistical Patterns (Repetitive or overly consistent sentence structures, Unusual or uniform sentence lengths, Predictable word frequency and distributions)\n"
        "Avoid Vocabulary Usage that has Frequent generic or vague language, Lacks human-like idiomatic or colloquial expressions, and Overuses certain common transitional phrases.\n"
        "Maintain Contextual Consistency by avoiding Abrupt changes in context or topic shifts and\n"
        "Superficial handling of complex or nuanced topics.\n"
        "Avoid Textual Predictability (High predictability measured by language models, Repetitive patterns that indicate probabilistic generation)\n"
        "Avoid Semantic and Stylistic Patterns that have a Uniform emotional tone or unnatural neutrality, or that Lack personal anecdotes or human experience indicators.\n"
        "Avoid  Excessively polished grammar with no natural variation, and the use of grammatical structures or rare linguistic anomalies.\n"
        "Avoid Overly symmetrical or formulaic paragraph and sentence structures as well as Systematic list creation or headings consistent with templated outputs.\n"
        "Do not use Hidden textual indicators, metadata, or digital signatures.\n"
        "Do not use specific linguistic markers typical of known AI language models. \n"
        "Vary sentence length; use contractions for conversational realism.  \n"
        "Insert verbal sign\u2011posts (\u201cLet me share\u2026\u201d, \u201cHere\u2019s the challenge\u2026\u201d, \u201cSo what\u2019s next?\u201d).  \n"
        "Use rhetorical devices sparingly for punch: contrast, triplets, rhetorical questions, callbacks.  \n"
        "Repeat the core mantra at least twice for memorability.  \n"
        "Banish these buzz\u2011phrases: *ever\u2011evolving, game\u2011changer, moving forward, leverage synergies, at the end of the day.*  \n"
        "Use inclusive pronouns (\u201cwe\u201d, \u201cour\u201d) and at least one idiom or reference your audience uses daily.  \n"
        "Explain any necessary technical term in one plain\u2011English clause.  \n"
        "Build an emotional arc\u2014rising intensity toward an uplifting crescendo in the finale.  \n"
        "Finish with the quotable closing line ( \u2264\u201012 words ).\n"
        "\n"
        "OUTPUT INSTRUCTIONS:\n"
        "Return **only** the speech text in the speaker\u2019s voice.  \n"
        "Use short paragraphs and intentional blank lines for breathable pauses.  \n"
        "No meta\u2011commentary, no AI disclaimers.\n"
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
