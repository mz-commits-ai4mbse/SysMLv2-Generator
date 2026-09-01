"""Errors for ADR-032 project-level semantic reconciliation."""


class ProjectSemanticReconciliationError(Exception):
    """Base error for project-level semantic reconciliation."""


class ProjectSemanticReconciliationValidationError(
    ProjectSemanticReconciliationError
):
    """Raised when reconciliation input or model output violates the contract."""


class ProjectSemanticReconciliationIntegrityError(
    ProjectSemanticReconciliationError
):
    """Raised when provenance, coverage, or fingerprints do not bind exactly."""
