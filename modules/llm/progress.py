"""Ephemeral progress events for observable LLM request execution.

These events are UI/runtime feedback only. They are not Engineering Authority,
Processing evidence, or persisted model state.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


LLM_PROGRESS_EVENT_VALUES = frozenset({"planned", "completed"})


@dataclass(frozen=True, slots=True)
class LLMRequestProgressEvent:
    """One additive update to the currently executing LLM request plan."""

    event_type: str
    stage: str
    request_count: int = 1
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.event_type not in LLM_PROGRESS_EVENT_VALUES:
            raise ValueError("Unsupported LLM progress event type.")
        if not isinstance(self.stage, str) or not self.stage.strip():
            raise ValueError("LLM progress stage must be non-empty.")
        if (
            isinstance(self.request_count, bool)
            or not isinstance(self.request_count, int)
            or self.request_count < 1
        ):
            raise ValueError(
                "LLM progress request_count must be a positive integer."
            )
        if self.detail is not None and (
            not isinstance(self.detail, str)
            or not self.detail.strip()
        ):
            raise ValueError(
                "LLM progress detail must be null or non-empty text."
            )


LLMRequestProgressObserver = Callable[[LLMRequestProgressEvent], None]


def notify_llm_progress(
    observer: LLMRequestProgressObserver | None,
    *,
    event_type: str,
    stage: str,
    request_count: int = 1,
    detail: str | None = None,
) -> None:
    """Notify one optional observer without changing processing semantics."""

    if observer is None:
        return
    observer(
        LLMRequestProgressEvent(
            event_type=event_type,
            stage=stage,
            request_count=request_count,
            detail=detail,
        )
    )
