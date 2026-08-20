"""Immutable types for semantic proposal consolidation."""

from __future__ import annotations

from dataclasses import dataclass


PROPOSAL_KINDS = frozenset({"element", "relationship"})
SEMANTIC_COMPARISON_OUTCOMES = frozenset(
    {"equivalent", "distinct", "uncertain"}
)
SEMANTIC_COMPARISON_METHODS = frozenset(
    {"deterministic_rule", "semantic_model"}
)


@dataclass(frozen=True)
class SemanticUpstreamArtifactBinding:
    """Exact immutable artifact consumed by semantic consolidation."""

    artifact_ref: str
    artifact_fingerprint: str


@dataclass(frozen=True)
class SemanticProposalBinding:
    """Exact proposal identity plus immutable derivation provenance."""

    proposal_ref: str
    proposal_kind: str
    agent_id: str
    persona_id: str
    run_index: int
    upstream_artifact_ref: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SemanticSubject:
    """One proposed semantic identity; not an approved engineering element."""

    semantic_subject_id: str
    proposal_kind: str
    member_proposal_refs: tuple[str, ...]


@dataclass(frozen=True)
class SemanticComparison:
    """Explicit comparison evidence between two exact proposals."""

    left_proposal_ref: str
    right_proposal_ref: str
    outcome: str
    method: str
    trace_ref: str
    rationale: str


@dataclass(frozen=True)
class SemanticConsolidationArtifact:
    """Immutable, fingerprinted result of semantic proposal consolidation."""

    schema_version: str
    artifact_kind: str
    project_id: str
    processing_run_id: str
    created_at_utc: str
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...]
    input_set_fingerprint: str
    proposals: tuple[SemanticProposalBinding, ...]
    subjects: tuple[SemanticSubject, ...]
    comparisons: tuple[SemanticComparison, ...]
    artifact_fingerprint: str
