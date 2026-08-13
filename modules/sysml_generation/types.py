"""Immutable domain contracts for deterministic Phase-J SysML v2 generation."""

from __future__ import annotations

from dataclasses import dataclass

from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
)


@dataclass(frozen=True, slots=True)
class TargetNotationReference:
    """Pinned identity of the allowed SysML v2 target-notation subset."""

    context_id: str
    version: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class SysMLGenerationProfileReference:
    """Pinned identity of IEM-semantic → SysML rendering rules."""

    profile_id: str
    profile_version: str
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class SysMLArtifactStructureReference:
    """Pinned identity of package/unit organization rules."""

    profile_id: str
    profile_version: str
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class SysMLGeneratorRulesReference:
    """Pinned identity of deterministic generator implementation rules."""

    rules_id: str
    rules_version: str
    rules_fingerprint: str


@dataclass(frozen=True, slots=True)
class SysMLGenerationContext:
    """Exact policy context required to reproduce one generation."""

    target_notation_reference: TargetNotationReference
    generation_profile_reference: SysMLGenerationProfileReference
    artifact_structure_reference: SysMLArtifactStructureReference
    generator_rules_reference: SysMLGeneratorRulesReference


@dataclass(frozen=True, slots=True)
class SysMLGenerationProvenance:
    """Traceable description of deterministic Phase-J serialization."""

    method: str
    implementation_reference: str | None
    context_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class SysMLGenerationFinding:
    """One explicit generation preflight or rendering finding."""

    code: str
    message: str
    issue_level: str
    blocking: bool
    target_type: str | None = None
    target_id: str | None = None
    profile_rule_id: str | None = None


@dataclass(frozen=True, slots=True)
class GeneratedSysMLLocation:
    """Optional deterministic source location inside a generated unit."""

    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class GeneratedSysMLTraceabilityEntry:
    """Exact machine-readable trace from generated text to reviewed authority."""

    generated_unit_id: str
    generated_symbol_id: str
    generated_location: GeneratedSysMLLocation | None
    source_internal_engineering_model_id: str
    source_internal_model_element_id: str | None
    source_internal_model_relationship_id: str | None
    source_model_candidate_id: str
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    review_decision_reference: ModelCandidateReviewDecisionReference
    accepted_exception_reference: (
        ModelCandidateReviewDecisionReference | None
    )


@dataclass(frozen=True, slots=True)
class GeneratedSysMLUnit:
    """One immutable textual unit inside a GeneratedSysMLArtifactSet."""

    unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str
    generated_symbol_ids: tuple[str, ...]
    source_internal_model_element_ids: tuple[str, ...]
    source_internal_model_relationship_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GeneratedSysMLArtifactSet:
    """Validation-ready immutable result of one successful Phase-J generation."""

    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_iem_content_fingerprint: str
    generation_context: SysMLGenerationContext
    generation_input_fingerprint: str
    generation_provenance: SysMLGenerationProvenance
    units: tuple[GeneratedSysMLUnit, ...]
    traceability_entries: tuple[GeneratedSysMLTraceabilityEntry, ...]
    nonblocking_diagnostics: tuple[SysMLGenerationFinding, ...]
    content_fingerprint: str
