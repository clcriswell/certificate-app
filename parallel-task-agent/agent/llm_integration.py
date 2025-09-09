import os
from typing import List
import openai

MODEL = "gpt-4o-mini"


def decompose_task(description: str) -> List[str]:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    prompt = (
        "Break down the following coding task into a sequence of shell commands"\
        " that can be executed to implement the task. One command per line.\n" + description
    )
    client = openai.OpenAI()
    res = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    commands = res.choices[0].message.content.splitlines()
    return [c.strip() for c in commands if c.strip()]
