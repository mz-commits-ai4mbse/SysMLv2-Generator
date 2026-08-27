"""Deterministic serialization for classification-alignment artifacts."""

from __future__ import annotations

import json
from typing import Any

from .types import (
    CLASSIFICATION_ALIGNMENT_SCHEMA_VERSION,
    ClassificationAlignmentResult,
)


def classification_alignment_result_to_dict(
    value: ClassificationAlignmentResult,
) -> dict[str, Any]:
    """Return one auditable JSON-compatible alignment artifact."""

    return {
        "schema_version": CLASSIFICATION_ALIGNMENT_SCHEMA_VERSION,
        "mapper_response_id": value.mapper_response_id,
        "mapper_output_text": value.mapper_output_text,
        "decisions": [
            {
                "item_id": item.item_id,
                "field_name": item.field_name,
                "raw_value": item.raw_value,
                "normalized_value": item.normalized_value,
                "mapping_status": item.mapping_status,
                "rationale": item.rationale,
                "mapper_response_id": item.mapper_response_id,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.decisions
        ],
    }


def classification_alignment_result_to_json(
    value: ClassificationAlignmentResult,
) -> str:
    """Serialize one alignment artifact deterministically."""

    return (
        json.dumps(
            classification_alignment_result_to_dict(value),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
