"""Tests for immutable Review Item manifests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.item_manifest import (
    REVIEW_ITEM_SCHEMA_VERSION,
    calculate_review_item_fingerprint,
    create_review_item,
    parse_review_item,
    review_item_from_json,
    review_item_to_dict,
    review_item_to_json,
    validate_review_item,
)
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItemContent,
    ReviewProperty,
    ReviewProposalReference,
    ReviewRelationshipRepresentation,
)


def _artifact(
    *,
    artifact_id: str = "AGENT-001",
    fingerprint: str = "a" * 64,
    project_id: str = "000001",
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="agent_outputs",
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=(
            f"data/projects/{project_id}/runs/"
            "RUN-000001/artifacts/agent_outputs/"
            f"{artifact_id}.json"
        ),
    )


def _proposal(
    *,
    proposal_id: str = "CAND-001",
    state: str = "selected",
    artifact_id: str = "AGENT-001",
    fingerprint: str = "b" * 64,
) -> ReviewProposalReference:
    return ReviewProposalReference(
        artifact_reference=_artifact(
            artifact_id=artifact_id,
        ),
        agent_id="AGENT_001",
        persona_id="systems_engineer",
        proposal_id=proposal_id,
        proposal_content_fingerprint=fingerprint,
        original_report_locator=(
            f"candidate-elements/{proposal_id}"
        ),
        review_state=state,
    )


def _evidence() -> ReviewEvidenceReference:
    return ReviewEvidenceReference(
        artifact_reference=_artifact(
            artifact_id="EVIDENCE-001",
            fingerprint="c" * 64,
        ),
        evidence_role="source_evidence",
        evidence_locator="source-information/SI-001",
        evidence_content_fingerprint="d" * 64,
    )


def _outcome_selection(
    outcome: str,
) -> ReviewDimensionSelection:
    return ReviewDimensionSelection(
        dimension="review_outcome",
        selected_values=(outcome,),
        value_origin="item_override",
        source_reference_ids=("CAND-001",),
        rationale=None,
        selected_by="reviewer@example.com",
        selected_at="2026-08-03T16:00:00Z",
    )


def _content(
    relationship: (
        ReviewRelationshipRepresentation | None
    ) = None,
) -> ReviewItemContent:
    return ReviewItemContent(
        title="Upload engineering source",
        primary_text=(
            "The system shall accept an engineering source."
        ),
        description=None,
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
        human_rationale=None,
        human_confidence="high",
        relationship_representation=relationship,
    )


def _relationship(
    *,
    status: str = "valid",
) -> ReviewRelationshipRepresentation:
    if status == "unresolved":
        construct = None
        preview = None
        fingerprint = None
    else:
        construct = "dependency"
        preview = (
            "dependency from 'Source' to 'Target';"
        )
        fingerprint = "e" * 64

    return ReviewRelationshipRepresentation(
        source_subject_key="source-subject",
        target_subject_key="target-subject",
        semantic_intent="Source depends on target.",
        sysml_v2_construct=construct,
        construct_properties=(
            ReviewProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSML_V2_TARGET",
        target_notation_profile_version="1.0.0",
        textual_notation_preview=preview,
        validation_status=status,
        validation_fingerprint=fingerprint,
    )


def _element_item():
    return create_review_item(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        stable_subject_key="upload-engineering-source",
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "candidate-elements/CAND-001"
        ),
        proposal_references=(_proposal(),),
        source_evidence_references=(_evidence(),),
        consensus_evidence_references=(),
        current_content=_content(),
        dimension_selections=(
            _outcome_selection(
                "accepted_as_generated"
            ),
        ),
        effective_review_outcome=(
            "accepted_as_generated"
        ),
    )


def _relationship_item(
    *,
    status: str = "valid",
    outcome: str = "accepted_with_modification",
):
    proposal = _proposal(
        proposal_id="REL-001",
    )

    return create_review_item(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000002",
        review_item_kind="relationship",
        stable_subject_key="source-depends-on-target",
        section="relationships",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "explicit-links/REL-001"
        ),
        proposal_references=(proposal,),
        source_evidence_references=(_evidence(),),
        consensus_evidence_references=(),
        current_content=_content(
            _relationship(status=status)
        ),
        dimension_selections=(
            _outcome_selection(outcome),
        ),
        effective_review_outcome=outcome,
    )


def test_create_review_item_is_fingerprinted() -> None:
    item = _element_item()

    assert item.schema_version == REVIEW_ITEM_SCHEMA_VERSION
    assert item.item_content_fingerprint == (
        calculate_review_item_fingerprint(item)
    )

    validate_review_item(item)


@pytest.mark.parametrize(
    "item",
    (
        _element_item(),
        _relationship_item(),
    ),
)
def test_review_item_round_trip_is_deterministic(
    item,
) -> None:
    serialized = review_item_to_json(item)

    assert serialized.endswith("\n")
    assert review_item_from_json(serialized) == item
    assert review_item_to_json(
        review_item_from_json(serialized)
    ) == serialized


def test_review_item_dict_has_exact_fields() -> None:
    payload = review_item_to_dict(_element_item())

    assert set(payload) == {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "review_item_id",
        "review_item_kind",
        "stable_subject_key",
        "section",
        "lineage_operation",
        "derived_from_review_item_ids",
        "original_report_locator",
        "proposal_references",
        "source_evidence_references",
        "consensus_evidence_references",
        "current_content",
        "dimension_selections",
        "effective_review_outcome",
        "item_content_fingerprint",
    }


def test_item_rejects_modified_content() -> None:
    item = _element_item()

    modified = replace(
        item,
        stable_subject_key="changed-subject",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_review_item(modified)


@pytest.mark.parametrize(
    ("kind", "section"),
    (
        ("element", "relationships"),
        ("relationship", "elements"),
        ("open_question", "elements"),
    ),
)
def test_kind_and_section_must_match(
    kind: str,
    section: str,
) -> None:
    item = _element_item()

    modified = replace(
        item,
        review_item_kind=kind,
        section=section,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="section",
    ):
        validate_review_item(modified)


def test_rejected_content_is_not_an_item_kind() -> None:
    item = _element_item()

    modified = replace(
        item,
        review_item_kind="rejected_content",
    )

    with pytest.raises(ReviewValidationError):
        validate_review_item(modified)


@pytest.mark.parametrize(
    ("operation", "parents"),
    (
        ("original", ("RIT-000010",)),
        ("human_created", ("RIT-000010",)),
        ("split", ()),
        ("split", ("RIT-000010", "RIT-000011")),
        ("merge", ("RIT-000010",)),
    ),
)
def test_lineage_contract_is_strict(
    operation: str,
    parents: tuple[str, ...],
) -> None:
    item = _element_item()

    modified = replace(
        item,
        lineage_operation=operation,
        derived_from_review_item_ids=parents,
    )

    with pytest.raises(ReviewIntegrityError):
        validate_review_item(modified)


def test_item_must_not_derive_from_itself() -> None:
    item = _element_item()

    modified = replace(
        item,
        lineage_operation="split",
        derived_from_review_item_ids=(
            item.review_item_id,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="itself",
    ):
        validate_review_item(modified)


def test_parent_ids_must_be_unique() -> None:
    item = _element_item()

    modified = replace(
        item,
        lineage_operation="merge",
        derived_from_review_item_ids=(
            "RIT-000010",
            "RIT-000010",
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unique",
    ):
        validate_review_item(modified)


def test_relationship_item_requires_representation() -> None:
    item = _relationship_item()

    modified = replace(
        item,
        current_content=replace(
            item.current_content,
            relationship_representation=None,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="requires",
    ):
        validate_review_item(modified)


def test_element_must_not_contain_relationship() -> None:
    item = _element_item()

    modified = replace(
        item,
        current_content=replace(
            item.current_content,
            relationship_representation=(
                _relationship()
            ),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Only relationship",
    ):
        validate_review_item(modified)


def test_unresolved_relationship_cannot_be_accepted() -> None:
    with pytest.raises(
        ReviewIntegrityError,
        match="valid SysML v2",
    ):
        _relationship_item(
            status="unresolved",
            outcome="accepted_with_modification",
        )


def test_unresolved_relationship_may_remain_unresolved() -> None:
    item = _relationship_item(
        status="unresolved",
        outcome="unresolved",
    )

    validate_review_item(item)


def test_relationship_rejects_not_applicable_status() -> None:
    relationship = replace(
        _relationship(),
        validation_status="not_applicable",
    )

    item = _relationship_item()

    modified = replace(
        item,
        current_content=replace(
            item.current_content,
            relationship_representation=relationship,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="not_applicable",
    ):
        validate_review_item(modified)


def test_accepted_as_generated_requires_one_selected() -> None:
    item = _element_item()

    modified = replace(
        item,
        proposal_references=(
            replace(
                item.proposal_references[0],
                review_state="available",
            ),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exactly one",
    ):
        validate_review_item(modified)


def test_multiple_selected_proposals_require_combined() -> None:
    item = _element_item()

    modified = replace(
        item,
        proposal_references=(
            _proposal(
                proposal_id="CAND-001",
                artifact_id="AGENT-001",
                fingerprint="b" * 64,
            ),
            _proposal(
                proposal_id="CAND-002",
                artifact_id="AGENT-002",
                fingerprint="c" * 64,
            ),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="combined",
    ):
        validate_review_item(modified)


def test_combined_requires_two_selected_proposals() -> None:
    item = _element_item()

    modified = replace(
        item,
        effective_review_outcome="combined",
        dimension_selections=(
            _outcome_selection("combined"),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="at least two",
    ):
        validate_review_item(modified)


def test_automatic_non_selection_requires_selection() -> None:
    item = _element_item()

    modified = replace(
        item,
        effective_review_outcome="open",
        dimension_selections=(
            _outcome_selection("open"),
        ),
        proposal_references=(
            replace(
                item.proposal_references[0],
                review_state=(
                    "not_selected_due_to_human_selection"
                ),
            ),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="selected proposal",
    ):
        validate_review_item(modified)


def test_proposal_references_must_be_unique() -> None:
    item = _element_item()
    proposal = item.proposal_references[0]

    modified = replace(
        item,
        proposal_references=(
            proposal,
            proposal,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unique",
    ):
        validate_review_item(modified)


def test_artifact_references_are_project_bound() -> None:
    item = _element_item()

    invalid_proposal = replace(
        item.proposal_references[0],
        artifact_reference=_artifact(
            project_id="000002",
        ),
    )

    modified = replace(
        item,
        proposal_references=(invalid_proposal,),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Project",
    ):
        validate_review_item(modified)


def test_dimension_selections_are_unique() -> None:
    item = _element_item()
    selection = item.dimension_selections[0]

    modified = replace(
        item,
        dimension_selections=(
            selection,
            selection,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="one selection",
    ):
        validate_review_item(modified)


def test_outcome_selection_must_match_effective_outcome() -> None:
    item = _element_item()

    modified = replace(
        item,
        dimension_selections=(
            _outcome_selection("rejected"),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must match",
    ):
        validate_review_item(modified)


def test_human_origin_requires_actor_and_time() -> None:
    item = _element_item()
    selection = item.dimension_selections[0]

    modified_selection = replace(
        selection,
        selected_by=None,
    )

    modified = replace(
        item,
        dimension_selections=(modified_selection,),
    )

    with pytest.raises(ReviewValidationError):
        validate_review_item(modified)


def test_agent_origin_rejects_human_metadata() -> None:
    item = _element_item()
    selection = item.dimension_selections[0]

    modified_selection = replace(
        selection,
        value_origin="agent_proposal",
    )

    modified = replace(
        item,
        dimension_selections=(modified_selection,),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="human selection metadata",
    ):
        validate_review_item(modified)


def test_parse_rejects_missing_and_unknown_fields() -> None:
    payload = review_item_to_dict(_element_item())

    missing = dict(payload)
    missing.pop("stable_subject_key")

    with pytest.raises(
        ReviewValidationError,
        match="missing",
    ):
        parse_review_item(missing)

    unknown = {
        **payload,
        "unexpected": True,
    }

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_review_item(unknown)


def test_json_rejects_duplicate_keys() -> None:
    text = review_item_to_json(_element_item())

    duplicated = text.replace(
        '"project_id": "000001",',
        (
            '"project_id": "000001",\n'
            '  "project_id": "000001",'
        ),
        1,
    )

    with pytest.raises(
        ReviewValidationError,
        match="Duplicate JSON object key",
    ):
        review_item_from_json(duplicated)


def test_json_rejects_invalid_input() -> None:
    with pytest.raises(ReviewValidationError):
        review_item_from_json(None)

    with pytest.raises(ReviewValidationError):
        review_item_from_json("{invalid")
