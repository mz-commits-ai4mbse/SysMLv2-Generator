"""Deterministic lexical normalization for semantic consensus.

This module performs comparison normalization only. It does not infer
synonyms, semantic equivalence, ontology mappings or embedding similarity.
"""

from __future__ import annotations

import json
import unicodedata
from typing import Any

from .errors import SemanticConsensusComparisonError


CONSENSUS_TEXT_NORMALIZATION_ID = (
    "unicode_nfkc_whitespace_casefold"
)
CONSENSUS_TEXT_NORMALIZATION_VERSION = "1.0.0"


def normalize_consensus_text(value: object) -> str:
    """Return a deterministic lexical comparison form."""

    if not isinstance(value, str):
        raise SemanticConsensusComparisonError(
            "Consensus text must be a string."
        )

    normalized = unicodedata.normalize("NFKC", value)
    collapsed = " ".join(normalized.split())

    if not collapsed:
        raise SemanticConsensusComparisonError(
            "Consensus text must contain visible characters."
        )

    if "\x00" in collapsed or "\r" in collapsed:
        raise SemanticConsensusComparisonError(
            "Consensus text contains unsupported control "
            "characters."
        )

    return collapsed.casefold()


def canonical_consensus_json(value: Any) -> str:
    """Return deterministic JSON for one structured comparison value."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SemanticConsensusComparisonError(
            "Consensus value is not deterministically "
            "JSON-serializable."
        ) from exc