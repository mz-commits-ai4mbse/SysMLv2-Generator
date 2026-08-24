"""Errors for canonical engineering-subject discovery."""


class EngineeringSubjectError(Exception):
    """Base error for canonical engineering-subject processing."""


class EngineeringSubjectValidationError(EngineeringSubjectError):
    """Raised when external or LLM-provided data violates the contract."""


class EngineeringSubjectIntegrityError(EngineeringSubjectError):
    """Raised when source identity or grounding cannot be preserved."""


class EngineeringSubjectConfigurationError(EngineeringSubjectError):
    """Raised when subject discovery cannot be configured safely."""
