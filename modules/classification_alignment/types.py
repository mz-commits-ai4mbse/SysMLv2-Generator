"""Immutable types for controlled classification alignment."""

from __future__ import annotations

from dataclasses import dataclass


CLASSIFICATION_ALIGNMENT_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ClassificationAlignmentNeed:
    item_id: str
    field_name: str
    raw_value: str
    interpreted_statement: str
    context: str | None = None


@dataclass(frozen=True, slots=True)
class ClassificationAlignmentDecision:
    item_id: str
    field_name: str
    raw_value: str
    normalized_value: str
    mapping_status: str
    rationale: str
    mapper_response_id: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ClassificationAlignmentResult:
    normalized_output_text: str
    decisions: tuple[ClassificationAlignmentDecision, ...]
    mapper_response_id: str | None = None
    mapper_output_text: str | None = None
