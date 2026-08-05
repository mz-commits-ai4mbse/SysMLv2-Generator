"""Tests for initial P4/P9 Review Document assembly."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.project_processing import (
    create_processing_artifact_reference,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
)
from modules.review_workspace.p4_evidence_reference_adapter import (
    construct_p4_evidence_references,
)
from modules.review_workspace.p9_evidence_reference_adapter import (
    construct_p9_evidence_references,
)
from modules.review_workspace.review_document_assembly import (
    assemble_initial_review_document,
)

from tests.test_review_workspace_p4_evidence_reference_adapter import (
    _complete_record,
    _evidence_set,
    _persist_record,
    _record,
)
from tests.test_review_workspace_p4_review_item_builder import (
    _with_information_type,
)
from tests.test_review_workspace_p9_evidence_reference_adapter import (
    _evidence,
    _proposal_set,
    _report,
    _write_consensus,
)


REVIEW_DOCUMENT_ID = "RVD-000001"
REVIEW_DOCUMENT_VERSION_ID = "RVV-000001"
REVIEW_REVISION_ID = "RVR-000001"
TIMESTAMP = "2026-08-05T17:30:00Z"
OPENED_BY = "moritz@example.com"


def _inputs(
    tmp_path: Path,
    *,
    p4_record=None,
):
    p9_root = tmp_path / "p9_repository"
    p9_root.mkdir()

    proposals, agent_references = (
        _proposal_set()
    )
    consensus_reference, _ = (
        _write_consensus(
            p9_root,
            _report(),
        )
    )
    p9_review_evidence = _evidence(
        agent_references,
        (consensus_reference,),
    )
    p9_structured_evidence = (
        construct_p9_evidence_references(
            p9_review_evidence,
            proposals,
            repository_root=p9_root,
        )
    )

    p4_root = tmp_path / "p4_repository"
    p4_root.mkdir()

    selected_record = (
        _complete_record()
        if p4_record is None
        else p4_record
    )
    _persist_record(
        p4_root,
        selected_record,
    )

    p4_review_evidence = _evidence_set(
        (selected_record,)
    )
    p4_evidence_references = (
        construct_p4_evidence_references(
            p4_review_evidence,
            repository_root=p4_root,
        )
    )

    return {
        "p9_review_evidence": (
            p9_review_evidence
        ),
        "p9_structured_proposals": proposals,
        "p9_structured_evidence": (
            p9_structured_evidence
        ),
        "p4_review_evidence": (
            p4_review_evidence
        ),
        "p4_evidence_references": (
            p4_evidence_references
        ),
    }


def _assemble(inputs):
    return assemble_initial_review_document(
        **inputs,
        review_document_id=(
            REVIEW_DOCUMENT_ID
        ),
        review_document_version_id=(
            REVIEW_DOCUMENT_VERSION_ID
        ),
        review_revision_id=(
            REVIEW_REVISION_ID
        ),
        opened_by=OPENED_BY,
        timestamp=TIMESTAMP,
    )


def test_assembles_complete_initial_bundle(
    tmp_path: Path,
) -> None:
    selected = _assemble(
        _inputs(tmp_path)
    )

    document = selected.review_document
    version = selected.review_document_version
    revision = selected.initial_revision

    assert (
        document.review_document_id
        == REVIEW_DOCUMENT_ID
    )
    assert (
        document.processing_run_id
        == selected.p9_review_items
        .processing_run_id
    )

    assert (
        version.review_document_version_id
        == REVIEW_DOCUMENT_VERSION_ID
    )
    assert version.version_number == 1
    assert version.version_state == "draft"
    assert (
        version.head_revision_id
        == REVIEW_REVISION_ID
    )

    assert (
        revision.review_revision_id
        == REVIEW_REVISION_ID
    )
    assert revision.revision_sequence == 1
    assert revision.predecessor_revision_id is None
    assert len(revision.review_items) == 4

    assert (
        selected.repository_bundle
        == (
            document,
            version,
            revision,
        )
    )


def test_supporting_artifacts_cover_p4_and_p9(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    selected = _assemble(inputs)

    p9 = inputs["p9_review_evidence"]
    p4 = inputs["p4_evidence_references"]

    expected = {
        (
            reference.artifact_type,
            reference.artifact_id,
            reference.content_fingerprint,
            reference.repository_relative_path,
        )
        for reference in (
            p9.agent_output_references
            + p9.consensus_report_references
            + p9.run_summary_references
        )
    }

    expected.update(
        (
            evidence_reference
            .artifact_reference.artifact_type,
            evidence_reference
            .artifact_reference.artifact_id,
            evidence_reference
            .artifact_reference.content_fingerprint,
            evidence_reference
            .artifact_reference.repository_relative_path,
        )
        for record in p4.records
        for evidence_reference
        in record.all_evidence_references
    )

    actual = {
        (
            reference.artifact_type,
            reference.artifact_id,
            reference.content_fingerprint,
            reference.repository_relative_path,
        )
        for reference
        in selected.review_document
        .supporting_artifact_references
    }

    assert actual == expected
    assert (
        selected.review_document
        .primary_review_artifact_reference
        not in selected.review_document
        .supporting_artifact_references
    )


def test_eligibility_distinguishes_review_from_promotion(
    tmp_path: Path,
) -> None:
    base_record = _record()
    gap_information_unit = _with_information_type(
        base_record.information_unit,
        "gap",
    )
    gap_record = _record(
        information_unit=gap_information_unit
    )

    selected = _assemble(
        _inputs(
            tmp_path,
            p4_record=gap_record,
        )
    )
    eligibility = selected.eligibility

    assert (
        eligibility
        .eligible_for_workspace_creation
        is True
    )
    assert (
        eligibility
        .promotion_ready_review_item_ids
        == ()
    )

    assert len(
        eligibility.p9_review_item_ids
    ) == 3
    assert len(
        eligibility.p4_review_item_ids
    ) == 1
    assert len(
        eligibility.included_review_item_ids
    ) == 4

    p4_item_id = (
        selected.p4_review_items
        .review_items[0]
        .review_item_id
    )

    assert (
        eligibility.non_promotable_review_item_ids
        == (p4_item_id,)
    )
    assert (
        p4_item_id
        not in eligibility
        .potentially_promotable_review_item_ids
    )
    assert len(
        eligibility
        .relationship_resolution_required_item_ids
    ) == 1


def test_assembly_is_deterministic(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)

    first = _assemble(inputs)

    reversed_inputs = {
        **inputs,
        "p9_review_evidence": replace(
            inputs["p9_review_evidence"],
            agent_output_references=tuple(
                reversed(
                    inputs[
                        "p9_review_evidence"
                    ].agent_output_references
                )
            ),
            consensus_report_references=tuple(
                reversed(
                    inputs[
                        "p9_review_evidence"
                    ].consensus_report_references
                )
            ),
        ),
        "p9_structured_proposals": replace(
            inputs[
                "p9_structured_proposals"
            ],
            element_proposals=tuple(
                reversed(
                    inputs[
                        "p9_structured_proposals"
                    ].element_proposals
                )
            ),
            relationship_proposals=tuple(
                reversed(
                    inputs[
                        "p9_structured_proposals"
                    ].relationship_proposals
                )
            ),
        ),
        "p9_structured_evidence": replace(
            inputs[
                "p9_structured_evidence"
            ],
            subject_evidence=tuple(
                reversed(
                    inputs[
                        "p9_structured_evidence"
                    ].subject_evidence
                )
            ),
        ),
        "p4_review_evidence": replace(
            inputs["p4_review_evidence"],
            records=tuple(
                reversed(
                    inputs[
                        "p4_review_evidence"
                    ].records
                )
            ),
        ),
        "p4_evidence_references": replace(
            inputs[
                "p4_evidence_references"
            ],
            records=tuple(
                reversed(
                    inputs[
                        "p4_evidence_references"
                    ].records
                )
            ),
        ),
    }

    second = _assemble(reversed_inputs)

    assert first == second


def test_p4_item_ids_follow_p9_item_ids(
    tmp_path: Path,
) -> None:
    selected = _assemble(
        _inputs(tmp_path)
    )

    assert tuple(
        item.review_item_id
        for item
        in selected.p9_review_items.review_items
    ) == (
        "RIT-000001",
        "RIT-000002",
        "RIT-000003",
    )

    assert tuple(
        item.review_item_id
        for item
        in selected.p4_review_items.review_items
    ) == (
        "RIT-000004",
    )


def test_rejects_empty_review_document(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)

    changed = {
        **inputs,
        "p9_structured_proposals": replace(
            inputs[
                "p9_structured_proposals"
            ],
            element_proposals=(),
            relationship_proposals=(),
        ),
        "p9_structured_evidence": replace(
            inputs[
                "p9_structured_evidence"
            ],
            subject_evidence=(),
        ),
        "p4_review_evidence": replace(
            inputs["p4_review_evidence"],
            records=(),
        ),
        "p4_evidence_references": replace(
            inputs[
                "p4_evidence_references"
            ],
            records=(),
        ),
    }

    with pytest.raises(
        ReviewReferenceError,
        match="at least one",
    ):
        _assemble(changed)


@pytest.mark.parametrize(
    ("field_name", "replacement_value"),
    (
        ("project_id", "654321"),
        ("source_id", "SRC-999999"),
        ("processing_run_id", "RUN-000999"),
        ("attempt_id", "ATT-000999"),
    ),
)
def test_rejects_p9_identity_mismatch(
    tmp_path: Path,
    field_name: str,
    replacement_value: str,
) -> None:
    inputs = _inputs(tmp_path)

    changed = {
        **inputs,
        "p9_structured_proposals": replace(
            inputs[
                "p9_structured_proposals"
            ],
            **{
                field_name: replacement_value
            },
        ),
    }

    with pytest.raises(
        ReviewIntegrityError,
        match=field_name,
    ):
        _assemble(changed)


@pytest.mark.parametrize(
    ("field_name", "replacement_value"),
    (
        ("project_id", "654321"),
        ("source_id", "SRC-999999"),
    ),
)
def test_rejects_p4_identity_mismatch(
    tmp_path: Path,
    field_name: str,
    replacement_value: str,
) -> None:
    inputs = _inputs(tmp_path)

    changed = {
        **inputs,
        "p4_evidence_references": replace(
            inputs[
                "p4_evidence_references"
            ],
            **{
                field_name: replacement_value
            },
        ),
    }

    with pytest.raises(
        ReviewIntegrityError,
        match=field_name,
    ):
        _assemble(changed)


def test_rejects_p9_item_artifact_outside_evidence_set(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    p9 = inputs["p9_review_evidence"]

    changed = {
        **inputs,
        "p9_review_evidence": replace(
            p9,
            agent_output_references=(
                p9.agent_output_references[1:]
            ),
        ),
    }

    with pytest.raises(
        ReviewReferenceError,
        match="outside the selected P9",
    ):
        _assemble(changed)


def test_rejects_conflicting_artifact_identity(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    p9 = inputs["p9_review_evidence"]
    original = p9.agent_output_references[0]

    conflicting = (
        create_processing_artifact_reference(
            artifact_type=original.artifact_type,
            artifact_id=original.artifact_id,
            content_fingerprint="f" * 64,
            repository_relative_path=(
                "data/projects/"
                f"{p9.project_id}/runs/"
                f"{p9.processing_run_id}/"
                "artifacts/agent_outputs/"
                "conflicting-agent-output.json"
            ),
        )
    )

    changed = {
        **inputs,
        "p9_review_evidence": replace(
            p9,
            run_summary_references=(
                conflicting,
            ),
        ),
    }

    with pytest.raises(
        ReviewIntegrityError,
        match="conflicting content",
    ):
        _assemble(changed)


def test_rejects_primary_artifact_reused_as_supporting(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    p9 = inputs["p9_review_evidence"]

    changed = {
        **inputs,
        "p9_review_evidence": replace(
            p9,
            run_summary_references=(
                p9
                .primary_review_artifact_reference,
            ),
        ),
    }

    with pytest.raises(
        ReviewIntegrityError,
        match="must not be duplicated",
    ):
        _assemble(changed)
