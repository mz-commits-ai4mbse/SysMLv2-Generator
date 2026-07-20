"""Provider-neutral LLM client interface."""

from __future__ import annotations

from typing import Protocol

from modules.llm.types import LLMRequest, LLMResult


class LLMClient(Protocol):
    """Protocol implemented by all LLM provider clients."""

    provider_name: str

    def generate(self, request: LLMRequest) -> LLMResult:
        """Execute one LLM request and return a provider-neutral result."""
        ...
