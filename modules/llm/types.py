"""Shared LLM request and response types for the Turing Generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMRequest:
    """Provider-neutral request object for one LLM call."""

    instructions: str
    input_text: str
    model: str
    provider: str = "openai"
    api_key: str | None = None
    temperature: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResult:
    """Provider-neutral result object for one LLM call."""

    text: str
    provider: str
    model: str
    response_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw_status: str | None = None
