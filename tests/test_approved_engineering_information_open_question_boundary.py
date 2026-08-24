from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.approved_engineering_information import (
    build_approved_engineering_information,
)
from modules.model_candidates.approved_engineering_deriver import (
    ApprovedEngineeringInformationDeriver,
)


def _review_item(
    subject_id: str,
    *,
    kind: str,
    outcome: str = "accepted_with_modification",
):
    return SimpleNamespace(
        original_report_locator=f"subject_review:{subject_id}",
        effective_review_outcome=outcome,
        stable_subject_key=f"subject:{subject_id.lower()}",
        review_item_kind=kind,
    )


def _manifest(subject_id: str, approved_input_id: str):
    return SimpleNamespace(
        review_document_version_id="RVV-000001",
        stable_subject_key=f"subject:{subject_id.lower()}",
        approved_input_id=approved_input_id,
        canonical_content=SimpleNamespace(
            title=subject_id,
            primary_text=f"{subject_id} statement",
            information_type="actor",
            modality="descriptive",
            epistemic_status="explicit",
        ),
        review_item_id=f"RIT-{subject_id.split('-')[1]}",
        review_item_fingerprint="1" * 64,
        content_fingerprint="2" * 64,
    )


def _decision(
    decision_id: str,
    source_subject_id: str,
    relationship_kind: str,
    target_subject_id: str,
):
    return SimpleNamespace(
        outcome="accepted",
        source_subject_id=source_subject_id,
        relationship_kind=relationship_kind,
        target_subject_id=target_subject_id,
        decision_id=decision_id,
        content_fingerprint="3" * 64,
        rationale=None,
    )


def _workspace(review_items, manifests):
    return SimpleNamespace(
        project_id="120412",
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            version_state="finalized",
            review_document_version_id="RVV-000001",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000062",
            review_items=tuple(review_items),
        ),
        approved_input_authority=tuple(
            SimpleNamespace(
                authority_state="active",
                manifest=manifest,
            )
            for manifest in manifests
        ),
    )


def _subject_payload(subject_ids):
    return {
        "canonical_subject_ids": tuple(subject_ids),
        "cards": tuple(
            {"canonical_subject_id": subject_id}
            for subject_id in subject_ids
        ),
    }


def test_accepted_open_questions_remain_non_promotable_context():
    workspace = _workspace(
        (
            _review_item("SUBJ-000001", kind="element"),
            _review_item("SUBJ-000018", kind="open_question"),
            _review_item("SUBJ-000019", kind="open_question"),
        ),
        (_manifest("SUBJ-000001", "AIN-000001"),),
    )

    value = build_approved_engineering_information(
        workspace_view=workspace,
        subject_review_payload=_subject_payload(
            ("SUBJ-000001", "SUBJ-000018", "SUBJ-000019")
        ),
        relationship_decisions=(
            _decision(
                "SRD-000023",
                "SUBJ-000018",
                "related_to",
                "SUBJ-000019",
            ),
        ),
        relationship_decision_authority_fingerprint="4" * 64,
    )

    assert tuple(
        item.canonical_subject_id for item in value.subjects
    ) == ("SUBJ-000001",)
    assert value.relationships == ()
    assert value.non_promotable_subject_ids == (
        "SUBJ-000018",
        "SUBJ-000019",
    )
    assert value.non_projectable_relationship_decision_ids == (
        "SRD-000023",
    )


def test_missing_promotion_for_accepted_element_still_fails_closed():
    workspace = _workspace(
        (_review_item("SUBJ-000001", kind="element"),),
        (),
    )

    with pytest.raises(ValueError, match="promotion is incomplete"):
        build_approved_engineering_information(
            workspace_view=workspace,
            subject_review_payload=_subject_payload(
                ("SUBJ-000001",)
            ),
            relationship_decisions=(),
            relationship_decision_authority_fingerprint="4" * 64,
        )


def test_non_projectable_relationship_is_explicit_phase_h_coverage():
    workspace = _workspace(
        (
            _review_item("SUBJ-000001", kind="element"),
            _review_item("SUBJ-000018", kind="open_question"),
        ),
        (_manifest("SUBJ-000001", "AIN-000001"),),
    )
    authority = build_approved_engineering_information(
        workspace_view=workspace,
        subject_review_payload=_subject_payload(
            ("SUBJ-000001", "SUBJ-000018")
        ),
        relationship_decisions=(
            _decision(
                "SRD-000023",
                "SUBJ-000018",
                "related_to",
                "SUBJ-000001",
            ),
        ),
        relationship_decision_authority_fingerprint="4" * 64,
    )

    deriver = ApprovedEngineeringInformationDeriver(
        base_deriver=SimpleNamespace(),
        profile=SimpleNamespace(relationship_semantics=()),
    )
    entries = deriver._non_projectable_relationship_entries(
        authority
    )

    assert len(entries) == 1
    assert entries[0].approved_input_id == "SRD-000023"
    assert entries[0].approved_input_kind == "semantic_relationship"
    assert entries[0].disposition == "intentionally_not_projected"
    assert (
        entries[0].reason_code
        == "non_promotable_relationship_endpoint"
    )
    assert entries[0].candidate_rule_ids == ()
