"""Resolve published R4c Subject Review artifacts from one Processing Attempt."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from modules.project_processing import ProcessingArtifactReference
from modules.project_processing.types import ProcessingRunHistory

from modules.subject_review.artifacts import (
    CANONICAL_SUBJECT_SET_FILENAME,
    SUBJECT_CONSENSUS_FILENAME,
    SUBJECT_INTERPRETATIONS_FILENAME,
    SUBJECT_PROCESSING_ARTIFACT_SCHEMA_VERSION,
    SUBJECT_REVIEW_BUNDLE_FILENAME,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)


@dataclass(frozen=True, slots=True)
class SubjectReviewPublishedArtifacts:
    """Published artifact chain required by Subject-centric Human Review."""

    primary_review_report: ProcessingArtifactReference
    canonical_subject_set: ProcessingArtifactReference
    subject_interpretations: ProcessingArtifactReference
    subject_consensus: ProcessingArtifactReference
    subject_review_bundle: ProcessingArtifactReference
    attempt_id: str


def select_subject_review_artifacts(
    history: ProcessingRunHistory,
) -> SubjectReviewPublishedArtifacts | None:
    """Select exactly one complete R4c artifact chain from the latest Attempt."""

    events = getattr(history, "events", None)
    if events is None:
        return None

    attempt_id = _latest_attempt_id(history)
    if attempt_id is None:
        return None

    by_name = {
        CANONICAL_SUBJECT_SET_FILENAME: [],
        SUBJECT_INTERPRETATIONS_FILENAME: [],
        SUBJECT_CONSENSUS_FILENAME: [],
        SUBJECT_REVIEW_BUNDLE_FILENAME: [],
        "ingestion_review_report.md": [],
    }

    for event in events:
        if (
            event.event_type != "artifact_published"
            or event.attempt_id != attempt_id
        ):
            continue

        for reference in event.artifact_references:
            name = Path(reference.repository_relative_path).name
            if name in by_name:
                by_name[name].append(reference)

    if not by_name[SUBJECT_REVIEW_BUNDLE_FILENAME]:
        return None

    for filename, references in by_name.items():
        if len(references) != 1:
            raise ReviewIntegrityError(
                "Latest Subject Review Attempt must publish exactly one "
                f"{filename} artifact."
            )

    return SubjectReviewPublishedArtifacts(
        primary_review_report=by_name["ingestion_review_report.md"][0],
        canonical_subject_set=by_name[
            CANONICAL_SUBJECT_SET_FILENAME
        ][0],
        subject_interpretations=by_name[
            SUBJECT_INTERPRETATIONS_FILENAME
        ][0],
        subject_consensus=by_name[SUBJECT_CONSENSUS_FILENAME][0],
        subject_review_bundle=by_name[SUBJECT_REVIEW_BUNDLE_FILENAME][0],
        attempt_id=attempt_id,
    )


def load_subject_review_bundle_payload(
    artifacts: SubjectReviewPublishedArtifacts,
    *,
    history: ProcessingRunHistory,
    repository_root: Path | str,
) -> dict:
    """Load and integrity-check the exact published Subject Review bundle."""

    if not isinstance(artifacts, SubjectReviewPublishedArtifacts):
        raise ReviewValidationError(
            "artifacts must be SubjectReviewPublishedArtifacts."
        )

    envelope = _load_published_json(
        artifacts.subject_review_bundle,
        repository_root=Path(repository_root),
    )

    if (
        envelope.get("schema_version")
        != SUBJECT_PROCESSING_ARTIFACT_SCHEMA_VERSION
        or envelope.get("artifact_kind") != "subject_review_bundle"
    ):
        raise ReviewIntegrityError(
            "Published Subject Review Bundle schema/kind is invalid."
        )

    manifest = history.manifest
    authority = envelope.get("authority")
    if not isinstance(authority, dict):
        raise ReviewIntegrityError(
            "Published Subject Review Bundle lacks authority binding."
        )

    expected = {
        "project_id": manifest.project_id,
        "source_id": manifest.source_id,
        "source_sha256": manifest.source_sha256,
        "processing_run_id": manifest.processing_run_id,
        "attempt_id": artifacts.attempt_id,
    }
    for field_name, expected_value in expected.items():
        if authority.get(field_name) != expected_value:
            raise ReviewIntegrityError(
                "Published Subject Review Bundle does not bind current "
                f"Processing authority: {field_name}."
            )

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise ReviewIntegrityError(
            "Published Subject Review Bundle payload is invalid."
        )

    if (
        payload.get("project_id") != manifest.project_id
        or payload.get("source_id") != manifest.source_id
    ):
        raise ReviewIntegrityError(
            "Subject Review Bundle payload does not bind the Processing Source."
        )

    if payload.get("human_review_required") is not True:
        raise ReviewIntegrityError(
            "Subject Review Bundle must require Human Engineering Review."
        )

    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        raise ReviewReferenceError(
            "Subject Review Bundle contains no Human Review cards."
        )

    return payload


def _load_published_json(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
) -> dict:
    path = repository_root / reference.repository_relative_path
    try:
        resolved = path.resolve()
        root = repository_root.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ReviewReferenceError(
            "Published Subject Review artifact escaped repository authority."
        ) from exc

    if not resolved.exists() or not resolved.is_file():
        raise ReviewReferenceError(
            "Published Subject Review artifact is unavailable."
        )

    try:
        content = resolved.read_bytes()
    except OSError as exc:
        raise ReviewReferenceError(
            "Published Subject Review artifact could not be read."
        ) from exc

    if sha256(content).hexdigest() != reference.content_fingerprint:
        raise ReviewIntegrityError(
            "Published Subject Review artifact fingerprint mismatch."
        )

    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewIntegrityError(
            "Published Subject Review artifact is not valid UTF-8 JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ReviewIntegrityError(
            "Published Subject Review artifact root must be a JSON object."
        )

    body = {
        key: value
        for key, value in payload.items()
        if key != "content_fingerprint"
    }
    expected_fingerprint = sha256(
        json.dumps(
            body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    if payload.get("content_fingerprint") != expected_fingerprint:
        raise ReviewIntegrityError(
            "Subject Review artifact internal fingerprint mismatch."
        )

    return payload



_OPEN_SUBJECT_INFORMATION_TYPES = frozenset(
    {
        "open_question",
        "gap",
        "ambiguity",
        "risk",
    }
)


@dataclass(frozen=True, slots=True)
class SubjectReviewInitialReviewAssembly:
    """Initial Review Workspace assembled from persisted R4c authority."""

    review_document: object
    review_document_version: object
    initial_revision: object

    @property
    def repository_bundle(self):
        return (
            self.review_document,
            self.review_document_version,
            self.initial_revision,
        )


def load_subject_review_consensus_filter_facts(
    artifacts: SubjectReviewPublishedArtifacts,
    *,
    history: ProcessingRunHistory,
    repository_root: Path | str,
):
    """Build exact G6 filter facts from persisted Subject Review cards."""

    from .scoped_workflow import ReviewConsensusFilterFact

    payload = load_subject_review_bundle_payload(
        artifacts,
        history=history,
        repository_root=repository_root,
    )
    reference = artifacts.subject_review_bundle

    facts = []
    for card in payload["cards"]:
        fields = (
            card["information_type"],
            card["statement_modality"],
            card["epistemic_class"],
        )
        confidences = {
            field["confidence"]
            for field in fields
        }
        if "low" in confidences:
            agreement = "conflict"
        elif "medium" in confidences:
            agreement = "majority_with_disagreement"
        else:
            agreement = "unanimous"

        facts.append(
            ReviewConsensusFilterFact(
                artifact_id=reference.artifact_id,
                evidence_locator=(
                    f"/cards/{card['canonical_subject_id']}/consensus"
                ),
                evidence_content_fingerprint=card["content_fingerprint"],
                agreement_level=agreement,
                review_required=True,
            )
        )

    if not facts:
        raise ReviewReferenceError(
            "Subject Review Bundle contains no consensus filter facts."
        )
    return tuple(facts)


def assemble_subject_review_initial_review(
    *,
    history: ProcessingRunHistory,
    source_manifest,
    project_manifest,
    artifacts: SubjectReviewPublishedArtifacts,
    repository_root: Path | str,
    review_document_id: str,
    review_document_version_id: str,
    review_revision_id: str,
    opened_by: str,
    timestamp: str,
    occupied_review_item_ids: tuple[str, ...],
) -> SubjectReviewInitialReviewAssembly:
    """Create one initial Review Workspace from persisted canonical SUBJ-* cards."""

    from .document_manifest import create_review_document
    from .identifiers import next_review_item_id
    from .item_manifest import create_review_item
    from .revision_manifest import create_review_revision
    from .types import ReviewEvidenceReference, ReviewItemContent
    from .version_manifest import create_review_document_version

    payload = load_subject_review_bundle_payload(
        artifacts,
        history=history,
        repository_root=repository_root,
    )
    manifest = history.manifest

    if (
        source_manifest.source_id != manifest.source_id
        or source_manifest.sha256 != manifest.source_sha256
    ):
        raise ReviewIntegrityError(
            "Source authority changed after Subject-centric Processing."
        )

    allocated = list(occupied_review_item_ids)
    review_items = []

    for card in payload["cards"]:
        subject_id = card["canonical_subject_id"]
        review_item_id = next_review_item_id(allocated)
        allocated.append(review_item_id)

        information_type = card["information_type"]["selected_value"]
        modality = card["statement_modality"]["selected_value"]
        epistemic_status = card["epistemic_class"]["selected_value"]

        observed_types = {
            item["value"]
            for item in card["information_type"]["value_distribution"]
        }
        open_subject = (
            information_type in _OPEN_SUBJECT_INFORMATION_TYPES
            or bool(observed_types & _OPEN_SUBJECT_INFORMATION_TYPES)
        )
        review_item_kind = (
            "open_question"
            if open_subject
            else "element"
        )
        section = (
            "open_questions"
            if open_subject
            else "elements"
        )

        source_reference = ReviewEvidenceReference(
            artifact_reference=artifacts.subject_review_bundle,
            evidence_role="source_evidence",
            evidence_locator=f"/cards/{subject_id}/mentions",
            evidence_content_fingerprint=card["content_fingerprint"],
        )
        consensus_reference = ReviewEvidenceReference(
            artifact_reference=artifacts.subject_review_bundle,
            evidence_role="semantic_consensus",
            evidence_locator=f"/cards/{subject_id}/consensus",
            evidence_content_fingerprint=card["content_fingerprint"],
        )

        review_items.append(
            create_review_item(
                project_id=manifest.project_id,
                review_document_id=review_document_id,
                review_document_version_id=review_document_version_id,
                review_item_id=review_item_id,
                review_item_kind=review_item_kind,
                stable_subject_key=(
                    "subject:" + subject_id.lower()
                ),
                section=section,
                lineage_operation="original",
                derived_from_review_item_ids=(),
                original_report_locator=(
                    f"subject_review:{subject_id}"
                ),
                proposal_references=(),
                source_evidence_references=(source_reference,),
                consensus_evidence_references=(consensus_reference,),
                current_content=ReviewItemContent(
                    title=card["canonical_label"],
                    primary_text=_subject_review_draft_statement(card),
                    description=(
                        "Canonical engineering Subject awaiting explicit "
                        "Human Engineering Review."
                    ),
                    information_type=information_type,
                    modality=modality,
                    epistemic_status=epistemic_status,
                    human_rationale=None,
                    human_confidence=None,
                    relationship_representation=None,
                ),
                dimension_selections=(),
                effective_review_outcome="open",
            )
        )

    supporting = (
        artifacts.canonical_subject_set,
        artifacts.subject_interpretations,
        artifacts.subject_consensus,
        artifacts.subject_review_bundle,
    )

    document = create_review_document(
        project_id=manifest.project_id,
        review_document_id=review_document_id,
        source_id=manifest.source_id,
        source_sha256=manifest.source_sha256,
        processing_run_id=manifest.processing_run_id,
        attempt_id=artifacts.attempt_id,
        primary_review_artifact_reference=artifacts.primary_review_report,
        supporting_artifact_references=supporting,
        framework_template=project_manifest.framework_template,
        semantic_reference_versions=tuple(
            sorted(
                manifest.semantic_reference_versions,
                key=lambda item: (
                    item.reference_system_id,
                    item.reference_version,
                ),
            )
        ),
        timestamp=timestamp,
    )
    revision = create_review_revision(
        project_id=manifest.project_id,
        review_document_id=review_document_id,
        review_document_version_id=review_document_version_id,
        review_revision_id=review_revision_id,
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=tuple(review_items),
        scoped_review_action_ids=(),
        created_by=opened_by,
        timestamp=timestamp,
    )
    version = create_review_document_version(
        project_id=manifest.project_id,
        review_document_id=review_document_id,
        review_document_version_id=review_document_version_id,
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by=opened_by,
        timestamp=timestamp,
        head_revision_id=review_revision_id,
    )

    return SubjectReviewInitialReviewAssembly(
        review_document=document,
        review_document_version=version,
        initial_revision=revision,
    )


def _subject_review_draft_statement(card: dict) -> str:
    """Return a visible draft only; Human Review remains mandatory."""

    statements = []
    for persona in card.get("persona_interpretations", ()):
        for statement in persona.get("interpreted_statements", ()):
            if isinstance(statement, str) and statement.strip():
                if statement not in statements:
                    statements.append(statement)

    if statements:
        return statements[0]

    mentions = card.get("mentions", ())
    if mentions:
        text = mentions[0].get("exact_text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    label = card.get("canonical_label")
    if isinstance(label, str) and label.strip():
        return label.strip()

    raise ReviewIntegrityError(
        "Subject Review Card has no usable draft engineering text."
    )

def _latest_attempt_id(history: ProcessingRunHistory) -> str | None:
    values = [
        event.attempt_id
        for event in history.events
        if event.attempt_id is not None
    ]
    return values[-1] if values else None
