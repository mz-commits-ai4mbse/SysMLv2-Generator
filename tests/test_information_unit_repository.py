"""Tests for immutable Information Unit persistence and references."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from modules.information_units.errors import (
    DuplicateInformationUnitContentError,
    IneligibleInformationUnitSourceError,
    InformationUnitAnchorError,
    InformationUnitError,
    InformationUnitNotFoundError,
    InformationUnitPersistenceError,
    InformationUnitReferenceError,
    InformationUnitValidationError,
    UnavailableSourceProjectionError,
    UnsafeInformationUnitPathError,
)
from modules.information_units.repository import (
    INFORMATION_UNITS_DIRECTORY_NAME,
    SEMANTICS_DIRECTORY_NAME,
    InformationUnitRepository,
)
from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitScanResult,
    InformationUnitSourceAnchor,
)
from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.source_projection.repository import (
    SourceProjectionRepository,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)


PROJECT_ID = "318604"
SECOND_PROJECT_ID = "907215"
SOURCE_TEXT = (
    "The system shall preserve source traceability."
)


def fixed_clock() -> datetime:
    return datetime(
        2026,
        7,
        23,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )


@dataclass(frozen=True)
class Environment:
    projects_root: Path
    inputs_root: Path
    workspace: ProjectWorkspace
    source_registry: ProjectSourceRegistry
    projection_repository: SourceProjectionRepository
    repository: InformationUnitRepository
    source_id: str
    projection: SourceProjectionArtifact


@pytest.fixture
def environment(tmp_path: Path) -> Environment:
    projects_root = tmp_path / "projects"
    inputs_root = tmp_path / "inputs"
    inputs_root.mkdir()
    project_ids = iter(
        (
            PROJECT_ID,
            SECOND_PROJECT_ID,
        )
    )
    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: next(project_ids),
        clock=fixed_clock,
    )
    workspace.create_project("Information Unit Test")

    input_path = inputs_root / "requirements.txt"
    input_path.write_text(
        SOURCE_TEXT,
        encoding="utf-8",
    )
    source_registry = ProjectSourceRegistry(
        root=projects_root,
        clock=fixed_clock,
    )
    source = source_registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )
    projection_repository = SourceProjectionRepository(
        root=projects_root,
        clock=fixed_clock,
    )
    projection = projection_repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )
    repository = InformationUnitRepository(
        root=projects_root,
        clock=fixed_clock,
        source_registry=source_registry,
        source_projection_repository=(
            projection_repository
        ),
    )

    return Environment(
        projects_root=projects_root,
        inputs_root=inputs_root,
        workspace=workspace,
        source_registry=source_registry,
        projection_repository=projection_repository,
        repository=repository,
        source_id=source.source_id,
        projection=projection,
    )


def provenance(
    *,
    consensus_report_id: str = "CONSENSUS_TEST",
    llm_model: str = "gpt-test",
) -> InformationUnitExtractionProvenance:
    return InformationUnitExtractionProvenance(
        team_id="TEAM_SEMANTIC_EXTRACTION",
        persona_ids=(
            "PERSONA_DOMAIN_EXPERT",
            "PERSONA_SYSTEMS_ENGINEER",
        ),
        llm_provider="openai",
        llm_model=llm_model,
        prompt_schema_version="1.0.0",
        consensus_report_id=consensus_report_id,
    )


def segment_text(
    projection: SourceProjectionArtifact,
    segment_index: int = 0,
) -> str:
    segment = projection.manifest.segments[segment_index]
    return projection.content[
        segment.start_offset:segment.end_offset
    ]


def full_segment_anchor(
    projection: SourceProjectionArtifact,
    segment_index: int = 0,
) -> InformationUnitSourceAnchor:
    segment = projection.manifest.segments[segment_index]
    text = segment_text(projection, segment_index)
    return InformationUnitSourceAnchor(
        segment_id=segment.segment_id,
        start_offset=0,
        end_offset=len(text),
    )


def create_unit(
    environment: Environment,
    **changes: object,
) -> InformationUnit:
    values: dict[str, object] = {
        "project_id": PROJECT_ID,
        "source_id": environment.source_id,
        "source_projection_id": (
            environment.projection
            .manifest.source_projection_id
        ),
        "source_anchors": (
            full_segment_anchor(environment.projection),
        ),
        "source_excerpt": segment_text(
            environment.projection
        ),
        "interpreted_statement": SOURCE_TEXT,
        "information_type": "requirement",
        "statement_modality": "normative",
        "epistemic_class": "explicit",
        "extraction_provenance": provenance(),
        "confidence": "high",
        "confidence_rationale": (
            "All required personas agreed."
        ),
    }
    values.update(changes)
    return environment.repository.create_information_unit(
        **values
    )


def register_and_project(
    environment: Environment,
    *,
    filename: str,
    text: str,
    source_role: str,
) -> tuple[object, SourceProjectionArtifact]:
    input_path = environment.inputs_root / filename
    input_path.write_text(text, encoding="utf-8")
    source = environment.source_registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=source_role,
    )
    projection = (
        environment.projection_repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )
    )
    return source, projection


def test_repository_constants_are_explicit() -> None:
    assert SEMANTICS_DIRECTORY_NAME == "semantics"
    assert (
        INFORMATION_UNITS_DIRECTORY_NAME
        == "information_units"
    )


def test_empty_repository_lists_no_units(
    environment: Environment,
) -> None:
    assert (
        environment.repository.list_information_units(
            PROJECT_ID
        )
        == ()
    )


def test_empty_repository_scan_is_clean(
    environment: Environment,
) -> None:
    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert result == InformationUnitScanResult()


def test_create_persists_expected_path(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    expected_path = (
        environment.projects_root
        / PROJECT_ID
        / "semantics"
        / "information_units"
        / "IU-000001.json"
    )

    assert information_unit.information_unit_id == "IU-000001"
    assert expected_path.is_file()
    assert (
        environment.repository.information_unit_path(
            PROJECT_ID,
            "IU-000001",
        )
        == expected_path
    )


def test_create_round_trip_is_lossless(
    environment: Environment,
) -> None:
    created = create_unit(environment)
    loaded = environment.repository.load_information_unit(
        PROJECT_ID,
        created.information_unit_id,
    )

    assert loaded == created


def test_public_repository_has_no_mutation_or_delete_api() -> None:
    prohibited = {
        "save_information_unit",
        "update_information_unit",
        "replace_information_unit",
        "delete_information_unit",
    }

    assert prohibited.isdisjoint(dir(InformationUnitRepository))


def test_ids_are_allocated_sequentially(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    second = create_unit(
        environment,
        source_anchors=(
            InformationUnitSourceAnchor(
                first.source_anchors[0].segment_id,
                0,
                10,
            ),
        ),
        source_excerpt=segment_text(
            environment.projection
        )[:10],
        interpreted_statement=(
            "The system exists as an identified subject."
        ),
        information_type="information_item",
        statement_modality="descriptive",
    )

    assert first.information_unit_id == "IU-000001"
    assert second.information_unit_id == "IU-000002"


def test_list_is_ordered_by_identifier(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    second = create_unit(
        environment,
        source_anchors=(
            InformationUnitSourceAnchor(
                first.source_anchors[0].segment_id,
                4,
                10,
            ),
        ),
        source_excerpt=segment_text(
            environment.projection
        )[4:10],
        interpreted_statement="A second semantic statement.",
        information_type="information_item",
        statement_modality="descriptive",
    )

    assert (
        environment.repository.list_information_units(
            PROJECT_ID
        )
        == (first, second)
    )


def test_list_filters_by_source_and_projection(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    other_source, other_projection = register_and_project(
        environment,
        filename="other.txt",
        text="The external unit shall provide status.",
        source_role=ENGINEERING_SOURCE_ROLE,
    )
    other_text = segment_text(other_projection)
    second = create_unit(
        environment,
        source_id=other_source.source_id,
        source_projection_id=(
            other_projection.manifest.source_projection_id
        ),
        source_anchors=(
            full_segment_anchor(other_projection),
        ),
        source_excerpt=other_text,
        interpreted_statement=other_text,
    )

    assert environment.repository.list_information_units(
        PROJECT_ID,
        source_id=first.source_id,
    ) == (first,)
    assert environment.repository.list_information_units(
        PROJECT_ID,
        source_projection_id=(
            second.source_projection_id
        ),
    ) == (second,)


def test_duplicate_professional_content_is_rejected(
    environment: Environment,
) -> None:
    first = create_unit(environment)

    with pytest.raises(
        DuplicateInformationUnitContentError,
        match=first.information_unit_id,
    ):
        create_unit(
            environment,
            extraction_provenance=provenance(
                consensus_report_id="CONSENSUS_REPROCESSING",
                llm_model="other-model",
            ),
            confidence="low",
            confidence_rationale=(
                "The reprocessing run disagreed."
            ),
        )


def test_same_statement_from_different_source_is_preserved(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    other_source, other_projection = register_and_project(
        environment,
        filename="same.txt",
        text=(
            "Independent source wording: "
            + SOURCE_TEXT
        ),
        source_role=ENGINEERING_SOURCE_ROLE,
    )
    second = create_unit(
        environment,
        source_id=other_source.source_id,
        source_projection_id=(
            other_projection.manifest.source_projection_id
        ),
        source_anchors=(
            full_segment_anchor(other_projection),
        ),
        source_excerpt=segment_text(other_projection),
    )

    assert (
        first.content_fingerprint
        != second.content_fingerprint
    )
    assert first.information_unit_id != second.information_unit_id


def test_context_only_source_is_rejected(
    environment: Environment,
) -> None:
    source, projection = register_and_project(
        environment,
        filename="context.txt",
        text="Context terminology only.",
        source_role=CONTEXT_ONLY_SOURCE_ROLE,
    )

    with pytest.raises(
        IneligibleInformationUnitSourceError
    ):
        create_unit(
            environment,
            source_id=source.source_id,
            source_projection_id=(
                projection.manifest.source_projection_id
            ),
            source_anchors=(
                full_segment_anchor(projection),
            ),
            source_excerpt=segment_text(projection),
            interpreted_statement=(
                "Context terminology only."
            ),
            information_type="definition",
            statement_modality="definitional",
        )


def test_role_change_invalidates_engineering_use(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    environment.source_registry.update_source_role(
        PROJECT_ID,
        environment.source_id,
        source_role=CONTEXT_ONLY_SOURCE_ROLE,
    )

    with pytest.raises(
        IneligibleInformationUnitSourceError
    ):
        environment.repository.load_information_unit(
            PROJECT_ID,
            information_unit.information_unit_id,
        )


def test_projection_must_belong_to_source(
    environment: Environment,
) -> None:
    other_source, other_projection = register_and_project(
        environment,
        filename="other-source.txt",
        text="Another source statement.",
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    with pytest.raises(InformationUnitReferenceError):
        create_unit(
            environment,
            source_id=environment.source_id,
            source_projection_id=(
                other_projection.manifest.source_projection_id
            ),
            source_anchors=(
                full_segment_anchor(other_projection),
            ),
            source_excerpt=segment_text(other_projection),
        )

    assert other_source.source_id != environment.source_id


def test_unknown_source_is_rejected(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitReferenceError):
        create_unit(
            environment,
            source_id="SRC-999999",
        )


def test_unknown_projection_is_rejected(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitReferenceError):
        create_unit(
            environment,
            source_projection_id="SP-999999",
        )


def test_unknown_segment_is_rejected(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitAnchorError):
        create_unit(
            environment,
            source_anchors=(
                InformationUnitSourceAnchor(
                    "SEG-999999",
                    0,
                    1,
                ),
            ),
            source_excerpt="T",
        )


def test_anchor_beyond_segment_is_rejected(
    environment: Environment,
) -> None:
    anchor = full_segment_anchor(environment.projection)

    with pytest.raises(InformationUnitAnchorError):
        create_unit(
            environment,
            source_anchors=(
                replace(
                    anchor,
                    end_offset=anchor.end_offset + 1,
                ),
            ),
            source_excerpt=(
                segment_text(environment.projection) + "x"
            ),
        )


def test_excerpt_must_equal_exact_anchor_text(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitAnchorError):
        create_unit(
            environment,
            source_excerpt="Normalized source text.",
        )


def test_multiple_anchors_use_unchanged_concatenation(
    environment: Environment,
) -> None:
    segment = environment.projection.manifest.segments[0]
    text = segment_text(environment.projection)
    anchors = (
        InformationUnitSourceAnchor(
            segment.segment_id,
            0,
            3,
        ),
        InformationUnitSourceAnchor(
            segment.segment_id,
            5,
            10,
        ),
    )
    expected_excerpt = text[0:3] + text[5:10]

    information_unit = create_unit(
        environment,
        source_anchors=anchors,
        source_excerpt=expected_excerpt,
        interpreted_statement=(
            "The selected evidence supports one claim."
        ),
        statement_modality="descriptive",
    )

    assert information_unit.source_excerpt == expected_excerpt


def test_repository_does_not_guess_atomicity(
    environment: Environment,
) -> None:
    information_unit = create_unit(
        environment,
        interpreted_statement=(
            "If a session starts, the system shall stream; "
            "the operator retains control."
        ),
    )

    assert ";" in information_unit.interpreted_statement


def test_same_source_derivation_is_accepted(
    environment: Environment,
) -> None:
    support = create_unit(environment)
    text = segment_text(environment.projection)
    derived = create_unit(
        environment,
        source_anchors=(
            InformationUnitSourceAnchor(
                support.source_anchors[0].segment_id,
                4,
                10,
            ),
        ),
        source_excerpt=text[4:10],
        interpreted_statement=(
            "Traceability is a system obligation."
        ),
        epistemic_class="derivation",
        supporting_information_unit_ids=(
            support.information_unit_id,
        ),
        derivation_rationale=(
            "The supporting requirement entails this "
            "classification."
        ),
    )

    assert (
        derived.supporting_information_unit_ids
        == (support.information_unit_id,)
    )


def test_repository_orders_derivation_support_ids(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    text = segment_text(environment.projection)
    second = create_unit(
        environment,
        source_anchors=(
            InformationUnitSourceAnchor(
                first.source_anchors[0].segment_id,
                0,
                5,
            ),
        ),
        source_excerpt=text[0:5],
        interpreted_statement="A second support statement.",
        information_type="information_item",
        statement_modality="descriptive",
    )
    derived = create_unit(
        environment,
        source_anchors=(
            InformationUnitSourceAnchor(
                first.source_anchors[0].segment_id,
                5,
                12,
            ),
        ),
        source_excerpt=text[5:12],
        interpreted_statement="A derived statement.",
        epistemic_class="derivation",
        supporting_information_unit_ids=(
            second.information_unit_id,
            first.information_unit_id,
        ),
        derivation_rationale="Both units support the result.",
    )

    assert derived.supporting_information_unit_ids == (
        first.information_unit_id,
        second.information_unit_id,
    )


def test_missing_derivation_support_is_rejected(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitReferenceError):
        create_unit(
            environment,
            information_type="rationale",
            statement_modality="descriptive",
            epistemic_class="derivation",
            supporting_information_unit_ids=(
                "IU-999999",
            ),
            derivation_rationale=(
                "The missing unit supposedly supports this."
            ),
        )


def test_cross_source_derivation_is_rejected(
    environment: Environment,
) -> None:
    support = create_unit(environment)
    other_source, other_projection = register_and_project(
        environment,
        filename="derivation-other.txt",
        text="Other source evidence.",
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    with pytest.raises(InformationUnitReferenceError):
        create_unit(
            environment,
            source_id=other_source.source_id,
            source_projection_id=(
                other_projection.manifest.source_projection_id
            ),
            source_anchors=(
                full_segment_anchor(other_projection),
            ),
            source_excerpt=segment_text(other_projection),
            interpreted_statement=(
                "A cross-source derived statement."
            ),
            epistemic_class="derivation",
            supporting_information_unit_ids=(
                support.information_unit_id,
            ),
            derivation_rationale=(
                "Cross-source support is prohibited in P4."
            ),
        )


def test_duplicate_support_input_is_rejected(
    environment: Environment,
) -> None:
    support = create_unit(environment)

    with pytest.raises(InformationUnitValidationError):
        create_unit(
            environment,
            epistemic_class="derivation",
            supporting_information_unit_ids=(
                support.information_unit_id,
                support.information_unit_id,
            ),
            derivation_rationale="Duplicated support.",
        )


def test_self_support_is_rejected(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitError):
        create_unit(
            environment,
            epistemic_class="derivation",
            supporting_information_unit_ids=(
                "IU-000001",
            ),
            derivation_rationale="Circular support.",
        )


class FixedProjectionRepository:
    def __init__(
        self,
        artifact: SourceProjectionArtifact,
    ) -> None:
        self.artifact = artifact

    def load_projection(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> SourceProjectionArtifact:
        return self.artifact


def repository_with_projection(
    environment: Environment,
    artifact: SourceProjectionArtifact,
) -> InformationUnitRepository:
    return InformationUnitRepository(
        root=environment.projects_root,
        clock=fixed_clock,
        source_registry=environment.source_registry,
        source_projection_repository=(
            FixedProjectionRepository(artifact)
        ),
    )


def test_partial_projection_is_accepted(
    environment: Environment,
) -> None:
    partial = replace(
        environment.projection,
        manifest=replace(
            environment.projection.manifest,
            projection_result="partial",
        ),
    )
    repository = repository_with_projection(
        environment,
        partial,
    )
    information_unit = repository.create_information_unit(
        PROJECT_ID,
        environment.source_id,
        partial.manifest.source_projection_id,
        source_anchors=(full_segment_anchor(partial),),
        source_excerpt=segment_text(partial),
        interpreted_statement=SOURCE_TEXT,
        information_type="requirement",
        statement_modality="normative",
        epistemic_class="explicit",
        extraction_provenance=provenance(),
        confidence="medium",
        confidence_rationale=(
            "The projection is partial and requires review."
        ),
    )

    assert information_unit.confidence == "medium"


def test_unavailable_projection_is_rejected(
    environment: Environment,
) -> None:
    unavailable = replace(
        environment.projection,
        manifest=replace(
            environment.projection.manifest,
            projection_result="unavailable",
        ),
    )
    repository = repository_with_projection(
        environment,
        unavailable,
    )

    with pytest.raises(UnavailableSourceProjectionError):
        repository.create_information_unit(
            PROJECT_ID,
            environment.source_id,
            unavailable.manifest.source_projection_id,
            source_anchors=(
                full_segment_anchor(unavailable),
            ),
            source_excerpt=segment_text(unavailable),
            interpreted_statement=SOURCE_TEXT,
            information_type="requirement",
            statement_modality="normative",
            epistemic_class="explicit",
            extraction_provenance=provenance(),
            confidence="low",
            confidence_rationale=(
                "Unavailable projections cannot be used."
            ),
        )


def test_projection_role_must_be_engineering_source(
    environment: Environment,
) -> None:
    context_projection = replace(
        environment.projection,
        manifest=replace(
            environment.projection.manifest,
            source_role=CONTEXT_ONLY_SOURCE_ROLE,
        ),
    )
    repository = repository_with_projection(
        environment,
        context_projection,
    )

    with pytest.raises(
        IneligibleInformationUnitSourceError
    ):
        repository.create_information_unit(
            PROJECT_ID,
            environment.source_id,
            context_projection.manifest.source_projection_id,
            source_anchors=(
                full_segment_anchor(context_projection),
            ),
            source_excerpt=segment_text(context_projection),
            interpreted_statement=SOURCE_TEXT,
            information_type="requirement",
            statement_modality="normative",
            epistemic_class="explicit",
            extraction_provenance=provenance(),
            confidence="low",
            confidence_rationale="Role mismatch.",
        )


def test_clean_scan_returns_valid_units(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert result.information_units == (information_unit,)
    assert result.issues == ()


def test_scan_result_is_immutable(
    environment: Environment,
) -> None:
    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    with pytest.raises(FrozenInstanceError):
        result.issues = ()


def test_scan_reports_invalid_json(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    path = environment.repository.information_unit_path(
        PROJECT_ID,
        information_unit.information_unit_id,
    )
    path.write_text("{invalid", encoding="utf-8")

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert result.information_units == ()
    assert len(result.issues) == 1
    assert result.issues[0].code == "invalid_information_unit"


def test_scan_reports_unexpected_entry(
    environment: Environment,
) -> None:
    create_unit(environment)
    unexpected = (
        environment.repository.information_units_path(
            PROJECT_ID
        )
        / "README.md"
    )
    unexpected.write_text("unexpected", encoding="utf-8")

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert len(result.information_units) == 1
    assert any(
        issue.code == "unexpected_information_unit_entry"
        for issue in result.issues
    )


def test_strict_list_rejects_unexpected_entry(
    environment: Environment,
) -> None:
    create_unit(environment)
    unexpected = (
        environment.repository.information_units_path(
            PROJECT_ID
        )
        / ".unexpected"
    )
    unexpected.write_text("unexpected", encoding="utf-8")

    with pytest.raises(InformationUnitError):
        environment.repository.list_information_units(
            PROJECT_ID
        )


def test_scan_reports_missing_derivation_support(
    environment: Environment,
) -> None:
    support = create_unit(environment)
    text = segment_text(environment.projection)
    derived = create_unit(
        environment,
        source_anchors=(
            InformationUnitSourceAnchor(
                support.source_anchors[0].segment_id,
                4,
                10,
            ),
        ),
        source_excerpt=text[4:10],
        interpreted_statement="Derived statement.",
        epistemic_class="derivation",
        supporting_information_unit_ids=(
            support.information_unit_id,
        ),
        derivation_rationale="Valid support before tampering.",
    )
    environment.repository.information_unit_path(
        PROJECT_ID,
        support.information_unit_id,
    ).unlink()

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert derived not in result.information_units
    assert any(
        issue.code == "invalid_information_unit_reference"
        for issue in result.issues
    )


def test_scan_reports_duplicate_fingerprint(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    first_path = environment.repository.information_unit_path(
        PROJECT_ID,
        first.information_unit_id,
    )
    payload = json.loads(
        first_path.read_text(encoding="utf-8")
    )
    payload["information_unit_id"] = "IU-000002"
    second_path = (
        environment.repository.information_units_path(
            PROJECT_ID
        )
        / "IU-000002.json"
    )
    second_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert result.information_units == ()
    assert any(
        issue.code == "duplicate_information_unit_content"
        for issue in result.issues
    )


def test_strict_list_rejects_duplicate_fingerprint(
    environment: Environment,
) -> None:
    first = create_unit(environment)
    first_path = environment.repository.information_unit_path(
        PROJECT_ID,
        first.information_unit_id,
    )
    payload = json.loads(
        first_path.read_text(encoding="utf-8")
    )
    payload["information_unit_id"] = "IU-000002"
    second_path = (
        environment.repository.information_units_path(
            PROJECT_ID
        )
        / "IU-000002.json"
    )
    second_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        DuplicateInformationUnitContentError
    ):
        environment.repository.list_information_units(
            PROJECT_ID
        )


def test_publishing_same_identifier_never_overwrites(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    path = environment.repository.information_unit_path(
        PROJECT_ID,
        information_unit.information_unit_id,
    )
    before = path.read_bytes()

    with pytest.raises(InformationUnitPersistenceError):
        environment.repository._publish_information_unit(
            information_unit
        )

    assert path.read_bytes() == before


def test_successful_publication_leaves_no_temp_file(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    path = environment.repository.information_unit_path(
        PROJECT_ID,
        information_unit.information_unit_id,
    )

    assert not (
        path.parent / f".{path.name}.tmp"
    ).exists()


def test_existing_temp_file_blocks_publication(
    environment: Environment,
) -> None:
    units_path = environment.repository.information_units_path(
        PROJECT_ID
    )
    units_path.mkdir(parents=True)
    temporary_path = units_path / ".IU-000001.json.tmp"
    temporary_path.write_text("occupied", encoding="utf-8")

    with pytest.raises(InformationUnitError):
        create_unit(environment)

    assert temporary_path.read_text(
        encoding="utf-8"
    ) == "occupied"


@pytest.mark.parametrize(
    "project_id",
    [
        "",
        "31860",
        "3186040",
        "../318604",
        "ABCDEF",
    ],
)
def test_unsafe_project_id_is_rejected(
    environment: Environment,
    project_id: str,
) -> None:
    with pytest.raises(UnsafeInformationUnitPathError):
        environment.repository.information_units_path(
            project_id
        )


@pytest.mark.parametrize(
    "information_unit_id",
    [
        "",
        "IU-000000",
        "IU-00001",
        "../IU-000001",
        "IU-1000000",
    ],
)
def test_unsafe_information_unit_id_is_rejected(
    environment: Environment,
    information_unit_id: str,
) -> None:
    with pytest.raises(UnsafeInformationUnitPathError):
        environment.repository.information_unit_path(
            PROJECT_ID,
            information_unit_id,
        )


def test_unknown_information_unit_is_rejected(
    environment: Environment,
) -> None:
    with pytest.raises(InformationUnitNotFoundError):
        environment.repository.load_information_unit(
            PROJECT_ID,
            "IU-999999",
        )


def test_project_isolation_is_enforced(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    environment.workspace.create_project("Second Project")

    with pytest.raises(InformationUnitNotFoundError):
        environment.repository.load_information_unit(
            SECOND_PROJECT_ID,
            information_unit.information_unit_id,
        )


def test_manifest_project_tampering_is_rejected(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    path = environment.repository.information_unit_path(
        PROJECT_ID,
        information_unit.information_unit_id,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["project_id"] = SECOND_PROJECT_ID
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(InformationUnitError):
        environment.repository.load_information_unit(
            PROJECT_ID,
            information_unit.information_unit_id,
        )


def test_filename_identity_mismatch_is_rejected(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    original = environment.repository.information_unit_path(
        PROJECT_ID,
        information_unit.information_unit_id,
    )
    mismatched = original.parent / "IU-000002.json"
    mismatched.write_bytes(original.read_bytes())

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert any(
        issue.code == "invalid_information_unit"
        and issue.information_unit_id == "IU-000002"
        for issue in result.issues
    )


def test_symlink_information_unit_is_rejected(
    environment: Environment,
    tmp_path: Path,
) -> None:
    units_path = environment.repository.information_units_path(
        PROJECT_ID
    )
    units_path.mkdir(parents=True)
    external = tmp_path / "external.json"
    external.write_text("{}", encoding="utf-8")
    link = units_path / "IU-000001.json"

    try:
        link.symlink_to(external)
    except OSError:
        pytest.skip("Symbolic links are unavailable.")

    with pytest.raises(UnsafeInformationUnitPathError):
        environment.repository.load_information_unit(
            PROJECT_ID,
            "IU-000001",
        )

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )
    assert any(
        issue.code == "unexpected_information_unit_entry"
        for issue in result.issues
    )


def test_symlink_directory_is_diagnostic(
    environment: Environment,
    tmp_path: Path,
) -> None:
    semantics_path = (
        environment.projects_root
        / PROJECT_ID
        / "semantics"
    )
    semantics_path.mkdir(exist_ok=True)
    external = tmp_path / "external-units"
    external.mkdir()
    units_path = semantics_path / "information_units"

    try:
        units_path.symlink_to(
            external,
            target_is_directory=True,
        )
    except OSError:
        pytest.skip("Symbolic links are unavailable.")

    result = environment.repository.scan_information_units(
        PROJECT_ID
    )

    assert result.information_units == ()
    assert result.issues


@pytest.mark.parametrize(
    "clock_value",
    [
        "2026-07-23T12:00:00Z",
        datetime(2026, 7, 23, 12, 0, 0),
    ],
)
def test_invalid_clock_is_rejected(
    environment: Environment,
    clock_value: object,
) -> None:
    repository = InformationUnitRepository(
        root=environment.projects_root,
        clock=lambda: clock_value,
        source_registry=environment.source_registry,
        source_projection_repository=(
            environment.projection_repository
        ),
    )

    with pytest.raises(InformationUnitPersistenceError):
        repository.create_information_unit(
            PROJECT_ID,
            environment.source_id,
            environment.projection
            .manifest.source_projection_id,
            source_anchors=(
                full_segment_anchor(environment.projection),
            ),
            source_excerpt=segment_text(
                environment.projection
            ),
            interpreted_statement=SOURCE_TEXT,
            information_type="requirement",
            statement_modality="normative",
            epistemic_class="explicit",
            extraction_provenance=provenance(),
            confidence="high",
            confidence_rationale="All personas agreed.",
        )


def test_persisted_payload_contains_no_downstream_state(
    environment: Environment,
) -> None:
    information_unit = create_unit(environment)
    path = environment.repository.information_unit_path(
        PROJECT_ID,
        information_unit.information_unit_id,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))

    prohibited = {
        "human_review",
        "engineering_approval",
        "framework_assignment",
        "supersedes_information_unit_id",
        "processing_run_id",
    }

    assert prohibited.isdisjoint(payload)