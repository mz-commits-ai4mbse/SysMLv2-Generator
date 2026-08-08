"""Tests for G6.3c1 scoped action impact and precedence."""

from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.revision_manifest import create_review_revision
from modules.review_workspace.scoped_workflow import (
    ReviewFilterSpec,
    ReviewItemFilterFact,
    ScopedReviewActionRequest,
    create_scoped_review_action_mutation,
    preview_scoped_review_action,
)
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewItemContent,
)
from modules.review_workspace.errors import ReviewIntegrityError

import pytest


def _item(item_id, *, origin="agent_proposal", outcome="open"):
    content = ReviewItemContent(
        title=item_id,
        primary_text=f"Statement {item_id}.",
        description=None,
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )
    human = origin != "agent_proposal"
    return create_review_item(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id=item_id,
        review_item_kind="element",
        stable_subject_key=f"requirement:{item_id.lower()}",
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=f"report:{item_id}",
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(
            ReviewDimensionSelection(
                dimension="framework_assignment",
                selected_values=("Existing",),
                value_origin=origin,
                source_reference_ids=("SRC",),
                rationale=("Human" if human else "Agent"),
                selected_by=("Reviewer A" if human else None),
                selected_at=(
                    "2026-08-08T08:00:00Z"
                    if human
                    else None
                ),
            ),
        ),
        effective_review_outcome=outcome,
    )


def _revision(items):
    return create_review_revision(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=tuple(items),
        scoped_review_action_ids=(),
        created_by="Reviewer A",
        timestamp="2026-08-08T08:00:00Z",
    )


def _fact(item):
    return ReviewItemFilterFact(
        review_item_id=item.review_item_id,
        item_content_fingerprint=item.item_content_fingerprint,
        review_status=item.effective_review_outcome,
        review_item_kind=item.review_item_kind,
        proposed_classifications=("requirement",),
        effective_classifications=("requirement",),
        proposed_framework_assignments=(),
        effective_framework_assignments=("Existing",),
        agent_identities=(),
        confidence_levels=(),
        consensus_states=("not_available",),
        agent_disagreement_state="not_available",
        human_modification_state=(
            "modified"
            if any(
                s.value_origin != "agent_proposal"
                for s in item.dimension_selections
            )
            else "unmodified"
        ),
        source_identities=("SRC-000001",),
        evidence_sufficiency_state="not_assessed",
        relationship_validation_status="not_applicable",
    )


def test_document_default_excludes_higher_precedence_item_override():
    first = _item("RIT-000001", origin="agent_proposal")
    second = _item("RIT-000002", origin="item_override")
    revision = _revision((first, second))

    preview = preview_scoped_review_action(
        revision,
        (_fact(first), _fact(second)),
        ScopedReviewActionRequest(
            expected_revision_id="RVR-000001",
            action_scope="document_default",
            decision_dimension="framework_assignment",
            selected_values=("System Requirements",),
        ),
    )

    assert preview.matched_count == 2
    assert preview.item_override_count == 1
    assert preview.excluded_review_item_ids == (
        "RIT-000002",
    )
    assert preview.would_overwrite_review_item_ids == (
        "RIT-000002",
    )
    assert preview.affected_review_item_ids == (
        "RIT-000001",
    )


def test_explicit_selection_can_overwrite_item_override_only_after_confirmation():
    item = _item("RIT-000001", origin="item_override")
    revision = _revision((item,))

    request = ScopedReviewActionRequest(
        expected_revision_id="RVR-000001",
        action_scope="explicit_selection",
        decision_dimension="framework_assignment",
        selected_values=("System Requirements",),
        explicit_review_item_ids=("RIT-000001",),
        confirm_higher_precedence_overwrite=True,
    )

    mutation = create_scoped_review_action_mutation(
        revision,
        facts=(_fact(item),),
        request=request,
        scoped_review_action_id="SRA-000001",
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert mutation.preview.overwrite_count == 1
    edited = mutation.revision.review_items[0]
    selection = next(
        s
        for s in edited.dimension_selections
        if s.dimension == "framework_assignment"
    )
    assert selection.value_origin == "explicit_selection"
    assert selection.selected_values == (
        "System Requirements",
    )
    assert mutation.action.materialized_items[0].review_item_id == (
        "RIT-000001"
    )


def test_filtered_action_persists_filter_and_exact_materialization():
    first = _item("RIT-000001")
    second = _item("RIT-000002", outcome="deferred")
    revision = _revision((first, second))
    facts = (_fact(first), _fact(second))

    mutation = create_scoped_review_action_mutation(
        revision,
        facts=facts,
        request=ScopedReviewActionRequest(
            expected_revision_id="RVR-000001",
            action_scope="filtered_set",
            decision_dimension="source_assignment",
            selected_values=("SRC_INFO_001",),
            filter_spec=ReviewFilterSpec(
                review_status=("deferred",),
            ),
        ),
        scoped_review_action_id="SRA-000001",
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert mutation.action.filter_definition == (
        '{"review_status":["deferred"]}'
    )
    assert tuple(
        ref.review_item_id
        for ref in mutation.action.materialized_items
    ) == ("RIT-000002",)


def test_bulk_rejection_requires_preview_confirmation_and_rationale():
    first = _item("RIT-000001")
    second = _item("RIT-000002")
    revision = _revision((first, second))
    request = ScopedReviewActionRequest(
        expected_revision_id="RVR-000001",
        action_scope="explicit_selection",
        decision_dimension="review_outcome",
        selected_values=("rejected",),
        explicit_review_item_ids=(
            "RIT-000001",
            "RIT-000002",
        ),
        rationale="Unsupported content.",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Bulk rejection",
    ):
        create_scoped_review_action_mutation(
            revision,
            facts=(_fact(first), _fact(second)),
            request=request,
            scoped_review_action_id="SRA-000001",
            new_review_revision_id="RVR-000002",
            actor_identity="Reviewer A",
            timestamp="2026-08-08T08:05:00Z",
        )


def test_classification_action_updates_content_and_origin():
    item = _item("RIT-000001")
    revision = _revision((item,))

    mutation = create_scoped_review_action_mutation(
        revision,
        facts=(_fact(item),),
        request=ScopedReviewActionRequest(
            expected_revision_id="RVR-000001",
            action_scope="explicit_selection",
            decision_dimension="classification",
            selected_values=(
                "information_type=constraint",
                "modality=<none>",
            ),
            explicit_review_item_ids=("RIT-000001",),
        ),
        scoped_review_action_id="SRA-000001",
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    edited = mutation.revision.review_items[0]
    assert edited.current_content.information_type == "constraint"
    assert edited.current_content.modality is None
    selection = next(
        s
        for s in edited.dimension_selections
        if s.dimension == "classification"
    )
    assert selection.value_origin == "explicit_selection"
