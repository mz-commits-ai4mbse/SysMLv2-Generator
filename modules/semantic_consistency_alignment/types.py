"""Immutable types for semantic field consistency alignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SEMANTIC_CONSISTENCY_ALIGNMENT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class SemanticConsistencyNeed:
    item_id: str
    interpreted_statement: str
    raw_epistemic_class: str
    raw_missing_evidence: Any
    context: str | None = None


@dataclass(frozen=True, slots=True)
class SemanticConsistencyDecision:
    item_id: str
    raw_epistemic_class: str
    raw_missing_evidence: Any
    normalized_epistemic_class: str
    normalized_missing_evidence: str | None
    rationale: str
    mapper_response_id: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class SemanticConsistencyResult:
    normalized_output_text: str
    decisions: tuple[SemanticConsistencyDecision, ...]
    mapper_response_id: str | None = None
    mapper_output_text: str | None = None
