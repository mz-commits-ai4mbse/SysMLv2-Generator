"""Errors for Phase-L final output publication."""


class OutputPublicationError(Exception):
    """Base error for final output publication."""


class OutputPublicationValidationError(OutputPublicationError):
    """Raised when publication data violates the output contract."""


class OutputPublicationIntegrityError(OutputPublicationError):
    """Raised when immutable output evidence no longer matches its identity."""


class OutputPublicationPersistenceError(OutputPublicationError):
    """Raised when final output cannot be persisted safely."""


class OutputPublicationNotFoundError(OutputPublicationError):
    """Raised when an explicitly addressed published output does not exist."""
