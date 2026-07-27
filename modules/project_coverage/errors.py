"""Error hierarchy for project coverage and preliminary support assessment."""


class ProjectCoverageError(Exception):
    """Base error for all P6 project-coverage operations."""


class CoverageValidationError(ProjectCoverageError, ValueError):
    """Raised when supplied coverage data violates the P6 contract."""


class CoverageProfileError(CoverageValidationError):
    """Raised when a Preliminary Support Profile is invalid."""


class CoverageReferenceError(ProjectCoverageError):
    """Raised when project-local assessment references cannot be resolved."""


class CoverageIntegrityError(ProjectCoverageError):
    """Raised when valid-looking records form an inconsistent evidence graph."""


class CoverageAssessmentError(ProjectCoverageError):
    """Raised when a deterministic project assessment cannot be completed."""