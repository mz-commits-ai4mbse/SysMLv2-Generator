"""Public contracts for semantic proposal consolidation."""

from .artifact import (
    SEMANTIC_CONSOLIDATION_ARTIFACT_KIND,
    SEMANTIC_CONSOLIDATION_SCHEMA_VERSION,
    build_semantic_consolidation_artifact,
    calculate_artifact_fingerprint,
    calculate_input_set_fingerprint,
    semantic_consolidation_artifact_from_dict,
    semantic_consolidation_artifact_to_dict,
    validate_semantic_consolidation_artifact,
)
from .errors import (
    SemanticConsolidationError,
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from .types import (
    PROPOSAL_KINDS,
    SEMANTIC_COMPARISON_METHODS,
    SEMANTIC_COMPARISON_OUTCOMES,
    SemanticComparison,
    SemanticConsolidationArtifact,
    SemanticProposalBinding,
    SemanticSubject,
    SemanticUpstreamArtifactBinding,
)

__all__ = [
    "PROPOSAL_KINDS",
    "SEMANTIC_COMPARISON_METHODS",
    "SEMANTIC_COMPARISON_OUTCOMES",
    "SEMANTIC_CONSOLIDATION_ARTIFACT_KIND",
    "SEMANTIC_CONSOLIDATION_SCHEMA_VERSION",
    "SemanticComparison",
    "SemanticConsolidationArtifact",
    "SemanticConsolidationError",
    "SemanticConsolidationIntegrityError",
    "SemanticConsolidationValidationError",
    "SemanticProposalBinding",
    "SemanticSubject",
    "SemanticUpstreamArtifactBinding",
    "build_semantic_consolidation_artifact",
    "calculate_artifact_fingerprint",
    "calculate_input_set_fingerprint",
    "semantic_consolidation_artifact_from_dict",
    "semantic_consolidation_artifact_to_dict",
    "validate_semantic_consolidation_artifact",
]
