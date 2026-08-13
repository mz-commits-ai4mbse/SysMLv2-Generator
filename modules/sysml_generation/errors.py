"""Exceptions raised by deterministic Phase-J SysML v2 generation."""


class SysMLGenerationError(Exception):
    """Base exception for Phase-J generation failures."""


class SysMLGenerationValidationError(SysMLGenerationError):
    """Raised when generation-domain data violates an explicit contract."""


class SysMLGenerationProfileError(SysMLGenerationError):
    """Raised when a pinned generation policy artifact is invalid."""


class SysMLGenerationIntegrityError(SysMLGenerationError):
    """Raised when generation inputs or outputs are internally inconsistent."""


class SysMLGenerationBlockedError(SysMLGenerationIntegrityError):
    """Raised when generation cannot proceed without semantic loss or ambiguity."""


class SysMLSyntaxEvidenceError(SysMLGenerationError):
    """Raised when syntax-evidence metadata violates the J1 evidence contract."""
