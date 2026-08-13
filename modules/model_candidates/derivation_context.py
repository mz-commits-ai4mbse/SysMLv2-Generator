"""Reference loader for the existing SysML model derivation-rules context."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .errors import ModelCandidateValidationError
from .types import ModelDerivationRulesReference


DEFAULT_MODEL_DERIVATION_RULES_PATH = Path(
    "context/mapping/sysml_model_derivation_rules.json"
)
EXPECTED_MODEL_DERIVATION_CONTEXT_ID = (
    "CTX_SYSML_MODEL_DERIVATION_RULES"
)
_REQUIRED_DECISION_LEVELS = frozenset(
    {
        "supported",
        "partially_supported",
        "not_supported",
        "conflicting",
    }
)
_REQUIRED_GLOBAL_RULE_IDS = frozenset(
    {
        "DERIVATION_RULE_001",
        "DERIVATION_RULE_002",
        "DERIVATION_RULE_003",
        "DERIVATION_RULE_004",
        "DERIVATION_RULE_005",
        "DERIVATION_RULE_006",
        "DERIVATION_RULE_007",
        "DERIVATION_RULE_008",
    }
)


def load_model_derivation_rules_reference(
    path: Path | str = DEFAULT_MODEL_DERIVATION_RULES_PATH,
) -> ModelDerivationRulesReference:
    """Load, minimally validate and fingerprint the accepted rules context."""

    context_path = Path(path)
    try:
        text = context_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ModelCandidateValidationError(
            f"Unable to read derivation-rules context: {context_path}."
        ) from exc
    try:
        data = json.loads(
            text,
            object_pairs_hook=_without_duplicate_keys,
        )
    except ModelCandidateValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ModelCandidateValidationError(
            "Derivation-rules context is not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise ModelCandidateValidationError(
            "Derivation-rules context must be a JSON object."
        )
    if data.get("context_id") != EXPECTED_MODEL_DERIVATION_CONTEXT_ID:
        raise ModelCandidateValidationError(
            "Unexpected derivation-rules context_id."
        )
    version = data.get("version")
    if (
        not isinstance(version, str)
        or len(version.split(".")) != 3
        or not all(part.isdigit() for part in version.split("."))
    ):
        raise ModelCandidateValidationError(
            "Derivation-rules version must use MAJOR.MINOR.PATCH."
        )

    levels = data.get("decision_levels")
    if not isinstance(levels, list):
        raise ModelCandidateValidationError(
            "Derivation-rules decision_levels must be an array."
        )
    observed_levels = {
        item.get("level")
        for item in levels
        if isinstance(item, dict)
    }
    if not _REQUIRED_DECISION_LEVELS.issubset(observed_levels):
        raise ModelCandidateValidationError(
            "Derivation-rules context is missing required support levels."
        )

    rules = data.get("global_generation_rules")
    if not isinstance(rules, list):
        raise ModelCandidateValidationError(
            "global_generation_rules must be an array."
        )
    observed_rule_ids = {
        item.get("rule_id")
        for item in rules
        if isinstance(item, dict)
    }
    if not _REQUIRED_GLOBAL_RULE_IDS.issubset(observed_rule_ids):
        raise ModelCandidateValidationError(
            "Derivation-rules context is missing accepted global rules."
        )

    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return ModelDerivationRulesReference(
        context_id=EXPECTED_MODEL_DERIVATION_CONTEXT_ID,
        context_version=version,
        context_fingerprint=hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
    )


def _without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModelCandidateValidationError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result
