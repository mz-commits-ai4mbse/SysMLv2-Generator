"""Deterministic validation of generated SysML artifact/package structure."""

from __future__ import annotations

import re

from modules.sysml_generation.artifact_structure import load_artifact_structure_profile
from modules.sysml_generation.errors import SysMLGenerationError
from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .finding_support import blocking_finding, sort_validation_findings
from .types import SysMLValidationFinding


_PACKAGE = re.compile(r"^package ([A-Za-z_][A-Za-z0-9_]*) \{$")


def validate_artifact_structure(
    artifact_set: GeneratedSysMLArtifactSet,
) -> tuple[SysMLValidationFinding, ...]:
    """Validate the current one-unit package projection and canonical placement."""

    findings: list[SysMLValidationFinding] = []
    category = "artifact_structure"
    try:
        profile = load_artifact_structure_profile()
    except (SysMLGenerationError, OSError, ValueError, TypeError):
        return (
            blocking_finding(
                code="K2_STRUCTURE_PROFILE_UNRESOLVABLE",
                category=category,
                message="Artifact Structure Profile could not be resolved for structure validation.",
            ),
        )

    expected_units = profile["output_units"]
    if len(artifact_set.units) != len(expected_units):
        findings.append(
            blocking_finding(
                code="K2_STRUCTURE_UNIT_COUNT_MISMATCH",
                category=category,
                message="Generated unit count does not match the pinned Artifact Structure Profile.",
            )
        )
        return sort_validation_findings(findings)

    for unit, expected in zip(artifact_set.units, expected_units, strict=True):
        if unit.unit_id != expected["unit_id"] or unit.relative_path != expected["relative_path"]:
            findings.append(
                blocking_finding(
                    code="K2_STRUCTURE_UNIT_IDENTITY_MISMATCH",
                    category=category,
                    message="Generated unit identity/path does not match the pinned Artifact Structure Profile.",
                    generated_unit_id=unit.unit_id,
                )
            )
            continue
        findings.extend(_validate_unit_structure(unit, artifact_set, profile))

    return sort_validation_findings(findings)


def _validate_unit_structure(unit, artifact_set, profile):
    findings: list[SysMLValidationFinding] = []
    category = "artifact_structure"
    traces = [
        entry
        for entry in artifact_set.traceability_entries
        if entry.generated_unit_id == unit.unit_id and entry.generated_location is not None
    ]
    covered_lines = {
        line
        for entry in traces
        for line in range(
            entry.generated_location.start_line,
            entry.generated_location.end_line + 1,
        )
        if entry.generated_location.start_line >= 1
    }
    traces_by_start = {entry.generated_location.start_line: entry for entry in traces}

    lines = unit.content.splitlines()
    stack: list[str] = []
    declarations: list[tuple[str, ...]] = []
    trace_paths: dict[str, tuple[str, ...]] = {}
    last_framework_close_line = 0

    for lineno, line in enumerate(lines, start=1):
        entry = traces_by_start.get(lineno)
        if entry is not None:
            trace_paths[entry.generated_symbol_id] = tuple(stack)
        if lineno in covered_lines:
            continue
        if not line.strip():
            continue
        stripped = line.strip()
        match = _PACKAGE.fullmatch(stripped)
        if match is not None:
            expected_indent = "    " * len(stack)
            if line[: len(line) - len(line.lstrip())] != expected_indent:
                findings.append(
                    blocking_finding(
                        code="K2_STRUCTURE_INDENTATION_MISMATCH",
                        category=category,
                        message="Package indentation does not match deterministic four-space nesting.",
                        generated_unit_id=unit.unit_id,
                    )
                )
            stack.append(match.group(1))
            declarations.append(tuple(stack))
            continue
        if stripped == "}":
            if not stack:
                findings.append(
                    blocking_finding(
                        code="K2_STRUCTURE_UNBALANCED_CLOSE",
                        category=category,
                        message="Generated package structure contains an unmatched closing brace.",
                        generated_unit_id=unit.unit_id,
                    )
                )
                continue
            expected_indent = "    " * (len(stack) - 1)
            if line[: len(line) - len(line.lstrip())] != expected_indent:
                findings.append(
                    blocking_finding(
                        code="K2_STRUCTURE_INDENTATION_MISMATCH",
                        category=category,
                        message="Package closing indentation does not match deterministic four-space nesting.",
                        generated_unit_id=unit.unit_id,
                    )
                )
            if len(stack) > 1:
                last_framework_close_line = lineno
            stack.pop()
            continue
        findings.append(
            blocking_finding(
                code="K2_STRUCTURE_UNTRACED_TEXT",
                category=category,
                message="Generated unit contains untraced text outside the permitted package skeleton.",
                generated_unit_id=unit.unit_id,
            )
        )

    if stack:
        findings.append(
            blocking_finding(
                code="K2_STRUCTURE_PACKAGE_UNCLOSED",
                category=category,
                message="Generated package structure is not balanced.",
                generated_unit_id=unit.unit_id,
            )
        )

    expected_paths = _expected_package_paths(profile)
    if declarations != expected_paths:
        findings.append(
            blocking_finding(
                code="K2_STRUCTURE_PACKAGE_HIERARCHY_MISMATCH",
                category=category,
                message="Generated package hierarchy/order does not match the pinned Artifact Structure Profile.",
                generated_unit_id=unit.unit_id,
            )
        )

    element_entries = [
        entry for entry in traces if entry.source_internal_model_element_id is not None
    ]
    relationship_entries = [
        entry for entry in traces if entry.source_internal_model_relationship_id is not None
    ]
    allowed_element_paths = set(expected_paths[1:])
    root_path = (profile["root_package"]["package_name"],)

    for entry in element_entries:
        path = trace_paths.get(entry.generated_symbol_id, ())
        if path not in allowed_element_paths or len(path) < 2:
            findings.append(
                blocking_finding(
                    code="K2_STRUCTURE_ELEMENT_PLACEMENT_INVALID",
                    category=category,
                    message="Generated element must be located inside a profile-defined Framework package.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

    for entry in relationship_entries:
        path = trace_paths.get(entry.generated_symbol_id, ())
        if path != root_path or entry.generated_location.start_line <= last_framework_close_line:
            findings.append(
                blocking_finding(
                    code="K2_STRUCTURE_RELATIONSHIP_PLACEMENT_INVALID",
                    category=category,
                    message="Generated relationships must be placed at root after all Framework packages.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

    groups: dict[tuple[str, ...], list] = {}
    for entry in element_entries:
        groups.setdefault(trace_paths.get(entry.generated_symbol_id, ()), []).append(entry)
    for entries in groups.values():
        source_ids = [entry.source_internal_model_element_id for entry in entries]
        if source_ids != sorted(source_ids):
            findings.append(
                blocking_finding(
                    code="K2_STRUCTURE_ELEMENT_ORDER_MISMATCH",
                    category=category,
                    message="Generated elements within a package must follow canonical IME ordering.",
                    generated_unit_id=unit.unit_id,
                )
            )
            break

    relationship_ids = [
        entry.source_internal_model_relationship_id for entry in relationship_entries
    ]
    if relationship_ids != sorted(relationship_ids):
        findings.append(
            blocking_finding(
                code="K2_STRUCTURE_RELATIONSHIP_ORDER_MISMATCH",
                category=category,
                message="Generated relationships must follow canonical IMR ordering.",
                generated_unit_id=unit.unit_id,
            )
        )

    return findings


def _expected_package_paths(profile) -> list[tuple[str, ...]]:
    root = profile["root_package"]["package_name"]
    mappings = profile["framework_package_mappings"]
    by_parent: dict[str | None, list[dict[str, object]]] = {}
    for item in mappings:
        by_parent.setdefault(item["parent_framework_node_id"], []).append(item)
    for children in by_parent.values():
        children.sort(key=lambda item: (item["order"], item["framework_node_id"]))

    result: list[tuple[str, ...]] = [(root,)]

    def visit(parent_id: str | None, prefix: tuple[str, ...]) -> None:
        for item in by_parent.get(parent_id, []):
            path = prefix + (item["package_name"],)
            result.append(path)
            visit(item["framework_node_id"], path)

    visit(None, (root,))
    return result
