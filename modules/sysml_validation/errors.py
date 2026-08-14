"""Exceptions raised by deterministic Phase-K SysML v2 validation."""


class SysMLValidationError(Exception):
    """Base exception for Phase-K validation failures."""


class SysMLValidationContractError(SysMLValidationError):
    """Raised when validation-domain data violates an explicit contract."""


class SysMLValidationProfileError(SysMLValidationError):
    """Raised when the pinned Phase-K Validation Profile is invalid."""
