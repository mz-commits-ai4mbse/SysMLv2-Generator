"""Errors for ADR-032 S5 Model Impact Reconciliation."""


class ModelImpactReconciliationError(Exception):
    """Base error for project-level Model Impact Reconciliation."""


class ModelImpactReconciliationValidationError(
    ModelImpactReconciliationError
):
    """Raised when S5 input violates the public contract."""


class ModelImpactReconciliationIntegrityError(
    ModelImpactReconciliationError
):
    """Raised when authority/model traceability is inconsistent."""
