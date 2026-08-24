"""Public API for persona-independent source-grounded Evidence."""

from .errors import (
    SourceEvidenceAnchorError,
    SourceEvidenceError,
    SourceEvidenceIdAllocationError,
    SourceEvidenceIntegrityError,
    SourceEvidenceNotFoundError,
    SourceEvidencePersistenceError,
    SourceEvidenceReferenceError,
    SourceEvidenceValidationError,
    UnavailableSourceEvidenceProjectionError,
    UnsafeSourceEvidencePathError,
)
from .identifiers import (
    format_source_evidence_id,
    is_valid_source_evidence_id,
    next_source_evidence_id,
    source_evidence_id_sequence,
    validate_source_evidence_id,
)
from .manifest import (
    SOURCE_EVIDENCE_SCHEMA_VERSION,
    calculate_source_evidence_content_fingerprint,
    create_source_evidence,
    parse_source_evidence,
    source_evidence_from_json,
    source_evidence_to_dict,
    source_evidence_to_json,
)
from .repository import (
    SEMANTICS_DIRECTORY_NAME,
    SOURCE_EVIDENCE_DIRECTORY_NAME,
    SourceEvidenceRepository,
)
from .types import (
    SourceEvidence,
    SourceEvidenceAnchor,
)


__all__ = [
    "SEMANTICS_DIRECTORY_NAME",
    "SOURCE_EVIDENCE_DIRECTORY_NAME",
    "SOURCE_EVIDENCE_SCHEMA_VERSION",
    "SourceEvidence",
    "SourceEvidenceAnchor",
    "SourceEvidenceAnchorError",
    "SourceEvidenceError",
    "SourceEvidenceIdAllocationError",
    "SourceEvidenceIntegrityError",
    "SourceEvidenceNotFoundError",
    "SourceEvidencePersistenceError",
    "SourceEvidenceReferenceError",
    "SourceEvidenceRepository",
    "SourceEvidenceValidationError",
    "UnavailableSourceEvidenceProjectionError",
    "UnsafeSourceEvidencePathError",
    "calculate_source_evidence_content_fingerprint",
    "create_source_evidence",
    "format_source_evidence_id",
    "is_valid_source_evidence_id",
    "next_source_evidence_id",
    "parse_source_evidence",
    "source_evidence_from_json",
    "source_evidence_id_sequence",
    "source_evidence_to_dict",
    "source_evidence_to_json",
    "validate_source_evidence_id",
]
