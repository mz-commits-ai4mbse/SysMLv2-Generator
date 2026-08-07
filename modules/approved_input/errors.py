"""Exceptions raised by Approved Input operations."""


class ApprovedInputError(Exception):
    """Base exception for all Approved Input failures."""


class ApprovedInputValidationError(ApprovedInputError):
    """Raised when Approved Input data violates its contract."""


class ApprovedInputIntegrityError(ApprovedInputError):
    """Raised when Approved Input data is internally inconsistent."""


class ApprovedInputReferenceError(ApprovedInputError):
    """Raised when Approved Input data references invalid evidence."""


class ApprovedInputPersistenceError(ApprovedInputError):
    """Raised when Approved Input data cannot be persisted safely."""


class ApprovedInputNotFoundError(
    ApprovedInputReferenceError
):
    """Raised when a requested Approved Input does not exist."""


class ApprovedInputEventNotFoundError(
    ApprovedInputReferenceError
):
    """Raised when a requested Approved Input Event does not exist."""


class ApprovedInputIdentifierAllocationError(
    ApprovedInputError
):
    """Base exception for unsafe or exhausted ID allocation."""


class ApprovedInputIdAllocationError(
    ApprovedInputIdentifierAllocationError
):
    """Raised when no safe Approved Input ID can be allocated."""


class ApprovedInputEventIdAllocationError(
    ApprovedInputIdentifierAllocationError
):
    """Raised when no safe Approved Input Event ID can be allocated."""


class ApprovedInputPromotionBlockedError(
    ApprovedInputIntegrityError
):
    """Raised when current authority snapshots block promotion."""


class ApprovedInputRecoveryRequiredError(
    ApprovedInputIntegrityError
):
    """Raised when an interrupted operation requires recovery."""


class UnsafeApprovedInputPathError(ApprovedInputError):
    """Raised when an Approved Input path violates isolation."""
