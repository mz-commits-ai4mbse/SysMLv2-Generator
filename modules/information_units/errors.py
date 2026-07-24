"""Exceptions raised by Information Unit operations."""


class InformationUnitError(Exception):
    """Base exception for Information Unit failures."""


class InformationUnitValidationError(InformationUnitError):
    """Raised when an Information Unit violates its contract."""


class InformationUnitIntegrityError(InformationUnitError):
    """Raised when persisted Information Unit data is inconsistent."""


class InformationUnitNotFoundError(InformationUnitError):
    """Raised when a requested Information Unit does not exist."""


class InformationUnitPersistenceError(InformationUnitError):
    """Raised when an Information Unit cannot be persisted safely."""


class UnsafeInformationUnitPathError(InformationUnitError):
    """Raised when an Information Unit path escapes its project boundary."""


class InformationUnitIdAllocationError(InformationUnitError):
    """Raised when no safe Information Unit ID can be allocated."""


class InformationUnitReferenceError(InformationUnitError):
    """Raised when an Information Unit reference violates isolation."""


class InformationUnitAnchorError(InformationUnitValidationError):
    """Raised when source anchors violate the projection contract."""


class InformationUnitDerivationError(InformationUnitValidationError):
    """Raised when derivation evidence violates the semantic contract."""


class InformationUnitAssumptionError(InformationUnitValidationError):
    """Raised when assumption evidence violates the semantic contract."""


class DuplicateInformationUnitContentError(
    InformationUnitIntegrityError
):
    """Raised when professional content is already persisted."""


class IneligibleInformationUnitSourceError(
    InformationUnitReferenceError
):
    """Raised when a source may not create engineering Information Units."""


class UnavailableSourceProjectionError(
    InformationUnitReferenceError
):
    """Raised when no usable deterministic projection is available."""