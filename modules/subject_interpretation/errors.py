"""Errors for canonical-subject Persona interpretation."""


class SubjectInterpretationError(Exception):
    """Base error for Subject interpretation."""


class SubjectInterpretationConfigurationError(SubjectInterpretationError):
    """Raised when Subject interpretation cannot be configured safely."""


class SubjectInterpretationValidationError(SubjectInterpretationError):
    """Raised when LLM output violates the Subject interpretation schema."""


class SubjectInterpretationIntegrityError(SubjectInterpretationError):
    """Raised when fixed Subject identity or provenance would be violated."""
