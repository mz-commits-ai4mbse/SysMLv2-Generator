"""Derived Approved Engineering Information authority for R4c."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION = "1.0.0"

_ACCEPTED_REVIEW_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)


@dataclass(frozen=True, slots=True)
class ApprovedEngineeringSubject:
    canonical_subject_id: str
    approved_input_id: str
    stable_subject_key: str
    title: str
    engineering_statement: str
    information_type: str | None
    statement_modality: str | None
    epistemic_class: str | None
    review_item_id: str
    review_item_fingerprint: str
    approved_input_fingerprint: str


@dataclass(frozen=True, slots=True)
class ApprovedEngineeringRelationship:
    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    relationship_decision_id: str
    relationship_decision_fingerprint: str
    rationale: str | None


@dataclass(frozen=True, slots=True)
class ApprovedEngineeringInformationSet:
    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    subjects: tuple[ApprovedEngineeringSubject, ...]
    relationships: tuple[ApprovedEngineeringRelationship, ...]
    relationship_decision_authority_fingerprint: str
    content_fingerprint: str
    non_promotable_subject_ids: tuple[str, ...] = ()
    non_projectable_relationship_decision_ids: tuple[str, ...] = ()


def build_approved_engineering_information(
    *,
    workspace_view,
    subject_review_payload: dict,
    relationship_decisions,
    relationship_decision_authority_fingerprint: str,
) -> ApprovedEngineeringInformationSet:
    """Compose finalized Subject Approved Inputs + accepted semantic relations."""

    if workspace_view.version.version_state != "finalized":
        raise ValueError(
            "Approved Engineering Information requires finalized Review."
        )

    canonical_ids = tuple(
        subject_review_payload.get("canonical_subject_ids", ())
    )
    cards = {
        card["canonical_subject_id"]: card
        for card in subject_review_payload.get("cards", ())
    }
    if tuple(cards) != canonical_ids:
        raise ValueError("Subject Review authority population is invalid.")

    review_items = {}
    for item in workspace_view.revision.review_items:
        subject_id = _subject_id_from_locator(
            item.original_report_locator
        )
        if subject_id is not None:
            review_items[subject_id] = item

    active_manifests = {}
    for snapshot in workspace_view.approved_input_authority:
        if snapshot.authority_state != "active":
            continue
        manifest = snapshot.manifest
        if (
            manifest.review_document_version_id
            != workspace_view.version.review_document_version_id
        ):
            continue
        active_manifests[manifest.stable_subject_key] = manifest

    subjects = []
    non_promotable_subject_ids = []
    for subject_id in canonical_ids:
        item = review_items.get(subject_id)
        if item is None:
            raise ValueError(
                "Finalized Subject Review Item is unavailable."
            )
        if item.effective_review_outcome not in _ACCEPTED_REVIEW_OUTCOMES:
            continue

        manifest = active_manifests.get(item.stable_subject_key)
        if manifest is None:
            if item.review_item_kind == "open_question":
                non_promotable_subject_ids.append(subject_id)
                continue
            raise ValueError(
                "Approved Input promotion is incomplete for accepted "
                f"Subject {subject_id}."
            )

        content = manifest.canonical_content
        subjects.append(
            ApprovedEngineeringSubject(
                canonical_subject_id=subject_id,
                approved_input_id=manifest.approved_input_id,
                stable_subject_key=manifest.stable_subject_key,
                title=content.title,
                engineering_statement=content.primary_text,
                information_type=content.information_type,
                statement_modality=content.modality,
                epistemic_class=content.epistemic_status,
                review_item_id=manifest.review_item_id,
                review_item_fingerprint=manifest.review_item_fingerprint,
                approved_input_fingerprint=(
                    manifest.content_fingerprint
                ),
            )
        )

    approved_subject_ids = {
        item.canonical_subject_id
        for item in subjects
    }
    non_promotable_subject_ids = tuple(
        sorted(set(non_promotable_subject_ids))
    )
    non_promotable_subject_id_set = set(non_promotable_subject_ids)

    relationships = []
    non_projectable_relationship_decision_ids = []
    for decision in relationship_decisions:
        if decision.outcome != "accepted":
            continue
        if (
            decision.source_subject_id not in approved_subject_ids
            or decision.target_subject_id not in approved_subject_ids
        ):
            outside = {
                subject_id
                for subject_id in (
                    decision.source_subject_id,
                    decision.target_subject_id,
                )
                if subject_id not in approved_subject_ids
            }
            if outside <= non_promotable_subject_id_set:
                non_projectable_relationship_decision_ids.append(
                    decision.decision_id
                )
                continue
            raise ValueError(
                "Accepted relationship does not bind two approved or "
                "explicitly non-promotable Subjects."
            )
        relationships.append(
            ApprovedEngineeringRelationship(
                source_subject_id=decision.source_subject_id,
                relationship_kind=decision.relationship_kind,
                target_subject_id=decision.target_subject_id,
                relationship_decision_id=decision.decision_id,
                relationship_decision_fingerprint=(
                    decision.content_fingerprint
                ),
                rationale=decision.rationale,
            )
        )

    body = {
        "schema_version": (
            APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION
        ),
        "project_id": workspace_view.project_id,
        "review_document_id": (
            workspace_view.document.review_document_id
        ),
        "review_document_version_id": (
            workspace_view.version.review_document_version_id
        ),
        "review_revision_id": (
            workspace_view.revision.review_revision_id
        ),
        "subjects": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "approved_input_id": item.approved_input_id,
                "stable_subject_key": item.stable_subject_key,
                "title": item.title,
                "engineering_statement": item.engineering_statement,
                "information_type": item.information_type,
                "statement_modality": item.statement_modality,
                "epistemic_class": item.epistemic_class,
                "review_item_id": item.review_item_id,
                "review_item_fingerprint": item.review_item_fingerprint,
                "approved_input_fingerprint": (
                    item.approved_input_fingerprint
                ),
            }
            for item in subjects
        ],
        "relationships": [
            {
                "source_subject_id": item.source_subject_id,
                "relationship_kind": item.relationship_kind,
                "target_subject_id": item.target_subject_id,
                "relationship_decision_id": (
                    item.relationship_decision_id
                ),
                "relationship_decision_fingerprint": (
                    item.relationship_decision_fingerprint
                ),
                "rationale": item.rationale,
            }
            for item in relationships
        ],
        "non_promotable_subject_ids": list(
            non_promotable_subject_ids
        ),
        "non_projectable_relationship_decision_ids": sorted(
            set(non_projectable_relationship_decision_ids)
        ),
        "relationship_decision_authority_fingerprint": (
            relationship_decision_authority_fingerprint
        ),
    }
    content_fingerprint = _canonical_sha256(body)

    return ApprovedEngineeringInformationSet(
        schema_version=APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION,
        project_id=workspace_view.project_id,
        review_document_id=workspace_view.document.review_document_id,
        review_document_version_id=(
            workspace_view.version.review_document_version_id
        ),
        review_revision_id=workspace_view.revision.review_revision_id,
        subjects=tuple(subjects),
        relationships=tuple(
            sorted(
                relationships,
                key=lambda item: (
                    item.source_subject_id,
                    item.relationship_kind,
                    item.target_subject_id,
                ),
            )
        ),
        relationship_decision_authority_fingerprint=(
            relationship_decision_authority_fingerprint
        ),
        content_fingerprint=content_fingerprint,
        non_promotable_subject_ids=non_promotable_subject_ids,
        non_projectable_relationship_decision_ids=tuple(
            sorted(set(non_projectable_relationship_decision_ids))
        ),
    )


def _subject_id_from_locator(locator: str) -> str | None:
    prefix = "subject_review:"
    if not isinstance(locator, str) or not locator.startswith(prefix):
        return None
    value = locator[len(prefix):]
    return value if value.startswith("SUBJ-") else None


def _canonical_sha256(value) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
