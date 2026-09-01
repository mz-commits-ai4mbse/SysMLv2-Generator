"""Errors for ADR-032 project-level Engineering Authority reconciliation."""


class ProjectEngineeringAuthorityError(Exception):
    """Base error for project-level Engineering Authority."""


class ProjectEngineeringAuthorityValidationError(
    ProjectEngineeringAuthorityError
):
    """Raised when S4 input violates the public contract."""


class ProjectEngineeringAuthorityIntegrityError(
    ProjectEngineeringAuthorityError
):
    """Raised when immutable authority/provenance bindings are inconsistent."""
