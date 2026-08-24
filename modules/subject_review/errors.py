"""Errors for subject-centric Human Engineering Review projection."""


class SubjectReviewError(Exception):
    """Base error for R4c.5 subject review."""


class SubjectReviewConfigurationError(SubjectReviewError):
    """Raised when review projection configuration is invalid."""


class SubjectReviewIntegrityError(SubjectReviewError):
    """Raised when bound Subject/interpretation/consensus inputs disagree."""


class SubjectReviewDecisionError(SubjectReviewError):
    """Raised when a Human Review decision is invalid."""
