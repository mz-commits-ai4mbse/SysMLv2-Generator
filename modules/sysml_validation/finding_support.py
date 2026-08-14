"""Shared deterministic finding helpers for Phase-K internal validators."""

from __future__ import annotations

from modules.sysml_generation.types import GeneratedSysMLLocation

from .types import SysMLValidationFinding, SysMLValidationLocation


def to_validation_location(
    location: GeneratedSysMLLocation | None,
) -> SysMLValidationLocation | None:
    """Project a Phase-J generated location into the Phase-K finding contract."""

    if location is None:
        return None
    return SysMLValidationLocation(
        start_line=location.start_line,
        end_line=location.end_line,
    )


def blocking_finding(
    *,
    code: str,
    category: str,
    message: str,
    generated_unit_id: str | None = None,
    generated_symbol_id: str | None = None,
    generated_location: GeneratedSysMLLocation | None = None,
) -> SysMLValidationFinding:
    """Build one normalized deterministic blocking error finding."""

    return SysMLValidationFinding(
        code=code,
        category=category,
        severity="error",
        blocking=True,
        message=message,
        generated_unit_id=generated_unit_id,
        generated_symbol_id=generated_symbol_id,
        generated_location=to_validation_location(generated_location),
    )


def sort_validation_findings(
    findings: tuple[SysMLValidationFinding, ...]
    | list[SysMLValidationFinding],
) -> tuple[SysMLValidationFinding, ...]:
    """Return findings in the Validation Profile canonical order."""

    def key(item: SysMLValidationFinding) -> tuple[object, ...]:
        location = item.generated_location
        return (
            0 if item.blocking else 1,
            item.category,
            item.generated_unit_id or "",
            location.start_line if location is not None else 0,
            location.start_column
            if location is not None and location.start_column is not None
            else 0,
            item.code,
            item.message,
        )

    return tuple(sorted(findings, key=key))
