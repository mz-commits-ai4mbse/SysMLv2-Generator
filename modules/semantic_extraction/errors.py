"""Exceptions raised by persona-specific semantic extraction."""


class SemanticExtractionError(Exception):
    """Base exception for semantic extraction failures."""


class SemanticExtractionValidationError(
    SemanticExtractionError
):
    """Raised when an extraction result violates its contract."""


class SemanticExtractionIntegrityError(
    SemanticExtractionError
):
    """Raised when extraction-result content is inconsistent."""


class SemanticExtractionReferenceError(
    SemanticExtractionError
):
    """Raised when an extraction result contains an invalid reference."""


class InformationUnitCandidateIdAllocationError(
    SemanticExtractionError
):
    """Raised when no safe candidate ID can be allocated."""


class InformationUnitCandidateAnchorError(
    SemanticExtractionValidationError
):
    """Raised when candidate anchors violate the projection contract."""


class InformationUnitCandidateDerivationError(
    SemanticExtractionValidationError
):
    """Raised when candidate derivation evidence is invalid."""


class InformationUnitCandidateAssumptionError(
    SemanticExtractionValidationError
):
    """Raised when an assumption candidate lacks missing evidence."""


class NoCandidateRationaleError(
    SemanticExtractionValidationError
):
    """Raised when the zero-candidate rationale contract is violated."""


class DuplicateInformationUnitCandidateError(
    SemanticExtractionIntegrityError
):
    """Raised when professional candidate content is duplicated."""