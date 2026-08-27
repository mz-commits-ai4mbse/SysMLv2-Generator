"""Errors for controlled classification alignment."""


class ClassificationAlignmentError(Exception):
    """Base error for classification alignment."""


class ClassificationAlignmentValidationError(ClassificationAlignmentError):
    """Raised when mapper-provided data violates the alignment contract."""


class ClassificationAlignmentIntegrityError(ClassificationAlignmentError):
    """Raised when immutable raw classification identity cannot be preserved."""
