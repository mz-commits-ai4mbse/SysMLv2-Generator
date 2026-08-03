"""Exceptions raised by Human Review Workspace operations."""


class ReviewWorkspaceError(Exception):
    """Base exception for all Human Review Workspace failures."""


class ReviewValidationError(ReviewWorkspaceError):
    """Raised when review data violates its explicit contract."""


class ReviewIntegrityError(ReviewWorkspaceError):
    """Raised when review data is internally inconsistent."""


class ReviewReferenceError(ReviewWorkspaceError):
    """Raised when review data references an unavailable artifact."""


class ReviewPersistenceError(ReviewWorkspaceError):
    """Raised when review data cannot be persisted safely."""


class ReviewDocumentNotFoundError(ReviewReferenceError):
    """Raised when a requested Review Document does not exist."""


class ReviewDocumentVersionNotFoundError(ReviewReferenceError):
    """Raised when a requested Review Document Version does not exist."""


class ReviewRevisionNotFoundError(ReviewReferenceError):
    """Raised when a requested Review Revision does not exist."""


class ReviewItemNotFoundError(ReviewReferenceError):
    """Raised when a requested Review Item does not exist."""


class ReviewIdentifierAllocationError(ReviewWorkspaceError):
    """Base exception for unsafe or exhausted identifier allocation."""


class ReviewDocumentIdAllocationError(
    ReviewIdentifierAllocationError
):
    """Raised when no safe Review Document ID can be allocated."""


class ReviewDocumentVersionIdAllocationError(
    ReviewIdentifierAllocationError
):
    """Raised when no safe Review Document Version ID can be allocated."""


class ReviewRevisionIdAllocationError(
    ReviewIdentifierAllocationError
):
    """Raised when no safe Review Revision ID can be allocated."""


class ReviewItemIdAllocationError(
    ReviewIdentifierAllocationError
):
    """Raised when no safe Review Item ID can be allocated."""


class ScopedReviewActionIdAllocationError(
    ReviewIdentifierAllocationError
):
    """Raised when no safe Scoped Review Action ID can be allocated."""


class DuplicateReviewRevisionError(ReviewIntegrityError):
    """Raised when an equivalent Review Revision already exists."""


class DuplicateScopedReviewActionError(ReviewIntegrityError):
    """Raised when an equivalent Scoped Review Action already exists."""


class InvalidReviewVersionTransitionError(ReviewValidationError):
    """Raised when a Review Document Version transition is invalid."""


class StaleReviewRevisionError(ReviewIntegrityError):
    """Raised when an operation targets a non-current Review Revision."""


class ReviewFinalizationBlockedError(ReviewIntegrityError):
    """Raised when a Review Document Version cannot be finalized."""


class ReviewRecoveryRequiredError(ReviewIntegrityError):
    """Raised when an interrupted review operation requires recovery."""


class UnsafeReviewWorkspacePathError(ReviewWorkspaceError):
    """Raised when a review path violates project isolation."""
