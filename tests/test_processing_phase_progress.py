from modules.llm.progress import (
    LLMRequestProgressEvent,
    notify_processing_phase,
)


def test_processing_phase_progress_event_is_non_counting():
    received = []

    notify_processing_phase(
        received.append,
        stage="compilation",
        detail="validating and assembling artifacts",
    )

    assert len(received) == 1
    event = received[0]
    assert event.event_type == "phase"
    assert event.stage == "compilation"
    assert event.request_count == 0


def test_phase_event_requires_zero_request_count():
    event = LLMRequestProgressEvent(
        event_type="phase",
        stage="compilation",
        request_count=0,
    )
    assert event.request_count == 0
