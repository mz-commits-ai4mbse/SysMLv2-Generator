"""Constrained deterministic Target Notation checks for generated artifacts."""

from __future__ import annotations

import re

from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .finding_support import blocking_finding, sort_validation_findings
from .types import SysMLValidationFinding


_ELEMENT_HEADER = re.compile(
    r"^(part|action|requirement|use case def) ([A-Za-z_][A-Za-z0-9_]*) \{$"
)
_REFERENCE = r"[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*"
_RELATIONSHIP = re.compile(
    rf"^(?:allocate {_REFERENCE} to {_REFERENCE};|"
    rf"dependency from {_REFERENCE} to {_REFERENCE};|"
    rf"satisfy {_REFERENCE} by {_REFERENCE};)$"
)


def validate_target_notation_subset(
    artifact_set: GeneratedSysMLArtifactSet,
) -> tuple[SysMLValidationFinding, ...]:
    """Validate only the Turing-generated production subset; not full SysML v2."""

    findings: list[SysMLValidationFinding] = []
    category = "target_notation"
    units = {unit.unit_id: unit for unit in artifact_set.units}

    for entry in artifact_set.traceability_entries:
        unit = units.get(entry.generated_unit_id)
        location = entry.generated_location
        if unit is None or location is None:
            continue
        lines = unit.content.splitlines()
        if (
            location.start_line < 1
            or location.end_line < location.start_line
            or location.end_line > len(lines)
        ):
            continue
        fragment = lines[location.start_line - 1 : location.end_line]

        if entry.source_internal_model_element_id is not None:
            match = _ELEMENT_HEADER.fullmatch(fragment[0].strip()) if fragment else None
            if match is None or match.group(2) != entry.generated_symbol_id:
                findings.append(
                    blocking_finding(
                        code="K2_TARGET_ELEMENT_FORM_INVALID",
                        category=category,
                        message="Generated element is outside the allowed Turing Target Notation element forms.",
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )
                continue
            if (
                len(fragment) < 3
                or fragment[-1].strip() != "}"
                or not fragment[1].lstrip().startswith("doc /* ")
                or not fragment[-2].rstrip().endswith("*/")
            ):
                findings.append(
                    blocking_finding(
                        code="K2_TARGET_ELEMENT_BODY_INVALID",
                        category=category,
                        message="Generated element body must remain the deterministic documentation-only Turing form.",
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )
        elif entry.source_internal_model_relationship_id is not None:
            if len(fragment) != 1 or _RELATIONSHIP.fullmatch(fragment[0].strip()) is None:
                findings.append(
                    blocking_finding(
                        code="K2_TARGET_RELATIONSHIP_FORM_INVALID",
                        category=category,
                        message="Generated relationship is outside the allowed Turing Target Notation relationship forms.",
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )

    return sort_validation_findings(findings)
