"""Semantic consistency alignment for coupled interpretation fields."""

from .contract import (
    PRE_REVIEW_EPISTEMIC_CLASSES,
    apply_semantic_consistency_alignment,
    find_semantic_consistency_needs,
    pair_is_consistent,
    parse_semantic_consistency_response,
)
from .errors import (
    SemanticConsistencyAlignmentError,
    SemanticConsistencyAlignmentIntegrityError,
    SemanticConsistencyAlignmentValidationError,
)
from .prompt import (
    SEMANTIC_CONSISTENCY_PROMPT_SCHEMA_VERSION,
    build_semantic_consistency_input,
    build_semantic_consistency_instructions,
)
from .serialization import (
    semantic_consistency_result_to_dict,
    semantic_consistency_result_to_json,
)
from .service import SemanticConsistencyAlignmentService
from .types import (
    SEMANTIC_CONSISTENCY_ALIGNMENT_SCHEMA_VERSION,
    SemanticConsistencyDecision,
    SemanticConsistencyNeed,
    SemanticConsistencyResult,
)

__all__ = [name for name in globals() if not name.startswith("_")]
