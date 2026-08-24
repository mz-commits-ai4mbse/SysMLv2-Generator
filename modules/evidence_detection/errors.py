"""Errors for specialized source-grounded Evidence Detection."""


class EvidenceDetectionError(Exception):
    """Base error for Evidence Detection operations."""


class EvidenceDetectionValidationError(EvidenceDetectionError):
    """Raised when detector input or output violates its contract."""


class EvidenceDetectionGroundingError(EvidenceDetectionError):
    """Raised when a detector excerpt cannot be grounded exactly."""


class EvidenceDetectionReferenceError(EvidenceDetectionError):
    """Raised when detector reference guidance is unavailable or invalid."""
