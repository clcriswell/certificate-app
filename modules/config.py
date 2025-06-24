from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence, Dict, Any
from pydantic import BaseModel, Field, validator

@dataclass
class LoopConfig:
    max_loops: int = 9
    confidence_threshold: float = 0.85
    whitelist_domains: Sequence[str] | None = None  # e.g., (".gov", ".edu")
    blacklist_domains: Sequence[str] | None = None
    enable_hallucination_guard: bool = True
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.5
    request_timeout: float = 30.0  # seconds

class SourceDoc(BaseModel):
    source: str
    title: str
    url: str
    content: str

    @validator("content")
    def truncate_content(cls, v: str):
        # Truncate content to avoid excessive length (token limits)
        return v[:15000]

class SocialDoc(BaseModel):
    platform: str
    author: str
    created_at: str
    content: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
