"""Errors for the Phase-L Final Model Review domain."""

class FinalModelReviewError(Exception):
    """Base error for Final Model Review operations."""


class FinalModelReviewValidationError(FinalModelReviewError):
    """Raised when Final Model Review data violates the domain contract."""


class FinalModelReviewIntegrityError(FinalModelReviewError):
    """Raised when immutable content no longer matches its fingerprint."""


class FinalModelReviewIdAllocationError(FinalModelReviewError):
    """Raised when a project-local Final Model Review ID cannot be allocated."""

class FinalModelReviewNotFoundError(FinalModelReviewError):
    """Raised when requested Final Model Review evidence does not exist."""


class FinalModelReviewPersistenceError(FinalModelReviewError):
    """Raised when Final Model Review evidence cannot be persisted safely."""

class FinalModelReviewReleaseGateError(FinalModelReviewError):
    """Raised when an exact Final Model Review revision is not releasable."""
