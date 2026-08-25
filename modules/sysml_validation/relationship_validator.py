"""Deterministic Phase-K relationship and endpoint consistency validation."""

from __future__ import annotations

from dataclasses import dataclass
import re

from modules.sysml_generation.errors import SysMLGenerationError
from modules.sysml_generation.generation_profile import load_generation_profile
from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .finding_support import blocking_finding, sort_validation_findings
from .types import SysMLValidationFinding


_PACKAGE = re.compile(r"^package ([A-Za-z_][A-Za-z0-9_]*) \{$")
_ELEMENT = re.compile(
    r"^(part def|part|action|requirement|use case def) ([A-Za-z_][A-Za-z0-9_]*) \{$"
)
_REFERENCE = r"[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*"
_RELATIONSHIP_FORMS = (
    (
        re.compile(
            rf"^allocate (?P<source>{_REFERENCE}) to (?P<target>{_REFERENCE});$"
        ),
        "TN_014",
        "source_to_target",
    ),
    (
        re.compile(
            rf"^dependency from (?P<source>{_REFERENCE}) to (?P<target>{_REFERENCE});$"
        ),
        "TN_013",
        "source_to_target",
    ),
    (
        re.compile(
            rf"^satisfy (?P<target>{_REFERENCE}) by (?P<source>{_REFERENCE});$"
        ),
        "TN_015",
        "target_by_source",
    ),
)
_KEYWORD_TO_CONSTRUCT = {
    "part def": "TN_003",
    "part": "TN_004",
    "action": "TN_006",
    "requirement": "TN_008",
    "use case def": "TN_012",
}


@dataclass(frozen=True, slots=True)
class _GeneratedEndpoint:
    qualified_reference: str
    generated_symbol_id: str
    target_construct_id: str
    target_element_kind: str


@dataclass(frozen=True, slots=True)
class _RelationshipContract:
    target_construct_id: str
    endpoint_rendering: str
    source_endpoint_kinds: frozenset[str]
    target_endpoint_kinds: frozenset[str]
    source_endpoint_construct_ids: frozenset[str]
    target_endpoint_construct_ids: frozenset[str]


def validate_relationship_consistency(
    artifact_set: GeneratedSysMLArtifactSet,
) -> tuple[SysMLValidationFinding, ...]:
    """Validate generated relationships against target-level endpoint contracts.

    Phase K deliberately validates only information present in the generated
    artifact plus the exact pinned Generation Profile. It does not reload the
    IEM and therefore does not reinterpret original IMR endpoint semantics.
    """

    category = "relationship_consistency"
    findings: list[SysMLValidationFinding] = []

    try:
        profile = load_generation_profile()
    except (SysMLGenerationError, OSError, ValueError, TypeError):
        return (
            blocking_finding(
                code="K3_GENERATION_PROFILE_UNRESOLVABLE",
                category=category,
                message=(
                    "Generation Profile could not be resolved for relationship "
                    "consistency validation."
                ),
            ),
        )

    construct_kinds, contracts, profile_findings = _profile_contracts(profile)
    findings.extend(profile_findings)
    if profile_findings:
        return sort_validation_findings(findings)

    for unit in artifact_set.units:
        entries = [
            entry
            for entry in artifact_set.traceability_entries
            if entry.generated_unit_id == unit.unit_id
        ]
        endpoints = _collect_generated_endpoints(
            unit=unit,
            entries=entries,
            construct_kinds=construct_kinds,
            findings=findings,
        )
        lines = unit.content.splitlines()

        for entry in entries:
            if entry.source_internal_model_relationship_id is None:
                continue
            location = entry.generated_location
            if (
                location is None
                or location.start_line < 1
                or location.end_line != location.start_line
                or location.end_line > len(lines)
            ):
                findings.append(
                    blocking_finding(
                        code="K3_RELATIONSHIP_LOCATION_UNRESOLVABLE",
                        category=category,
                        message=(
                            "Generated relationship requires one resolvable "
                            "single-line location."
                        ),
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )
                continue

            parsed = _parse_relationship(lines[location.start_line - 1].strip())
            if parsed is None:
                findings.append(
                    blocking_finding(
                        code="K3_RELATIONSHIP_FORM_UNRESOLVED",
                        category=category,
                        message=(
                            "Generated relationship form cannot be resolved to a "
                            "supported target-level relationship contract."
                        ),
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )
                continue

            target_construct_id, endpoint_rendering, source_ref, target_ref = parsed
            contract = contracts.get((target_construct_id, endpoint_rendering))
            if contract is None:
                findings.append(
                    blocking_finding(
                        code="K3_RELATIONSHIP_CONTRACT_MISSING",
                        category=category,
                        message=(
                            "Generated relationship has no unambiguous supported "
                            "Generation Profile endpoint contract."
                        ),
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )
                continue

            _validate_endpoint_role(
                role="source",
                reference=source_ref,
                endpoint=endpoints.get(source_ref),
                allowed_kinds=contract.source_endpoint_kinds,
                allowed_constructs=contract.source_endpoint_construct_ids,
                entry=entry,
                findings=findings,
            )
            _validate_endpoint_role(
                role="target",
                reference=target_ref,
                endpoint=endpoints.get(target_ref),
                allowed_kinds=contract.target_endpoint_kinds,
                allowed_constructs=contract.target_endpoint_construct_ids,
                entry=entry,
                findings=findings,
            )

    return sort_validation_findings(findings)


def _profile_contracts(profile):
    category = "relationship_consistency"
    findings: list[SysMLValidationFinding] = []

    construct_kinds: dict[str, str] = {}
    for mapping in profile["element_mappings"]:
        if (
            mapping["mapping_status"] != "supported"
            or mapping["production_generation_allowed"] is not True
        ):
            continue
        construct_id = mapping["target_construct_id"]
        element_kind = mapping["target_element_kind"]
        existing = construct_kinds.get(construct_id)
        if existing is not None and existing != element_kind:
            findings.append(
                blocking_finding(
                    code="K3_PROFILE_ELEMENT_KIND_AMBIGUOUS",
                    category=category,
                    message=(
                        "Generation Profile assigns conflicting target element "
                        "kinds to the same construct."
                    ),
                )
            )
        construct_kinds[construct_id] = element_kind

    contracts: dict[tuple[str, str], _RelationshipContract] = {}
    for mapping in profile["relationship_mappings"]:
        if (
            mapping["mapping_status"] != "supported"
            or mapping["production_generation_allowed"] is not True
        ):
            continue
        contract = _RelationshipContract(
            target_construct_id=mapping["target_construct_id"],
            endpoint_rendering=mapping["endpoint_rendering"],
            source_endpoint_kinds=frozenset(mapping["source_endpoint_kinds"]),
            target_endpoint_kinds=frozenset(mapping["target_endpoint_kinds"]),
            source_endpoint_construct_ids=frozenset(
                mapping["source_endpoint_construct_ids"]
            ),
            target_endpoint_construct_ids=frozenset(
                mapping["target_endpoint_construct_ids"]
            ),
        )
        key = (contract.target_construct_id, contract.endpoint_rendering)
        existing = contracts.get(key)
        if existing is not None and existing != contract:
            findings.append(
                blocking_finding(
                    code="K3_PROFILE_RELATIONSHIP_CONTRACT_AMBIGUOUS",
                    category=category,
                    message=(
                        "Generation Profile exposes conflicting endpoint contracts "
                        "for one rendered relationship construct."
                    ),
                )
            )
        contracts[key] = contract

    return construct_kinds, contracts, findings


def _collect_generated_endpoints(*, unit, entries, construct_kinds, findings):
    category = "relationship_consistency"
    lines = unit.content.splitlines()
    element_entries = [
        entry
        for entry in entries
        if entry.source_internal_model_element_id is not None
    ]
    covered_lines = {
        line_number
        for entry in entries
        if entry.generated_location is not None
        for line_number in range(
            entry.generated_location.start_line,
            entry.generated_location.end_line + 1,
        )
        if entry.generated_location.start_line >= 1
    }
    package_paths = _package_paths_at_trace_starts(lines, covered_lines, element_entries)

    result: dict[str, _GeneratedEndpoint] = {}
    for entry in element_entries:
        location = entry.generated_location
        if (
            location is None
            or location.start_line < 1
            or location.start_line > len(lines)
        ):
            continue
        match = _ELEMENT.fullmatch(lines[location.start_line - 1].strip())
        if match is None or match.group(2) != entry.generated_symbol_id:
            findings.append(
                blocking_finding(
                    code="K3_ENDPOINT_DECLARATION_UNRESOLVABLE",
                    category=category,
                    message=(
                        "Generated endpoint declaration cannot be resolved to its "
                        "traceability symbol."
                    ),
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=location,
                )
            )
            continue

        construct_id = _KEYWORD_TO_CONSTRUCT[match.group(1)]
        element_kind = construct_kinds.get(construct_id)
        if element_kind is None:
            findings.append(
                blocking_finding(
                    code="K3_ENDPOINT_CONSTRUCT_UNSUPPORTED",
                    category=category,
                    message=(
                        "Generated endpoint construct is not supported by the "
                        "pinned Generation Profile."
                    ),
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=location,
                )
            )
            continue

        package_path = package_paths.get(entry.generated_symbol_id)
        if package_path is None or len(package_path) < 2:
            findings.append(
                blocking_finding(
                    code="K3_ENDPOINT_QUALIFICATION_UNRESOLVABLE",
                    category=category,
                    message=(
                        "Generated endpoint cannot be assigned a root-relative "
                        "qualified reference."
                    ),
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=location,
                )
            )
            continue

        qualified_reference = "::".join(
            (*package_path[1:], entry.generated_symbol_id)
        )
        if qualified_reference in result:
            findings.append(
                blocking_finding(
                    code="K3_ENDPOINT_REFERENCE_DUPLICATE",
                    category=category,
                    message=(
                        "Generated endpoint root-relative qualified reference must "
                        "be unique within a generated unit."
                    ),
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=location,
                )
            )
            continue

        result[qualified_reference] = _GeneratedEndpoint(
            qualified_reference=qualified_reference,
            generated_symbol_id=entry.generated_symbol_id,
            target_construct_id=construct_id,
            target_element_kind=element_kind,
        )

    return result


def _package_paths_at_trace_starts(lines, covered_lines, element_entries):
    starts = {
        entry.generated_location.start_line: entry.generated_symbol_id
        for entry in element_entries
        if entry.generated_location is not None
        and entry.generated_location.start_line >= 1
    }
    result: dict[str, tuple[str, ...]] = {}
    stack: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        symbol = starts.get(line_number)
        if symbol is not None:
            result[symbol] = tuple(stack)
        if line_number in covered_lines:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        package = _PACKAGE.fullmatch(stripped)
        if package is not None:
            stack.append(package.group(1))
        elif stripped == "}" and stack:
            stack.pop()

    return result


def _parse_relationship(line: str):
    for pattern, construct_id, endpoint_rendering in _RELATIONSHIP_FORMS:
        match = pattern.fullmatch(line)
        if match is not None:
            return (
                construct_id,
                endpoint_rendering,
                match.group("source"),
                match.group("target"),
            )
    return None


def _validate_endpoint_role(
    *,
    role,
    reference,
    endpoint,
    allowed_kinds,
    allowed_constructs,
    entry,
    findings,
):
    category = "relationship_consistency"
    prefix = "SOURCE" if role == "source" else "TARGET"

    if endpoint is None:
        findings.append(
            blocking_finding(
                code=f"K3_REL_{prefix}_ENDPOINT_UNRESOLVED",
                category=category,
                message=(
                    f"Generated relationship {role} endpoint {reference!r} does "
                    "not resolve to an exact generated element reference."
                ),
                generated_unit_id=entry.generated_unit_id,
                generated_symbol_id=entry.generated_symbol_id,
                generated_location=entry.generated_location,
            )
        )
        return

    if endpoint.target_element_kind not in allowed_kinds:
        findings.append(
            blocking_finding(
                code=f"K3_REL_{prefix}_ENDPOINT_KIND_INCOMPATIBLE",
                category=category,
                message=(
                    f"Generated relationship {role} endpoint kind is incompatible "
                    "with the pinned relationship contract."
                ),
                generated_unit_id=entry.generated_unit_id,
                generated_symbol_id=entry.generated_symbol_id,
                generated_location=entry.generated_location,
            )
        )
    if endpoint.target_construct_id not in allowed_constructs:
        findings.append(
            blocking_finding(
                code=f"K3_REL_{prefix}_ENDPOINT_CONSTRUCT_INCOMPATIBLE",
                category=category,
                message=(
                    f"Generated relationship {role} endpoint construct is "
                    "incompatible with the pinned relationship contract."
                ),
                generated_unit_id=entry.generated_unit_id,
                generated_symbol_id=entry.generated_symbol_id,
                generated_location=entry.generated_location,
            )
        )
