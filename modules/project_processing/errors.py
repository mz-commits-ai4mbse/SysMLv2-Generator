"""Exceptions raised by project-oriented processing operations."""


class ProjectProcessingError(Exception):
    """Base exception for all project-processing failures."""


class ProcessingValidationError(ProjectProcessingError):
    """Raised when processing data violates its explicit contract."""


class ProcessingIntegrityError(ProjectProcessingError):
    """Raised when persisted processing data is inconsistent."""


class ProcessingReferenceError(ProjectProcessingError):
    """Raised when processing data references an invalid artifact."""


class ProcessingPersistenceError(ProjectProcessingError):
    """Raised when processing data cannot be persisted safely."""


class ProcessingRunNotFoundError(ProjectProcessingError):
    """Raised when a requested Processing Run does not exist."""


class ProcessingDecisionNotFoundError(ProjectProcessingError):
    """Raised when a requested Processing Decision does not exist."""


class ProcessingIdentifierAllocationError(ProjectProcessingError):
    """Base exception for exhausted or unsafe identifier allocation."""


class ProcessingRunIdAllocationError(
    ProcessingIdentifierAllocationError
):
    """Raised when no safe Processing Run ID can be allocated."""


class ProcessingEventIdAllocationError(
    ProcessingIdentifierAllocationError
):
    """Raised when no safe Processing Event ID can be allocated."""


class ProcessingAttemptIdAllocationError(
    ProcessingIdentifierAllocationError
):
    """Raised when no safe Processing Attempt ID can be allocated."""


class ProcessingDecisionIdAllocationError(
    ProcessingIdentifierAllocationError
):
    """Raised when no safe Processing Decision ID can be allocated."""


class InvalidProcessingTransitionError(
    ProcessingValidationError
):
    """Raised when a Processing Run transition is not permitted."""


class DuplicateProcessingEventError(
    ProcessingIntegrityError
):
    """Raised when an equivalent Processing Event already exists."""


class DuplicateProcessingDecisionError(
    ProcessingIntegrityError
):
    """Raised when an equivalent Processing Decision already exists."""


class ProcessingEventChainError(
    ProcessingIntegrityError
):
    """Raised when an Event History is incomplete or inconsistent."""


class ProcessingRecoveryRequiredError(
    ProcessingIntegrityError
):
    """Raised when an interrupted operation requires explicit recovery."""


class UnsafeProcessingPathError(ProjectProcessingError):
    """Raised when a processing path violates project isolation."""