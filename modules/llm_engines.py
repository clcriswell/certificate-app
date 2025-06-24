import os
import openai
from typing import List, Dict

class OpenAIEngine:
    """Async OpenAI LLM wrapper for chat completion."""
    def __init__(self, model: str, temperature: float, timeout: float):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            timeout=self.timeout,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()
