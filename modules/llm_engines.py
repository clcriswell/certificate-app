import os
import openai
from typing import List, Dict

class OpenAIEngine:
    """Async OpenAI LLM wrapper for chat completion."""
    def __init__(self, model: str, temperature: float, timeout: float):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        openai.api_key = os.getenv("OPENAI_API_KEY")

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            timeout=self.timeout
        )
        return response.choices[0].message.content.strip()
