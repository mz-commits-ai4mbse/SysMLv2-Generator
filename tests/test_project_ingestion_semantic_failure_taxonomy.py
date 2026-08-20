from modules.project_ingestion.service import (
    _semantic_consolidation_failure_reason,
)
from modules.semantic_consolidation.errors import (
    SemanticConsolidationError,
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)


def test_integrity_failure_keeps_explicit_integrity_reason() -> None:
    error = SemanticConsolidationIntegrityError(
        "Upstream proposal identity does not match the exact C2 artifact."
    )

    assert _semantic_consolidation_failure_reason(error) == (
        "semantic_consolidation_integrity_failed"
    )


def test_validation_failure_is_not_mislabeled_as_integrity() -> None:
    error = SemanticConsolidationValidationError(
        "Semantic artifact is structurally invalid."
    )

    assert _semantic_consolidation_failure_reason(error) == (
        "semantic_consolidation_validation_failed"
    )


def test_generic_semantic_contract_failure_is_not_mislabeled_as_integrity() -> None:
    error = SemanticConsolidationError(
        "Semantic consolidation contract failed."
    )

    assert _semantic_consolidation_failure_reason(error) == (
        "semantic_consolidation_contract_failed"
    )
