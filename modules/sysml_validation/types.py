"""Immutable domain contracts for deterministic Phase-K SysML v2 validation."""

from __future__ import annotations

from dataclasses import dataclass


VALIDATION_STATUSES = ("valid", "invalid", "incomplete")
PUBLICATION_GATES = ("passed", "blocked")
VALIDATION_SEVERITIES = ("info", "warning", "error")
VALIDATION_FINDING_CATEGORIES = (
    "artifact_integrity",
    "validation_context",
    "target_notation",
    "artifact_structure",
    "relationship_consistency",
    "traceability",
    "external_syntax",
    "external_semantics",
    "external_warning",
    "validator_infrastructure",
)
EXTERNAL_VALIDATOR_EXECUTION_STATUSES = (
    "completed",
    "unavailable",
    "failed",
)


@dataclass(frozen=True, slots=True)
class SysMLValidationProfileReference:
    """Pinned identity of the Phase-K validation policy."""

    profile_id: str
    profile_version: str
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class SysMLValidationLocation:
    """Normalized generated-unit location for one validation finding."""

    start_line: int
    end_line: int
    start_column: int | None = None
    end_column: int | None = None


@dataclass(frozen=True, slots=True)
class SysMLExternalValidatorIdentity:
    """Resolved identity of one external validation environment."""

    validator_id: str
    tool_name: str
    tool_version: str | None
    command_contract_id: str
    configuration_fingerprint: str


@dataclass(frozen=True, slots=True)
class SysMLExternalValidationEvidence:
    """Deterministic evidence from one required external-validator execution."""

    validator_identity: SysMLExternalValidatorIdentity
    execution_status: str
    exit_code: int | None
    normalized_diagnostic_count: int


@dataclass(frozen=True, slots=True)
class SysMLExternalValidationRun:
    """One normalized external-validator run ready for Phase-K assembly."""

    evidence: SysMLExternalValidationEvidence
    findings: tuple["SysMLValidationFinding", ...]


@dataclass(frozen=True, slots=True)
class SysMLValidationFinding:
    """One normalized Phase-K validation finding."""

    code: str
    category: str
    severity: str
    blocking: bool
    message: str
    generated_unit_id: str | None = None
    generated_symbol_id: str | None = None
    generated_location: SysMLValidationLocation | None = None
    validator_id: str | None = None
    validator_rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class SysMLValidationResult:
    """Immutable fingerprint-bound result transferred from Phase K to Phase L."""

    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str
    validation_profile_reference: SysMLValidationProfileReference
    validation_input_fingerprint: str
    external_validator_evidence: tuple[SysMLExternalValidationEvidence, ...]
    findings: tuple[SysMLValidationFinding, ...]
    validation_status: str
    publication_gate: str
    content_fingerprint: str
