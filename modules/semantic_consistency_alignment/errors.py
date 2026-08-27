"""Errors for semantic field consistency alignment."""


class SemanticConsistencyAlignmentError(Exception):
    """Base error for semantic consistency alignment."""


class SemanticConsistencyAlignmentValidationError(
    SemanticConsistencyAlignmentError
):
    """Raised when consistency data violates the alignment contract."""


class SemanticConsistencyAlignmentIntegrityError(
    SemanticConsistencyAlignmentError
):
    """Raised when immutable raw semantic data cannot be preserved."""
