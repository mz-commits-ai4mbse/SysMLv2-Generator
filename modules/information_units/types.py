"""Immutable data types for source-traceable Information Units."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


INFORMATION_TYPES = frozenset(
    {
        "stakeholder",
        "actor",
        "user_need",
        "requirement",
        "use_case",
        "function",
        "logical_element",
        "physical_element",
        "interface",
        "constraint",
        "information_item",
        "definition",
        "rationale",
        "decision",
        "risk",
        "ambiguity",
        "gap",
        "open_question",
        "unclassified",
    }
)

STATEMENT_MODALITIES = frozenset(
    {
        "descriptive",
        "normative",
        "definitional",
        "interrogative",
    }
)

EPISTEMIC_CLASSES = frozenset(
    {
        "explicit",
        "interpretation",
        "derivation",
        "assumption",
    }
)

SEMANTIC_CONFIDENCE_LEVELS = frozenset(
    {
        "high",
        "medium",
        "low",
    }
)


@dataclass(frozen=True, slots=True)
class InformationUnitSourceAnchor:
    """One segment-local, zero-based, end-exclusive source range."""

    segment_id: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True, slots=True)
class InformationUnitExtractionProvenance:
    """Reproducibility references for semantic extraction."""

    team_id: str
    persona_ids: tuple[str, ...]
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    consensus_report_id: str


@dataclass(frozen=True, slots=True)
class InformationUnit:
    """One immutable and independently reviewable semantic claim."""

    schema_version: str
    project_id: str
    information_unit_id: str
    source_id: str
    source_projection_id: str
    source_anchors: tuple[
        InformationUnitSourceAnchor,
        ...
    ]
    source_excerpt: str
    interpreted_statement: str
    information_type: str
    statement_modality: str
    epistemic_class: str
    supporting_information_unit_ids: tuple[str, ...]
    derivation_rationale: str | None
    missing_evidence: str | None
    extraction_provenance: InformationUnitExtractionProvenance
    confidence: str
    confidence_rationale: str
    content_fingerprint: str
    created_at: str


@dataclass(frozen=True, slots=True)
class InformationUnitIssue:
    """One deterministic issue found in Information Unit persistence."""

    project_id: str
    code: str
    message: str
    path: Path
    information_unit_id: str | None = None
    source_id: str | None = None
    source_projection_id: str | None = None


@dataclass(frozen=True, slots=True)
class InformationUnitScanResult:
    """Validated Information Units and blocking persistence issues."""

    information_units: tuple[InformationUnit, ...] = ()
    issues: tuple[InformationUnitIssue, ...] = ()