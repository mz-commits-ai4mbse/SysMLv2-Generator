"""Render one deterministic human-readable Reviewed Report."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import re

from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .effective_decisions_manifest import (
    EffectiveReviewDecisionSet,
    validate_effective_review_decision_set,
)
from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
)
from .reviewed_document_manifest import (
    FinalizedReviewedDocument,
    validate_finalized_reviewed_document,
)
from .types import ReviewItem


REVIEWED_REPORT_SCHEMA_VERSION = "1.0.0"

_REVIEW_SUMMARY_OUTCOMES = (
    "accepted_as_generated",
    "accepted_with_modification",
    "combined",
    "rejected",
    "deferred",
    "out_of_scope",
)

_REVIEW_SECTIONS = (
    ("elements", "Elements"),
    ("relationships", "Relationships"),
    ("open_questions", "Open Questions"),
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


@dataclass(frozen=True, slots=True)
class RenderedReviewedReport:
    """One exact rendered human-readable finalized review."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    finalized_reviewed_document_fingerprint: str
    effective_decision_set_fingerprint: str
    finalization_decision_id: str
    finalization_decision_fingerprint: str
    finalization_validation_fingerprint: str
    reviewer_identity: str
    finalized_at: str
    markdown: str
    content_fingerprint: str


def create_rendered_reviewed_report(
    reviewed_document: FinalizedReviewedDocument,
    decision_set: EffectiveReviewDecisionSet,
) -> RenderedReviewedReport:
    """Render one deterministic Reviewed Report."""

    validate_reviewed_report_source_binding(
        reviewed_document,
        decision_set,
    )

    markdown = _render_markdown(
        reviewed_document,
        decision_set,
    )

    provisional = RenderedReviewedReport(
        schema_version=REVIEWED_REPORT_SCHEMA_VERSION,
        project_id=reviewed_document.project_id,
        review_document_id=(
            reviewed_document.review_document_id
        ),
        review_document_version_id=(
            reviewed_document.review_document_version_id
        ),
        review_revision_id=(
            reviewed_document.review_revision_id
        ),
        finalized_reviewed_document_fingerprint=(
            reviewed_document.content_fingerprint
        ),
        effective_decision_set_fingerprint=(
            decision_set.content_fingerprint
        ),
        finalization_decision_id=(
            reviewed_document.finalization_decision_id
        ),
        finalization_decision_fingerprint=(
            reviewed_document
            .finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            reviewed_document
            .finalization_validation_fingerprint
        ),
        reviewer_identity=(
            reviewed_document.reviewer_identity
        ),
        finalized_at=reviewed_document.finalized_at,
        markdown=markdown,
        content_fingerprint="0" * 64,
    )

    report = replace(
        provisional,
        content_fingerprint=(
            calculate_reviewed_report_fingerprint(
                markdown
            )
        ),
    )

    validate_rendered_reviewed_report(report)

    return report


def reviewed_report_to_markdown(
    report: RenderedReviewedReport,
) -> str:
    """Return the exact validated Markdown representation."""

    validate_rendered_reviewed_report(report)

    return report.markdown


def calculate_reviewed_report_fingerprint(
    markdown: object,
) -> str:
    """Calculate the SHA-256 of the exact Markdown bytes."""

    if not isinstance(markdown, str):
        raise ReviewValidationError(
            "Reviewed Report Markdown must be a string."
        )

    return hashlib.sha256(
        markdown.encode("utf-8")
    ).hexdigest()


def validate_rendered_reviewed_report(
    report: RenderedReviewedReport,
) -> None:
    """Validate one complete rendered Reviewed Report."""

    if not isinstance(report, RenderedReviewedReport):
        raise ReviewValidationError(
            "report must be a RenderedReviewedReport."
        )

    if report.schema_version != REVIEWED_REPORT_SCHEMA_VERSION:
        raise ReviewValidationError(
            "Invalid Reviewed Report schema_version."
        )

    if not is_valid_project_id(report.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit "
            "Project ID."
        )

    validate_review_document_id(
        report.review_document_id
    )
    validate_review_document_version_id(
        report.review_document_version_id
    )
    validate_review_revision_id(
        report.review_revision_id
    )

    for label, value in (
        (
            "finalized_reviewed_document_fingerprint",
            report
            .finalized_reviewed_document_fingerprint,
        ),
        (
            "effective_decision_set_fingerprint",
            report.effective_decision_set_fingerprint,
        ),
        (
            "finalization_decision_fingerprint",
            report.finalization_decision_fingerprint,
        ),
        (
            "finalization_validation_fingerprint",
            report
            .finalization_validation_fingerprint,
        ),
        (
            "content_fingerprint",
            report.content_fingerprint,
        ),
    ):
        _sha256(value, label)

    _text(
        report.finalization_decision_id,
        "finalization_decision_id",
    )
    _text(
        report.reviewer_identity,
        "reviewer_identity",
    )
    _utc_timestamp(
        report.finalized_at,
        "finalized_at",
    )

    if not isinstance(report.markdown, str):
        raise ReviewValidationError(
            "markdown must be a string."
        )

    if not report.markdown.strip():
        raise ReviewValidationError(
            "markdown must not be empty."
        )

    if not report.markdown.endswith("\n"):
        raise ReviewIntegrityError(
            "Reviewed Report Markdown must end "
            "with exactly one persisted newline."
        )

    if (
        report.content_fingerprint
        != calculate_reviewed_report_fingerprint(
            report.markdown
        )
    ):
        raise ReviewIntegrityError(
            "Reviewed Report fingerprint does not "
            "match its Markdown content."
        )


def validate_reviewed_report_source_binding(
    reviewed_document: FinalizedReviewedDocument,
    decision_set: EffectiveReviewDecisionSet,
) -> None:
    """Validate the exact sources used to render the report."""

    validate_finalized_reviewed_document(
        reviewed_document
    )
    validate_effective_review_decision_set(
        decision_set
    )

    if (
        reviewed_document.project_id
        != decision_set.project_id
    ):
        raise ReviewIntegrityError(
            "Reviewed Report sources do not belong "
            "to the same Project."
        )

    if (
        reviewed_document.review_document_id
        != decision_set.review_document_id
    ):
        raise ReviewIntegrityError(
            "Reviewed Report sources do not belong "
            "to the same Review Document."
        )

    if (
        reviewed_document.review_document_version_id
        != decision_set.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Reviewed Report sources do not belong "
            "to the same Review Document Version."
        )

    if (
        reviewed_document.review_revision_id
        != decision_set.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Reviewed Report sources do not bind "
            "the same Review Revision."
        )

    if (
        decision_set
        .finalized_reviewed_document_fingerprint
        != reviewed_document.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not bind the exact "
            "Finalized Reviewed Document."
        )

    if (
        decision_set.review_revision_fingerprint
        != reviewed_document
        .review_revision_fingerprint
    ):
        raise ReviewIntegrityError(
            "Reviewed Report sources do not bind "
            "the same Review Revision fingerprint."
        )

    if (
        decision_set.finalization_decision_id
        != reviewed_document.finalization_decision_id
        or decision_set
        .finalization_decision_fingerprint
        != reviewed_document
        .finalization_decision_fingerprint
        or decision_set
        .finalization_validation_fingerprint
        != reviewed_document
        .finalization_validation_fingerprint
    ):
        raise ReviewIntegrityError(
            "Reviewed Report sources do not bind "
            "the same finalization evidence."
        )

    if (
        decision_set.finalized_at
        != reviewed_document.finalized_at
    ):
        raise ReviewIntegrityError(
            "Reviewed Report source timestamps "
            "do not match."
        )

    expected_items = tuple(
        (
            reference.review_item_id,
            reference.stable_subject_key,
            reference.review_item_kind,
            reference.section,
            reference.effective_review_outcome,
            reference.item_content_fingerprint,
        )
        for reference in reviewed_document.review_items
    )

    actual_items = tuple(
        (
            item.review_item_id,
            item.stable_subject_key,
            item.review_item_kind,
            item.section,
            item.effective_review_outcome,
            item.item_content_fingerprint,
        )
        for item in decision_set.effective_decisions
    )

    if actual_items != expected_items:
        raise ReviewIntegrityError(
            "Reviewed Report sources do not contain "
            "the same finalized Review Items."
        )


def _render_markdown(
    reviewed_document: FinalizedReviewedDocument,
    decision_set: EffectiveReviewDecisionSet,
) -> str:
    items = decision_set.effective_decisions
    outcome_counts = Counter(
        item.effective_review_outcome
        for item in items
    )

    lines = [
        "# Reviewed Report",
        "",
        "## Finalization Metadata",
        "",
        (
            "- Project ID: "
            f"`{reviewed_document.project_id}`"
        ),
        (
            "- Review Document ID: "
            f"`{reviewed_document.review_document_id}`"
        ),
        (
            "- Review Document Version ID: "
            f"`{reviewed_document.review_document_version_id}`"
        ),
        (
            "- Review Revision ID: "
            f"`{reviewed_document.review_revision_id}`"
        ),
        (
            "- Source ID: "
            f"`{reviewed_document.source_id}`"
        ),
        (
            "- Processing Run ID: "
            f"`{reviewed_document.processing_run_id}`"
        ),
        (
            "- Attempt ID: "
            f"`{reviewed_document.attempt_id}`"
        ),
        (
            "- Finalization Decision ID: "
            f"`{reviewed_document.finalization_decision_id}`"
        ),
        (
            "- Reviewer: "
            f"`{_inline(reviewed_document.reviewer_identity)}`"
        ),
        (
            "- Decision Time: "
            f"`{reviewed_document.decision_at}`"
        ),
        (
            "- Finalized At: "
            f"`{reviewed_document.finalized_at}`"
        ),
        (
            "- Finalized Reviewed Document Fingerprint: "
            f"`{reviewed_document.content_fingerprint}`"
        ),
        (
            "- Effective Decision Set Fingerprint: "
            f"`{decision_set.content_fingerprint}`"
        ),
        (
            "- Finalization Validation Fingerprint: "
            f"`{reviewed_document.finalization_validation_fingerprint}`"
        ),
        "",
        "## Review Summary",
        "",
        "| Outcome | Count |",
        "| --- | ---: |",
    ]

    for outcome in _REVIEW_SUMMARY_OUTCOMES:
        lines.append(
            f"| `{outcome}` | {outcome_counts[outcome]} |"
        )

    lines.extend(
        [
            f"| **Total** | **{len(items)}** |",
            "",
        ]
    )

    for section_key, section_title in _REVIEW_SECTIONS:
        lines.extend(
            [
                f"## {section_title}",
                "",
            ]
        )

        section_items = tuple(
            item
            for item in items
            if item.section == section_key
        )

        if not section_items:
            lines.extend(
                [
                    "_No finalized Review Items "
                    "in this section._",
                    "",
                ]
            )
            continue

        for item in section_items:
            lines.extend(_render_review_item(item))

    lines.extend(
        [
            "## Rejected Content",
            "",
        ]
    )

    rejected_items = tuple(
        item
        for item in items
        if item.effective_review_outcome
        == "rejected"
    )

    if not rejected_items:
        lines.extend(
            [
                "_No rejected Review Items._",
                "",
            ]
        )
    else:
        for item in rejected_items:
            lines.extend(_render_rejected_item(item))

    return "\n".join(lines).rstrip("\n") + "\n"


def _render_review_item(
    item: ReviewItem,
) -> list[str]:
    content = item.current_content
    title = _heading_text(content.title)

    lines = [
        f"### {item.review_item_id} — {title}",
        "",
        f"- Kind: `{item.review_item_kind}`",
        f"- Stable Subject Key: `{item.stable_subject_key}`",
        f"- Review Outcome: `{item.effective_review_outcome}`",
        (
            "- Original Report Locator: "
            f"`{_inline(item.original_report_locator)}`"
        ),
        (
            "- Item Content Fingerprint: "
            f"`{item.item_content_fingerprint}`"
        ),
        "",
        "**Reviewed Content**",
        "",
    ]

    lines.extend(_blockquote(content.primary_text))
    lines.append("")

    if content.description is not None:
        lines.extend(
            [
                "**Description**",
                "",
            ]
        )
        lines.extend(_blockquote(content.description))
        lines.append("")

    lines.extend(
        [
            "**Review Metadata**",
            "",
            (
                "- Information Type: "
                f"{_optional_code(content.information_type)}"
            ),
            (
                "- Modality: "
                f"{_optional_code(content.modality)}"
            ),
            (
                "- Epistemic Status: "
                f"{_optional_code(content.epistemic_status)}"
            ),
            (
                "- Human Confidence: "
                f"{_optional_code(content.human_confidence)}"
            ),
        ]
    )

    if content.human_rationale is not None:
        lines.extend(
            [
                "",
                "**Human Rationale**",
                "",
            ]
        )
        lines.extend(
            _blockquote(content.human_rationale)
        )

    lines.extend(
        [
            "",
            "**Effective Dimensions**",
            "",
        ]
    )

    if not item.dimension_selections:
        lines.append(
            "_No explicit dimension selections recorded._"
        )
    else:
        for selection in sorted(
            item.dimension_selections,
            key=lambda value: value.dimension,
        ):
            selected_values = ", ".join(
                f"`{_inline(value)}`"
                for value in selection.selected_values
            )

            lines.append(
                f"- `{selection.dimension}`: "
                f"{selected_values} "
                f"(origin: `{selection.value_origin}`)"
            )

            if selection.rationale is not None:
                lines.append(
                    "  - Rationale: "
                    f"{_inline(selection.rationale)}"
                )

    if content.relationship_representation is not None:
        lines.extend(
            _render_relationship(
                content.relationship_representation
            )
        )

    lines.extend(
        _render_proposal_references(item)
    )
    lines.extend(
        _render_evidence_references(
            "Source Evidence",
            item.source_evidence_references,
        )
    )
    lines.extend(
        _render_evidence_references(
            "Consensus Evidence",
            item.consensus_evidence_references,
        )
    )

    lines.append("")

    return lines


def _render_relationship(
    relationship,
) -> list[str]:
    lines = [
        "",
        "**Relationship Representation**",
        "",
        (
            "- Source Subject: "
            f"`{relationship.source_subject_key}`"
        ),
        (
            "- Target Subject: "
            f"`{relationship.target_subject_key}`"
        ),
        (
            "- Semantic Intent: "
            f"`{relationship.semantic_intent}`"
        ),
        (
            "- SysML v2 Construct: "
            f"{_optional_code(relationship.sysml_v2_construct)}"
        ),
        (
            "- Target-Notation Profile: "
            f"`{relationship.target_notation_profile_id}` "
            f"`{relationship.target_notation_profile_version}`"
        ),
        (
            "- Validation Status: "
            f"`{relationship.validation_status}`"
        ),
        (
            "- Validation Fingerprint: "
            f"{_optional_code(relationship.validation_fingerprint)}"
        ),
    ]

    if relationship.construct_properties:
        lines.extend(
            [
                "",
                "**Construct Properties**",
                "",
            ]
        )

        for prop in sorted(
            relationship.construct_properties,
            key=lambda value: (
                value.name,
                value.value,
            ),
        ):
            lines.append(
                f"- `{_inline(prop.name)}`: "
                f"`{_inline(prop.value)}`"
            )

    if relationship.textual_notation_preview is not None:
        lines.extend(
            [
                "",
                "**Textual-Notation Preview**",
                "",
            ]
        )
        lines.extend(
            _indented_code(
                relationship.textual_notation_preview
            )
        )

    return lines


def _render_proposal_references(
    item: ReviewItem,
) -> list[str]:
    lines = [
        "",
        "**Agent Proposal References**",
        "",
    ]

    if not item.proposal_references:
        lines.append("_No Agent proposals recorded._")
        return lines

    for reference in sorted(
        item.proposal_references,
        key=lambda value: (
            value.proposal_id,
            value.agent_id,
        ),
    ):
        artifact = reference.artifact_reference

        lines.extend(
            [
                (
                    f"- Proposal `{reference.proposal_id}` "
                    f"from Agent `{reference.agent_id}`"
                ),
                (
                    "  - Persona: "
                    f"`{reference.persona_id}`"
                ),
                (
                    "  - Review State: "
                    f"`{reference.review_state}`"
                ),
                (
                    "  - Artifact: "
                    f"`{artifact.artifact_type}:"
                    f"{artifact.artifact_id}`"
                ),
                (
                    "  - Proposal Fingerprint: "
                    f"`{reference.proposal_content_fingerprint}`"
                ),
            ]
        )

    return lines


def _render_evidence_references(
    title: str,
    references,
) -> list[str]:
    lines = [
        "",
        f"**{title}**",
        "",
    ]

    if not references:
        lines.append("_No references recorded._")
        return lines

    for reference in sorted(
        references,
        key=lambda value: (
            value.evidence_role,
            value.evidence_locator,
            value.artifact_reference.artifact_id,
        ),
    ):
        artifact = reference.artifact_reference

        lines.extend(
            [
                (
                    f"- `{reference.evidence_role}` — "
                    f"`{_inline(reference.evidence_locator)}`"
                ),
                (
                    "  - Artifact: "
                    f"`{artifact.artifact_type}:"
                    f"{artifact.artifact_id}`"
                ),
                (
                    "  - Evidence Fingerprint: "
                    f"`{reference.evidence_content_fingerprint}`"
                ),
            ]
        )

    return lines


def _render_rejected_item(
    item: ReviewItem,
) -> list[str]:
    lines = [
        (
            f"### {item.review_item_id} — "
            f"{_heading_text(item.current_content.title)}"
        ),
        "",
        f"- Kind: `{item.review_item_kind}`",
        f"- Stable Subject Key: `{item.stable_subject_key}`",
        (
            "- Original Report Locator: "
            f"`{_inline(item.original_report_locator)}`"
        ),
        (
            "- Item Content Fingerprint: "
            f"`{item.item_content_fingerprint}`"
        ),
    ]

    if item.current_content.human_rationale is None:
        lines.append("- Rejection Rationale: _Not recorded._")
    else:
        lines.extend(
            [
                "- Rejection Rationale:",
                "",
            ]
        )
        lines.extend(
            _blockquote(
                item.current_content.human_rationale
            )
        )

    lines.append("")

    return lines


def _blockquote(value: str) -> list[str]:
    return [
        f"> {line}"
        for line in value.splitlines()
    ] or [">"]


def _indented_code(value: str) -> list[str]:
    return [
        f"    {line}"
        for line in value.splitlines()
    ] or ["    "]


def _heading_text(value: str) -> str:
    return " ".join(value.split())


def _inline(value: str) -> str:
    return (
        value.replace("`", "\\`")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _optional_code(value: str | None) -> str:
    if value is None:
        return "_Not specified._"

    return f"`{_inline(value)}`"


def _sha256(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a lowercase SHA-256."
        )

    return value


def _text(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ReviewValidationError(
            f"{label} must be non-empty text "
            "without surrounding whitespace."
        )

    return value


def _utc_timestamp(
    value: object,
    label: str,
) -> datetime:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a UTC timestamp."
        )

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
