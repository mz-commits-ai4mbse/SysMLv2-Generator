"""Errors for immutable project-level reconciliation persistence."""


class ProjectReconciliationPersistenceError(ValueError):
    """Base error for I2A persistence and binding failures."""


class ProjectReconciliationPersistenceIntegrityError(
    ProjectReconciliationPersistenceError
):
    """Raised when persisted reconciliation evidence is inconsistent."""


class ProjectReconciliationPersistenceValidationError(
    ProjectReconciliationPersistenceError
):
    """Raised when persistence input violates the exact contract."""
