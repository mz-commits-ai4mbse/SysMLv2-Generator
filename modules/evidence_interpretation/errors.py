"""Errors for shared source-grounded Evidence interpretation."""


class EvidenceInterpretationError(Exception):
    """Base error for shared-Evidence interpretation."""


class EvidenceInterpretationValidationError(EvidenceInterpretationError):
    """Raised when interpretation input or output violates its contract."""


class EvidenceInterpretationConfigurationError(EvidenceInterpretationError):
    """Raised when the configured persona team cannot execute the contract."""


class EvidenceInterpretationIntegrityError(EvidenceInterpretationError):
    """Raised when deterministic Evidence/result binding is inconsistent."""
