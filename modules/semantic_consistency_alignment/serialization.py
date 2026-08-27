"""Serialization for semantic consistency alignment artifacts."""

from __future__ import annotations

import json
from typing import Any

from .types import (
    SEMANTIC_CONSISTENCY_ALIGNMENT_SCHEMA_VERSION,
    SemanticConsistencyResult,
)


def semantic_consistency_result_to_dict(
    value: SemanticConsistencyResult,
) -> dict[str, Any]:
    return {
        "schema_version": SEMANTIC_CONSISTENCY_ALIGNMENT_SCHEMA_VERSION,
        "mapper_response_id": value.mapper_response_id,
        "mapper_output_text": value.mapper_output_text,
        "decisions": [
            {
                "item_id": item.item_id,
                "raw_epistemic_class": item.raw_epistemic_class,
                "raw_missing_evidence": item.raw_missing_evidence,
                "normalized_epistemic_class": (
                    item.normalized_epistemic_class
                ),
                "normalized_missing_evidence": (
                    item.normalized_missing_evidence
                ),
                "rationale": item.rationale,
                "mapper_response_id": item.mapper_response_id,
                "content_fingerprint": item.content_fingerprint,
            }
            for item in value.decisions
        ],
    }


def semantic_consistency_result_to_json(
    value: SemanticConsistencyResult,
) -> str:
    return (
        json.dumps(
            semantic_consistency_result_to_dict(value),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
