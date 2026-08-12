"""G7.3 retry and failure-classification integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.project_ingestion import (
    ProjectIngestionConfiguration,
    ProjectIngestionConfigurationError,
    calculate_ingestion_configuration_fingerprint,
)
from modules.project_ingestion.failure_classification import (
    classify_pipeline_failure,
)
from modules.project_processing import ProjectProcessingRepository

from tests.test_project_ingestion_publication import (
    CompletePipeline,
    prepare_service,
)


class AuthenticationFailure(RuntimeError):
    status_code = 401


class FailThenCompletePipeline(CompletePipeline):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next = True

    def __call__(self, **kwargs):
        if self.fail_next:
            self.calls.append(dict(kwargs))
            self.fail_next = False
            raise AuthenticationFailure("private provider message")
        return super().__call__(**kwargs)


def test_failure_classifier_is_secret_free_and_stable() -> None:
    assert (
        classify_pipeline_failure(AuthenticationFailure("secret"))
        == "llm_authentication_failed"
    )

    class APIConnectionError(RuntimeError):
        pass

    assert (
        classify_pipeline_failure(APIConnectionError("private"))
        == "llm_connection_failed"
    )
    assert (
        classify_pipeline_failure(RuntimeError("private"))
        == "team_agentic_ingestion_failed"
    )


def test_failed_attempt_retries_same_run_with_new_attempt(
    tmp_path: Path,
) -> None:
    pipeline = FailThenCompletePipeline()
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
    )
    configuration = ProjectIngestionConfiguration(
        dry_run=False,
    )

    failed = service.execute_registered_source(
        "123456",
        source.source_id,
        configuration=configuration,
        api_key="wrong-key-not-persisted",
    )
    assert failed.processing_run_id == "RUN-000001"
    assert failed.attempt_id == "ATT-000001"
    assert failed.run_state == "failed"
    assert failed.failure_reason == "llm_authentication_failed"

    state = service.source_execution_state(
        "123456",
        source.source_id,
    )
    assert state.can_retry is True
    assert state.configuration_fingerprint == (
        calculate_ingestion_configuration_fingerprint(
            configuration
        )
    )

    retried = service.retry_registered_source(
        "123456",
        source.source_id,
        "RUN-000001",
        configuration=configuration,
        api_key="correct-key-not-persisted",
    )
    assert retried.processing_run_id == "RUN-000001"
    assert retried.attempt_id == "ATT-000002"
    assert retried.run_state == "awaiting_review"

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run("123456", "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "run_failed",
        "retry_started",
        "artifact_published",
        "review_requested",
    )
    assert history.events[3].attempt_id == "ATT-000002"

    assert "wrong-key-not-persisted" not in repr(history)
    assert "correct-key-not-persisted" not in repr(history)


def test_retry_rejects_changed_material_configuration(
    tmp_path: Path,
) -> None:
    pipeline = FailThenCompletePipeline()
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
    )
    original = ProjectIngestionConfiguration(dry_run=False)

    failed = service.execute_registered_source(
        "123456",
        source.source_id,
        configuration=original,
    )
    assert failed.run_state == "failed"

    with pytest.raises(
        ProjectIngestionConfigurationError,
        match="material configuration",
    ):
        service.retry_registered_source(
            "123456",
            source.source_id,
            "RUN-000001",
            configuration=ProjectIngestionConfiguration(
                dry_run=False,
                model="gpt-5-mini",
            ),
        )

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run("123456", "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "run_failed",
    )


def test_source_without_run_is_startable(
    tmp_path: Path,
) -> None:
    service, _, _, source = prepare_service(
        tmp_path,
        CompletePipeline(),
    )
    state = service.source_execution_state(
        "123456",
        source.source_id,
    )
    assert state.processing_run_id is None
    assert state.can_start_new is True
    assert state.can_retry is False
