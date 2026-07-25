"""Canonical project-local paths for Processing Run persistence."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import ProcessingValidationError
from .identifiers import (
    validate_processing_attempt_id,
    validate_processing_decision_id,
    validate_processing_event_id,
    validate_processing_run_id,
)
from .types import PROCESSING_STAGES


RUNS_DIRECTORY_NAME = "runs"
EVENTS_DIRECTORY_NAME = "events"
ARTIFACTS_DIRECTORY_NAME = "artifacts"
AGENT_OUTPUTS_DIRECTORY_NAME = "agent_outputs"
CONSENSUS_REPORTS_DIRECTORY_NAME = "consensus_reports"
WORK_DIRECTORY_NAME = "work"
PROCESSING_DECISIONS_DIRECTORY_NAME = "processing_decisions"

PROCESSING_ARTIFACT_KINDS = frozenset(
    {
        AGENT_OUTPUTS_DIRECTORY_NAME,
        CONSENSUS_REPORTS_DIRECTORY_NAME,
    }
)


def project_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the canonical path of one validated project."""

    if not is_valid_project_id(project_id):
        raise ProcessingValidationError(
            "project_id must be a string containing exactly six digits."
        )

    return Path(root) / project_id


def runs_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the Processing Run root for one project."""

    return project_path(root, project_id) / RUNS_DIRECTORY_NAME


def run_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
) -> Path:
    """Return the canonical directory of one Processing Run."""

    validated_run_id = validate_processing_run_id(
        processing_run_id
    )

    return runs_path(root, project_id) / validated_run_id


def run_manifest_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
) -> Path:
    """Return the canonical Run Manifest path."""

    from .run_manifest import PROCESSING_RUN_MANIFEST_FILENAME

    return (
        run_path(root, project_id, processing_run_id)
        / PROCESSING_RUN_MANIFEST_FILENAME
    )


def events_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
) -> Path:
    """Return the Event History directory of one run."""

    return (
        run_path(root, project_id, processing_run_id)
        / EVENTS_DIRECTORY_NAME
    )


def event_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
    event_id: object,
) -> Path:
    """Return the canonical path of one immutable event."""

    validated_event_id = validate_processing_event_id(event_id)

    return (
        events_path(root, project_id, processing_run_id)
        / f"{validated_event_id}.json"
    )


def artifacts_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
) -> Path:
    """Return the run-owned artifact root."""

    return (
        run_path(root, project_id, processing_run_id)
        / ARTIFACTS_DIRECTORY_NAME
    )


def attempt_artifact_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
    *,
    artifact_kind: object,
    processing_stage: object,
    attempt_id: object,
) -> Path:
    """Return one stage- and attempt-specific artifact directory."""

    if artifact_kind not in PROCESSING_ARTIFACT_KINDS:
        raise ProcessingValidationError(
            "artifact_kind must be agent_outputs or "
            "consensus_reports."
        )

    if processing_stage not in PROCESSING_STAGES:
        raise ProcessingValidationError(
            "processing_stage is not supported."
        )

    validated_attempt_id = validate_processing_attempt_id(
        attempt_id
    )

    return (
        artifacts_path(root, project_id, processing_run_id)
        / artifact_kind
        / processing_stage
        / validated_attempt_id
    )


def work_path(
    root: Path | str,
    project_id: object,
    processing_run_id: object,
) -> Path:
    """Return the non-authoritative temporary work directory."""

    return (
        run_path(root, project_id, processing_run_id)
        / WORK_DIRECTORY_NAME
    )


def processing_decisions_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the Processing Decision root for one project."""

    return (
        project_path(root, project_id)
        / PROCESSING_DECISIONS_DIRECTORY_NAME
    )


def processing_decision_path(
    root: Path | str,
    project_id: object,
    processing_decision_id: object,
) -> Path:
    """Return the canonical path of one Processing Decision."""

    validated_decision_id = validate_processing_decision_id(
        processing_decision_id
    )

    return (
        processing_decisions_path(root, project_id)
        / f"{validated_decision_id}.json"
    )