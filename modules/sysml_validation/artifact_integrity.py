"""Standalone Phase-K integrity validation for GeneratedSysMLArtifactSet."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
from pathlib import PurePosixPath

from modules.sysml_generation.artifact_builder import (
    GENERATED_SYSML_ARTIFACT_SET_SCHEMA_VERSION,
)
from modules.sysml_generation.errors import SysMLGenerationError
from modules.sysml_generation.identifiers import (
    validate_generated_sysml_symbol,
    validate_generated_sysml_unit_id,
)
from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .fingerprints import calculate_json_fingerprint, validate_sha256_fingerprint
from .finding_support import blocking_finding, sort_validation_findings
from .types import SysMLValidationFinding


def calculate_received_generation_input_fingerprint(
    artifact_set: GeneratedSysMLArtifactSet,
) -> str:
    """Recalculate the J6 generation-input identity from transferred evidence."""

    return calculate_json_fingerprint(
        {
            "source_iem_content_fingerprint": (
                artifact_set.source_iem_content_fingerprint
            ),
            "target_notation_reference": asdict(
                artifact_set.generation_context.target_notation_reference
            ),
            "generation_profile_reference": asdict(
                artifact_set.generation_context.generation_profile_reference
            ),
            "artifact_structure_reference": asdict(
                artifact_set.generation_context.artifact_structure_reference
            ),
            "generator_rules_reference": asdict(
                artifact_set.generation_context.generator_rules_reference
            ),
        }
    )


def calculate_received_artifact_set_fingerprint(
    artifact_set: GeneratedSysMLArtifactSet,
) -> str:
    """Recalculate the exact J6 artifact-set content identity without the IEM."""

    return calculate_json_fingerprint(
        {
            "schema_version": artifact_set.schema_version,
            "project_id": artifact_set.project_id,
            "source_internal_engineering_model_id": (
                artifact_set.source_internal_engineering_model_id
            ),
            "source_iem_content_fingerprint": (
                artifact_set.source_iem_content_fingerprint
            ),
            "generation_context": asdict(artifact_set.generation_context),
            "generation_input_fingerprint": artifact_set.generation_input_fingerprint,
            "generation_provenance": asdict(artifact_set.generation_provenance),
            "units": [asdict(item) for item in artifact_set.units],
            "traceability_entries": [
                asdict(item) for item in artifact_set.traceability_entries
            ],
            "nonblocking_diagnostics": [
                asdict(item) for item in artifact_set.nonblocking_diagnostics
            ],
        }
    )


def validate_artifact_set_integrity(
    artifact_set: GeneratedSysMLArtifactSet,
) -> tuple[SysMLValidationFinding, ...]:
    """Validate the received Phase-J artifact contract without source-IEM access."""

    findings: list[SysMLValidationFinding] = []
    category = "artifact_integrity"

    if not isinstance(artifact_set, GeneratedSysMLArtifactSet):
        return (
            blocking_finding(
                code="K2_ARTIFACT_TYPE_INVALID",
                category=category,
                message="Phase K requires a GeneratedSysMLArtifactSet input.",
            ),
        )

    if artifact_set.schema_version != GENERATED_SYSML_ARTIFACT_SET_SCHEMA_VERSION:
        findings.append(
            blocking_finding(
                code="K2_ARTIFACT_SCHEMA_UNSUPPORTED",
                category=category,
                message="GeneratedSysMLArtifactSet schema_version is unsupported.",
            )
        )
    if not artifact_set.project_id.strip():
        findings.append(
            blocking_finding(
                code="K2_PROJECT_ID_MISSING",
                category=category,
                message="Generated artifact project_id must be non-empty.",
            )
        )
    if not artifact_set.source_internal_engineering_model_id.strip():
        findings.append(
            blocking_finding(
                code="K2_SOURCE_IEM_ID_MISSING",
                category=category,
                message="Generated artifact source IEM identity must be non-empty.",
            )
        )

    for value, label, code in (
        (
            artifact_set.source_iem_content_fingerprint,
            "source IEM content fingerprint",
            "K2_SOURCE_IEM_FINGERPRINT_INVALID",
        ),
        (
            artifact_set.generation_input_fingerprint,
            "generation input fingerprint",
            "K2_GENERATION_INPUT_FINGERPRINT_INVALID",
        ),
        (
            artifact_set.content_fingerprint,
            "artifact-set content fingerprint",
            "K2_ARTIFACT_FINGERPRINT_INVALID",
        ),
    ):
        try:
            validate_sha256_fingerprint(value, label=label)
        except Exception:
            findings.append(
                blocking_finding(
                    code=code,
                    category=category,
                    message=f"{label} is not a valid SHA-256 fingerprint.",
                )
            )

    if not artifact_set.units:
        findings.append(
            blocking_finding(
                code="K2_ARTIFACT_UNITS_EMPTY",
                category=category,
                message="Generated artifact set must contain generated units.",
            )
        )

    unit_ids: set[str] = set()
    unit_paths: set[str] = set()
    global_symbols: set[str] = set()
    for unit in artifact_set.units:
        try:
            validate_generated_sysml_unit_id(unit.unit_id)
        except SysMLGenerationError:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_ID_INVALID",
                    category=category,
                    message="Generated unit ID violates the Phase-J unit-ID contract.",
                    generated_unit_id=unit.unit_id,
                )
            )
        if unit.unit_id in unit_ids:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_ID_DUPLICATE",
                    category=category,
                    message="Generated unit IDs must be unique within the artifact set.",
                    generated_unit_id=unit.unit_id,
                )
            )
        unit_ids.add(unit.unit_id)

        if not _safe_relative_sysml_path(unit.relative_path):
            findings.append(
                blocking_finding(
                    code="K2_UNIT_PATH_UNSAFE",
                    category=category,
                    message="Generated unit path must be a safe relative .sysml path.",
                    generated_unit_id=unit.unit_id,
                )
            )
        if unit.relative_path in unit_paths:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_PATH_DUPLICATE",
                    category=category,
                    message="Generated unit paths must be unique within the artifact set.",
                    generated_unit_id=unit.unit_id,
                )
            )
        unit_paths.add(unit.relative_path)

        expected_content_fingerprint = hashlib.sha256(
            unit.content.encode("utf-8")
        ).hexdigest()
        if expected_content_fingerprint != unit.content_fingerprint:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_FINGERPRINT_MISMATCH",
                    category=category,
                    message="Generated unit content fingerprint does not match exact UTF-8 bytes.",
                    generated_unit_id=unit.unit_id,
                )
            )
        if "\r" in unit.content:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_LINE_ENDING_INVALID",
                    category=category,
                    message="Generated unit must use controlled LF line endings only.",
                    generated_unit_id=unit.unit_id,
                )
            )
        if not unit.content.endswith("\n"):
            findings.append(
                blocking_finding(
                    code="K2_UNIT_TERMINAL_NEWLINE_MISSING",
                    category=category,
                    message="Generated unit must end with the controlled terminal newline.",
                    generated_unit_id=unit.unit_id,
                )
            )

        local_symbols: set[str] = set()
        for symbol in unit.generated_symbol_ids:
            try:
                validate_generated_sysml_symbol(symbol)
            except SysMLGenerationError:
                findings.append(
                    blocking_finding(
                        code="K2_GENERATED_SYMBOL_INVALID",
                        category=category,
                        message="Generated symbol violates the Phase-J symbol contract.",
                        generated_unit_id=unit.unit_id,
                        generated_symbol_id=symbol,
                    )
                )
            if symbol in local_symbols or symbol in global_symbols:
                findings.append(
                    blocking_finding(
                        code="K2_GENERATED_SYMBOL_DUPLICATE",
                        category=category,
                        message="Generated symbols must be unique within the artifact set.",
                        generated_unit_id=unit.unit_id,
                        generated_symbol_id=symbol,
                    )
                )
            local_symbols.add(symbol)
            global_symbols.add(symbol)

        for values, code, label in (
            (
                unit.source_internal_model_element_ids,
                "K2_UNIT_SOURCE_IME_DUPLICATE",
                "source IME IDs",
            ),
            (
                unit.source_internal_model_relationship_ids,
                "K2_UNIT_SOURCE_IMR_DUPLICATE",
                "source IMR IDs",
            ),
        ):
            if len(values) != len(set(values)):
                findings.append(
                    blocking_finding(
                        code=code,
                        category=category,
                        message=f"Generated unit {label} must not contain duplicates.",
                        generated_unit_id=unit.unit_id,
                    )
                )

    if any(item.blocking for item in artifact_set.nonblocking_diagnostics):
        findings.append(
            blocking_finding(
                code="K2_NONBLOCKING_DIAGNOSTIC_CONTRACT_VIOLATION",
                category=category,
                message="Artifact nonblocking_diagnostics must not contain blocking findings.",
            )
        )

    try:
        expected_input = calculate_received_generation_input_fingerprint(artifact_set)
    except Exception:
        expected_input = None
        findings.append(
            blocking_finding(
                code="K2_GENERATION_INPUT_RECALCULATION_FAILED",
                category=category,
                message="Generation-input fingerprint could not be deterministically recalculated.",
            )
        )
    if (
        expected_input is not None
        and expected_input != artifact_set.generation_input_fingerprint
    ):
        findings.append(
            blocking_finding(
                code="K2_GENERATION_INPUT_FINGERPRINT_MISMATCH",
                category=category,
                message="generation_input_fingerprint does not match transferred generation evidence.",
            )
        )

    try:
        expected_artifact = calculate_received_artifact_set_fingerprint(artifact_set)
    except Exception:
        expected_artifact = None
        findings.append(
            blocking_finding(
                code="K2_ARTIFACT_RECALCULATION_FAILED",
                category=category,
                message="Artifact-set fingerprint could not be deterministically recalculated.",
            )
        )
    if expected_artifact is not None and expected_artifact != artifact_set.content_fingerprint:
        findings.append(
            blocking_finding(
                code="K2_ARTIFACT_FINGERPRINT_MISMATCH",
                category=category,
                message="GeneratedSysMLArtifactSet content fingerprint does not match transferred content.",
            )
        )

    return sort_validation_findings(findings)


def _safe_relative_sysml_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and value == path.as_posix()
        and path.suffix == ".sysml"
        and all(part not in {"", ".", ".."} for part in path.parts)
    )
