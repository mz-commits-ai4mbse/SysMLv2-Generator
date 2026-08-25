from __future__ import annotations

import hashlib
import json

from modules.internal_model.authority_backed import (
    build_authority_backed_internal_model,
)
from modules.internal_model.semantic_successor import (
    build_sem015_internal_model_successor,
)
from tests.test_authority_backed_internal_model import (
    _draft,
    _final,
    _profile,
    _template,
)


def _fp(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _source():
    return build_authority_backed_internal_model(
        draft=_draft(),
        final_decision=_final(),
        profile=_profile(),
        framework_template=_template(),
        internal_engineering_model_id="IEM-000001",
        created_at="2026-08-25T10:00:00Z",
    )


def _decision(payload):
    return {**payload, "content_fingerprint": _fp(payload)}


def _tfa(source, *, omit_relationship=False):
    decisions = [
        _decision(
            {
                "schema_version": "1.0.0",
                "project_id": source.project_id,
                "decision_id": "TFD-000001",
                "review_id": "TFR-000001",
                "review_fingerprint": "a" * 64,
                "subject_kind": "element",
                "authority_subject_id": "IME-000001",
                "review_item_fingerprint": "b" * 64,
                "selected_candidate_id": "TFC-000001",
                "selected_candidate_fingerprint": "c" * 64,
                "selected_relevance_outcome": "materialize_formally",
                "selected_target_model_pattern_id": "action_usage",
                "selected_target_notation_construct_id": "TN_006",
                "selected_formulation_text": None,
                "reviewer_identity": "MZ",
                "rationale": "Accepted.",
                "decided_at": "2026-08-25T10:01:00Z",
                "supersedes_decision_id": None,
            }
        )
    ]
    if omit_relationship:
        decisions.append(
            _decision(
                {
                    "schema_version": "1.0.0",
                    "project_id": source.project_id,
                    "decision_id": "TFD-000002",
                    "review_id": "TFR-000001",
                    "review_fingerprint": "a" * 64,
                    "subject_kind": "relationship",
                    "authority_subject_id": "IMR-000001",
                    "review_item_fingerprint": "d" * 64,
                    "selected_candidate_id": "TFC-000002",
                    "selected_candidate_fingerprint": "e" * 64,
                    "selected_relevance_outcome": (
                        "intentionally_not_materialized"
                    ),
                    "selected_target_model_pattern_id": None,
                    "selected_target_notation_construct_id": None,
                    "selected_formulation_text": None,
                    "reviewer_identity": "MZ",
                    "rationale": "No faithful formal notation.",
                    "decided_at": "2026-08-25T10:02:00Z",
                    "supersedes_decision_id": None,
                }
            )
        )
    body = {
        "schema_version": "1.0.0",
        "project_id": source.project_id,
        "authority_set_id": "TFA-000001",
        "review_id": "TFR-000001",
        "review_fingerprint": "a" * 64,
        "source_internal_engineering_model_id": (
            source.internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            source.content_fingerprint
        ),
        "effective_decisions": decisions,
        "created_at": "2026-08-25T10:03:00Z",
    }
    return {**body, "content_fingerprint": _fp(body)}


def _mqa(source):
    decisions = []
    for number, element in enumerate(source.elements, start=1):
        body = {
            "schema_version": "1.0.0",
            "project_id": source.project_id,
            "decision_id": f"MQD-{number:06d}",
            "review_id": "MQR-000001",
            "review_fingerprint": "f" * 64,
            "internal_model_element_id": element.internal_model_element_id,
            "proposal_fingerprint": str(number) * 64,
            "decision": "approved",
            "approved_name": f"Refined {number}",
            "approved_description": f"Refined description {number}.",
            "reviewer_identity": "MZ",
            "rationale": "Meaning preserved.",
            "decided_at": "2026-08-25T10:04:00Z",
            "supersedes_decision_id": None,
        }
        decisions.append(_decision(body))
    body = {
        "schema_version": "1.0.0",
        "project_id": source.project_id,
        "authority_set_id": "MQA-000001",
        "review_id": "MQR-000001",
        "review_fingerprint": "f" * 64,
        "source_internal_engineering_model_id": (
            source.internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            source.content_fingerprint
        ),
        "effective_decisions": decisions,
        "created_at": "2026-08-25T10:05:00Z",
    }
    return {**body, "content_fingerprint": _fp(body)}


def test_successor_applies_only_human_authorized_quality_wording():
    source = _source()
    result = build_sem015_internal_model_successor(
        source=source,
        target_model_formulation_authority=_tfa(source),
        model_quality_authority=_mqa(source),
        internal_engineering_model_id="IEM-000002",
        created_at="2026-08-25T10:06:00Z",
    )

    assert result.snapshot.schema_version == "2.1.0"
    assert result.snapshot.source_internal_engineering_model_id == "IEM-000001"
    assert [item.name for item in result.snapshot.elements] == [
        "Refined 1",
        "Refined 2",
    ]
    assert len(result.snapshot.relationships) == 1
    assert result.snapshot.relationships[0].semantic_intent == "dependency"


def test_intentionally_not_materialized_relationship_is_removed_formally_but_audited():
    source = _source()
    result = build_sem015_internal_model_successor(
        source=source,
        target_model_formulation_authority=_tfa(
            source,
            omit_relationship=True,
        ),
        model_quality_authority=_mqa(source),
        internal_engineering_model_id="IEM-000002",
        created_at="2026-08-25T10:06:00Z",
    )

    assert result.snapshot.relationships == ()
    binding = result.authority_manifest["authority_binding"]
    assert binding[
        "intentionally_not_materialized_relationship_ids"
    ] == ["IMR-000001"]
    assert (
        result.snapshot.semantic_successor_authority_fingerprint
        == result.authority_manifest["authority_binding_fingerprint"]
    )


def test_source_iem_remains_unchanged():
    source = _source()
    before = source.content_fingerprint
    build_sem015_internal_model_successor(
        source=source,
        target_model_formulation_authority=_tfa(source),
        model_quality_authority=_mqa(source),
        internal_engineering_model_id="IEM-000002",
        created_at="2026-08-25T10:06:00Z",
    )
    assert source.content_fingerprint == before
    assert source.internal_engineering_model_id == "IEM-000001"
