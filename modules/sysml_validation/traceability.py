"""Deterministic validation of Phase-J generated traceability evidence."""

from __future__ import annotations

from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .finding_support import blocking_finding, sort_validation_findings
from .types import SysMLValidationFinding


def validate_traceability(
    artifact_set: GeneratedSysMLArtifactSet,
) -> tuple[SysMLValidationFinding, ...]:
    """Validate generated-unit/symbol/source coverage without source-IEM reload."""

    findings: list[SysMLValidationFinding] = []
    category = "traceability"
    units = {unit.unit_id: unit for unit in artifact_set.units}
    expected_symbols = {
        (unit.unit_id, symbol)
        for unit in artifact_set.units
        for symbol in unit.generated_symbol_ids
    }
    expected_ime = {
        item
        for unit in artifact_set.units
        for item in unit.source_internal_model_element_ids
    }
    expected_imr = {
        item
        for unit in artifact_set.units
        for item in unit.source_internal_model_relationship_ids
    }

    seen_symbols: set[tuple[str, str]] = set()
    seen_ime: set[str] = set()
    seen_imr: set[str] = set()
    occupied_lines: dict[tuple[str, int], str] = {}

    for entry in artifact_set.traceability_entries:
        key = (entry.generated_unit_id, entry.generated_symbol_id)
        if key in seen_symbols:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SYMBOL_DUPLICATE",
                    category=category,
                    message="Generated unit/symbol traceability key must be unique.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        seen_symbols.add(key)

        unit = units.get(entry.generated_unit_id)
        if unit is None:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_UNIT_UNKNOWN",
                    category=category,
                    message="Traceability entry references an unknown generated unit.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        elif entry.generated_symbol_id not in unit.generated_symbol_ids:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SYMBOL_UNKNOWN",
                    category=category,
                    message="Traceability entry references a symbol not declared by its generated unit.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

        if (
            entry.source_internal_engineering_model_id
            != artifact_set.source_internal_engineering_model_id
        ):
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SOURCE_IEM_MISMATCH",
                    category=category,
                    message="Traceability entry source IEM identity differs from the artifact-set source IEM.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

        has_ime = entry.source_internal_model_element_id is not None
        has_imr = entry.source_internal_model_relationship_id is not None
        if has_ime == has_imr:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SOURCE_KIND_INVALID",
                    category=category,
                    message="Traceability entry must reference exactly one source IME or source IMR.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        elif has_ime:
            source_id = entry.source_internal_model_element_id
            assert source_id is not None
            if source_id in seen_ime:
                findings.append(
                    blocking_finding(
                        code="K2_TRACE_IME_DUPLICATE",
                        category=category,
                        message="A source IME must have exactly one generated traceability entry.",
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=entry.generated_location,
                    )
                )
            seen_ime.add(source_id)
        else:
            source_id = entry.source_internal_model_relationship_id
            assert source_id is not None
            if source_id in seen_imr:
                findings.append(
                    blocking_finding(
                        code="K2_TRACE_IMR_DUPLICATE",
                        category=category,
                        message="A source IMR must have exactly one generated traceability entry.",
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=entry.generated_location,
                    )
                )
            seen_imr.add(source_id)

        if not entry.source_model_candidate_id.strip():
            findings.append(
                blocking_finding(
                    code="K2_TRACE_CANDIDATE_ID_MISSING",
                    category=category,
                    message="Traceability entry must retain its source Model Candidate identity.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        if not entry.approved_input_references:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_APPROVED_INPUT_MISSING",
                    category=category,
                    message="Traceability entry must retain at least one Approved Input reference.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        if entry.review_decision_reference.candidate_id != entry.source_model_candidate_id:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_REVIEW_CANDIDATE_MISMATCH",
                    category=category,
                    message="Review Decision reference must target the traced source Model Candidate.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        if (
            entry.accepted_exception_reference is not None
            and entry.accepted_exception_reference.candidate_id
            != entry.source_model_candidate_id
        ):
            findings.append(
                blocking_finding(
                    code="K2_TRACE_EXCEPTION_CANDIDATE_MISMATCH",
                    category=category,
                    message="Accepted-exception reference must target the traced source Model Candidate.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

        location = entry.generated_location
        if location is None:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_LOCATION_MISSING",
                    category=category,
                    message="Every generated engineering representation requires a generated line location.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                )
            )
            continue
        if unit is None:
            continue
        line_count = len(unit.content.splitlines())
        if (
            location.start_line < 1
            or location.end_line < location.start_line
            or location.end_line > line_count
        ):
            findings.append(
                blocking_finding(
                    code="K2_TRACE_LOCATION_OUT_OF_RANGE",
                    category=category,
                    message="Traceability location is outside generated unit content.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=location,
                )
            )
            continue
        for line in range(location.start_line, location.end_line + 1):
            line_key = (entry.generated_unit_id, line)
            owner = occupied_lines.get(line_key)
            if owner is not None and owner != entry.generated_symbol_id:
                findings.append(
                    blocking_finding(
                        code="K2_TRACE_LOCATION_OVERLAP",
                        category=category,
                        message="Generated traceability locations for different symbols must not overlap.",
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )
                break
            occupied_lines[line_key] = entry.generated_symbol_id

    if seen_symbols != expected_symbols:
        findings.append(
            blocking_finding(
                code="K2_TRACE_SYMBOL_COVERAGE_MISMATCH",
                category=category,
                message="Traceability must cover every generated unit/symbol exactly once.",
            )
        )
    if seen_ime != expected_ime:
        findings.append(
            blocking_finding(
                code="K2_TRACE_IME_COVERAGE_MISMATCH",
                category=category,
                message="Traceability source-IME coverage must match generated-unit source evidence exactly.",
            )
        )
    if seen_imr != expected_imr:
        findings.append(
            blocking_finding(
                code="K2_TRACE_IMR_COVERAGE_MISMATCH",
                category=category,
                message="Traceability source-IMR coverage must match generated-unit source evidence exactly.",
            )
        )

    return sort_validation_findings(findings)
