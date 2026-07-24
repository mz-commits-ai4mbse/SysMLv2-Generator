"""Tests for read-only Framework Assignment reference validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from modules.framework_assignment.agent_manifest import (
    create_framework_assignment_basis,
    create_framework_assignment_proposal,
)
from modules.framework_assignment.reference_validation import (
    FrameworkAssignmentReferenceValidationResult,
    validate_framework_assignment_references,
)
from modules.framework_assignment.errors import (
    FrameworkAssignmentReferenceError,
)
from modules.information_units.types import InformationUnit
from modules.project_glossary.types import ProjectGlossary
from modules.project_sources.types import SourceManifest
from modules.semantics.types import (
    TuringCoreConcept,
    TuringCoreVocabulary,
)
from modules.terminology_mapping.reference_validation import (
    TerminologyMappingReferenceValidationResult,
)
from modules.terminology_mapping.types import (
    TerminologyMappingCandidate,
)

from tests.test_framework_assignment_candidate_manifest import (
    candidate,
    outcome,
)


PROJECT_ID = "318604"
ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = (
    ROOT / "context/frameworks/turing_rflp_framework.json"
)


def partial(data_type: type, **values: object) -> object:
    value = object.__new__(data_type)
    for name, field_value in values.items():
        object.__setattr__(value, name, field_value)
    return value


def template() -> dict[str, object]:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def information_unit() -> InformationUnit:
    return partial(
        InformationUnit,
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        information_unit_id="IU-000001",
        content_fingerprint="a" * 64,
    )


def source_manifest(
    *,
    role: str = "engineering_source",
    project_id: str = PROJECT_ID,
    source_id: str = "SRC-000001",
) -> SourceManifest:
    return partial(
        SourceManifest,
        project_id=project_id,
        source_id=source_id,
        source_role=role,
    )


def project_glossary(
    *,
    project_id: str = PROJECT_ID,
    revision: int = 1,
) -> ProjectGlossary:
    return partial(
        ProjectGlossary,
        project_id=project_id,
        glossary_revision=revision,
    )


def turing_concept(
    *,
    concept_id: str = "TC-000001",
    targets: tuple[str, ...] = ("FW_SYSTEM_REQUIREMENTS",),
) -> TuringCoreConcept:
    return partial(
        TuringCoreConcept,
        concept_id=concept_id,
        candidate_framework_node_ids=targets,
    )


def vocabulary(
    *,
    version: str = "1.0.0",
    concepts: tuple[TuringCoreConcept, ...] | None = None,
) -> TuringCoreVocabulary:
    return partial(
        TuringCoreVocabulary,
        vocabulary_version=version,
        concepts=(
            (turing_concept(),)
            if concepts is None
            else concepts
        ),
    )


def terminology_candidate(
    *,
    candidate_id: str = "TMC-000001",
    fingerprint: str = "b" * 64,
    project_id: str = PROJECT_ID,
) -> TerminologyMappingCandidate:
    return partial(
        TerminologyMappingCandidate,
        terminology_mapping_candidate_id=candidate_id,
        content_fingerprint=fingerprint,
        project_id=project_id,
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        information_unit_id="IU-000001",
    )


def terminology_validation(
    *,
    candidate_id: str = "TMC-000001",
    valid: bool = True,
) -> TerminologyMappingReferenceValidationResult:
    return TerminologyMappingReferenceValidationResult(
        project_id=PROJECT_ID,
        terminology_mapping_candidate_id=candidate_id,
        checked_proposal_count=1,
        references_valid=valid,
        issues=(),
    )


def validate(
    selected_candidate: object | None = None,
    *,
    unit: object | None = None,
    source: object | None = None,
    selected_template: object | None = None,
    terminology: object | None = None,
    terminology_results: object | None = None,
    selected_vocabulary: object | None = None,
    glossary: object | None = None,
) -> FrameworkAssignmentReferenceValidationResult:
    return validate_framework_assignment_references(
        candidate() if selected_candidate is None else selected_candidate,
        information_unit=(
            information_unit() if unit is None else unit
        ),
        source_manifest=(
            source_manifest() if source is None else source
        ),
        framework_template=(
            template()
            if selected_template is None
            else selected_template
        ),
        terminology_mapping_candidates=(
            (terminology_candidate(),)
            if terminology is None
            else terminology
        ),
        terminology_reference_validation_results=(
            (terminology_validation(),)
            if terminology_results is None
            else terminology_results
        ),
        turing_core_vocabulary=(
            vocabulary()
            if selected_vocabulary is None
            else selected_vocabulary
        ),
        project_glossary=(
            project_glossary()
            if glossary is None
            else glossary
        ),
    )


def codes(
    result: FrameworkAssignmentReferenceValidationResult,
) -> set[str]:
    return {issue.code for issue in result.issues}


def candidate_with_bases(
    *bases: object,
    node_id: str = "FW_SYSTEM_REQUIREMENTS",
) -> object:
    selected_proposal = create_framework_assignment_proposal(
        framework_node_id=node_id,
        assignment_bases=bases,
        rationale="Reference validation test.",
    )
    selected_outcome = outcome(
        proposals=(selected_proposal,)
    )
    return candidate(selected_outcome=selected_outcome)


def information_basis(
    fingerprint: str = "a" * 64,
) -> object:
    return create_framework_assignment_basis(
        basis_type="information_unit",
        reference_id="IU-000001",
        reference_version=fingerprint,
        rationale="Exact Information Unit.",
    )


def terminology_basis(
    fingerprint: str = "b" * 64,
) -> object:
    return create_framework_assignment_basis(
        basis_type="terminology_mapping_candidate",
        reference_id="TMC-000001",
        reference_version=fingerprint,
        rationale="Validated terminology.",
    )


def turing_basis(
    *,
    concept_id: str = "TC-000001",
    version: str = "1.0.0",
) -> object:
    return create_framework_assignment_basis(
        basis_type="turing_core_concept",
        reference_id=concept_id,
        reference_version=version,
        rationale="Curated Turing Core concept.",
    )


def test_valid_references_are_accepted() -> None:
    result = validate()

    assert result.references_valid is True
    assert result.issues == ()
    assert result.checked_proposal_count == 1


def test_result_is_frozen_and_slotted() -> None:
    result = validate()

    assert result.__dataclass_params__.frozen
    assert result.__slots__
    with pytest.raises(FrozenInstanceError):
        result.references_valid = False


def test_unknown_framework_node_is_blocking() -> None:
    selected = candidate_with_bases(
        information_basis(),
        node_id="FW_UNKNOWN",
    )
    result = validate(selected)

    assert "framework_node_not_found" in codes(result)
    assert result.references_valid is False


def test_level_node_is_not_mapping_target() -> None:
    selected = candidate_with_bases(
        information_basis(),
        node_id="FW_LEVEL_SYSTEM",
    )
    result = validate(selected)

    assert "framework_node_not_mapping_target" in codes(result)


def test_invalid_framework_template_is_blocking() -> None:
    selected = template()
    selected["nodes"] = []
    result = validate(selected_template=selected)

    assert "invalid_framework_template" in codes(result)


@pytest.mark.parametrize(
    ("field_name", "value", "expected_code"),
    (
        (
            "framework_template_id",
            "OTHER_FRAMEWORK",
            "framework_template_id_mismatch",
        ),
        (
            "framework_template_version",
            "2.0.0",
            "framework_template_version_mismatch",
        ),
        (
            "turing_core_version",
            "2.0.0",
            "turing_core_version_mismatch",
        ),
        (
            "project_glossary_revision",
            2,
            "project_glossary_revision_mismatch",
        ),
    ),
)
def test_stale_candidate_context_is_blocking(
    field_name: str,
    value: object,
    expected_code: str,
) -> None:
    selected = replace(candidate(), **{field_name: value})
    result = validate(selected)

    assert expected_code in codes(result)


def test_context_only_source_is_forbidden() -> None:
    result = validate(source=source_manifest(role="context_only"))

    assert "source_role_not_framework_eligible" in codes(result)
    assert (
        "context_only_source_assignment_forbidden"
        in codes(result)
    )


def test_unknown_source_role_is_not_eligible() -> None:
    result = validate(source=source_manifest(role="unknown"))

    assert "source_role_not_framework_eligible" in codes(result)


def test_information_unit_context_mismatch_is_blocking() -> None:
    changed = partial(
        InformationUnit,
        project_id=PROJECT_ID,
        source_id="SRC-000999",
        source_projection_id="SP-000001",
        information_unit_id="IU-000001",
        content_fingerprint="a" * 64,
    )
    result = validate(unit=changed)

    assert "candidate_information_unit_source_mismatch" in codes(
        result
    )


def test_source_manifest_context_mismatch_is_blocking() -> None:
    result = validate(
        source=source_manifest(source_id="SRC-000999")
    )

    assert "source_manifest_source_mismatch" in codes(result)


def test_project_glossary_context_mismatch_is_blocking() -> None:
    result = validate(
        glossary=project_glossary(project_id="999999")
    )

    assert "project_glossary_project_mismatch" in codes(result)


def test_declared_terminology_candidates_must_be_supplied() -> None:
    result = validate(terminology=())

    assert "terminology_candidate_collection_mismatch" in codes(
        result
    )


def test_terminology_validations_must_cover_candidates() -> None:
    result = validate(terminology_results=())

    assert "terminology_validation_collection_mismatch" in codes(
        result
    )


def test_invalid_terminology_references_block_assignment() -> None:
    result = validate(
        terminology_results=(
            terminology_validation(valid=False),
        )
    )

    assert (
        "terminology_candidate_references_invalid"
        in codes(result)
    )


def test_terminology_candidate_context_must_match() -> None:
    result = validate(
        terminology=(
            terminology_candidate(project_id="999999"),
        )
    )

    assert "terminology_candidate_context_mismatch" in codes(
        result
    )


def test_information_basis_fingerprint_is_checked() -> None:
    selected = candidate_with_bases(
        information_basis("f" * 64)
    )
    result = validate(selected)

    assert "information_unit_basis_mismatch" in codes(result)


def test_valid_terminology_basis_is_accepted() -> None:
    selected = candidate_with_bases(
        information_basis(),
        terminology_basis(),
    )

    assert validate(selected).references_valid is True


def test_terminology_basis_fingerprint_is_checked() -> None:
    selected = candidate_with_bases(
        information_basis(),
        terminology_basis("f" * 64),
    )
    result = validate(selected)

    assert "terminology_basis_fingerprint_mismatch" in codes(
        result
    )


def test_valid_turing_basis_and_target_are_accepted() -> None:
    selected = candidate_with_bases(
        information_basis(),
        turing_basis(),
    )

    assert validate(selected).references_valid is True


def test_unknown_turing_concept_is_blocking() -> None:
    selected = candidate_with_bases(
        information_basis(),
        turing_basis(concept_id="TC-999999"),
    )
    result = validate(selected)

    assert "turing_core_basis_not_found" in codes(result)


def test_stale_turing_basis_is_blocking() -> None:
    selected = candidate_with_bases(
        information_basis(),
        turing_basis(version="2.0.0"),
    )
    result = validate(selected)

    assert "turing_core_basis_version_mismatch" in codes(result)


def test_turing_framework_target_conflict_is_blocking() -> None:
    selected = candidate_with_bases(
        information_basis(),
        turing_basis(),
        node_id="FW_SYSTEM_FUNCTIONAL",
    )
    result = validate(selected)

    assert "turing_core_framework_target_conflict" in codes(
        result
    )


def test_turing_concept_can_nominate_multiple_targets() -> None:
    selected = candidate_with_bases(
        information_basis(),
        turing_basis(),
        node_id="FW_SYSTEM_FUNCTIONAL",
    )
    selected_vocabulary = vocabulary(
        concepts=(
            turing_concept(
                targets=(
                    "FW_SYSTEM_REQUIREMENTS",
                    "FW_SYSTEM_FUNCTIONAL",
                )
            ),
        )
    )

    assert validate(
        selected,
        selected_vocabulary=selected_vocabulary,
    ).references_valid is True


def test_validation_does_not_mutate_inputs() -> None:
    selected = candidate()
    selected_template = template()
    before = json.dumps(selected_template, sort_keys=True)

    validate(selected, selected_template=selected_template)

    assert json.dumps(selected_template, sort_keys=True) == before
    assert selected == candidate()


@pytest.mark.parametrize(
    ("argument", "bad_value"),
    (
        ("candidate", object()),
        ("information_unit", object()),
        ("source_manifest", object()),
        ("framework_template", []),
        ("terminology_mapping_candidates", []),
        (
            "terminology_reference_validation_results",
            [],
        ),
        ("turing_core_vocabulary", object()),
        ("project_glossary", object()),
    ),
)
def test_wrong_input_types_are_rejected(
    argument: str,
    bad_value: object,
) -> None:
    arguments = {
        "candidate": candidate(),
        "information_unit": information_unit(),
        "source_manifest": source_manifest(),
        "framework_template": template(),
        "terminology_mapping_candidates": (
            terminology_candidate(),
        ),
        "terminology_reference_validation_results": (
            terminology_validation(),
        ),
        "turing_core_vocabulary": vocabulary(),
        "project_glossary": project_glossary(),
    }
    arguments[argument] = bad_value

    with pytest.raises(FrameworkAssignmentReferenceError):
        validate_framework_assignment_references(**arguments)


def test_duplicate_terminology_inputs_are_rejected() -> None:
    item = terminology_candidate()
    validation = terminology_validation()

    with pytest.raises(FrameworkAssignmentReferenceError):
        validate(
            terminology=(item, item),
        )
    with pytest.raises(FrameworkAssignmentReferenceError):
        validate(
            terminology_results=(validation, validation),
        )