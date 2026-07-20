"""OpenAI provider implementation for the Turing Generator.

This module is the only place where the OpenAI SDK is used directly.

It supports two modes:
1. api_key provided explicitly, for future UI-based key input
2. OPENAI_API_KEY environment variable, for terminal-based local testing
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from modules.llm.types import LLMRequest, LLMResult


class OpenAILLMClient:
    """OpenAI implementation of the provider-neutral LLM client."""

    provider_name = "openai"

    def generate(self, request: LLMRequest) -> LLMResult:
        """Execute one OpenAI Responses API call."""

        api_key = clean_api_key(request.api_key)

        if api_key:
            client = OpenAI(api_key=api_key)
        else:
            if not os.environ.get("OPENAI_API_KEY"):
                raise RuntimeError(
                    "No OpenAI API key available. "
                    "Set OPENAI_API_KEY or provide api_key via LLMRequest."
                )
            client = OpenAI()

        kwargs: dict[str, Any] = {
            "model": request.model,
            "instructions": request.instructions,
            "input": request.input_text,
        }

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        response = client.responses.create(**kwargs)

        return LLMResult(
            text=get_response_text(response),
            provider=self.provider_name,
            model=request.model,
            response_id=getattr(response, "id", None),
            usage=get_usage_dict(response),
            raw_status=getattr(response, "status", None),
        )


def clean_api_key(api_key: str | None) -> str | None:
    """Normalize API key input from UI or config."""

    if api_key is None:
        return None

    cleaned = api_key.strip()

    if not cleaned:
        return None

    return cleaned


def get_response_text(response: Any) -> str:
    """Extract text from an OpenAI response object."""

    output_text = getattr(response, "output_text", None)

    if output_text:
        return str(output_text)

    return ""


def get_usage_dict(response: Any) -> dict[str, Any]:
    """Return usage information if available."""

    usage = getattr(response, "usage", None)

    if usage is None:
        return {}

    if hasattr(usage, "model_dump"):
        return usage.model_dump()

    if isinstance(usage, dict):
        return usage

    return {"usage": str(usage)}
