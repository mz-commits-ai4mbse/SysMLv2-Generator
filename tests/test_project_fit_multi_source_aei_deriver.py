"""BLK-002 MVP-B2B1 multi-source AEI derivation tests."""

from types import SimpleNamespace

import modules.model_candidates.approved_engineering_deriver as module
from modules.model_candidates.approved_engineering_deriver import (
    ApprovedEngineeringInformationDeriver,
)
from modules.model_candidates.types import (
    ModelCandidateDerivationPlan,
)


def _input(source_id, approved_id, review_id):
    return SimpleNamespace(
        project_id="308131",
        source_id=source_id,
        approved_input_id=approved_id,
        stable_subject_key="shared.subject",
        review_document_id=review_id,
        review_document_version_id=f"{review_id}-V1",
        content_fingerprint=approved_id[-1] * 64,
    )


def _aei(source_id, approved_id, review_id, fingerprint):
    subject_id = f"{source_id}:SUBJ-000001"

    return SimpleNamespace(
        project_id="308131",
        review_document_id=review_id,
        review_document_version_id=f"{review_id}-V1",
        subjects=(
            SimpleNamespace(
                canonical_subject_id=subject_id,
                approved_input_id=approved_id,
                stable_subject_key="shared.subject",
            ),
        ),
        relationships=(
            SimpleNamespace(
                source_subject_id=subject_id,
                relationship_kind="dependency",
                target_subject_id=subject_id,
                relationship_decision_id=(
                    f"REL-{source_id[-1]}"
                ),
                relationship_decision_fingerprint=(
                    source_id[-1] * 64
                ),
                rationale="source-local",
            ),
        ),
        non_projectable_relationship_decision_ids=(),
        content_fingerprint=fingerprint,
    )


def test_project_fit_views_keep_aei_sets_separate_and_source_scoped(
    monkeypatch,
):
    first = _input(
        "SRC-000001",
        "AIN-000001",
        "RVD-1",
    )
    second = _input(
        "SRC-000002",
        "AIN-000002",
        "RVD-2",
    )

    first_aei = _aei(
        first.source_id,
        first.approved_input_id,
        first.review_document_id,
        "a" * 64,
    )
    second_aei = _aei(
        second.source_id,
        second.approved_input_id,
        second.review_document_id,
        "b" * 64,
    )

    request = SimpleNamespace(
        project_id="308131",
        approved_inputs=(first, second),
        approved_engineering_information=None,
        project_authority_handoff=None,
        project_fit_handoff=SimpleNamespace(
            approved_engineering_information_sets=(
                first_aei,
                second_aei,
            )
        ),
    )

    monkeypatch.setattr(
        module,
        "validate_project_fit_phase_h_request",
        lambda request: None,
    )
    monkeypatch.setattr(
        module,
        "validate_approved_engineering_information_binding",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        module,
        "phase_h_subject_key",
        lambda request, item: (
            "project_subject:"
            f"{item.source_id.lower()}:"
            f"{item.stable_subject_key}"
        ),
    )

    deriver = object.__new__(
        ApprovedEngineeringInformationDeriver
    )

    views = deriver._project_fit_relationship_views(
        request
    )

    assert tuple(item.source_id for item in views) == (
        "SRC-000001",
        "SRC-000002",
    )

    assert views[0].content_fingerprint == "a" * 64
    assert views[1].content_fingerprint == "b" * 64

    assert views[0].subjects[0].stable_subject_key == (
        "project_subject:src-000001:shared.subject"
    )
    assert views[1].subjects[0].stable_subject_key == (
        "project_subject:src-000002:shared.subject"
    )


class _Base:
    def derive(self, request):
        return ModelCandidateDerivationPlan()


def test_project_fit_relationships_keep_per_source_aei_fingerprint(
    monkeypatch,
):
    deriver = ApprovedEngineeringInformationDeriver(
        base_deriver=_Base(),
        profile=object(),
    )

    request = SimpleNamespace(
        project_fit_handoff=object(),
        project_authority_handoff=None,
        approved_engineering_information=None,
    )

    views = (
        SimpleNamespace(
            source_id="SRC-000001",
            relationships=(object(),),
            content_fingerprint="a" * 64,
        ),
        SimpleNamespace(
            source_id="SRC-000002",
            relationships=(object(),),
            content_fingerprint="b" * 64,
        ),
    )

    monkeypatch.setattr(
        module,
        "validate_project_fit_phase_h_request",
        lambda request: None,
    )
    monkeypatch.setattr(
        deriver,
        "_project_fit_relationship_views",
        lambda request: views,
    )
    monkeypatch.setattr(
        deriver,
        "_relationship_projection_entries",
        lambda authority: (
            SimpleNamespace(
                approved_input_id=(
                    f"REL-{authority.source_id[-1]}"
                ),
                disposition="mapped",
                selected_rule_id="RULE-1",
            ),
        ),
    )

    calls = []

    def drafts(**kwargs):
        calls.append(
            (
                kwargs["authority"].source_id,
                kwargs["authority"].content_fingerprint,
                kwargs["authority_evidence_key"],
                kwargs["draft_prefix"],
            )
        )
        return (
            SimpleNamespace(
                draft_key=(
                    kwargs["draft_prefix"] + "REL"
                )
            ),
        )

    monkeypatch.setattr(
        deriver,
        "_relationship_drafts",
        drafts,
    )

    plan = deriver.derive(request)

    assert len(plan.relationship_drafts) == 2

    assert calls == [
        (
            "SRC-000001",
            "a" * 64,
            "approved_engineering_information_fingerprint",
            "relationship:source:src-000001:aaaaaaaaaaaa:",
        ),
        (
            "SRC-000002",
            "b" * 64,
            "approved_engineering_information_fingerprint",
            "relationship:source:src-000002:bbbbbbbbbbbb:",
        ),
    ]
