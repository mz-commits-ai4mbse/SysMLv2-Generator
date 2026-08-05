"""Tests for structured P9 Agent proposal adaptation."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from modules.project_processing import (
    create_processing_artifact_reference,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.evidence_adapter import (
    P9ReviewEvidenceSet,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from modules.review_workspace.p9_proposal_adapter import (
    adapt_p9_agent_proposals,
)


PROJECT_ID = "123456"
RUN_ID = "RUN-000001"
ATTEMPT_ID = "ATT-000001"
SOURCE_ID = "SRC-000001"


def _candidate(
    candidate_id: str,
    element_type: str,
    candidate_name: str,
    *,
    description: str | None = None,
):
    selected_description = (
        f"Description of {candidate_name}."
        if description is None
        else description
    )

    return {
        "candidate_id": candidate_id,
        "element_type": element_type,
        "candidate_name": candidate_name,
        "description": selected_description,
        "source_basis": ["SRC_INFO_001"],
        "assigned_source_information": [
            {
                "source_info_id": "SRC_INFO_001",
                "source_statement": (
                    f"The source identifies "
                    f"{candidate_name}."
                ),
                "assignment_type": "defines_element",
                "confidence": "high",
            }
        ],
        "confidence": "high",
        "generation_readiness": "ready",
        "missing_information": [],
        "rationale_summary": (
            "The candidate is directly source-supported."
        ),
    }


def _link(
    *,
    link_id: str = "LINK_001",
    source: str = "ELEM_001",
    target: str = "ELEM_002",
):
    return {
        "link_id": link_id,
        "source_element_candidate": source,
        "link_type": "controls",
        "target_element_candidate": target,
        "source_basis": ["SRC_INFO_002"],
        "source_statement": (
            "The operator controls the microscope."
        ),
        "confidence": "high",
        "rationale_summary": (
            "The relationship is explicitly stated."
        ),
    }


def _derivation_output(
    *,
    candidates=None,
    links=None,
):
    return {
        "candidate_model_elements": (
            [
                _candidate(
                    "ELEM_001",
                    "actor",
                    "Microscope Operator",
                ),
                _candidate(
                    "ELEM_002",
                    "system",
                    "Microscope",
                ),
            ]
            if candidates is None
            else candidates
        ),
        "explicit_source_links": (
            [_link()]
            if links is None
            else links
        ),
        "sysml_model_buildability": [],
        "missing_information_for_model_building": [],
        "possible_but_unsupported_interpretations": [],
        "model_artifact_assessments": [],
        "cross_artifact_observations": [],
        "blocked_generation_tasks": [],
    }


def _write_agent_output(
    repository_root: Path,
    *,
    artifact_index: int,
    output,
    stage_directory: str = (
        "03_derivation_assessment"
    ),
    agent_id: str = "AGENT_DERIVATION_A",
    persona_id: str = "PERSONA_DERIVATION_A",
    run_index: int = 1,
    status: str = "completed",
    attempt_id: str = ATTEMPT_ID,
):
    relative_path = (
        Path("data")
        / "projects"
        / PROJECT_ID
        / "runs"
        / RUN_ID
        / "artifacts"
        / "agent_outputs"
        / "agentic_ingestion"
        / attempt_id
        / stage_directory
        / "team_derivation_assessment"
        / agent_id.lower()
        / f"agent_{artifact_index:02d}.json"
    )
    target = repository_root / relative_path
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_text = (
        output
        if isinstance(output, str)
        else json.dumps(
            output,
            ensure_ascii=False,
        )
    )

    wrapper = {
        "team_id": "TEAM_DERIVATION_ASSESSMENT",
        "agent_id": agent_id,
        "persona_id": persona_id,
        "run_index": run_index,
        "status": status,
        "output_text": output_text,
    }

    content = json.dumps(
        wrapper,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")

    target.write_bytes(content)

    return create_processing_artifact_reference(
        artifact_type="agent_outputs",
        artifact_id=(
            f"AGOUT-{ATTEMPT_ID}-"
            f"{artifact_index:04d}"
        ),
        content_fingerprint=hashlib.sha256(
            content
        ).hexdigest(),
        repository_relative_path=(
            relative_path.as_posix()
        ),
    )


def _p9_evidence(
    agent_references,
):
    review_reference = (
        create_processing_artifact_reference(
            artifact_type="review_reports",
            artifact_id="REVIEW-ATT-000001-0001",
            content_fingerprint="a" * 64,
            repository_relative_path=(
                "data/projects/123456/runs/RUN-000001/"
                "artifacts/review_reports/"
                "agentic_ingestion/ATT-000001/"
                "ingestion_review_report.md"
            ),
        )
    )

    return P9ReviewEvidenceSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_sha256="b" * 64,
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(),
        primary_review_artifact_reference=(
            review_reference
        ),
        agent_output_references=tuple(
            agent_references
        ),
        consensus_report_references=(),
        run_summary_references=(),
    )


def test_adapts_elements_and_relationships(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=_derivation_output(),
    )

    selected = adapt_p9_agent_proposals(
        _p9_evidence((reference,)),
        repository_root=repository_root,
    )

    assert selected.project_id == PROJECT_ID
    assert selected.processing_run_id == RUN_ID
    assert selected.attempt_id == ATTEMPT_ID
    assert selected.proposal_count == 3

    assert len(selected.element_proposals) == 2
    assert len(
        selected.relationship_proposals
    ) == 1

    operator = next(
        item
        for item in selected.element_proposals
        if item.candidate_name
        == "Microscope Operator"
    )

    assert operator.element_type == "actor"
    assert operator.source_basis == (
        "SRC_INFO_001",
    )
    assert operator.proposal_reference.review_state == (
        "available"
    )
    assert (
        operator.proposal_reference
        .artifact_reference
        == reference
    )

    relationship = (
        selected.relationship_proposals[0]
    )

    assert relationship.link_type == "controls"
    assert (
        relationship.source_subject_key
        != relationship.target_subject_key
    )


def test_equivalent_content_has_same_subject_and_fingerprint(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    first_output = _derivation_output(
        candidates=[
            _candidate(
                "ELEM_001",
                "actor",
                "Microscope Operator",
            ),
        ],
        links=[],
    )
    second_output = _derivation_output(
        candidates=[
            _candidate(
                "ELEM_999",
                "actor",
                "Microscope Operator",
            ),
        ],
        links=[],
    )

    first = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=first_output,
        agent_id="AGENT_DERIVATION_A",
        persona_id="PERSONA_DERIVATION_A",
    )
    second = _write_agent_output(
        repository_root,
        artifact_index=2,
        output=second_output,
        agent_id="AGENT_DERIVATION_B",
        persona_id="PERSONA_DERIVATION_B",
    )

    selected = adapt_p9_agent_proposals(
        _p9_evidence((first, second)),
        repository_root=repository_root,
    )

    assert len(selected.element_proposals) == 2

    left, right = selected.element_proposals

    assert (
        left.stable_subject_key
        == right.stable_subject_key
    )
    assert (
        left.proposal_reference
        .proposal_content_fingerprint
        == right.proposal_reference
        .proposal_content_fingerprint
    )
    assert left.candidate_id != right.candidate_id


def test_changed_content_changes_only_proposal_fingerprint(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    first = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=_derivation_output(
            candidates=[
                _candidate(
                    "ELEM_001",
                    "actor",
                    "Microscope Operator",
                    description=(
                        "The local microscope operator."
                    ),
                ),
            ],
            links=[],
        ),
        agent_id="AGENT_DERIVATION_A",
        persona_id="PERSONA_DERIVATION_A",
    )
    second = _write_agent_output(
        repository_root,
        artifact_index=2,
        output=_derivation_output(
            candidates=[
                _candidate(
                    "ELEM_002",
                    "actor",
                    "Microscope Operator",
                    description=(
                        "The primary microscope operator."
                    ),
                ),
            ],
            links=[],
        ),
        agent_id="AGENT_DERIVATION_B",
        persona_id="PERSONA_DERIVATION_B",
    )

    selected = adapt_p9_agent_proposals(
        _p9_evidence((first, second)),
        repository_root=repository_root,
    )

    left, right = selected.element_proposals

    assert (
        left.stable_subject_key
        == right.stable_subject_key
    )
    assert (
        left.proposal_reference
        .proposal_content_fingerprint
        != right.proposal_reference
        .proposal_content_fingerprint
    )


def test_output_order_is_deterministic(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    first = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=_derivation_output(
            candidates=[
                _candidate(
                    "ELEM_010",
                    "system",
                    "Zulu System",
                ),
            ],
            links=[],
        ),
        agent_id="AGENT_DERIVATION_Z",
        persona_id="PERSONA_DERIVATION_Z",
    )
    second = _write_agent_output(
        repository_root,
        artifact_index=2,
        output=_derivation_output(
            candidates=[
                _candidate(
                    "ELEM_001",
                    "actor",
                    "Alpha Operator",
                ),
            ],
            links=[],
        ),
        agent_id="AGENT_DERIVATION_A",
        persona_id="PERSONA_DERIVATION_A",
    )

    forward = adapt_p9_agent_proposals(
        _p9_evidence((first, second)),
        repository_root=repository_root,
    )
    reverse = adapt_p9_agent_proposals(
        _p9_evidence((second, first)),
        repository_root=repository_root,
    )

    assert forward == reverse


def test_ignores_non_derivation_agent_outputs(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    interpretation = _write_agent_output(
        repository_root,
        artifact_index=1,
        output={"source_information": []},
        stage_directory="01_legacy_interpretation",
        agent_id="AGENT_INTERPRETATION_A",
        persona_id="PERSONA_INTERPRETATION_A",
    )
    derivation = _write_agent_output(
        repository_root,
        artifact_index=2,
        output=_derivation_output(),
    )

    selected = adapt_p9_agent_proposals(
        _p9_evidence(
            (
                interpretation,
                derivation,
            )
        ),
        repository_root=repository_root,
    )

    assert selected.proposal_count == 3


def test_requires_derivation_output(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    interpretation = _write_agent_output(
        repository_root,
        artifact_index=1,
        output={"source_information": []},
        stage_directory="01_legacy_interpretation",
        agent_id="AGENT_INTERPRETATION_A",
        persona_id="PERSONA_INTERPRETATION_A",
    )

    with pytest.raises(
        ReviewReferenceError,
        match="no structured derivation",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((interpretation,)),
            repository_root=repository_root,
        )


@pytest.mark.parametrize(
    "status",
    (
        "dry_run",
        "failed",
    ),
)
def test_rejects_non_completed_output(
    tmp_path: Path,
    status: str,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=_derivation_output(),
        status=status,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Only completed",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


@pytest.mark.parametrize(
    "invalid_output",
    (
        "{invalid",
        "```json\n{}\n```",
    ),
)
def test_rejects_non_raw_json_output(
    tmp_path: Path,
    invalid_output: str,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=invalid_output,
    )

    with pytest.raises(ReviewValidationError):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_missing_derivation_field(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    output = _derivation_output()
    del output["blocked_generation_tasks"]

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=output,
    )

    with pytest.raises(
        ReviewValidationError,
        match="fields do not match",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_duplicate_candidate_ids(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    output = _derivation_output(
        candidates=[
            _candidate(
                "ELEM_001",
                "actor",
                "Operator",
            ),
            _candidate(
                "ELEM_001",
                "system",
                "Microscope",
            ),
        ],
        links=[],
    )

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=output,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Candidate IDs",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_unresolved_link_candidate(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    output = _derivation_output(
        links=[
            _link(
                target="ELEM_999",
            ),
        ],
    )

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=output,
    )

    with pytest.raises(
        ReviewReferenceError,
        match="unavailable element candidate",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_ambiguous_candidate_name(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    output = _derivation_output(
        candidates=[
            _candidate(
                "ELEM_001",
                "actor",
                "Controller",
            ),
            _candidate(
                "ELEM_002",
                "item",
                "Controller",
            ),
            _candidate(
                "ELEM_003",
                "system",
                "Microscope",
            ),
        ],
        links=[
            _link(
                source="Controller",
                target="ELEM_003",
            ),
        ],
    )

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=output,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="ambiguous",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_agent_artifact_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=_derivation_output(),
    )

    target = (
        repository_root
        / reference.repository_relative_path
    )
    target.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint does not match",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_wrong_attempt_path(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=_derivation_output(),
        attempt_id="ATT-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Project, Run and Attempt",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )


def test_rejects_unsupported_element_type(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    candidate = _candidate(
        "ELEM_001",
        "actor",
        "Operator",
    )
    candidate["element_type"] = "automatic_truth"

    output = _derivation_output(
        candidates=[candidate],
        links=[],
    )

    reference = _write_agent_output(
        repository_root,
        artifact_index=1,
        output=output,
    )

    with pytest.raises(
        ReviewValidationError,
        match="element_type",
    ):
        adapt_p9_agent_proposals(
            _p9_evidence((reference,)),
            repository_root=repository_root,
        )
