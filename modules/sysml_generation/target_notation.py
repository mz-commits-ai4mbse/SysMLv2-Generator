"""Load and validate the Phase-J SysML v2 Target Notation Profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import SysMLGenerationProfileError
from .fingerprints import calculate_json_fingerprint
from .types import TargetNotationReference


DEFAULT_TARGET_NOTATION_PATH = (
    Path("context") / "sysml" / "sysml_v2_target_notation.json"
)
EXPECTED_TARGET_NOTATION_CONTEXT_ID = "CTX_SYSML_V2_TARGET_NOTATION"
PHASE_J_TARGET_NOTATION_VERSION = "0.2.0"

_REQUIRED_ARTIFACT_RULES = frozenset(
    {
        "required_generation_input",
        "generation_input_service",
        "raw_legacy_data_allowed_as_direct_generation_input",
        "approved_input_allowed_as_direct_generation_input",
        "candidate_artifacts_allowed_as_direct_generation_input",
        "internal_engineering_model_required",
        "phase_j_result",
        "phase_k_validation_required_before_publication",
        "final_publication_phase",
        "final_published_output_folder",
        "traceability_required",
        "validation_preparation_required",
    }
)


def load_target_notation(
    path: Path | str = DEFAULT_TARGET_NOTATION_PATH,
) -> dict[str, Any]:
    """Load and validate one target-notation JSON document."""

    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SysMLGenerationProfileError(
            f"Unable to load target notation from {target}."
        ) from exc
    return validate_target_notation(payload)


def validate_target_notation(
    payload: object,
) -> dict[str, Any]:
    """Validate the J1 Phase-J target-notation authority contract."""

    if not isinstance(payload, dict):
        raise SysMLGenerationProfileError(
            "Target notation must be a JSON object."
        )

    if payload.get("context_id") != EXPECTED_TARGET_NOTATION_CONTEXT_ID:
        raise SysMLGenerationProfileError(
            "Target notation context_id is not the expected Turing context."
        )

    version = payload.get("version")
    if version != PHASE_J_TARGET_NOTATION_VERSION:
        raise SysMLGenerationProfileError(
            "Phase-J target notation version must be 0.2.0."
        )

    constructs = payload.get("allowed_constructs")
    if not isinstance(constructs, list) or not constructs:
        raise SysMLGenerationProfileError(
            "Target notation requires a non-empty allowed_constructs list."
        )

    construct_ids: list[str] = []
    for item in constructs:
        if not isinstance(item, dict):
            raise SysMLGenerationProfileError(
                "Every allowed construct must be an object."
            )
        construct_id = item.get("construct_id")
        if not isinstance(construct_id, str) or not construct_id:
            raise SysMLGenerationProfileError(
                "Every allowed construct requires construct_id."
            )
        if item.get("allowed") is not True:
            raise SysMLGenerationProfileError(
                f"Allowed construct {construct_id} must have allowed=true."
            )
        construct_ids.append(construct_id)

    if len(construct_ids) != len(set(construct_ids)):
        raise SysMLGenerationProfileError(
            "Target notation construct IDs must be unique."
        )

    rules = payload.get("artifact_generation_rules")
    if not isinstance(rules, dict):
        raise SysMLGenerationProfileError(
            "Target notation requires artifact_generation_rules."
        )
    missing = sorted(_REQUIRED_ARTIFACT_RULES - set(rules))
    if missing:
        raise SysMLGenerationProfileError(
            "Target notation artifact_generation_rules are missing: "
            + ", ".join(missing)
        )

    if rules["required_generation_input"] != (
        "validated_explicit_internal_engineering_model_snapshot"
    ):
        raise SysMLGenerationProfileError(
            "Phase J must generate only from the validated explicit IEM snapshot."
        )
    if rules["internal_engineering_model_required"] is not True:
        raise SysMLGenerationProfileError(
            "internal_engineering_model_required must be true."
        )
    if rules["raw_legacy_data_allowed_as_direct_generation_input"] is not False:
        raise SysMLGenerationProfileError(
            "Raw legacy data must not be direct Phase-J input."
        )
    if rules["approved_input_allowed_as_direct_generation_input"] is not False:
        raise SysMLGenerationProfileError(
            "Approved Input must not bypass the IEM boundary."
        )
    if rules["candidate_artifacts_allowed_as_direct_generation_input"] is not False:
        raise SysMLGenerationProfileError(
            "Model Candidates must not bypass the IEM boundary."
        )
    if rules["phase_k_validation_required_before_publication"] is not True:
        raise SysMLGenerationProfileError(
            "Phase-K validation must precede final publication."
        )
    if rules["final_publication_phase"] != "L":
        raise SysMLGenerationProfileError(
            "Final publication must remain Phase L."
        )

    evidence = payload.get("syntax_evidence_policy")
    if not isinstance(evidence, dict):
        raise SysMLGenerationProfileError(
            "Target notation requires syntax_evidence_policy."
        )
    if evidence.get("target_environment") != "SYSIDE":
        raise SysMLGenerationProfileError(
            "SYSIDE must be the target syntax-validation environment."
        )
    if evidence.get("pending_fixture_grants_generation_permission") is not False:
        raise SysMLGenerationProfileError(
            "Pending syntax fixtures must not grant generation permission."
        )

    return payload


def calculate_target_notation_fingerprint(
    payload: object,
) -> str:
    """Return canonical fingerprint of one validated target-notation profile."""

    validated = validate_target_notation(payload)
    return calculate_json_fingerprint(validated)


def load_target_notation_reference(
    path: Path | str = DEFAULT_TARGET_NOTATION_PATH,
) -> TargetNotationReference:
    """Load the exact pinned TargetNotationReference for Phase J."""

    payload = load_target_notation(path)
    return TargetNotationReference(
        context_id=payload["context_id"],
        version=payload["version"],
        content_fingerprint=calculate_json_fingerprint(payload),
    )
