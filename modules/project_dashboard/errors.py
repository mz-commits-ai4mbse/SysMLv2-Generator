"""Errors raised by the read-only Project Dashboard presentation layer."""


class ProjectDashboardError(Exception):
    """Base error for P7 dashboard behavior."""


class DashboardValidationError(ProjectDashboardError):
    """Raised when dashboard input or a view-model contract is invalid."""


class DashboardReferenceError(ProjectDashboardError):
    """Raised when an Evidence Reference cannot be resolved safely."""


class DashboardIntegrityError(ProjectDashboardError):
    """Raised when supposedly equivalent dashboard evidence conflicts."""


class DashboardPresentationError(ProjectDashboardError):
    """Raised when domain state cannot be presented without guessing."""



class DashboardDocumentError(ProjectDashboardError):
    """Raised when an internal document preview cannot be prepared safely."""
