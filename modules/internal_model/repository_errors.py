"""Repository-specific errors for immutable Internal Engineering Models."""

from .errors import (
    InternalModelPersistenceError,
    InternalModelReferenceError,
)


class InternalEngineeringModelNotFoundError(InternalModelReferenceError):
    """Raised when an explicitly addressed IEM snapshot does not exist."""


class InternalModelRecoveryRequiredError(InternalModelPersistenceError):
    """Raised when interrupted or post-publication state needs recovery."""


class UnsafeInternalModelPathError(InternalModelPersistenceError):
    """Raised when persistence encounters a symbolic-link or unsafe path."""
