"""Errors for deterministic field-level canonical Subject consensus."""


class SubjectConsensusError(Exception):
    """Base error for R4c.4 Subject consensus."""


class SubjectConsensusConfigurationError(SubjectConsensusError):
    """Raised when consensus configuration is invalid."""


class SubjectConsensusIntegrityError(SubjectConsensusError):
    """Raised when fixed Subject/Persona invariants are violated."""
