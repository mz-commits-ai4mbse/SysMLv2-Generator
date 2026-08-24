"""Adapt corrected shared-Evidence Processing output into Human Review."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from modules.evidence_interpretation.review_input import (
    shared_evidence_review_input_from_json,
)
from modules.project_processing import ProcessingArtifactReference
from modules.project_processing.types import ProcessingRunHistory
from modules.project_sources.types import SourceManifest
from modules.project_workspace.types import ProjectManifest
from modules.source_evidence import SourceEvidenceRepository

from .document_manifest import create_review_document
from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .identifiers import next_review_item_id
from .item_manifest import create_review_item
from .revision_manifest import create_review_revision
from .scoped_workflow import ReviewConsensusFilterFact
from .types import ReviewEvidenceReference, ReviewItemContent
from .version_manifest import create_review_document_version


SHARED_EVIDENCE_REVIEW_INPUT_FILENAME = (
    "shared_evidence_review_input.json"
)

_OPEN_QUESTION_TYPES = frozenset(
    {
        "open_question",
        "gap",
        "ambiguity",
        "risk",
    }
)


@dataclass(frozen=True, slots=True)
class SharedEvidenceReviewArtifacts:
    """Published artifacts required by corrected Human Review."""

    primary_review_report: ProcessingArtifactReference
    structured_review_input: ProcessingArtifactReference


@dataclass(frozen=True, slots=True)
class SharedEvidenceInitialReviewAssembly:
    """Initial Review Workspace bundle for the corrected path."""

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


def select_shared_evidence_review_artifact(
    history: ProcessingRunHistory,
) -> SharedEvidenceReviewArtifacts | None:
    """Resolve corrected primary Review Report and structured input."""

    review_inputs = []
    review_reports = []

    events = getattr(history, "events", None)
    if events is None:
        # Legacy/test-double histories without Processing events cannot
        # advertise the corrected shared-Evidence review contract.
        # Return no match so ReviewApprovalWorkflowService preserves the
        # existing P4/P9 legacy fallback path.
        return None

    for event in events:
        if event.event_type != "artifact_published":
            continue

        for reference in event.artifact_references:
            if (
                reference.artifact_type == "consensus_reports"
                and Path(
                    reference.repository_relative_path
                ).name
                == SHARED_EVIDENCE_REVIEW_INPUT_FILENAME
            ):
                review_inputs.append(reference)

            if (
                reference.artifact_type == "review_reports"
                and Path(
                    reference.repository_relative_path
                ).name
                == "ingestion_review_report.md"
            ):
                review_reports.append(reference)

    if not review_inputs:
        return None

    if len(review_inputs) != 1:
        raise ReviewIntegrityError(
            "Corrected Processing Run must publish exactly one "
            "shared_evidence_review_input.json artifact."
        )
    if len(review_reports) != 1:
        raise ReviewIntegrityError(
            "Corrected Processing Run must publish exactly one "
            "primary ingestion_review_report.md artifact."
        )

    return SharedEvidenceReviewArtifacts(
        primary_review_report=review_reports[0],
        structured_review_input=review_inputs[0],
    )


def load_shared_evidence_review_consensus_filter_facts(
    artifacts: SharedEvidenceReviewArtifacts,
    *,
    repository_root: Path,
) -> tuple[ReviewConsensusFilterFact, ...]:
    """Reconstruct exact filter facts from corrected shared-Evidence authority."""

    if not isinstance(artifacts, SharedEvidenceReviewArtifacts):
        raise ReviewValidationError(
            "artifacts must be SharedEvidenceReviewArtifacts."
        )

    payload = _load_review_input(
        artifacts.structured_review_input,
        repository_root=repository_root,
    )
    reference = artifacts.structured_review_input

    facts = []
    seen_keys = set()

    for subject in payload["subjects"]:
        consensus = subject["consensus"]
        locator = (
            f"/subjects/{subject['source_evidence_id']}/consensus"
        )
        fingerprint = subject["consensus_content_fingerprint"]
        key = (
            reference.artifact_id,
            locator,
            fingerprint,
        )
        if key in seen_keys:
            raise ReviewIntegrityError(
                "Shared-Evidence consensus filter fact is duplicated."
            )
        seen_keys.add(key)

        facts.append(
            ReviewConsensusFilterFact(
                artifact_id=reference.artifact_id,
                evidence_locator=locator,
                evidence_content_fingerprint=fingerprint,
                agreement_level=_shared_consensus_filter_state(
                    consensus
                ),
                review_required=consensus["review_required"],
            )
        )

    if not facts:
        raise ReviewReferenceError(
            "Corrected shared-Evidence review input contains no "
            "Consensus filter facts."
        )

    return tuple(facts)


def _shared_consensus_filter_state(consensus) -> str:
    """Derive one filter state from exact persona-support cardinalities."""

    supporting = tuple(consensus["supporting_personas"])
    dissenting = tuple(consensus["dissenting_personas"])
    omitting = tuple(consensus["omitting_personas"])

    if dissenting:
        if not supporting or len(supporting) == len(dissenting):
            return "conflict"
        if len(supporting) > len(dissenting):
            return "majority_with_disagreement"
        return "minority_interpretation"

    if omitting:
        return "incomplete_consensus"

    if supporting:
        return "unanimous"

    return "not_available"


def assemble_shared_evidence_initial_review(
    *,
    history: ProcessingRunHistory,
    source_manifest: SourceManifest,
    project_manifest: ProjectManifest,
    primary_artifact_reference: ProcessingArtifactReference,
    structured_review_input_reference: ProcessingArtifactReference,
    repository_root: Path,
    projects_root: Path,
    review_document_id: str,
    review_document_version_id: str,
    review_revision_id: str,
    opened_by: str,
    timestamp: str,
    occupied_review_item_ids: tuple[str, ...],
) -> SharedEvidenceInitialReviewAssembly:
    """Create one Review Document directly from fixed Evidence subjects."""

    if primary_artifact_reference.artifact_type != "review_reports":
        raise ReviewIntegrityError(
            "Corrected primary review artifact must be review_reports."
        )
    if (
        structured_review_input_reference.artifact_type
        != "consensus_reports"
    ):
        raise ReviewIntegrityError(
            "Corrected structured review input must be consensus_reports."
        )

    payload = _load_review_input(
        structured_review_input_reference,
        repository_root=repository_root,
    )
    manifest = history.manifest
    attempt_id = _latest_attempt_id(history)

    expected = {
        "project_id": manifest.project_id,
        "source_id": manifest.source_id,
        "source_sha256": manifest.source_sha256,
        "processing_run_id": manifest.processing_run_id,
        "attempt_id": attempt_id,
    }
    for field_name, expected_value in expected.items():
        if payload[field_name] != expected_value:
            raise ReviewIntegrityError(
                "Shared-Evidence review input does not bind current "
                f"Processing authority: {field_name}."
            )

    if (
        source_manifest.source_id != manifest.source_id
        or source_manifest.sha256 != manifest.source_sha256
    ):
        raise ReviewIntegrityError(
            "Source authority changed after corrected Processing."
        )

    evidence_repository = SourceEvidenceRepository(
        root=projects_root,
    )

    allocated = list(occupied_review_item_ids)
    review_items = []

    for subject in payload["subjects"]:
        evidence = evidence_repository.load_source_evidence(
            manifest.project_id,
            subject["source_evidence_id"],
        )
        _validate_subject_evidence(subject, evidence)

        review_item_id = next_review_item_id(allocated)
        allocated.append(review_item_id)

        draft = subject["consensus"]["proposed_information_unit"]
        if draft is None:
            primary_text = evidence.source_excerpt
            information_type = "unclassified"
            modality = "descriptive"
            epistemic_status = "explicit"
        else:
            primary_text = draft["interpreted_statement"]
            information_type = draft["information_type"]
            modality = draft["statement_modality"]
            epistemic_status = draft["epistemic_class"]

        review_item_kind = _shared_review_item_kind(
            information_type=information_type,
            subject=subject,
        )
        section = (
            "open_questions"
            if review_item_kind == "open_question"
            else "elements"
        )

        source_reference = ReviewEvidenceReference(
            artifact_reference=structured_review_input_reference,
            evidence_role="source_evidence",
            evidence_locator=(
                f"/subjects/{subject['source_evidence_id']}"
                "/source_evidence"
            ),
            evidence_content_fingerprint=(
                evidence.content_fingerprint
            ),
        )
        consensus_reference = ReviewEvidenceReference(
            artifact_reference=structured_review_input_reference,
            evidence_role="semantic_consensus",
            evidence_locator=(
                f"/subjects/{subject['source_evidence_id']}"
                "/consensus"
            ),
            evidence_content_fingerprint=(
                subject["consensus_content_fingerprint"]
            ),
        )

        review_items.append(
            create_review_item(
                project_id=manifest.project_id,
                review_document_id=review_document_id,
                review_document_version_id=(
                    review_document_version_id
                ),
                review_item_id=review_item_id,
                review_item_kind=review_item_kind,
                stable_subject_key=(
                    "evidence:"
                    f"{evidence.source_evidence_id.lower()}"
                ),
                section=section,
                lineage_operation="original",
                derived_from_review_item_ids=(),
                original_report_locator=(
                    "shared_evidence:"
                    f"{evidence.source_evidence_id}"
                ),
                proposal_references=(),
                source_evidence_references=(source_reference,),
                consensus_evidence_references=(
                    consensus_reference,
                ),
                current_content=ReviewItemContent(
                    title=_review_title(
                        primary_text,
                        evidence.source_evidence_id,
                    ),
                    primary_text=primary_text,
                    description=_review_description(subject),
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

    if not review_items:
        raise ReviewReferenceError(
            "Corrected shared-Evidence review input contains no subjects."
        )

    published = _published_references_for_attempt(
        history,
        attempt_id,
    )
    supporting = tuple(
        reference
        for reference in published
        if reference != primary_artifact_reference
    )

    if structured_review_input_reference not in supporting:
        raise ReviewIntegrityError(
            "Structured shared-Evidence review input must be a "
            "published supporting artifact."
        )

    document = create_review_document(
        project_id=manifest.project_id,
        review_document_id=review_document_id,
        source_id=manifest.source_id,
        source_sha256=manifest.source_sha256,
        processing_run_id=manifest.processing_run_id,
        attempt_id=attempt_id,
        primary_review_artifact_reference=(
            primary_artifact_reference
        ),
        supporting_artifact_references=supporting,
        framework_template=project_manifest.framework_template,
        semantic_reference_versions=(
            manifest.semantic_reference_versions
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

    return SharedEvidenceInitialReviewAssembly(
        review_document=document,
        review_document_version=version,
        initial_revision=revision,
    )


def _shared_review_item_kind(
    *,
    information_type: str,
    subject,
) -> str:
    """Classify Review presentation without inventing model semantics.

    A missing/incomparable consensus draft is represented as ``unclassified``.
    That state alone is not an engineering Open Question. For corrected
    shared-Evidence reviews, persona interpretation types may therefore be
    used only to distinguish explicit question/gap/ambiguity/risk subjects
    from ordinary engineering information.
    """

    if information_type in _OPEN_QUESTION_TYPES:
        return "open_question"

    if information_type != "unclassified":
        return "element"

    interpretation_types = tuple(
        interpretation.get("information_type")
        for interpretation in subject.get("persona_interpretations", ())
        if interpretation.get("information_type")
    )

    if not interpretation_types:
        return "element"

    open_votes = sum(
        value in _OPEN_QUESTION_TYPES
        for value in interpretation_types
    )
    non_open_votes = len(interpretation_types) - open_votes

    return (
        "open_question"
        if open_votes > non_open_votes
        else "element"
    )


def _load_review_input(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
):
    path = repository_root / reference.repository_relative_path
    try:
        resolved = path.resolve()
        resolved.relative_to(repository_root.resolve())
    except ValueError as exc:
        raise ReviewReferenceError(
            "Shared-Evidence review input escaped repository root."
        ) from exc

    if not resolved.is_file():
        raise ReviewReferenceError(
            "Shared-Evidence review input file is unavailable."
        )

    content = resolved.read_bytes()
    if sha256(content).hexdigest() != reference.content_fingerprint:
        raise ReviewIntegrityError(
            "Shared-Evidence review input artifact fingerprint mismatch."
        )

    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        raise ReviewReferenceError(
            "Shared-Evidence review input is not UTF-8."
        ) from exc

    try:
        return shared_evidence_review_input_from_json(text)
    except Exception as exc:
        raise ReviewValidationError(
            "Shared-Evidence review input failed contract validation."
        ) from exc


def _validate_subject_evidence(subject, evidence) -> None:
    if (
        subject["source_evidence_content_fingerprint"]
        != evidence.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Review subject Source Evidence fingerprint mismatch."
        )
    if subject["source_excerpt"] != evidence.source_excerpt:
        raise ReviewIntegrityError(
            "Review subject Source Evidence excerpt mismatch."
        )

    expected_anchors = [
        {
            "segment_id": anchor.segment_id,
            "start_offset": anchor.start_offset,
            "end_offset": anchor.end_offset,
        }
        for anchor in evidence.source_anchors
    ]
    if subject["source_anchors"] != expected_anchors:
        raise ReviewIntegrityError(
            "Review subject Source Evidence anchors mismatch."
        )


def _review_description(subject) -> str:
    consensus = subject["consensus"]
    interpretations = subject["persona_interpretations"]
    summary = "; ".join(
        (
            f"{item['persona_id']}: "
            f"{item['interpreted_statement']}"
        )
        for item in interpretations
    )
    return (
        "Source-grounded Engineering Information before model derivation. "
        f"Consensus={consensus['consensus_level']}, "
        f"variance={consensus['variance_level']}, "
        f"confidence={consensus['confidence']}. "
        f"Persona interpretations: {summary}"
    )


def _review_title(primary_text: str, evidence_id: str) -> str:
    compact = " ".join(primary_text.split())
    if len(compact) > 96:
        compact = compact[:93].rstrip() + "..."
    return compact or evidence_id


def _latest_attempt_id(history: ProcessingRunHistory) -> str:
    attempts = [
        event.attempt_id
        for event in history.events
        if event.attempt_id is not None
    ]
    if not attempts:
        raise ReviewReferenceError(
            "Corrected Processing Run has no Attempt identity."
        )
    return attempts[-1]


def _published_references_for_attempt(
    history: ProcessingRunHistory,
    attempt_id: str,
):
    refs = []
    for event in history.events:
        if (
            event.event_type == "artifact_published"
            and event.attempt_id == attempt_id
        ):
            refs.extend(event.artifact_references)
    return tuple(refs)
