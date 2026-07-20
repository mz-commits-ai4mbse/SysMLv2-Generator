"""Factory for LLM provider clients."""

from __future__ import annotations

from modules.llm.base import LLMClient
from modules.llm.openai_client import OpenAILLMClient


def create_llm_client(provider: str) -> LLMClient:
    """Create a provider-specific LLM client.

    Currently supported:
    - openai

    Later:
    - anthropic
    - azure_openai
    - local
    """

    normalized = provider.strip().lower()

    if normalized == "openai":
        return OpenAILLMClient()

    raise ValueError(f"Unsupported LLM provider: {provider}")
