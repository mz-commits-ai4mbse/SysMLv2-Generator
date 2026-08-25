"""Bounded Target-Model Formulation authority."""

from .contract import (
    APOLLO_REFERENCE_SOURCE_ID,
    PRIMARY_SYNTAX_ROLE,
    PRIMARY_SYNTAX_SOURCE_ID,
    PROJECT_MODEL_CONTEXT_ROLE,
    TARGET_MODEL_FORMULATION_REVIEW_SCHEMA_VERSION,
    TURING_MODEL_REFERENCE_SOURCE_ID,
    VALIDATED_FIXTURE_ROLE,
    create_formulation_candidate,
    create_formulation_review,
    create_reference_evidence,
    create_review_item,
)
from .errors import TargetModelFormulationError
from .types import (
    REFERENCE_EVIDENCE_ROLES,
    TARGET_MODEL_RELEVANCE_OUTCOMES,
    TARGET_MODEL_SUBJECT_KINDS,
    TargetModelFormulationCandidate,
    TargetModelFormulationReview,
    TargetModelFormulationReviewItem,
    TargetModelReferenceEvidence,
)

__all__ = [
    "APOLLO_REFERENCE_SOURCE_ID",
    "PRIMARY_SYNTAX_ROLE",
    "PRIMARY_SYNTAX_SOURCE_ID",
    "PROJECT_MODEL_CONTEXT_ROLE",
    "REFERENCE_EVIDENCE_ROLES",
    "TARGET_MODEL_FORMULATION_REVIEW_SCHEMA_VERSION",
    "TARGET_MODEL_RELEVANCE_OUTCOMES",
    "TARGET_MODEL_SUBJECT_KINDS",
    "TURING_MODEL_REFERENCE_SOURCE_ID",
    "VALIDATED_FIXTURE_ROLE",
    "TargetModelFormulationCandidate",
    "TargetModelFormulationError",
    "TargetModelFormulationReview",
    "TargetModelFormulationReviewItem",
    "TargetModelReferenceEvidence",
    "create_formulation_candidate",
    "create_formulation_review",
    "create_reference_evidence",
    "create_review_item",
]


# C6c.3b bounded evidence/proposal exports
from .evidence import (
    LocalReferenceAssessment,
    assess_local_references,
)
from .proposals import (
    SUPPORTED_BRIDGE_ELEMENT_TYPES,
    SUPPORTED_BRIDGE_RELATIONSHIP_SEMANTICS,
    build_blk006_formulation_review,
)

# C6c.3c Human formulation authority exports
from .authority import (
    TARGET_MODEL_FORMULATION_AUTHORITY_SET_SCHEMA_VERSION,
    TARGET_MODEL_FORMULATION_DECISION_SCHEMA_VERSION,
    TargetModelFormulationAuthoritySet,
    TargetModelFormulationDecision,
    create_formulation_authority_set,
    create_formulation_decision,
    validate_decision_against_review,
)
from .repository import TargetModelFormulationAuthorityRepository

# C6c.3c.1 live Human review exports
from .live_review import (
    TargetModelFormulationLiveReviewService,
    TargetModelFormulationLiveState,
)
