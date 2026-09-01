"""Errors for project-level source-fit assessment."""


class ProjectFitError(Exception):
    """Base error for Project Fit assessment."""


class ProjectFitValidationError(ProjectFitError):
    """Raised when Project Fit input or model output violates the contract."""


class ProjectFitIntegrityError(ProjectFitError):
    """Raised when Project Fit provenance or fingerprints do not bind exactly."""
