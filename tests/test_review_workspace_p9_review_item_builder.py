"""Tests for initial open P9 Review Item construction."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
)
from modules.review_workspace.p9_evidence_reference_adapter import (
    construct_p9_evidence_references,
)
from modules.review_workspace.p9_review_item_builder import (
    DEFAULT_TARGET_NOTATION_PROFILE_ID,
    DEFAULT_TARGET_NOTATION_PROFILE_VERSION,
    construct_initial_p9_review_items,
)
from modules.review_workspace.p9_proposal_adapter import (
    create_element_stable_subject_key,
)
from tests.test_review_workspace_p9_evidence_reference_adapter import (
    PROJECT_ID,
    RUN_ID,
    SOURCE_ID,
    ATTEMPT_ID,
    _evidence,
    _proposal_set,
    _report,
    _write_consensus,
)


REVIEW_DOCUMENT_ID = "RVD-000001"
REVIEW_DOCUMENT_VERSION_ID = "RVV-000001"


def _inputs(
    tmp_path: Path,
):
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = (
        _proposal_set()
    )
    consensus_reference, _ = (
        _write_consensus(
            repository_root,
            _report(),
        )
    )
    p9_evidence = _evidence(
        agent_references,
        (consensus_reference,),
    )
    structured_evidence = (
        construct_p9_evidence_references(
            p9_evidence,
            proposals,
            repository_root=repository_root,
        )
    )

    return proposals, structured_evidence


def _construct(
    proposals,
    evidence,
    *,
    occupied_review_item_ids=(),
):
    return construct_initial_p9_review_items(
        proposals,
        evidence,
        review_document_id=(
            REVIEW_DOCUMENT_ID
        ),
        review_document_version_id=(
            REVIEW_DOCUMENT_VERSION_ID
        ),
        occupied_review_item_ids=(
            occupied_review_item_ids
        ),
    )


def test_constructs_one_item_per_stable_subject(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    selected = _construct(
        proposals,
        evidence,
    )

    assert selected.project_id == PROJECT_ID
    assert selected.source_id == SOURCE_ID
    assert (
        selected.processing_run_id
        == RUN_ID
    )
    assert selected.attempt_id == ATTEMPT_ID

    assert len(selected.review_items) == 3
    assert len(selected.element_items) == 2
    assert len(
        selected.relationship_items
    ) == 1

    assert tuple(
        item.review_item_id
        for item in selected.review_items
    ) == (
        "RIT-000001",
        "RIT-000002",
        "RIT-000003",
    )

    assert tuple(
        item.stable_subject_key
        for item in selected.review_items
    ) == tuple(
        sorted(
            item.stable_subject_key
            for item
            in selected.review_items
        )
    )


def test_element_item_is_open_and_traceable(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    selected = _construct(
        proposals,
        evidence,
    )

    operator_key = (
        create_element_stable_subject_key(
            element_type="actor",
            candidate_name=(
                "Microscope Operator"
            ),
        )
    )
    item = selected.item_for_subject(
        operator_key
    )

    assert item.review_item_kind == "element"
    assert item.section == "elements"
    assert item.lineage_operation == "original"
    assert item.original_report_locator == (
        f"report:recognized_elements/"
        f"{operator_key}"
    )
    assert (
        item.effective_review_outcome
        == "open"
    )

    assert len(item.proposal_references) == 2
    assert {
        reference.review_state
        for reference
        in item.proposal_references
    } == {"available"}

    assert len(
        item.source_evidence_references
    ) == 2
    assert len(
        item.consensus_evidence_references
    ) == 1

    assert (
        item.current_content.title
        == "Microscope Operator"
    )
    assert (
        item.current_content.information_type
        == "actor"
    )
    assert (
        item.current_content
        .relationship_representation
        is None
    )

    assert {
        selection.dimension
        for selection
        in item.dimension_selections
    } == {
        "content",
        "classification",
    }

    assert {
        selection.value_origin
        for selection
        in item.dimension_selections
    } == {"agent_proposal"}

    assert all(
        selection.selected_by is None
        and selection.selected_at is None
        for selection
        in item.dimension_selections
    )


def test_relationship_item_starts_unresolved(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    selected = _construct(
        proposals,
        evidence,
    )
    item = selected.relationship_items[0]

    assert (
        item.review_item_kind
        == "relationship"
    )
    assert item.section == "relationships"
    assert item.original_report_locator == (
        "report:explicit_source_links/"
        f"{item.stable_subject_key}"
    )
    assert (
        item.effective_review_outcome
        == "open"
    )
    assert len(item.proposal_references) == 2
    assert len(
        item.source_evidence_references
    ) == 2
    assert (
        item.consensus_evidence_references
        == ()
    )

    representation = (
        item.current_content
        .relationship_representation
    )

    assert representation is not None
    assert (
        representation.validation_status
        == "unresolved"
    )
    assert (
        representation.sysml_v2_construct
        is None
    )
    assert (
        representation
        .textual_notation_preview
        is None
    )
    assert (
        representation
        .validation_fingerprint
        is None
    )
    assert (
        representation
        .target_notation_profile_id
        == DEFAULT_TARGET_NOTATION_PROFILE_ID
    )
    assert (
        representation
        .target_notation_profile_version
        == DEFAULT_TARGET_NOTATION_PROFILE_VERSION
    )


def test_construction_is_deterministic(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    reversed_proposals = replace(
        proposals,
        element_proposals=tuple(
            reversed(
                proposals.element_proposals
            )
        ),
        relationship_proposals=tuple(
            reversed(
                proposals.relationship_proposals
            )
        ),
    )
    reversed_evidence = replace(
        evidence,
        subject_evidence=tuple(
            reversed(
                evidence.subject_evidence
            )
        ),
    )

    forward = _construct(
        proposals,
        evidence,
    )
    reverse = _construct(
        reversed_proposals,
        reversed_evidence,
    )

    assert forward == reverse


def test_allocates_after_highest_occupied_id(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    selected = _construct(
        proposals,
        evidence,
        occupied_review_item_ids=(
            "RIT-000002",
            "RIT-000005",
        ),
    )

    assert tuple(
        item.review_item_id
        for item in selected.review_items
    ) == (
        "RIT-000006",
        "RIT-000007",
        "RIT-000008",
    )


def test_empty_input_produces_empty_item_set(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    empty_proposals = replace(
        proposals,
        element_proposals=(),
        relationship_proposals=(),
    )
    empty_evidence = replace(
        evidence,
        subject_evidence=(),
    )

    selected = _construct(
        empty_proposals,
        empty_evidence,
    )

    assert selected.review_items == ()


@pytest.mark.parametrize(
    "field_name",
    (
        "project_id",
        "source_id",
        "processing_run_id",
        "attempt_id",
    ),
)
def test_rejects_identity_mismatch(
    tmp_path: Path,
    field_name: str,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    replacement_values = {
        "project_id": "654321",
        "source_id": "SRC-000999",
        "processing_run_id": "RUN-000999",
        "attempt_id": "ATT-000999",
    }

    changed_evidence = replace(
        evidence,
        **{
            field_name: replacement_values[
                field_name
            ]
        },
    )

    with pytest.raises(
        ReviewIntegrityError,
        match=field_name,
    ):
        _construct(
            proposals,
            changed_evidence,
        )


def test_rejects_missing_subject_evidence(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    changed = replace(
        evidence,
        subject_evidence=(
            evidence.subject_evidence[:-1]
        ),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="missing_evidence",
    ):
        _construct(proposals, changed)


def test_rejects_unexpected_subject_evidence(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    first = evidence.subject_evidence[0]
    unexpected = replace(
        first,
        stable_subject_key=(
            "element:unexpected:subject"
        ),
    )
    changed = replace(
        evidence,
        subject_evidence=(
            *evidence.subject_evidence,
            unexpected,
        ),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="unexpected_evidence",
    ):
        _construct(proposals, changed)


def test_rejects_evidence_kind_mismatch(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    first = evidence.subject_evidence[0]
    changed_first = replace(
        first,
        review_item_kind="relationship",
    )
    changed = replace(
        evidence,
        subject_evidence=(
            changed_first,
            *evidence.subject_evidence[1:],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="kind",
    ):
        _construct(proposals, changed)


def test_rejects_non_available_proposal(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    first = proposals.element_proposals[0]
    changed_reference = replace(
        first.proposal_reference,
        review_state="selected",
    )
    changed_first = replace(
        first,
        proposal_reference=(
            changed_reference
        ),
    )
    changed = replace(
        proposals,
        element_proposals=(
            changed_first,
            *proposals.element_proposals[1:],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="available",
    ):
        _construct(changed, evidence)


def test_rejects_tampered_stable_subject_key(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    first = proposals.element_proposals[0]
    changed_first = replace(
        first,
        stable_subject_key=(
            "element:tampered:subject"
        ),
    )
    changed = replace(
        proposals,
        element_proposals=(
            changed_first,
            *proposals.element_proposals[1:],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="semantic identity",
    ):
        _construct(changed, evidence)


def test_rejects_missing_relationship_endpoint(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    removed_subject = (
        proposals.element_proposals[1]
        .stable_subject_key
    )

    changed_proposals = replace(
        proposals,
        element_proposals=tuple(
            proposal
            for proposal
            in proposals.element_proposals
            if proposal.stable_subject_key
            != removed_subject
        ),
    )
    changed_evidence = replace(
        evidence,
        subject_evidence=tuple(
            record
            for record
            in evidence.subject_evidence
            if record.stable_subject_key
            != removed_subject
        ),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="target element subject",
    ):
        _construct(
            changed_proposals,
            changed_evidence,
        )


def test_rejects_incorrect_source_evidence_locator(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    element_record = next(
        record
        for record in evidence.subject_evidence
        if record.review_item_kind
        == "element"
    )
    first_reference = (
        element_record
        .source_evidence_references[0]
    )
    changed_reference = replace(
        first_reference,
        evidence_locator=(
            "output_text:/candidate_model_elements/"
            "WRONG/source_evidence"
        ),
    )
    changed_record = replace(
        element_record,
        source_evidence_references=(
            changed_reference,
            *element_record
            .source_evidence_references[1:],
        ),
    )
    changed_evidence = replace(
        evidence,
        subject_evidence=tuple(
            (
                changed_record
                if record.stable_subject_key
                == element_record
                .stable_subject_key
                else record
            )
            for record
            in evidence.subject_evidence
        ),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="one-to-one",
    ):
        _construct(
            proposals,
            changed_evidence,
        )


def test_subject_lookup_is_fail_closed(
    tmp_path: Path,
) -> None:
    proposals, evidence = _inputs(tmp_path)

    selected = _construct(
        proposals,
        evidence,
    )

    with pytest.raises(
        ReviewReferenceError,
        match="No initial P9 Review Item",
    ):
        selected.item_for_subject(
            "element:missing:subject"
        )
