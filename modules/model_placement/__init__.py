"""Human-reviewed target-framework placement contracts."""

from .comparison import compare_model_placement_personas
from .errors import ModelPlacementContractError
from .types import (
    MODEL_PLACEMENT_AGREEMENT_LEVELS,
    MODEL_PLACEMENT_RESULTS,
    MODEL_PLACEMENT_SCHEMA_VERSION,
    ModelPlacementBatchComparison,
    ModelPlacementPersonaProposal,
    ModelPlacementReviewItem,
    ModelPlacementRuleSupport,
)

__all__ = [
    "MODEL_PLACEMENT_AGREEMENT_LEVELS",
    "MODEL_PLACEMENT_RESULTS",
    "MODEL_PLACEMENT_SCHEMA_VERSION",
    "ModelPlacementBatchComparison",
    "ModelPlacementContractError",
    "ModelPlacementPersonaProposal",
    "ModelPlacementReviewItem",
    "ModelPlacementRuleSupport",
    "compare_model_placement_personas",
]

from .review_repository import ModelPlacementReviewRepository
from .approved_set import (
    APPROVED_MODEL_PLACEMENT_SET_SCHEMA_VERSION,
    ApprovedModelPlacement,
    ApprovedModelPlacementSet,
    build_approved_model_placement_set,
)
from .review_types import (
    MODEL_PLACEMENT_REVIEW_OUTCOMES,
    ModelPlacementReviewDecision,
    ModelPlacementReviewState,
)

__all__ += [
    "APPROVED_MODEL_PLACEMENT_SET_SCHEMA_VERSION",
    "ApprovedModelPlacement",
    "ApprovedModelPlacementSet",
    "build_approved_model_placement_set",
    "MODEL_PLACEMENT_REVIEW_OUTCOMES",
    "ModelPlacementReviewDecision",
    "ModelPlacementReviewRepository",
    "ModelPlacementReviewState",
]
