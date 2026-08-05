"""Tests for independent initial P4 Review Item construction."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.information_units import (
    create_information_unit,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
)
from modules.review_workspace.p4_evidence_reference_adapter import (
    P4_INFORMATION_UNIT_EVIDENCE_ROLE,
    construct_p4_evidence_references,
)
from modules.review_workspace.p4_review_item_builder import (
    P4_OPEN_QUESTION_INFORMATION_TYPES,
    construct_initial_p4_review_items,
    create_p4_information_unit_stable_subject_key,
)

from tests.test_review_workspace_p4_evidence_reference_adapter import (
    PROJECT_ID,
    SOURCE_ID,
    _complete_record,
    _evidence_set,
    _persist_record,
    _record,
)


REVIEW_DOCUMENT_ID = "RVD-000001"
REVIEW_DOCUMENT_VERSION_ID = "RVV-000001"


def _inputs(
    tmp_path: Path,
):
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    record = _complete_record()
    _persist_record(
        repository_root,
        record,
    )
    p4_evidence = _evidence_set((record,))
    references = (
        construct_p4_evidence_references(
            p4_evidence,
            repository_root=repository_root,
        )
    )

    return record, p4_evidence, references


def _construct(
    p4_evidence,
    references,
    *,
    occupied_review_item_ids=(),
):
    return construct_initial_p4_review_items(
        p4_evidence,
        references,
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


def _with_information_type(
    information_unit,
    information_type: str,
):
    return create_information_unit(
        project_id=information_unit.project_id,
        information_unit_id=(
            information_unit.information_unit_id
        ),
        source_id=information_unit.source_id,
        source_projection_id=(
            information_unit.source_projection_id
        ),
        source_anchors=(
            information_unit.source_anchors
        ),
        source_excerpt=(
            information_unit.source_excerpt
        ),
        interpreted_statement=(
            information_unit.interpreted_statement
        ),
        information_type=information_type,
        statement_modality=(
            information_unit.statement_modality
        ),
        epistemic_class=(
            information_unit.epistemic_class
        ),
        supporting_information_unit_ids=(
            information_unit
            .supporting_information_unit_ids
        ),
        derivation_rationale=(
            information_unit.derivation_rationale
        ),
        missing_evidence=(
            information_unit.missing_evidence
        ),
        extraction_provenance=(
            information_unit
            .extraction_provenance
        ),
        confidence=information_unit.confidence,
        confidence_rationale=(
            information_unit.confidence_rationale
        ),
        timestamp=information_unit.created_at,
    )


def test_constructs_open_traceable_p4_item(
    tmp_path: Path,
) -> None:
    record, p4_evidence, references = (
        _inputs(tmp_path)
    )

    selected = _construct(
        p4_evidence,
        references,
    )

    assert selected.project_id == PROJECT_ID
    assert selected.source_id == SOURCE_ID
    assert len(selected.review_items) == 1

    item = selected.review_items[0]
    information_unit = record.information_unit

    assert item.review_item_id == "RIT-000001"
    assert item.review_item_kind == "element"
    assert item.section == "elements"
    assert item.lineage_operation == "original"
    assert item.derived_from_review_item_ids == ()
    assert item.proposal_references == ()
    assert (
        item.consensus_evidence_references
        == ()
    )
    assert (
        item.effective_review_outcome
        == "open"
    )

    assert item.stable_subject_key == (
        create_p4_information_unit_stable_subject_key(
            information_unit.information_unit_id
        )
    )
    assert item.original_report_locator == (
        "p4:information_units/"
        f"{information_unit.information_unit_id}"
    )

    assert len(
        item.source_evidence_references
    ) == 6
    assert {
        reference.artifact_reference.artifact_id
        for reference
        in item.source_evidence_references
    } == {
        information_unit.information_unit_id,
        *(
            candidate
            .terminology_mapping_candidate_id
            for candidate
            in record.terminology_mapping_candidates
        ),
        *(
            candidate
            .framework_assignment_candidate_id
            for candidate
            in record.framework_assignment_candidates
        ),
        *(
            decision.human_review_decision_id
            for decision
            in record.human_review_decisions
        ),
    }

    content = item.current_content

    assert (
        content.primary_text
        == information_unit.interpreted_statement
    )
    assert (
        content.information_type
        == information_unit.information_type
    )
    assert (
        content.modality
        == information_unit.statement_modality
    )
    assert (
        content.epistemic_status
        == information_unit.epistemic_class
    )
    assert content.human_rationale is None
    assert content.human_confidence is None
    assert (
        content.relationship_representation
        is None
    )

    assert {
        selection.dimension
        for selection
        in item.dimension_selections
    } == {
        "content",
        "classification",
        "source_assignment",
    }

    assert all(
        selection.value_origin
        == "agent_proposal"
        and selection.selected_by is None
        and selection.selected_at is None
        for selection
        in item.dimension_selections
    )


@pytest.mark.parametrize(
    "information_type",
    tuple(
        sorted(
            P4_OPEN_QUESTION_INFORMATION_TYPES
        )
    ),
)
def test_attention_information_types_become_open_questions(
    tmp_path: Path,
    information_type: str,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    base_record = _record()
    information_unit = _with_information_type(
        base_record.information_unit,
        information_type,
    )
    record = _record(
        information_unit=information_unit
    )

    _persist_record(repository_root, record)

    p4_evidence = _evidence_set((record,))
    references = (
        construct_p4_evidence_references(
            p4_evidence,
            repository_root=repository_root,
        )
    )

    selected = _construct(
        p4_evidence,
        references,
    )
    item = selected.review_items[0]

    assert (
        item.review_item_kind
        == "open_question"
    )
    assert item.section == "open_questions"
    assert (
        item.current_content.information_type
        == information_type
    )


def test_construction_is_deterministic(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    first = _record()
    second_information_unit = (
        create_information_unit(
            project_id=(
                first.information_unit.project_id
            ),
            information_unit_id="IU-000002",
            source_id=(
                first.information_unit.source_id
            ),
            source_projection_id=(
                first.information_unit
                .source_projection_id
            ),
            source_anchors=(
                first.information_unit.source_anchors
            ),
            source_excerpt=(
                first.information_unit.source_excerpt
            ),
            interpreted_statement=(
                "The pump shall preserve "
                "model traceability."
            ),
            information_type="requirement",
            statement_modality="normative",
            epistemic_class="explicit",
            supporting_information_unit_ids=(),
            derivation_rationale=None,
            missing_evidence=None,
            extraction_provenance=(
                first.information_unit
                .extraction_provenance
            ),
            confidence="high",
            confidence_rationale=(
                "The statement is explicit."
            ),
            timestamp=(
                first.information_unit.created_at
            ),
        )
    )
    second = _record(
        information_unit=second_information_unit
    )

    _persist_record(repository_root, first)
    _persist_record(repository_root, second)

    forward_evidence = _evidence_set(
        (first, second)
    )
    reverse_evidence = _evidence_set(
        (second, first)
    )

    forward_references = (
        construct_p4_evidence_references(
            forward_evidence,
            repository_root=repository_root,
        )
    )
    reverse_references = replace(
        forward_references,
        records=tuple(
            reversed(
                forward_references.records
            )
        ),
    )

    forward = _construct(
        forward_evidence,
        forward_references,
    )
    reverse = _construct(
        reverse_evidence,
        reverse_references,
    )

    assert forward == reverse
    assert tuple(
        item.review_item_id
        for item in forward.review_items
    ) == (
        "RIT-000001",
        "RIT-000002",
    )


def test_allocates_after_occupied_item_ids(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    selected = _construct(
        p4_evidence,
        references,
        occupied_review_item_ids=(
            "RIT-000003",
            "RIT-000008",
        ),
    )

    assert (
        selected.review_items[0]
        .review_item_id
        == "RIT-000009"
    )


def test_empty_inputs_produce_empty_item_set(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    p4_evidence = _evidence_set(())
    references = (
        construct_p4_evidence_references(
            p4_evidence,
            repository_root=repository_root,
        )
    )

    selected = _construct(
        p4_evidence,
        references,
    )

    assert selected.review_items == ()


@pytest.mark.parametrize(
    ("field_name", "replacement_value"),
    (
        ("project_id", "654321"),
        ("source_id", "SRC-999999"),
    ),
)
def test_rejects_identity_mismatch(
    tmp_path: Path,
    field_name: str,
    replacement_value: str,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    changed = replace(
        references,
        **{
            field_name: replacement_value
        },
    )

    with pytest.raises(
        ReviewIntegrityError,
        match=field_name,
    ):
        _construct(
            p4_evidence,
            changed,
        )


def test_rejects_missing_reference_record(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    changed = replace(
        references,
        records=(),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="missing_references",
    ):
        _construct(
            p4_evidence,
            changed,
        )


def test_rejects_unexpected_reference_record(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    unexpected = replace(
        references.records[0],
        information_unit_id="IU-999999",
    )
    changed = replace(
        references,
        records=(unexpected,),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="unexpected_references",
    ):
        _construct(
            p4_evidence,
            changed,
        )


def test_rejects_incorrect_evidence_role(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    record = references.records[0]
    changed_information_unit_reference = replace(
        record.information_unit_reference,
        evidence_role="incorrect_role",
    )
    changed_record = replace(
        record,
        information_unit_reference=(
            changed_information_unit_reference
        ),
    )
    changed = replace(
        references,
        records=(changed_record,),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="evidence role",
    ):
        _construct(
            p4_evidence,
            changed,
        )


def test_rejects_missing_supporting_evidence(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    record = references.records[0]
    changed_record = replace(
        record,
        terminology_mapping_references=(),
    )
    changed = replace(
        references,
        records=(changed_record,),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="missing",
    ):
        _construct(
            p4_evidence,
            changed,
        )


def test_rejects_incorrect_evidence_fingerprint(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    record = references.records[0]
    changed_information_unit_reference = replace(
        record.information_unit_reference,
        evidence_content_fingerprint="f" * 64,
    )
    changed_record = replace(
        record,
        information_unit_reference=(
            changed_information_unit_reference
        ),
    )
    changed = replace(
        references,
        records=(changed_record,),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="content fingerprint",
    ):
        _construct(
            p4_evidence,
            changed,
        )


def test_rejects_duplicate_p4_records(
    tmp_path: Path,
) -> None:
    record, p4_evidence, references = (
        _inputs(tmp_path)
    )

    changed = replace(
        p4_evidence,
        records=(record, record),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unique Information Unit",
    ):
        _construct(
            changed,
            references,
        )


def test_information_unit_lookup_is_fail_closed(
    tmp_path: Path,
) -> None:
    _, p4_evidence, references = (
        _inputs(tmp_path)
    )

    selected = _construct(
        p4_evidence,
        references,
    )

    with pytest.raises(
        ReviewReferenceError,
        match="No initial P4 Review Item",
    ):
        selected.item_for_information_unit(
            "IU-000999"
        )
