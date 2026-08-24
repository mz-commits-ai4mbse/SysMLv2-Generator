"""Canonical engineering-subject discovery before Persona interpretation."""

from .context import (
    build_context_preserving_source_input,
    build_discovery_source_spans,
)
from .contract import (
    canonical_subject_set_to_dict,
    canonical_subject_set_to_json,
    materialize_canonical_subject_set,
    parse_subject_discovery_output,
)
from .discovery import EngineeringSubjectDiscoveryAgent
from .errors import (
    EngineeringSubjectConfigurationError,
    EngineeringSubjectError,
    EngineeringSubjectIntegrityError,
    EngineeringSubjectValidationError,
)
from .identifiers import (
    format_canonical_subject_id,
    format_engineering_mention_id,
    format_source_span_id,
    format_source_token_id,
    validate_canonical_subject_id,
    validate_engineering_mention_id,
    validate_source_span_id,
    validate_source_token_id,
)
from .prompt import (
    ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION,
    build_engineering_subject_discovery_instructions,
)
from .types import (
    CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
    IDENTITY_STATUSES,
    SUBJECT_FORMS,
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    DiscoveryMentionProposal,
    DiscoverySourceSpan,
    DiscoverySourceToken,
    DiscoverySubjectProposal,
    EngineeringMention,
    EngineeringSubjectDiscoveryResult,
)

__all__ = [
    "CANONICAL_SUBJECT_SET_SCHEMA_VERSION",
    "ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION",
    "IDENTITY_STATUSES",
    "SUBJECT_FORMS",
    "CanonicalEngineeringSubject",
    "CanonicalSubjectSet",
    "DiscoveryMentionProposal",
    "DiscoverySourceSpan",
    "DiscoverySourceToken",
    "DiscoverySubjectProposal",
    "EngineeringMention",
    "EngineeringSubjectConfigurationError",
    "EngineeringSubjectDiscoveryAgent",
    "EngineeringSubjectDiscoveryResult",
    "EngineeringSubjectError",
    "EngineeringSubjectIntegrityError",
    "EngineeringSubjectValidationError",
    "build_context_preserving_source_input",
    "build_discovery_source_spans",
    "build_engineering_subject_discovery_instructions",
    "canonical_subject_set_to_dict",
    "canonical_subject_set_to_json",
    "format_canonical_subject_id",
    "format_engineering_mention_id",
    "format_source_span_id",
    "format_source_token_id",
    "materialize_canonical_subject_set",
    "parse_subject_discovery_output",
    "validate_canonical_subject_id",
    "validate_engineering_mention_id",
    "validate_source_span_id",
    "validate_source_token_id",
]
