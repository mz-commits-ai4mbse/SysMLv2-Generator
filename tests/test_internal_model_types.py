from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from modules.internal_model import (
    InternalModelAssemblyContext,
    InternalModelAssemblyFinding,
    InternalModelAssemblyRulesReference,
    InternalModelStructure,
    InternalModelStructureNode,
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


def test_assembly_context_preserves_all_pinned_references():
    context = _context()
    assert context.framework_template_reference.template_id == "TURING_RFLP_FRAMEWORK"
    assert context.model_structure_profile_reference.profile_id == "TURING_MODEL_STRUCTURE"
    assert context.derivation_rules_reference.context_id == "CTX_SYSML_MODEL_DERIVATION_RULES"
    assert context.assembly_rules_reference.rules_id == "TURING_INTERNAL_MODEL_ASSEMBLY"


def test_structure_binds_project_and_iem_snapshot():
    structure = InternalModelStructure(
        schema_version="1.0.0",
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        framework_template_reference=_context().framework_template_reference,
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
        content_fingerprint="d" * 64,
    )
    assert structure.project_id == "000001"
    assert structure.internal_engineering_model_id == "IEM-000001"


def test_structure_node_is_immutable():
    node = InternalModelStructureNode(
        framework_node_id="FW_LEVEL_SYSTEM",
        mapping_key="system_level",
        name="System Level",
        node_type="level",
        parent_framework_node_id=None,
        order=1,
        internal_model_element_ids=(),
    )
    with pytest.raises(FrozenInstanceError):
        node.order = 2  # type: ignore[misc]


def test_assembly_finding_is_immutable():
    finding = InternalModelAssemblyFinding(
        code="ASSEMBLY_BLOCKED",
        message="New semantic decision required.",
        issue_level="blocking",
    )
    with pytest.raises(FrozenInstanceError):
        finding.code = "changed"  # type: ignore[misc]
