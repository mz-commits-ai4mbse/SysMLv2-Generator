"""Errors for Source Analysis Unit contracts and persistence."""

class SourceAnalysisUnitError(Exception):
    """Base error for Source Analysis Unit operations."""


class SourceAnalysisUnitValidationError(SourceAnalysisUnitError):
    """Raised when Source Analysis Unit data violates its schema contract."""


class SourceAnalysisUnitIdAllocationError(SourceAnalysisUnitError):
    """Raised when a Source Analysis Unit identifier cannot be allocated."""


class SourceAnalysisUnitReferenceError(SourceAnalysisUnitError):
    """Raised when a referenced Project or Source Projection is invalid."""


class SourceAnalysisUnitAnchorError(SourceAnalysisUnitError):
    """Raised when exact Source Projection anchoring is invalid."""


class SourceAnalysisUnitIntegrityError(SourceAnalysisUnitError):
    """Raised when persisted Source Analysis Unit state is inconsistent."""


class SourceAnalysisUnitPersistenceError(SourceAnalysisUnitError):
    """Raised when Source Analysis Unit persistence fails."""


class SourceAnalysisUnitNotFoundError(SourceAnalysisUnitError):
    """Raised when a requested Source Analysis Unit does not exist."""


class UnsafeSourceAnalysisUnitPathError(SourceAnalysisUnitError):
    """Raised when Source Analysis Unit persistence uses an unsafe path."""


class UnavailableSourceAnalysisProjectionError(SourceAnalysisUnitError):
    """Raised when an unavailable Source Projection cannot be analyzed."""
