import os
import openai
from typing import List, Dict, Tuple

class ChatBot:
    """Lightweight wrapper around the OpenAI chat API for quick conversations."""

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.5):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature

    def reply(
        self,
        user_message: str,
        history: List[Dict[str, str]] | None = None,
        temperature: float | None = None,
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Generate a single response and return updated history."""
        messages = history[:] if history else []
        messages.append({"role": "user", "content": user_message})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=2000,
        )
        assistant_message = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": assistant_message})
        return assistant_message, messages
