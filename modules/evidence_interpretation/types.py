"""Immutable types for shared source-grounded Evidence interpretation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.semantic_consensus.types import SemanticConsensusResult
from modules.semantic_extraction.types import SemanticExtractionAgentResult


@dataclass(frozen=True, slots=True)
class EvidenceInterpretationValue:
    """One persona interpretation bound only by an existing Evidence ID."""

    source_evidence_id: str
    interpreted_statement: str
    information_type: str
    statement_modality: str
    epistemic_class: str
    missing_evidence: str | None
    extraction_rationale: str
    uncertainties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SharedEvidenceInterpretationResult:
    """One complete multi-persona interpretation and consensus result."""

    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    source_evidence_ids: tuple[str, ...]
    required_personas: tuple[str, ...]
    runs_per_persona: int
    agent_results: tuple[SemanticExtractionAgentResult, ...]
    consensus_result: SemanticConsensusResult
    binding_summary_path: Path
    consensus_result_path: Path
