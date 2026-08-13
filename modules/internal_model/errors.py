"""Exceptions raised by the Phase-I Internal Engineering Model layer."""


class InternalModelError(Exception):
    """Base exception for Internal Engineering Model failures."""


class InternalModelValidationError(InternalModelError):
    """Raised when Internal Model data violates its explicit contract."""


class InternalModelIntegrityError(InternalModelError):
    """Raised when Internal Model content is internally inconsistent."""


class InternalModelReferenceError(InternalModelError):
    """Raised when Internal Model data references an invalid artifact."""


class InternalModelPersistenceError(InternalModelError):
    """Raised when validated Internal Model content cannot be persisted."""


class InternalModelAssemblyError(InternalModelError):
    """Raised when deterministic Internal Model assembly fails."""


class InternalModelAssemblyBlockedError(InternalModelIntegrityError):
    """Raised when Phase-I assembly cannot proceed without new semantics."""


class InternalEngineeringModelIdAllocationError(InternalModelError):
    """Raised when no safe Internal Engineering Model ID is available."""


class InternalModelElementIdAllocationError(InternalModelError):
    """Raised when no safe Internal Model Element ID is available."""


class InternalModelRelationshipIdAllocationError(InternalModelError):
    """Raised when no safe Internal Model Relationship ID is available."""
