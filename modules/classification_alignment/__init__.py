"""Controlled vocabulary alignment for LLM semantic classifications."""

from .contract import (
    CONTROLLED_CLASSIFICATION_VALUES,
    NEUTRAL_CLASSIFICATION_FALLBACKS,
    apply_classification_alignment,
    fallback_unclassified_decisions,
    find_classification_alignment_needs,
    lexical_alignment_decision,
    parse_classification_alignment_response,
)
from .errors import (
    ClassificationAlignmentError,
    ClassificationAlignmentIntegrityError,
    ClassificationAlignmentValidationError,
)
from .prompt import (
    CLASSIFICATION_ALIGNMENT_PROMPT_SCHEMA_VERSION,
    build_classification_alignment_input,
    build_classification_alignment_instructions,
)
from .serialization import (
    classification_alignment_result_to_dict,
    classification_alignment_result_to_json,
)
from .service import ClassificationAlignmentService
from .types import (
    CLASSIFICATION_ALIGNMENT_SCHEMA_VERSION,
    ClassificationAlignmentDecision,
    ClassificationAlignmentNeed,
    ClassificationAlignmentResult,
)

__all__ = [name for name in globals() if not name.startswith("_")]
