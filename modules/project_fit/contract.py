"""Deterministic contract for project-level source-fit assessment."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
import re
from typing import Any

from modules.project_processing.identifiers import (
    validate_processing_attempt_id,
    validate_processing_run_id,
)
from modules.project_processing.run_manifest import validate_processing_run_manifest
from modules.project_processing.types import ProcessingRunManifest
from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
)
from modules.project_workspace.manifest import (
    project_manifest_to_dict,
    validate_project_manifest,
)
from modules.project_workspace.types import ProjectManifest
from modules.source_projection.manifest import validate_source_projection_artifact
from modules.source_projection.types import SourceProjectionArtifact

from .errors import ProjectFitIntegrityError, ProjectFitValidationError
from .prompt import PROJECT_FIT_PROMPT_SCHEMA_VERSION
from .types import (
    PROJECT_FIT_GATE_STATES,
    PROJECT_FIT_OUTCOMES,
    ProjectFitAssessment,
    ProjectFitContextReference,
)


PROJECT_FIT_ASSESSMENT_SCHEMA_VERSION = "1.0.0"

_JSON_FENCE = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.S | re.I,
)

_RESPONSE_FIELDS = frozenset(
    {
        "outcome",
        "rationale",
        "matched_concepts",
        "incompatible_concepts",
        "supporting_context_refs",
    }
)


def prepare_project_fit_context(
    project: ProjectManifest,
    run_manifest: ProcessingRunManifest,
    candidate: SourceProjectionArtifact,
    available_projections: object,
    *,
    attempt_id: str,
) -> tuple[
    tuple[ProjectFitContextReference, ...],
    dict[str, str],
    str,
]:
    """Validate inputs and build deterministic independent Project context."""

    _validate_primary_binding(
        project,
        run_manifest,
        candidate,
        attempt_id=attempt_id,
    )
    if not isinstance(available_projections, tuple):
        raise ProjectFitValidationError(
            "available_projections must be a tuple."
        )

    project_reference = ProjectFitContextReference(
        reference_kind="project_manifest",
        reference_id=f"project_manifest:{project.project_id}",
        source_id=None,
        source_role=None,
        content_fingerprint=_sha(project_manifest_to_dict(project)),
    )

    newest_by_source: dict[str, SourceProjectionArtifact] = {}
    for artifact in available_projections:
        _validate_projection(artifact)
        manifest = artifact.manifest

        if manifest.project_id != project.project_id:
            raise ProjectFitIntegrityError(
                "Project Fit context cannot cross a Project boundary."
            )

        # A source must not prove its own Project fit.
        if manifest.source_id == candidate.manifest.source_id:
            continue

        current = newest_by_source.get(manifest.source_id)
        if (
            current is None
            or manifest.source_projection_id
            > current.manifest.source_projection_id
        ):
            newest_by_source[manifest.source_id] = artifact

    selected = tuple(
        sorted(
            newest_by_source.values(),
            key=lambda artifact: (
                0
                if artifact.manifest.source_role == CONTEXT_ONLY_SOURCE_ROLE
                else 1,
                artifact.manifest.source_id,
                artifact.manifest.source_projection_id,
            ),
        )
    )

    context_references = [project_reference]
    content_by_ref: dict[str, str] = {}
    for artifact in selected:
        manifest = artifact.manifest
        if manifest.projection_result == "unavailable":
            continue
        reference_id = f"source_projection:{manifest.source_projection_id}"
        context_references.append(
            ProjectFitContextReference(
                reference_kind="source_projection",
                reference_id=reference_id,
                source_id=manifest.source_id,
                source_role=manifest.source_role,
                content_fingerprint=_projection_context_fingerprint(artifact),
            )
        )
        content_by_ref[reference_id] = artifact.content

    input_binding = {
        "prompt_schema_version": PROJECT_FIT_PROMPT_SCHEMA_VERSION,
        "project_context": [
            asdict(reference)
            for reference in context_references
        ],
        "candidate": {
            "project_id": candidate.manifest.project_id,
            "source_id": candidate.manifest.source_id,
            "source_role": candidate.manifest.source_role,
            "source_sha256": candidate.manifest.source_sha256,
            "source_projection_id": candidate.manifest.source_projection_id,
            "projection_fingerprint": candidate.manifest.projection_fingerprint,
            "content_sha256": candidate.manifest.content_sha256,
            "processing_run_id": run_manifest.processing_run_id,
            "attempt_id": attempt_id,
        },
    }

    return (
        tuple(context_references),
        content_by_ref,
        _sha(input_binding),
    )


def parse_project_fit_response(
    text: str,
    *,
    allowed_context_refs: tuple[str, ...],
) -> dict[str, Any]:
    """Parse one strict model response without granting authority."""

    payload = _require_object(text)
    if frozenset(payload) != _RESPONSE_FIELDS:
        raise ProjectFitValidationError(
            "Project Fit output fields do not match the exact schema."
        )

    outcome = payload["outcome"]
    if outcome not in PROJECT_FIT_OUTCOMES:
        raise ProjectFitValidationError(
            "Project Fit outcome is not supported."
        )

    rationale = _required_text(payload["rationale"], "rationale")
    matched = _string_tuple(
        payload["matched_concepts"],
        "matched_concepts",
    )
    incompatible = _string_tuple(
        payload["incompatible_concepts"],
        "incompatible_concepts",
    )
    supporting = _string_tuple(
        payload["supporting_context_refs"],
        "supporting_context_refs",
    )

    if set(matched) & set(incompatible):
        raise ProjectFitValidationError(
            "One concept cannot be both matched and incompatible."
        )

    allowed = set(allowed_context_refs)
    if any(reference not in allowed for reference in supporting):
        raise ProjectFitValidationError(
            "Project Fit output references context that was not supplied."
        )

    if outcome == "plausible_in_scope":
        if not matched or not supporting:
            raise ProjectFitValidationError(
                "plausible_in_scope requires positive matched evidence."
            )
    elif outcome == "likely_out_of_scope":
        if not incompatible or not supporting:
            raise ProjectFitValidationError(
                "likely_out_of_scope requires positive incompatibility evidence."
            )

    return {
        "outcome": outcome,
        "rationale": rationale,
        "matched_concepts": matched,
        "incompatible_concepts": incompatible,
        "supporting_context_refs": supporting,
    }


def create_project_fit_assessment(
    *,
    project: ProjectManifest,
    run_manifest: ProcessingRunManifest,
    candidate: SourceProjectionArtifact,
    attempt_id: str,
    context_references: tuple[ProjectFitContextReference, ...],
    input_fingerprint: str,
    parsed_response: dict[str, Any],
    llm_provider: str,
    llm_model: str,
    llm_response_id: str | None,
) -> ProjectFitAssessment:
    """Create and fingerprint one immutable Project Fit assessment."""

    _validate_primary_binding(
        project,
        run_manifest,
        candidate,
        attempt_id=attempt_id,
    )
    _validate_sha256(input_fingerprint, "input_fingerprint")
    _required_text(llm_provider, "llm_provider")
    _required_text(llm_model, "llm_model")
    if llm_response_id is not None:
        _required_text(llm_response_id, "llm_response_id")

    allowed_refs = tuple(
        reference.reference_id
        for reference in context_references
    )
    parsed = parse_project_fit_response(
        json.dumps(parsed_response, ensure_ascii=False),
        allowed_context_refs=allowed_refs,
    )

    body = {
        "schema_version": PROJECT_FIT_ASSESSMENT_SCHEMA_VERSION,
        "project_id": project.project_id,
        "source_id": candidate.manifest.source_id,
        "source_role": candidate.manifest.source_role,
        "source_sha256": candidate.manifest.source_sha256,
        "source_projection_id": candidate.manifest.source_projection_id,
        "candidate_projection_fingerprint": (
            candidate.manifest.projection_fingerprint
        ),
        "candidate_content_sha256": candidate.manifest.content_sha256,
        "processing_run_id": run_manifest.processing_run_id,
        "attempt_id": attempt_id,
        **parsed,
        "context_references": tuple(context_references),
        "prompt_schema_version": PROJECT_FIT_PROMPT_SCHEMA_VERSION,
        "llm_provider": llm_provider.strip(),
        "llm_model": llm_model.strip(),
        "llm_response_id": (
            None
            if llm_response_id is None
            else llm_response_id.strip()
        ),
        "input_fingerprint": input_fingerprint,
    }

    fingerprint_body = {
        **body,
        "context_references": [
            asdict(reference)
            for reference in body["context_references"]
        ],
        "matched_concepts": list(body["matched_concepts"]),
        "incompatible_concepts": list(body["incompatible_concepts"]),
        "supporting_context_refs": list(
            body["supporting_context_refs"]
        ),
    }
    assessment = ProjectFitAssessment(
        **body,
        assessment_fingerprint=_sha(fingerprint_body),
    )
    validate_project_fit_assessment(assessment)
    return assessment


def validate_project_fit_assessment(
    assessment: ProjectFitAssessment,
) -> None:
    """Validate the complete assessment and its canonical fingerprint."""

    if not isinstance(assessment, ProjectFitAssessment):
        raise ProjectFitValidationError(
            "assessment must be a ProjectFitAssessment."
        )
    if assessment.schema_version != PROJECT_FIT_ASSESSMENT_SCHEMA_VERSION:
        raise ProjectFitValidationError(
            "Unsupported Project Fit assessment schema_version."
        )

    validate_processing_run_id(assessment.processing_run_id)
    validate_processing_attempt_id(assessment.attempt_id)
    if assessment.outcome not in PROJECT_FIT_OUTCOMES:
        raise ProjectFitValidationError(
            "Unsupported Project Fit assessment outcome."
        )

    for label, value in (
        ("project_id", assessment.project_id),
        ("source_id", assessment.source_id),
        ("source_role", assessment.source_role),
        ("source_projection_id", assessment.source_projection_id),
        ("rationale", assessment.rationale),
        ("prompt_schema_version", assessment.prompt_schema_version),
        ("llm_provider", assessment.llm_provider),
        ("llm_model", assessment.llm_model),
    ):
        _required_text(value, label)

    for label, value in (
        ("source_sha256", assessment.source_sha256),
        (
            "candidate_projection_fingerprint",
            assessment.candidate_projection_fingerprint,
        ),
        (
            "candidate_content_sha256",
            assessment.candidate_content_sha256,
        ),
        ("input_fingerprint", assessment.input_fingerprint),
        ("assessment_fingerprint", assessment.assessment_fingerprint),
    ):
        _validate_sha256(value, label)

    reference_ids = []
    for reference in assessment.context_references:
        if not isinstance(reference, ProjectFitContextReference):
            raise ProjectFitValidationError(
                "context_references entries must be "
                "ProjectFitContextReference values."
            )
        _required_text(reference.reference_kind, "reference_kind")
        _required_text(reference.reference_id, "reference_id")
        _validate_sha256(
            reference.content_fingerprint,
            "content_fingerprint",
        )
        reference_ids.append(reference.reference_id)

    if len(reference_ids) != len(set(reference_ids)):
        raise ProjectFitValidationError(
            "Project Fit context references must be unique."
        )
    if any(
        reference not in set(reference_ids)
        for reference in assessment.supporting_context_refs
    ):
        raise ProjectFitIntegrityError(
            "Assessment supporting context is not bound to input context."
        )

    if (
        assessment.outcome == "plausible_in_scope"
        and (
            not assessment.matched_concepts
            or not assessment.supporting_context_refs
        )
    ):
        raise ProjectFitValidationError(
            "plausible_in_scope requires positive matched evidence."
        )
    if (
        assessment.outcome == "likely_out_of_scope"
        and (
            not assessment.incompatible_concepts
            or not assessment.supporting_context_refs
        )
    ):
        raise ProjectFitValidationError(
            "likely_out_of_scope requires positive incompatibility evidence."
        )

    body = {
        key: value
        for key, value in asdict(assessment).items()
        if key != "assessment_fingerprint"
    }
    expected = _sha(body)
    if assessment.assessment_fingerprint != expected:
        raise ProjectFitIntegrityError(
            "Project Fit assessment_fingerprint does not match content."
        )


def derive_project_fit_gate_state(
    assessment: ProjectFitAssessment,
) -> str:
    """Derive the non-authoritative gate state from one assessment."""

    validate_project_fit_assessment(assessment)
    if assessment.outcome != "plausible_in_scope":
        state = "human_resolution_required"
    elif assessment.source_role == CONTEXT_ONLY_SOURCE_ROLE:
        state = "context_only"
    elif assessment.source_role == ENGINEERING_SOURCE_ROLE:
        state = "admitted"
    else:
        raise ProjectFitValidationError(
            "Project Fit assessment contains an unsupported source role."
        )

    if state not in PROJECT_FIT_GATE_STATES:
        raise ProjectFitIntegrityError(
            "Derived Project Fit gate state is unsupported."
        )
    return state


def project_fit_assessment_to_dict(
    assessment: ProjectFitAssessment,
) -> dict[str, Any]:
    """Return a validated JSON-compatible assessment payload."""

    validate_project_fit_assessment(assessment)
    return asdict(assessment)


def project_fit_assessment_to_json(
    assessment: ProjectFitAssessment,
) -> str:
    """Serialize a Project Fit assessment deterministically."""

    return json.dumps(
        project_fit_assessment_to_dict(assessment),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _validate_primary_binding(
    project: ProjectManifest,
    run_manifest: ProcessingRunManifest,
    candidate: SourceProjectionArtifact,
    *,
    attempt_id: str,
) -> None:
    try:
        validate_project_manifest(project)
        validate_processing_run_manifest(run_manifest)
        validate_source_projection_artifact(candidate)
        validate_processing_attempt_id(attempt_id)
    except Exception as exc:
        raise ProjectFitValidationError(
            "Project Fit primary inputs must satisfy their source contracts."
        ) from exc

    manifest = candidate.manifest
    if manifest.projection_result == "unavailable":
        raise ProjectFitValidationError(
            "An unavailable Source Projection cannot be assessed for Project fit."
        )

    bindings = (
        (run_manifest.project_id, project.project_id, "project_id"),
        (manifest.project_id, project.project_id, "projection project_id"),
        (manifest.source_id, run_manifest.source_id, "source_id"),
        (
            manifest.source_sha256,
            run_manifest.source_sha256,
            "source_sha256",
        ),
        (
            manifest.source_role,
            run_manifest.source_role_snapshot,
            "source_role",
        ),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise ProjectFitIntegrityError(
                "Project Fit primary provenance does not match: "
                f"{label}."
            )


def _validate_projection(artifact: object) -> None:
    try:
        validate_source_projection_artifact(artifact)
    except Exception as exc:
        raise ProjectFitValidationError(
            "Project Fit context contains an invalid Source Projection."
        ) from exc


def _projection_context_fingerprint(
    artifact: SourceProjectionArtifact,
) -> str:
    manifest = artifact.manifest
    return _sha(
        {
            "project_id": manifest.project_id,
            "source_id": manifest.source_id,
            "source_role": manifest.source_role,
            "source_sha256": manifest.source_sha256,
            "source_projection_id": manifest.source_projection_id,
            "projection_fingerprint": manifest.projection_fingerprint,
            "content_sha256": manifest.content_sha256,
        }
    )


def _require_object(text: str) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ProjectFitValidationError(
            "Project Fit output must be non-empty JSON object text."
        )
    match = _JSON_FENCE.fullmatch(text)
    normalized = match.group(1) if match else text.strip()
    try:
        value = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ProjectFitValidationError(
            "Project Fit output must be valid JSON."
        ) from exc
    if not isinstance(value, dict):
        raise ProjectFitValidationError(
            "Project Fit output must be a JSON object."
        )
    return value


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectFitValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise ProjectFitValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ProjectFitValidationError(
            f"{label} must be a JSON array."
        )
    normalized = []
    for item in value:
        normalized.append(_required_text(item, label))
    if len(normalized) != len(set(normalized)):
        raise ProjectFitValidationError(
            f"{label} must not contain duplicates."
        )
    return tuple(sorted(normalized))


def _validate_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ProjectFitValidationError(
            f"{label} must be a lowercase SHA-256 string."
        )
    return value


def _sha(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
