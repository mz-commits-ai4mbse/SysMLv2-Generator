from __future__ import annotations

from dataclasses import replace

import pytest

from modules.internal_model import (
    InternalEngineeringModelSnapshot,
    InternalModelAssemblyContext,
    InternalModelAssemblyProvenance,
    InternalModelAssemblyRulesReference,
    InternalModelIntegrityError,
    InternalModelReadService,
    InternalModelRepositoryIssue,
    InternalModelRepositoryScanResult,
    InternalModelStructure,
    InternalModelStructureNode,
    create_internal_engineering_model_manifest,
    create_internal_model_structure,
)
from modules.model_candidates.types import (
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.project_workspace.types import FrameworkTemplateReference


def _context() -> InternalModelAssemblyContext:
    return InternalModelAssemblyContext(
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint="a" * 64,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="b" * 64,
        ),
        assembly_rules_reference=InternalModelAssemblyRulesReference(
            rules_id="TURING_INTERNAL_MODEL_ASSEMBLY",
            rules_version="1.0.0",
            rules_fingerprint="c" * 64,
        ),
    )


def _snapshot(
    *,
    project_id: str = "000042",
    iem_id: str = "IEM-000007",
) -> InternalEngineeringModelSnapshot:
    structure = create_internal_model_structure(
        project_id=project_id,
        internal_engineering_model_id=iem_id,
        framework_template_reference=(
            _context().framework_template_reference
        ),
        nodes=(
            InternalModelStructureNode(
                framework_node_id="FW_LEVEL_SYSTEM",
                mapping_key="system_level",
                name="System Level",
                node_type="level",
                parent_framework_node_id=None,
                order=1,
                internal_model_element_ids=(),
            ),
        ),
    )
    manifest = create_internal_engineering_model_manifest(
        project_id=project_id,
        internal_engineering_model_id=iem_id,
        assembly_input_fingerprint="d" * 64,
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="e" * 64,
        approved_input_snapshot_fingerprint="f" * 64,
        assembly_context=_context(),
        assembly_provenance=InternalModelAssemblyProvenance(
            method="deterministic",
            implementation_reference="I6-test",
            recipe_reference=None,
            context_fingerprint=None,
        ),
        structure_content_fingerprint=structure.content_fingerprint,
        internal_model_element_ids=(),
        internal_model_relationship_ids=(),
        review_decision_references=(),
        accepted_exception_references=(),
        created_at="2026-08-13T10:00:00Z",
    )
    return InternalEngineeringModelSnapshot(
        manifest=manifest,
        structure=structure,
        elements=(),
        relationships=(),
    )


class _Repository:
    def __init__(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        *,
        issues=(),
    ):
        self.snapshot = snapshot
        self.issues = tuple(issues)
        self.scan_calls = []
        self.load_calls = []

    def scan_project(self, project_id):
        self.scan_calls.append(project_id)
        return InternalModelRepositoryScanResult(
            snapshots=(() if self.issues else (self.snapshot,)),
            issues=self.issues,
        )

    def load_snapshot(self, project_id, internal_engineering_model_id):
        self.load_calls.append(
            (project_id, internal_engineering_model_id)
        )
        return self.snapshot


def test_phase_j_read_service_returns_exact_explicit_snapshot():
    snapshot = _snapshot()
    repository = _Repository(snapshot)
    service = InternalModelReadService(repository=repository)

    result = service.load_phase_j_input(
        "000042",
        "IEM-000007",
    )

    assert result == snapshot
    assert repository.scan_calls == ["000042"]
    assert repository.load_calls == [
        ("000042", "IEM-000007")
    ]


def test_phase_j_read_service_never_requests_implicit_latest_snapshot():
    snapshot = _snapshot(iem_id="IEM-000123")
    repository = _Repository(snapshot)
    service = InternalModelReadService(repository=repository)

    service.load_phase_j_input("000042", "IEM-000123")

    assert repository.load_calls == [
        ("000042", "IEM-000123")
    ]


def test_phase_j_read_service_blocks_dirty_repository_before_load():
    snapshot = _snapshot()
    issue = InternalModelRepositoryIssue(
        project_id="000042",
        code="internal_model_persistence_interrupted",
        message="Temporary state requires recovery.",
        issue_level="blocking",
        path=None,
        internal_engineering_model_id="IEM-000008",
    )
    repository = _Repository(snapshot, issues=(issue,))
    service = InternalModelReadService(repository=repository)

    with pytest.raises(InternalModelIntegrityError):
        service.load_phase_j_input("000042", "IEM-000007")

    assert repository.load_calls == []


def test_phase_j_read_service_revalidates_returned_snapshot():
    snapshot = _snapshot()
    corrupted = replace(
        snapshot,
        structure=replace(
            snapshot.structure,
            content_fingerprint="0" * 64,
        ),
    )
    repository = _Repository(corrupted)
    service = InternalModelReadService(repository=repository)

    with pytest.raises(InternalModelIntegrityError):
        service.load_phase_j_input("000042", "IEM-000007")


def test_phase_j_read_contract_returns_representation_neutral_iem():
    snapshot = _snapshot()
    service = InternalModelReadService(
        repository=_Repository(snapshot)
    )

    result = service.load_phase_j_input(
        "000042",
        "IEM-000007",
    )

    assert isinstance(result, InternalEngineeringModelSnapshot)
    assert not hasattr(result, "sysml_text")
    assert not hasattr(result, "generated_sysml")
