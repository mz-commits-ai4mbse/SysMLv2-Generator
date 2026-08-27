"""Errors for canonical engineering-subject discovery."""

from __future__ import annotations

from dataclasses import dataclass


GROUNDING_VIOLATION_CODES = frozenset(
    {
        "unknown_source_span",
        "context_only_positive_mention",
        "unknown_token",
        "token_not_in_claimed_span",
        "reversed_token_range",
    }
)


class EngineeringSubjectError(Exception):
    """Base error for canonical engineering-subject processing."""


class EngineeringSubjectValidationError(EngineeringSubjectError):
    """Raised when external or LLM-provided data violates the contract."""


class EngineeringSubjectIntegrityError(EngineeringSubjectError):
    """Raised when source identity or grounding cannot be preserved."""


@dataclass(frozen=True, slots=True)
class EngineeringSubjectGroundingViolation:
    """One deterministic LLM-to-source grounding contract violation."""

    code: str
    subject_index: int
    mention_index: int
    source_span_id: str
    start_token_id: str
    end_token_id: str
    token_role: str | None = None
    actual_source_span_id: str | None = None

    def __post_init__(self) -> None:
        if self.code not in GROUNDING_VIOLATION_CODES:
            raise ValueError(f"Unsupported grounding violation code: {self.code}")
        if self.subject_index < 1 or self.mention_index < 1:
            raise ValueError(
                "Grounding violation subject/mention indices must be positive."
            )
        if self.token_role not in {None, "start", "end"}:
            raise ValueError(
                "Grounding violation token_role must be start, end, or None."
            )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "subject_index": self.subject_index,
            "mention_index": self.mention_index,
            "source_span_id": self.source_span_id,
            "start_token_id": self.start_token_id,
            "end_token_id": self.end_token_id,
        }
        if self.token_role is not None:
            payload["token_role"] = self.token_role
        if self.actual_source_span_id is not None:
            payload["actual_source_span_id"] = self.actual_source_span_id
        return payload


class EngineeringSubjectGroundingError(EngineeringSubjectIntegrityError):
    """Raised for repairable LLM grounding violations only."""

    def __init__(
        self,
        violations: tuple[EngineeringSubjectGroundingViolation, ...],
    ) -> None:
        if not violations:
            raise ValueError(
                "EngineeringSubjectGroundingError requires at least one violation."
            )
        self.violations = tuple(violations)
        codes = ", ".join(item.code for item in self.violations)
        super().__init__(
            "Subject discovery grounding violated "
            f"{len(self.violations)} rule(s): {codes}."
        )


class EngineeringSubjectConfigurationError(EngineeringSubjectError):
    """Raised when subject discovery cannot be configured safely."""
