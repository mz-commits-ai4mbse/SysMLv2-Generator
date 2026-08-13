"""Strict deterministic support for Phase-I Internal Model manifests."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from modules.approved_input.identifiers import validate_approved_input_id
from modules.model_candidates.candidate_review_identifiers import (
    validate_model_candidate_review_decision_id,
)
from modules.model_candidates.identifiers import (
    validate_model_element_candidate_id,
    validate_model_relationship_candidate_id,
)
from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateGenerationProvenance,
    ModelCandidateReviewDecisionReference,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.project_workspace.identifiers import is_valid_project_id
from modules.project_workspace.types import FrameworkTemplateReference

from .errors import InternalModelIntegrityError, InternalModelValidationError
from .types import (
    InternalModelAssemblyProvenance,
    InternalModelAssemblyRulesReference,
)


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
STABLE_SUBJECT_KEY_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._:-]{0,239}$"
)
GENERAL_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)


def strict_json_loads(text: object, *, label: str) -> Any:
    if not isinstance(text, str):
        raise InternalModelValidationError(f"{label} JSON must be a string.")
    try:
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except InternalModelValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise InternalModelValidationError(
            f"{label} is not valid JSON."
        ) from exc


def deterministic_json(payload: dict[str, object]) -> str:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def canonical_fingerprint(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InternalModelValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected_fields:
        raise InternalModelValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected_fields - actual)}, "
            f"unknown={sorted(actual - expected_fields)}."
        )
    return value


def text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InternalModelValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise InternalModelValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def optional_text(value: object, *, label: str) -> str | None:
    return None if value is None else text(value, label=label)


def identifier(value: object, *, label: str) -> str:
    checked = text(value, label=label)
    if GENERAL_IDENTIFIER_PATTERN.fullmatch(checked) is None:
        raise InternalModelValidationError(
            f"{label} has invalid identifier syntax."
        )
    return checked


def optional_identifier(value: object, *, label: str) -> str | None:
    return None if value is None else identifier(value, label=label)


def semver(value: object, *, label: str) -> str:
    checked = text(value, label=label)
    if SEMVER_PATTERN.fullmatch(checked) is None:
        raise InternalModelValidationError(
            f"{label} must be a semantic version."
        )
    return checked


def sha256(value: object, *, label: str) -> str:
    checked = text(value, label=label)
    if SHA256_PATTERN.fullmatch(checked) is None:
        raise InternalModelValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )
    return checked


def optional_sha256(value: object, *, label: str) -> str | None:
    return None if value is None else sha256(value, label=label)


def timestamp(value: object, *, label: str) -> str:
    checked = text(value, label=label)
    if UTC_TIMESTAMP_PATTERN.fullmatch(checked) is None:
        raise InternalModelValidationError(
            f"{label} must be an ISO-8601 UTC timestamp ending in Z."
        )
    return checked


def stable_subject_key(value: object, *, label: str) -> str:
    checked = text(value, label=label)
    if STABLE_SUBJECT_KEY_PATTERN.fullmatch(checked) is None:
        raise InternalModelValidationError(
            f"{label} has invalid stable-subject-key syntax."
        )
    return checked


def validate_project_id(value: object) -> str:
    if not is_valid_project_id(value):
        raise InternalModelValidationError(
            "project_id must be a valid six-digit Project ID."
        )
    return value


def framework_template_reference_payload(
    value: FrameworkTemplateReference,
) -> dict[str, object]:
    return {
        "template_id": value.template_id,
        "template_version": value.template_version,
    }


def parse_framework_template_reference(value: object) -> FrameworkTemplateReference:
    data = exact_object(
        value,
        expected_fields=frozenset({"template_id", "template_version"}),
        label="Framework Template Reference",
    )
    return FrameworkTemplateReference(
        template_id=identifier(data["template_id"], label="template_id"),
        template_version=semver(
            data["template_version"],
            label="template_version",
        ),
    )


def model_structure_profile_reference_payload(
    value: ModelStructureProfileReference,
) -> dict[str, object]:
    return {
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
    }


def parse_model_structure_profile_reference(
    value: object,
) -> ModelStructureProfileReference:
    data = exact_object(
        value,
        expected_fields=frozenset(
            {"profile_id", "profile_version", "profile_fingerprint"}
        ),
        label="Model Structure Profile Reference",
    )
    return ModelStructureProfileReference(
        profile_id=identifier(data["profile_id"], label="profile_id"),
        profile_version=semver(
            data["profile_version"],
            label="profile_version",
        ),
        profile_fingerprint=sha256(
            data["profile_fingerprint"],
            label="profile_fingerprint",
        ),
    )


def derivation_rules_reference_payload(
    value: ModelDerivationRulesReference,
) -> dict[str, object]:
    return {
        "context_id": value.context_id,
        "context_version": value.context_version,
        "context_fingerprint": value.context_fingerprint,
    }


def parse_derivation_rules_reference(
    value: object,
) -> ModelDerivationRulesReference:
    data = exact_object(
        value,
        expected_fields=frozenset(
            {"context_id", "context_version", "context_fingerprint"}
        ),
        label="Model Derivation Rules Reference",
    )
    return ModelDerivationRulesReference(
        context_id=identifier(data["context_id"], label="context_id"),
        context_version=semver(
            data["context_version"],
            label="context_version",
        ),
        context_fingerprint=sha256(
            data["context_fingerprint"],
            label="context_fingerprint",
        ),
    )


def assembly_rules_reference_payload(
    value: InternalModelAssemblyRulesReference,
) -> dict[str, object]:
    return {
        "rules_id": value.rules_id,
        "rules_version": value.rules_version,
        "rules_fingerprint": value.rules_fingerprint,
    }


def parse_assembly_rules_reference(
    value: object,
) -> InternalModelAssemblyRulesReference:
    data = exact_object(
        value,
        expected_fields=frozenset(
            {"rules_id", "rules_version", "rules_fingerprint"}
        ),
        label="Internal Model Assembly Rules Reference",
    )
    return InternalModelAssemblyRulesReference(
        rules_id=identifier(data["rules_id"], label="rules_id"),
        rules_version=semver(
            data["rules_version"],
            label="rules_version",
        ),
        rules_fingerprint=sha256(
            data["rules_fingerprint"],
            label="rules_fingerprint",
        ),
    )


def assembly_provenance_payload(
    value: InternalModelAssemblyProvenance,
) -> dict[str, object]:
    return {
        "method": value.method,
        "implementation_reference": value.implementation_reference,
        "recipe_reference": value.recipe_reference,
        "context_fingerprint": value.context_fingerprint,
    }


def parse_assembly_provenance(value: object) -> InternalModelAssemblyProvenance:
    data = exact_object(
        value,
        expected_fields=frozenset(
            {
                "method",
                "implementation_reference",
                "recipe_reference",
                "context_fingerprint",
            }
        ),
        label="Internal Model Assembly Provenance",
    )
    return InternalModelAssemblyProvenance(
        method=text(data["method"], label="assembly method"),
        implementation_reference=optional_text(
            data["implementation_reference"],
            label="implementation_reference",
        ),
        recipe_reference=optional_text(
            data["recipe_reference"],
            label="recipe_reference",
        ),
        context_fingerprint=optional_sha256(
            data["context_fingerprint"],
            label="context_fingerprint",
        ),
    )


def candidate_generation_provenance_payload(
    value: ModelCandidateGenerationProvenance,
) -> dict[str, object]:
    return {
        "method": value.method,
        "recipe_reference": value.recipe_reference,
        "agent_reference": value.agent_reference,
        "model_reference": value.model_reference,
        "context_fingerprint": value.context_fingerprint,
    }


def approved_input_reference_payload(
    value: ModelCandidateApprovedInputReference,
) -> dict[str, object]:
    return {
        "approved_input_id": value.approved_input_id,
        "content_fingerprint": value.content_fingerprint,
        "stable_subject_key": value.stable_subject_key,
        "provenance_role": value.provenance_role,
    }


def parse_approved_input_reference(
    value: object,
) -> ModelCandidateApprovedInputReference:
    data = exact_object(
        value,
        expected_fields=frozenset(
            {
                "approved_input_id",
                "content_fingerprint",
                "stable_subject_key",
                "provenance_role",
            }
        ),
        label="Approved Input Reference",
    )
    try:
        approved_input_id = validate_approved_input_id(
            data["approved_input_id"]
        )
    except Exception as exc:
        raise InternalModelValidationError(
            "approved_input_id is invalid."
        ) from exc
    return ModelCandidateApprovedInputReference(
        approved_input_id=approved_input_id,
        content_fingerprint=sha256(
            data["content_fingerprint"],
            label="Approved Input content_fingerprint",
        ),
        stable_subject_key=stable_subject_key(
            data["stable_subject_key"],
            label="Approved Input stable_subject_key",
        ),
        provenance_role=text(
            data["provenance_role"],
            label="Approved Input provenance_role",
        ),
    )


def parse_approved_input_reference_tuple(
    value: object,
    *,
    label: str,
) -> tuple[ModelCandidateApprovedInputReference, ...]:
    if not isinstance(value, (tuple, list)):
        raise InternalModelValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(parse_approved_input_reference(item) for item in value)
    keys = tuple(item.approved_input_id for item in checked)
    if keys != tuple(sorted(keys)):
        raise InternalModelValidationError(
            f"{label} must use deterministic Approved Input ID order."
        )
    if len(keys) != len(set(keys)):
        raise InternalModelIntegrityError(
            f"{label} must contain unique Approved Input IDs."
        )
    return checked


def review_reference_payload(
    value: ModelCandidateReviewDecisionReference,
) -> dict[str, object]:
    return {
        "model_candidate_review_decision_id": (
            value.model_candidate_review_decision_id
        ),
        "target_type": value.target_type,
        "candidate_id": value.candidate_id,
        "decision": value.decision,
        "decision_fingerprint": value.decision_fingerprint,
    }


def parse_review_reference(
    value: object,
) -> ModelCandidateReviewDecisionReference:
    data = exact_object(
        value,
        expected_fields=frozenset(
            {
                "model_candidate_review_decision_id",
                "target_type",
                "candidate_id",
                "decision",
                "decision_fingerprint",
            }
        ),
        label="Model Candidate Review Decision Reference",
    )
    try:
        decision_id = validate_model_candidate_review_decision_id(
            data["model_candidate_review_decision_id"]
        )
    except Exception as exc:
        raise InternalModelValidationError(
            "model_candidate_review_decision_id is invalid."
        ) from exc
    target_type = text(data["target_type"], label="target_type")
    try:
        if target_type == "element_candidate":
            candidate_id = validate_model_element_candidate_id(
                data["candidate_id"]
            )
        elif target_type == "relationship_candidate":
            candidate_id = validate_model_relationship_candidate_id(
                data["candidate_id"]
            )
        else:
            raise InternalModelValidationError(
                "target_type must be element_candidate or relationship_candidate."
            )
    except InternalModelValidationError:
        raise
    except Exception as exc:
        raise InternalModelValidationError(
            "candidate_id is invalid for target_type."
        ) from exc
    decision = text(data["decision"], label="decision")
    if decision not in {
        "accepted",
        "rejected",
        "deferred",
        "accepted_exception",
    }:
        raise InternalModelValidationError(
            "review decision has unsupported value."
        )
    return ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id=decision_id,
        target_type=target_type,
        candidate_id=candidate_id,
        decision=decision,
        decision_fingerprint=sha256(
            data["decision_fingerprint"],
            label="decision_fingerprint",
        ),
    )


def parse_review_reference_tuple(
    value: object,
    *,
    label: str,
) -> tuple[ModelCandidateReviewDecisionReference, ...]:
    if not isinstance(value, (tuple, list)):
        raise InternalModelValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(parse_review_reference(item) for item in value)
    keys = tuple(
        item.model_candidate_review_decision_id for item in checked
    )
    if keys != tuple(sorted(keys)):
        raise InternalModelValidationError(
            f"{label} must use deterministic decision-ID order."
        )
    if len(keys) != len(set(keys)):
        raise InternalModelIntegrityError(
            f"{label} must contain unique decisions."
        )
    return checked


def _object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InternalModelValidationError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result
