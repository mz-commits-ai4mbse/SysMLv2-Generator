from modules.engineering_subjects import (
    EngineeringSubjectGroundingError,
    EngineeringSubjectGroundingViolation,
    EngineeringSubjectIntegrityError,
    EngineeringSubjectValidationError,
)
from modules.project_ingestion.service import (
    _subject_discovery_failure_reason,
)


def _grounding_error():
    return EngineeringSubjectGroundingError(
        (
            EngineeringSubjectGroundingViolation(
                code="unknown_source_span",
                subject_index=1,
                mention_index=1,
                source_span_id="SPAN-999999",
                start_token_id="TOK-000001",
                end_token_id="TOK-000002",
            ),
        )
    )


def test_subject_discovery_failure_reason_is_specific():
    assert (
        _subject_discovery_failure_reason(_grounding_error())
        == "subject_discovery_grounding_failed"
    )
    assert (
        _subject_discovery_failure_reason(
            EngineeringSubjectValidationError("invalid JSON contract")
        )
        == "subject_discovery_validation_failed"
    )
    assert (
        _subject_discovery_failure_reason(
            EngineeringSubjectIntegrityError("internal integrity")
        )
        == "subject_discovery_integrity_failed"
    )
    assert (
        _subject_discovery_failure_reason(RuntimeError("provider failure"))
        == "subject_discovery_execution_failed"
    )
