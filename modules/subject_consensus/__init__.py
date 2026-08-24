"""Public API for deterministic canonical Subject consensus."""

from .analyzer import (
    analyze_subject_consensus,
    subject_consensus_result_to_dict,
    subject_consensus_result_to_json,
)
from .errors import (
    SubjectConsensusConfigurationError,
    SubjectConsensusError,
    SubjectConsensusIntegrityError,
)
from .types import (
    CONFIDENCE_LEVELS,
    CONSENSUS_LEVELS,
    SUBJECT_CONSENSUS_SCHEMA_VERSION,
    ConsensusValueDistribution,
    FieldConsensusAssessment,
    PersonaDiagnosticVariant,
    PersonaStatementVariant,
    RelationshipConsensusOutcome,
    SharedSubjectConsensusResult,
    SubjectConsensusOutcome,
)


__all__ = [
    "CONFIDENCE_LEVELS",
    "CONSENSUS_LEVELS",
    "SUBJECT_CONSENSUS_SCHEMA_VERSION",
    "ConsensusValueDistribution",
    "FieldConsensusAssessment",
    "PersonaDiagnosticVariant",
    "PersonaStatementVariant",
    "RelationshipConsensusOutcome",
    "SharedSubjectConsensusResult",
    "SubjectConsensusConfigurationError",
    "SubjectConsensusError",
    "SubjectConsensusIntegrityError",
    "SubjectConsensusOutcome",
    "analyze_subject_consensus",
    "subject_consensus_result_to_dict",
    "subject_consensus_result_to_json",
]
