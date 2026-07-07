"""Section-aware deterministic Markdown extractor for the first MVP run.

This is not intended to replace LLM-based extraction. It creates a basic,
traceable ingestion report from simple Markdown-like text so the workflow can
be executed end-to-end before integrating an LLM backend.

Important MVP rule:
Information listed in "Missing or Weakly Described Information" is treated as
missing information, not as positive evidence for downstream model derivation.
"""

from dataclasses import dataclass
import re


@dataclass
class SourceInfo:
    source_info_id: str
    extracted_information: str
    source_reference: str
    notes: str = ""


@dataclass
class CandidateElement:
    candidate_id: str
    candidate_type: str
    name: str
    description: str
    source_basis: str
    confidence: str


@dataclass
class ExtractionResult:
    source_information: list[SourceInfo]
    candidate_elements: list[CandidateElement]
    assumptions: list[dict[str, str]]
    gaps: list[dict[str, str]]
    risks: list[dict[str, str]]
    review_questions: list[dict[str, str]]


def extract_basic_markdown_information(text: str) -> ExtractionResult:
    lines = [line.rstrip() for line in text.splitlines()]

    source_information: list[SourceInfo] = []
    candidate_elements: list[CandidateElement] = []
    assumptions: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    risks: list[dict[str, str]] = []
    review_questions: list[dict[str, str]] = []

    info_counter = 1
    candidate_counter = 1
    gap_counter = 1

    current_section = "unknown"

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            current_section = classify_section(heading)

            source_information.append(
                SourceInfo(
                    source_info_id=f"SRC_INFO_{info_counter:03d}",
                    extracted_information=heading,
                    source_reference=f"line {idx}",
                    notes=f"Markdown heading; section={current_section}",
                )
            )
            info_counter += 1
            continue

        if stripped.startswith("- "):
            item = stripped[2:].strip()

            if current_section == "missing_information":
                gaps.append(
                    {
                        "gap_id": f"GAP_{gap_counter:03d}",
                        "missing_information": item,
                        "why_it_matters": (
                            "The source explicitly lists this as missing or "
                            "weakly described information."
                        ),
                        "suggested_human_action": (
                            "Confirm whether this information is available "
                            "in another source artifact."
                        ),
                    }
                )
                gap_counter += 1
                continue

            if current_section == "mvp_testing_notes":
                continue

            source_information.append(
                SourceInfo(
                    source_info_id=f"SRC_INFO_{info_counter:03d}",
                    extracted_information=item,
                    source_reference=f"line {idx}",
                    notes=f"Markdown bullet item; section={current_section}",
                )
            )

            candidate_type = classify_candidate(item, current_section)

            if candidate_type:
                candidate_elements.append(
                    CandidateElement(
                        candidate_id=f"CAND_{candidate_counter:03d}",
                        candidate_type=candidate_type,
                        name=to_candidate_name(item),
                        description=item,
                        source_basis=f"SRC_INFO_{info_counter:03d}",
                        confidence=confidence_for_section(current_section),
                    )
                )
                candidate_counter += 1

            info_counter += 1
            continue

        if "shall" in stripped.lower():
            if current_section in {"missing_information", "mvp_testing_notes"}:
                continue

            source_information.append(
                SourceInfo(
                    source_info_id=f"SRC_INFO_{info_counter:03d}",
                    extracted_information=stripped,
                    source_reference=f"line {idx}",
                    notes=f"Requirement-like statement; section={current_section}",
                )
            )

            candidate_elements.append(
                CandidateElement(
                    candidate_id=f"CAND_{candidate_counter:03d}",
                    candidate_type="requirement_candidate",
                    name=to_candidate_name(stripped),
                    description=stripped,
                    source_basis=f"SRC_INFO_{info_counter:03d}",
                    confidence="high",
                )
            )

            candidate_counter += 1
            info_counter += 1
            continue

    assumptions.append(
        {
            "assumption_id": "ASSUMP_001",
            "assumption": (
                "The input artifact is intentionally incomplete and is used "
                "only for the first ingestion workflow test."
            ),
            "reason": (
                "The source context states that the file is intentionally "
                "incomplete."
            ),
            "impact": (
                "Downstream model derivation must be limited to sufficiently "
                "supported artifact types."
            ),
            "requires_human_confirmation": "yes",
        }
    )

    risks.append(
        {
            "risk_id": "RISK_001",
            "topic": "Incomplete evidence",
            "description": (
                "The input does not contain enough evidence for a complete "
                "SysML v2 model."
            ),
            "potential_impact": (
                "Unsupported model artifacts may be incorrectly inferred if "
                "derivation rules are ignored."
            ),
            "suggested_review_action": (
                "Use the derivation assessment before selecting candidate "
                "generation tasks."
            ),
        }
    )

    review_questions.append(
        {
            "question_id": "RQ_001",
            "question": (
                "Which downstream model artifact types should be allowed for "
                "the next MVP step?"
            ),
            "related_artifact_or_candidate": (
                "Downstream model derivation assessment"
            ),
            "reason": (
                "The system should not generate unsupported model artifacts "
                "from incomplete evidence."
            ),
        }
    )

    return ExtractionResult(
        source_information=source_information,
        candidate_elements=candidate_elements,
        assumptions=assumptions,
        gaps=gaps,
        risks=risks,
        review_questions=review_questions,
    )


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

    if normalized == "informal system description":
        return "informal_system_description"

    if normalized == "system name":
        return "system_name"

    if normalized == "source context":
        return "source_context"

    return "other"


def classify_candidate(text: str, section: str) -> str | None:
    lowered = text.lower()

    if section == "mentioned_users":
        return "actor_candidate"

    if section == "mentioned_system_capabilities":
        return "function_candidate"

    if section == "mentioned_constraints":
        return "constraint_candidate"

    if section == "mentioned_system_elements":
        if any(
            term in lowered
            for term in [
                "workstation",
                "application",
                "client",
                "server",
                "module",
                "device",
                "hardware",
            ]
        ):
            return "physical_component_candidate"

        if any(
            term in lowered
            for term in [
                "stream",
                "request",
                "information",
                "record",
                "data",
                "message",
                "file",
                "artifact",
            ]
        ):
            return "artifact_candidate"

        return "logical_component_candidate"

    if section == "informal_system_description":
        if "shall" in lowered:
            return "requirement_candidate"

        if any(
            term in lowered
            for term in [
                "only one",
                "requires",
                "must",
                "prevent",
                "constraint",
            ]
        ):
            return "constraint_candidate"

        if any(
            term in lowered
            for term in [
                "operator",
                "expert",
                "user",
                "stakeholder",
            ]
        ):
            return "actor_candidate"

        if any(
            term in lowered
            for term in [
                "session",
                "view",
                "request",
                "accept",
                "reject",
                "record",
                "show",
                "adjust",
                "join",
                "start",
            ]
        ):
            return "function_candidate"

    return None


def confidence_for_section(section: str) -> str:
    if section in {
        "mentioned_users",
        "mentioned_system_capabilities",
        "mentioned_system_elements",
        "mentioned_constraints",
    }:
        return "medium"

    if section == "informal_system_description":
        return "low"

    return "medium"


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip().lower()


def to_candidate_name(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", text).strip()
    words = cleaned.split()[:6]

    if not words:
        return "UnnamedCandidate"

    return "".join(word[:1].upper() + word[1:] for word in words)