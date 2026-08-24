"""Errors for source-grounded Evidence contracts and persistence."""


class SourceEvidenceError(Exception):
    """Base error for Source Evidence operations."""


class SourceEvidenceValidationError(SourceEvidenceError):
    """Raised when Source Evidence data violates its schema contract."""


class SourceEvidenceIdAllocationError(SourceEvidenceError):
    """Raised when a Source Evidence identifier cannot be allocated."""


class SourceEvidenceReferenceError(SourceEvidenceError):
    """Raised when a referenced Project or Source Projection is invalid."""


class SourceEvidenceAnchorError(SourceEvidenceError):
    """Raised when exact Source Projection anchoring is invalid."""


class SourceEvidenceIntegrityError(SourceEvidenceError):
    """Raised when persisted Source Evidence state is inconsistent."""


class SourceEvidencePersistenceError(SourceEvidenceError):
    """Raised when Source Evidence persistence fails."""


class SourceEvidenceNotFoundError(SourceEvidenceError):
    """Raised when requested Source Evidence does not exist."""


class UnsafeSourceEvidencePathError(SourceEvidenceError):
    """Raised when Source Evidence persistence uses an unsafe path."""


class UnavailableSourceEvidenceProjectionError(SourceEvidenceError):
    """Raised when an unavailable Source Projection cannot back Evidence."""
