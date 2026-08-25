from __future__ import annotations

import pytest

from modules.llm.progress import (
    LLMRequestProgressEvent,
    notify_llm_progress,
)


def test_progress_event_reports_planned_and_completed_request_deltas():
    events = []

    notify_llm_progress(
        events.append,
        event_type="planned",
        stage="evidence_detection",
        request_count=4,
    )
    notify_llm_progress(
        events.append,
        event_type="completed",
        stage="evidence_detection",
        detail="SAU-000001",
    )

    assert events == [
        LLMRequestProgressEvent(
            event_type="planned",
            stage="evidence_detection",
            request_count=4,
        ),
        LLMRequestProgressEvent(
            event_type="completed",
            stage="evidence_detection",
            detail="SAU-000001",
        ),
    ]


def test_progress_event_rejects_non_positive_request_count():
    with pytest.raises(ValueError):
        LLMRequestProgressEvent(
            event_type="planned",
            stage="subject_interpretation",
            request_count=0,
        )
