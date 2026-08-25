"""Reference-grounded Target-Model Formulation review builder."""

from __future__ import annotations

import hashlib
import json
import re

from .errors import TargetModelFormulationError
from .types import (
    REFERENCE_EVIDENCE_ROLES,
    TARGET_MODEL_RELEVANCE_OUTCOMES,
    TARGET_MODEL_SUBJECT_KINDS,
    TargetModelFormulationCandidate,
    TargetModelFormulationReview,
    TargetModelFormulationReviewItem,
    TargetModelReferenceEvidence,
)


TARGET_MODEL_FORMULATION_REVIEW_SCHEMA_VERSION = "1.0.0"

_REVIEW_ID = re.compile(r"^TFR-[0-9]{6}$")
_CANDIDATE_ID = re.compile(r"^TFC-[0-9]{6}$")
_IEM_ID = re.compile(r"^IEM-[0-9]{6}$")
_FAD_ID = re.compile(r"^FAD-[0-9]{6}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

PRIMARY_SYNTAX_SOURCE_ID = "SRC_SYSML_V2_RELEASE"
APOLLO_REFERENCE_SOURCE_ID = "SRC_APOLLO11_SYSML_V2"
TURING_MODEL_REFERENCE_SOURCE_ID = "SRC_TURING_ARCHITECTURE_MODEL"

PRIMARY_SYNTAX_ROLE = "primary_language_and_syntax_reference"
VALIDATED_FIXTURE_ROLE = "validated_syntax_fixture"
NON_NORMATIVE_PATTERN_ROLE = "non_normative_modeling_pattern_reference"
PROJECT_MODEL_CONTEXT_ROLE = "project_modeling_context_reference"


def create_reference_evidence(
    *,
    source_id: str,
    role: str,
    locator: str,
    evidence_note: str,
) -> TargetModelReferenceEvidence:
    """Create one immutable reference with strict authority-role separation."""

    sid = _text(source_id, "source_id")
    selected_role = _text(role, "role")
    if selected_role not in REFERENCE_EVIDENCE_ROLES:
        raise TargetModelFormulationError("Unsupported reference evidence role.")

    location = _text(locator, "locator")
    note = _text(evidence_note, "evidence_note")

    if sid == APOLLO_REFERENCE_SOURCE_ID and selected_role != NON_NORMATIVE_PATTERN_ROLE:
        raise TargetModelFormulationError(
            "Apollo reference evidence is non-normative modeling-pattern evidence only."
        )

    if sid == PRIMARY_SYNTAX_SOURCE_ID and selected_role != PRIMARY_SYNTAX_ROLE:
        raise TargetModelFormulationError(
            "The local SysML v2 release repository must retain primary syntax authority."
        )
    if selected_role == PRIMARY_SYNTAX_ROLE and sid != PRIMARY_SYNTAX_SOURCE_ID:
        raise TargetModelFormulationError(
            "Primary SysML v2 syntax authority may only be the registered release repository."
        )
    if (
        selected_role == NON_NORMATIVE_PATTERN_ROLE
        and sid == PRIMARY_SYNTAX_SOURCE_ID
    ):
        raise TargetModelFormulationError(
            "The SysML v2 release repository must not be downgraded to example-pattern authority."
        )

    if (
        sid == TURING_MODEL_REFERENCE_SOURCE_ID
        and selected_role != PROJECT_MODEL_CONTEXT_ROLE
    ):
        raise TargetModelFormulationError(
            "The Turing architecture model is project modeling context, not syntax authority."
        )

    body = {
        "source_id": sid,
        "role": selected_role,
        "locator": location,
        "evidence_note": note,
    }
    return TargetModelReferenceEvidence(
        **body,
        content_fingerprint=_fingerprint(body),
    )


def create_formulation_candidate(
    *,
    candidate_id: str,
    relevance_outcome: str,
    target_model_pattern_id: str | None,
    target_notation_construct_id: str | None,
    formulation_text: str | None,
    applied_formulation_rule_ids: tuple[str, ...] = (),
    reference_evidence: tuple[TargetModelReferenceEvidence, ...],
    rationale: str,
    unresolved_questions: tuple[str, ...] = (),
) -> TargetModelFormulationCandidate:
    """Create one candidate without conflating reference roles or authority."""

    if _CANDIDATE_ID.fullmatch(candidate_id) is None:
        raise TargetModelFormulationError("Target-Model candidate ID is invalid.")
    if relevance_outcome not in TARGET_MODEL_RELEVANCE_OUTCOMES:
        raise TargetModelFormulationError("Target-Model relevance outcome is invalid.")

    references = tuple(reference_evidence)
    if not references:
        raise TargetModelFormulationError(
            "Target-Model formulation candidates require reference evidence."
        )
    _validate_reference_uniqueness(references)

    rules = tuple(
        _text(item, "formulation rule ID")
        for item in applied_formulation_rule_ids
    )
    if len(set(rules)) != len(rules):
        raise TargetModelFormulationError(
            "Applied formulation rule IDs must be unique."
        )

    questions = tuple(
        _text(item, "unresolved question")
        for item in unresolved_questions
    )
    reason = _text(rationale, "rationale")

    pattern = _optional_text(target_model_pattern_id, "target_model_pattern_id")
    notation = _optional_text(
        target_notation_construct_id,
        "target_notation_construct_id",
    )
    text = _optional_text(formulation_text, "formulation_text")

    roles = {item.role for item in references}

    if relevance_outcome == "materialize_formally":
        if pattern is None:
            raise TargetModelFormulationError(
                "Formal materialization requires an explicit Target-Model pattern."
            )
        if notation is None:
            raise TargetModelFormulationError(
                "Formal materialization requires an explicit Target Notation construct."
            )
        if PRIMARY_SYNTAX_ROLE not in roles:
            raise TargetModelFormulationError(
                "Formal materialization requires primary SysML v2 release/spec evidence."
            )
        if VALIDATED_FIXTURE_ROLE not in roles:
            raise TargetModelFormulationError(
                "Formal materialization requires validated syntax-fixture evidence."
            )
    else:
        if pattern is not None or notation is not None:
            raise TargetModelFormulationError(
                "Non-materializing outcomes must not claim a formal Target-Model pattern "
                "or Target Notation construct."
            )

    if relevance_outcome == "unresolved_human_review" and not questions:
        raise TargetModelFormulationError(
            "Unresolved Human Review candidates require explicit unresolved questions."
        )

    body = {
        "candidate_id": candidate_id,
        "relevance_outcome": relevance_outcome,
        "target_model_pattern_id": pattern,
        "target_notation_construct_id": notation,
        "formulation_text": text,
        "applied_formulation_rule_ids": list(rules),
        "reference_evidence": [_reference_payload(item) for item in references],
        "rationale": reason,
        "unresolved_questions": list(questions),
    }
    return TargetModelFormulationCandidate(
        candidate_id=candidate_id,
        relevance_outcome=relevance_outcome,
        target_model_pattern_id=pattern,
        target_notation_construct_id=notation,
        formulation_text=text,
        applied_formulation_rule_ids=rules,
        reference_evidence=references,
        rationale=reason,
        unresolved_questions=questions,
        content_fingerprint=_fingerprint(body),
    )


def create_review_item(
    *,
    subject_kind: str,
    authority_subject_id: str,
    current_engineering_type: str,
    current_target_representation: str,
    candidates: tuple[TargetModelFormulationCandidate, ...],
) -> TargetModelFormulationReviewItem:
    """Bind candidate proposals to one exact current authority subject."""

    if subject_kind not in TARGET_MODEL_SUBJECT_KINDS:
        raise TargetModelFormulationError("Target-Model subject kind is invalid.")
    subject_id = _text(authority_subject_id, "authority_subject_id")
    engineering_type = _text(current_engineering_type, "current_engineering_type")
    representation = _text(
        current_target_representation,
        "current_target_representation",
    )
    options = tuple(candidates)
    if not options:
        raise TargetModelFormulationError(
            "Target-Model review items require at least one candidate."
        )
    ids = tuple(item.candidate_id for item in options)
    if len(set(ids)) != len(ids):
        raise TargetModelFormulationError(
            "Target-Model candidate IDs must be unique within a review item."
        )

    body = {
        "subject_kind": subject_kind,
        "authority_subject_id": subject_id,
        "current_engineering_type": engineering_type,
        "current_target_representation": representation,
        "candidates": [_candidate_payload(item) for item in options],
    }
    return TargetModelFormulationReviewItem(
        subject_kind=subject_kind,
        authority_subject_id=subject_id,
        current_engineering_type=engineering_type,
        current_target_representation=representation,
        candidates=options,
        content_fingerprint=_fingerprint(body),
    )


def create_formulation_review(
    *,
    project_id: str,
    review_id: str,
    source_internal_engineering_model_id: str,
    source_internal_engineering_model_fingerprint: str,
    final_model_review_decision_id: str,
    final_model_review_decision_fingerprint: str,
    target_model_profile_id: str,
    target_model_profile_version: str,
    target_model_profile_fingerprint: str,
    target_notation_fingerprint: str,
    items: tuple[TargetModelFormulationReviewItem, ...],
    created_at: str,
) -> TargetModelFormulationReview:
    """Create one immutable review snapshot over exact existing C6 authority."""

    pid = _text(project_id, "project_id")
    if _REVIEW_ID.fullmatch(review_id) is None:
        raise TargetModelFormulationError(
            "Target-Model formulation review ID is invalid."
        )
    if _IEM_ID.fullmatch(source_internal_engineering_model_id) is None:
        raise TargetModelFormulationError("Source Internal Model ID is invalid.")
    if _FAD_ID.fullmatch(final_model_review_decision_id) is None:
        raise TargetModelFormulationError("Final Model Review decision ID is invalid.")

    source_iem_fp = _sha256(
        source_internal_engineering_model_fingerprint,
        "source Internal Model fingerprint",
    )
    fad_fp = _sha256(
        final_model_review_decision_fingerprint,
        "Final Model Review fingerprint",
    )
    profile_fp = _sha256(
        target_model_profile_fingerprint,
        "Target-Model profile fingerprint",
    )
    notation_fp = _sha256(
        target_notation_fingerprint,
        "Target Notation fingerprint",
    )

    profile_id = _text(target_model_profile_id, "target_model_profile_id")
    profile_version = _text(
        target_model_profile_version,
        "target_model_profile_version",
    )
    timestamp = _text(created_at, "created_at")

    review_items = tuple(items)
    if not review_items:
        raise TargetModelFormulationError(
            "Target-Model formulation review requires at least one review item."
        )
    subject_keys = tuple(
        (item.subject_kind, item.authority_subject_id)
        for item in review_items
    )
    if len(set(subject_keys)) != len(subject_keys):
        raise TargetModelFormulationError(
            "Target-Model formulation review subjects must be unique."
        )

    body = {
        "schema_version": TARGET_MODEL_FORMULATION_REVIEW_SCHEMA_VERSION,
        "project_id": pid,
        "review_id": review_id,
        "source_internal_engineering_model_id": source_internal_engineering_model_id,
        "source_internal_engineering_model_fingerprint": source_iem_fp,
        "final_model_review_decision_id": final_model_review_decision_id,
        "final_model_review_decision_fingerprint": fad_fp,
        "target_model_profile_id": profile_id,
        "target_model_profile_version": profile_version,
        "target_model_profile_fingerprint": profile_fp,
        "target_notation_fingerprint": notation_fp,
        "items": [_review_item_payload(item) for item in review_items],
        "created_at": timestamp,
    }
    return TargetModelFormulationReview(
        schema_version=body["schema_version"],
        project_id=pid,
        review_id=review_id,
        source_internal_engineering_model_id=source_internal_engineering_model_id,
        source_internal_engineering_model_fingerprint=source_iem_fp,
        final_model_review_decision_id=final_model_review_decision_id,
        final_model_review_decision_fingerprint=fad_fp,
        target_model_profile_id=profile_id,
        target_model_profile_version=profile_version,
        target_model_profile_fingerprint=profile_fp,
        target_notation_fingerprint=notation_fp,
        items=review_items,
        created_at=timestamp,
        content_fingerprint=_fingerprint(body),
    )


def _validate_reference_uniqueness(
    references: tuple[TargetModelReferenceEvidence, ...],
) -> None:
    keys = tuple(
        (item.source_id, item.role, item.locator)
        for item in references
    )
    if len(set(keys)) != len(keys):
        raise TargetModelFormulationError(
            "Duplicate Target-Model reference evidence is not allowed."
        )


def _reference_payload(value: TargetModelReferenceEvidence) -> dict:
    return {
        "source_id": value.source_id,
        "role": value.role,
        "locator": value.locator,
        "evidence_note": value.evidence_note,
        "content_fingerprint": value.content_fingerprint,
    }


def _candidate_payload(value: TargetModelFormulationCandidate) -> dict:
    return {
        "candidate_id": value.candidate_id,
        "relevance_outcome": value.relevance_outcome,
        "target_model_pattern_id": value.target_model_pattern_id,
        "target_notation_construct_id": value.target_notation_construct_id,
        "formulation_text": value.formulation_text,
        "applied_formulation_rule_ids": list(value.applied_formulation_rule_ids),
        "reference_evidence": [
            _reference_payload(item)
            for item in value.reference_evidence
        ],
        "rationale": value.rationale,
        "unresolved_questions": list(value.unresolved_questions),
        "content_fingerprint": value.content_fingerprint,
    }


def _review_item_payload(value: TargetModelFormulationReviewItem) -> dict:
    return {
        "subject_kind": value.subject_kind,
        "authority_subject_id": value.authority_subject_id,
        "current_engineering_type": value.current_engineering_type,
        "current_target_representation": value.current_target_representation,
        "candidates": [_candidate_payload(item) for item in value.candidates],
        "content_fingerprint": value.content_fingerprint,
    }


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TargetModelFormulationError(f"{label} is required.")
    return value.strip()


def _optional_text(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise TargetModelFormulationError(
            f"{label} must be a SHA-256 fingerprint."
        )
    return value


def _fingerprint(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
