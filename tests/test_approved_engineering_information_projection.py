"""R4c.5c Approved Engineering Information projection tests."""

from types import SimpleNamespace

from modules.approved_engineering_information import (
    build_approved_engineering_information,
)


def test_projection_uses_active_approved_subjects_and_accepted_relations():
    item1 = SimpleNamespace(
        original_report_locator="subject_review:SUBJ-000001",
        stable_subject_key="subject:subj-000001",
        effective_review_outcome="accepted_with_modification",
    )
    item2 = SimpleNamespace(
        original_report_locator="subject_review:SUBJ-000002",
        stable_subject_key="subject:subj-000002",
        effective_review_outcome="accepted_with_modification",
    )

    def manifest(approved_input_id, stable_key, review_item_id):
        return SimpleNamespace(
            approved_input_id=approved_input_id,
            stable_subject_key=stable_key,
            review_document_version_id="RVV-000001",
            canonical_content=SimpleNamespace(
                title=stable_key,
                primary_text=f"statement {stable_key}",
                information_type="actor",
                modality="descriptive",
                epistemic_status="explicit",
            ),
            review_item_id=review_item_id,
            review_item_fingerprint="a" * 64,
            content_fingerprint="b" * 64,
        )

    view = SimpleNamespace(
        project_id="396272",
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            version_state="finalized",
            review_document_version_id="RVV-000001",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000004",
            review_items=(item1, item2),
        ),
        approved_input_authority=(
            SimpleNamespace(
                authority_state="active",
                manifest=manifest(
                    "AIN-000001",
                    "subject:subj-000001",
                    "RIT-000001",
                ),
            ),
            SimpleNamespace(
                authority_state="active",
                manifest=manifest(
                    "AIN-000002",
                    "subject:subj-000002",
                    "RIT-000002",
                ),
            ),
        ),
    )

    payload = {
        "canonical_subject_ids": [
            "SUBJ-000001",
            "SUBJ-000002",
        ],
        "cards": [
            {"canonical_subject_id": "SUBJ-000001"},
            {"canonical_subject_id": "SUBJ-000002"},
        ],
    }
    decisions = (
        SimpleNamespace(
            source_subject_id="SUBJ-000001",
            relationship_kind="uses",
            target_subject_id="SUBJ-000002",
            decision_id="SRD-000001",
            outcome="accepted",
            rationale=None,
            content_fingerprint="c" * 64,
        ),
        SimpleNamespace(
            source_subject_id="SUBJ-000002",
            relationship_kind="related_to",
            target_subject_id="SUBJ-000001",
            decision_id="SRD-000002",
            outcome="rejected",
            rationale="Not supported.",
            content_fingerprint="d" * 64,
        ),
    )

    value = build_approved_engineering_information(
        workspace_view=view,
        subject_review_payload=payload,
        relationship_decisions=decisions,
        relationship_decision_authority_fingerprint="e" * 64,
    )

    assert tuple(
        item.canonical_subject_id for item in value.subjects
    ) == ("SUBJ-000001", "SUBJ-000002")
    assert len(value.relationships) == 1
    assert value.relationships[0].relationship_kind == "uses"
