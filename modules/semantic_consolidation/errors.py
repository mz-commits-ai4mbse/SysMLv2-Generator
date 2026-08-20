"""Error hierarchy for semantic proposal consolidation contracts."""


class SemanticConsolidationError(RuntimeError):
    """Base error for semantic consolidation."""


class SemanticConsolidationValidationError(SemanticConsolidationError):
    """Raised when a semantic consolidation artifact is structurally invalid."""


class SemanticConsolidationIntegrityError(SemanticConsolidationError):
    """Raised when a semantic consolidation artifact violates integrity rules."""
