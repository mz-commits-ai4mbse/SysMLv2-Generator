"""Assess which downstream model artifact types are supported by input evidence.

The assessor is intentionally conservative.

Important principle:
Evidence must be positive evidence.

A sentence such as "the input does not describe validation criteria" must not
create validation evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass
class DerivationAssessment:
    model_artifact_type: str
    support_level: str
    evidence_basis: str
    reason: str
    missing_information: str
    recommended_action: str


POSITIVE_SECTIONS = {
    "informal_system_description",
    "mentioned_users",
    "mentioned_system_capabilities",
    "mentioned_system_elements",
    "mentioned_constraints",
}

IGNORED_FOR_POSITIVE_EVIDENCE_SECTIONS = {
    "source_context",
    "system_name",
    "missing_information",
    "mvp_testing_notes",
    "informal_notes",
    "other",
}


def detect_evidence_types(text: str) -> list[str]:
    """Detect evidence types from Markdown text.

    This function is deliberately conservative and section-aware.
    It should detect evidence that is actually present in the input, not
    evidence mentioned as missing, absent or out of scope.
    """

    evidence: set[str] = set()
    current_section = "unknown"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            current_section = classify_section(heading)
            continue

        if current_section in IGNORED_FOR_POSITIVE_EVIDENCE_SECTIONS:
            continue

        if is_negative_or_absence_statement(line):
            continue

        if current_section == "mentioned_users":
            evidence.add("EV_USER_ROLE")
            continue

        if current_section == "mentioned_system_capabilities":
            evidence.add("EV_FUNCTION_OR_CAPABILITY")
            continue

        if current_section == "mentioned_system_elements":
            lowered = line.lower()

            if contains_any(
                lowered,
                [
                    "workstation",
                    "application",
                    "client",
                    "server",
                    "hardware",
                    "module",
                    "device",
                    "controller",
                ],
            ):
                evidence.add("EV_PHYSICAL_ELEMENT")

            if contains_any(
                lowered,
                [
                    "stream",
                    "request",
                    "information",
                    "record",
                    "data",
                    "message",
                    "file",
                    "artifact",
                ],
            ):
                evidence.add("EV_DATA_OR_ARTIFACT")

            continue

        if current_section == "mentioned_constraints":
            evidence.add("EV_CONSTRAINT")
            continue

        if current_section == "informal_system_description":
            detect_from_informal_system_description(line, evidence)
            continue

    return sorted(evidence)


def detect_from_informal_system_description(line: str, evidence: set[str]) -> None:
    lowered = line.lower()

    if contains_requirement_statement(lowered):
        evidence.add("EV_REQUIREMENT_STATEMENT")

    if contains_any(
        lowered,
        [
            "operator",
            "expert",
            "user",
            "actor",
            "stakeholder",
        ],
    ):
        evidence.add("EV_USER_ROLE")

    if contains_any(
        lowered,
        [
            "starts",
            "joins",
            "requests",
            "accepts",
            "rejects",
            "session",
            "workflow",
            "view",
            "adjust",
            "record",
            "show",
        ],
    ):
        evidence.add("EV_USE_CASE_OR_WORKFLOW")

    if contains_any(
        lowered,
        [
            "start",
            "join",
            "view",
            "request",
            "record",
            "show",
            "prevent",
            "adjust",
            "accept",
            "reject",
        ],
    ):
        evidence.add("EV_FUNCTION_OR_CAPABILITY")

    if contains_any(
        lowered,
        [
            "workstation",
            "application",
            "client",
            "server",
            "hardware",
            "module",
            "device",
        ],
    ):
        evidence.add("EV_PHYSICAL_ELEMENT")

    if contains_any(
        lowered,
        [
            "stream",
            "request",
            "information",
            "record",
            "data",
            "message",
        ],
    ):
        evidence.add("EV_DATA_OR_ARTIFACT")

    if contains_any(
        lowered,
        [
            "only one",
            "prevent",
            "requires acceptance",
            "must be visible",
            "at the same time",
        ],
    ):
        evidence.add("EV_CONSTRAINT")

    if contains_interface_evidence(lowered):
        evidence.add("EV_INTERFACE")

    if contains_explicit_stakeholder_need(lowered):
        evidence.add("EV_STAKEHOLDER_NEED")

    if contains_explicit_validation_criterion(lowered):
        evidence.add("EV_VALIDATION_CRITERION")

    if contains_explicit_regulatory_reference(lowered):
        evidence.add("EV_REGULATORY_OR_STANDARD_REFERENCE")


def assess_derivation_support(
    derivation_rules: dict[str, Any],
    detected_evidence_types: list[str],
) -> list[DerivationAssessment]:
    detected = set(detected_evidence_types)
    assessments: list[DerivationAssessment] = []

    for rule in derivation_rules.get("model_artifact_derivation_rules", []):
        model_artifact_type = rule.get("model_artifact_type", "unknown")
        supported_required = set(rule.get("minimum_evidence_types_for_supported", []))
        partial_required = set(rule.get("minimum_evidence_types_for_partially_supported", []))

        support_level, reason, missing, action = assess_single_rule(
            model_artifact_type=model_artifact_type,
            supported_required=supported_required,
            partial_required=partial_required,
            detected=detected,
        )

        assessments.append(
            DerivationAssessment(
                model_artifact_type=model_artifact_type,
                support_level=support_level,
                evidence_basis=", ".join(sorted(detected)) if detected else "No evidence types detected",
                reason=reason,
                missing_information=missing,
                recommended_action=action,
            )
        )

    return assessments


def assess_single_rule(
    model_artifact_type: str,
    supported_required: set[str],
    partial_required: set[str],
    detected: set[str],
) -> tuple[str, str, str, str]:
    """Assess one model artifact type with conservative MVP-specific overrides."""

    if has_full_support(model_artifact_type, supported_required, detected):
        return (
            "supported",
            "Minimum evidence types for supported derivation are present.",
            "None identified by deterministic assessment. Human review still required.",
            "Generate candidate model content and mark it as requiring human review.",
        )

    if partial_required and partial_required.issubset(detected):
        return (
            "partially_supported",
            "Minimum evidence types for partial derivation are present, but full support evidence is missing.",
            summarize_missing(supported_required, detected),
            "Generate only preliminary candidates with assumptions, gaps and review questions.",
        )

    return (
        "not_supported",
        "Required evidence types are not present.",
        summarize_missing(supported_required or partial_required, detected),
        "Do not generate candidate model content. Record missing information and review questions.",
    )


def has_full_support(
    model_artifact_type: str,
    supported_required: set[str],
    detected: set[str],
) -> bool:
    """Apply stricter full-support rules than simple subset matching."""

    if not supported_required:
        return False

    if not supported_required.issubset(detected):
        return False

    if model_artifact_type == "stakeholder_needs":
        return "EV_STAKEHOLDER_NEED" in detected and "EV_USER_ROLE" in detected

    if model_artifact_type == "stakeholder_requirements":
        return {
            "EV_STAKEHOLDER_NEED",
            "EV_REQUIREMENT_STATEMENT",
            "EV_USER_ROLE",
        }.issubset(detected)

    if model_artifact_type == "validation_or_verification_model":
        return "EV_VALIDATION_CRITERION" in detected

    if model_artifact_type == "physical_architecture":
        return "EV_PHYSICAL_ELEMENT" in detected and (
            "EV_INTERFACE" in detected or "EV_DATA_OR_ARTIFACT" in detected
        )

    if model_artifact_type == "interface_model":
        return "EV_INTERFACE" in detected and "EV_DATA_OR_ARTIFACT" in detected

    return True


def classify_section(heading: str) -> str:
    normalized = normalize_text(heading)

    if normalized == "mentioned users":
        return "mentioned_users"

    if normalized == "mentioned system capabilities":
        return "mentioned_system_capabilities"

    if normalized == "mentioned system elements":
        return "mentioned_system_elements"

    if normalized == "mentioned constraints":
        return "mentioned_constraints"

    if normalized == "missing or weakly described information":
        return "missing_information"

    if normalized == "notes for mvp testing":
        return "mvp_testing_notes"

    if normalized == "informal notes":
        return "informal_notes"

    if normalized == "informal system description":
        return "informal_system_description"

    if normalized == "system name":
        return "system_name"

    if normalized == "source context":
        return "source_context"

    return "other"


def is_negative_or_absence_statement(text: str) -> bool:
    lowered = text.lower()

    absence_patterns = [
        "does not describe",
        "does not define",
        "does not contain",
        "not describe",
        "not defined",
        "not explicitly",
        "missing",
        "absent",
        "without",
        "no ",
        "no explicit",
    ]

    return any(pattern in lowered for pattern in absence_patterns)


def contains_requirement_statement(text: str) -> bool:
    return contains_any(
        text,
        [
            " shall ",
            " must ",
            " required ",
            " requires ",
        ],
    ) or text.startswith(("the system shall", "system shall"))


def contains_interface_evidence(text: str) -> bool:
    return contains_any(
        text,
        [
            "through a client",
            "through an application",
            "from the microscope workstation",
            "join the session through",
            "view a live",
            "live image stream",
            "request control",
            "control request",
        ],
    )


def contains_explicit_stakeholder_need(text: str) -> bool:
    return contains_any(
        text,
        [
            "needs to",
            "need to",
            "needs a",
            "need a",
            "pain point",
            "stakeholder need",
            "user need",
        ],
    )


def contains_explicit_validation_criterion(text: str) -> bool:
    return contains_any(
        text,
        [
            "acceptance criterion",
            "acceptance criteria",
            "validation criterion",
            "validation criteria",
            "verification criterion",
            "verification criteria",
            "test criterion",
            "test criteria",
            "success criterion",
            "success criteria",
            "shall be validated by",
            "shall be verified by",
            "test shall",
        ],
    )


def contains_explicit_regulatory_reference(text: str) -> bool:
    return contains_any(
        text,
        [
            "iec ",
            "iso ",
            "ivdr",
            "mdr",
            "regulation ",
            "standard ",
        ],
    )


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def summarize_missing(required: set[str], detected: set[str]) -> str:
    if not required:
        return "No explicit required evidence configured."

    missing = sorted(required - detected)

    if not missing:
        return "No required evidence missing for this support level."

    return "Missing evidence types: " + ", ".join(missing)


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip().lower()