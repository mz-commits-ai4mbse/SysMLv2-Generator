from __future__ import annotations

from dataclasses import replace

import pytest

from modules.internal_model import (
    InternalModelAssemblyContext,
    InternalModelAssemblyProvenance,
    InternalModelAssemblyRulesReference,
    InternalModelAttribute,
    InternalModelIntegrityError,
    InternalModelStructureNode,
    create_internal_engineering_model_manifest,
    create_internal_model_element,
    create_internal_model_relationship,
    create_internal_model_structure,
    internal_engineering_model_manifest_from_json,
    internal_engineering_model_manifest_to_json,
    internal_model_element_from_json,
    internal_model_element_to_json,
    internal_model_relationship_from_json,
    internal_model_relationship_to_json,
    internal_model_structure_from_json,
    internal_model_structure_to_json,
    validate_internal_engineering_model_manifest,
    validate_internal_model_element,
    validate_internal_model_relationship,
    validate_internal_model_structure,
)
from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.project_workspace.types import FrameworkTemplateReference


def _ain():
    return ModelCandidateApprovedInputReference(
        approved_input_id="AIN-000001",
        content_fingerprint="a" * 64,
        stable_subject_key="subject.alpha",
        provenance_role="direct_support",
    )


def _element_review(decision="accepted"):
    return ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCD-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision=decision,
        decision_fingerprint="b" * 64,
    )


def _relationship_review(decision="accepted"):
    return ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCD-000002",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision=decision,
        decision_fingerprint="c" * 64,
    )


def _context():
    return InternalModelAssemblyContext(
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint="d" * 64,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="e" * 64,
        ),
        assembly_rules_reference=InternalModelAssemblyRulesReference(
            rules_id="TURING_INTERNAL_MODEL_ASSEMBLY",
            rules_version="1.0.0",
            rules_fingerprint="f" * 64,
        ),
    )


def _element():
    return create_internal_model_element(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        internal_model_element_id="IME-000001",
        model_subject_key="subject.alpha",
        source_model_element_candidate_id="MCE-000001",
        source_model_element_candidate_fingerprint="1" * 64,
        name="Alpha",
        description="Logical component.",
        model_area="system.logical",
        element_type="logical_component",
        framework_assignment="FW_SYSTEM_LOGICAL",
        terminology_assignment=None,
        attributes=(InternalModelAttribute(name="kind", value="logical"),),
        comparison_anchor_id="system.logical:subject.alpha",
        approved_input_references=(_ain(),),
        review_decision_reference=_element_review(),
        accepted_exception_reference=None,
    )


def _relationship():
    return create_internal_model_relationship(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        internal_model_relationship_id="IMR-000001",
        source_internal_model_element_id="IME-000001",
        target_internal_model_element_id="IME-000002",
        source_model_subject_key="subject.alpha",
        target_model_subject_key="subject.beta",
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        source_model_relationship_candidate_id="MCR-000001",
        source_model_relationship_candidate_fingerprint="2" * 64,
        approved_input_references=(_ain(),),
        review_decision_reference=_relationship_review(),
        accepted_exception_reference=None,
    )


def _structure():
    return create_internal_model_structure(
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
            InternalModelStructureNode(
                framework_node_id="FW_SYSTEM_LOGICAL",
                mapping_key="system.logical",
                name="Logical",
                node_type="framework_node",
                parent_framework_node_id="FW_LEVEL_SYSTEM",
                order=1,
                internal_model_element_ids=("IME-000001",),
            ),
        ),
    )


def _manifest():
    return create_internal_engineering_model_manifest(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        assembly_input_fingerprint="3" * 64,
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="4" * 64,
        approved_input_snapshot_fingerprint="5" * 64,
        assembly_context=_context(),
        assembly_provenance=InternalModelAssemblyProvenance(
            method="deterministic",
            implementation_reference="ff4ee4e",
            recipe_reference=None,
            context_fingerprint=None,
        ),
        structure_content_fingerprint=_structure().content_fingerprint,
        internal_model_element_ids=("IME-000001",),
        internal_model_relationship_ids=("IMR-000001",),
        review_decision_references=(
            _element_review(),
            _relationship_review(),
        ),
        accepted_exception_references=(),
        created_at="2026-08-13T09:15:00Z",
    )


@pytest.mark.parametrize(
    ("factory", "serializer", "parser"),
    [
        (_element, internal_model_element_to_json, internal_model_element_from_json),
        (_relationship, internal_model_relationship_to_json, internal_model_relationship_from_json),
        (_structure, internal_model_structure_to_json, internal_model_structure_from_json),
        (_manifest, internal_engineering_model_manifest_to_json, internal_engineering_model_manifest_from_json),
    ],
)
def test_round_trip_is_deterministic(factory, serializer, parser):
    value = factory()
    encoded = serializer(value)
    assert parser(encoded) == value
    assert serializer(parser(encoded)) == encoded


def test_element_fingerprint_detects_mutation():
    with pytest.raises(InternalModelIntegrityError):
        validate_internal_model_element(replace(_element(), name="Changed"))


def test_relationship_fingerprint_detects_semantic_mutation():
    with pytest.raises(InternalModelIntegrityError):
        validate_internal_model_relationship(
            replace(_relationship(), semantic_intent="dependency")
        )


def test_structure_fingerprint_detects_membership_mutation():
    value = _structure()
    changed = replace(value.nodes[1], internal_model_element_ids=())
    with pytest.raises(InternalModelIntegrityError):
        validate_internal_model_structure(
            replace(value, nodes=(value.nodes[0], changed))
        )


def test_model_manifest_fingerprint_detects_candidate_set_mutation():
    with pytest.raises(InternalModelIntegrityError):
        validate_internal_engineering_model_manifest(
            replace(_manifest(), candidate_set_id="MCS-000002")
        )


def test_element_requires_exact_review_reference():
    value = _element()
    with pytest.raises(InternalModelIntegrityError):
        validate_internal_model_element(
            replace(
                value,
                review_decision_reference=replace(
                    value.review_decision_reference,
                    candidate_id="MCE-000002",
                ),
            )
        )


def test_relationship_requires_exact_review_reference():
    value = _relationship()
    with pytest.raises(InternalModelIntegrityError):
        validate_internal_model_relationship(
            replace(
                value,
                review_decision_reference=replace(
                    value.review_decision_reference,
                    candidate_id="MCR-000002",
                ),
            )
        )


def test_accepted_exception_remains_explicit():
    exception = _element_review("accepted_exception")
    value = create_internal_model_element(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        internal_model_element_id="IME-000001",
        model_subject_key="subject.alpha",
        source_model_element_candidate_id="MCE-000001",
        source_model_element_candidate_fingerprint="1" * 64,
        name="Alpha",
        description=None,
        model_area="system.logical",
        element_type="logical_component",
        framework_assignment="FW_SYSTEM_LOGICAL",
        terminology_assignment=None,
        attributes=(),
        comparison_anchor_id=None,
        approved_input_references=(_ain(),),
        review_decision_reference=exception,
        accepted_exception_reference=exception,
    )
    assert value.accepted_exception_reference == exception


def test_structure_rejects_unknown_parent():
    value = _structure()
    bad = replace(value.nodes[1], parent_framework_node_id="FW_UNKNOWN")
    with pytest.raises(InternalModelIntegrityError):
        create_internal_model_structure(
            project_id=value.project_id,
            internal_engineering_model_id=value.internal_engineering_model_id,
            framework_template_reference=value.framework_template_reference,
            nodes=(value.nodes[0], bad),
        )


def test_structure_rejects_duplicate_ime_membership():
    value = _structure()
    duplicate = replace(
        value.nodes[0],
        internal_model_element_ids=("IME-000001",),
    )
    with pytest.raises(InternalModelIntegrityError):
        create_internal_model_structure(
            project_id=value.project_id,
            internal_engineering_model_id=value.internal_engineering_model_id,
            framework_template_reference=value.framework_template_reference,
            nodes=(duplicate, value.nodes[1]),
        )


def test_model_manifest_exception_must_be_subset_of_review_refs():
    exception = ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCD-000003",
        target_type="element_candidate",
        candidate_id="MCE-000003",
        decision="accepted_exception",
        decision_fingerprint="9" * 64,
    )
    with pytest.raises(InternalModelIntegrityError):
        create_internal_engineering_model_manifest(
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            assembly_input_fingerprint="3" * 64,
            candidate_set_id="MCS-000001",
            candidate_set_content_fingerprint="4" * 64,
            approved_input_snapshot_fingerprint="5" * 64,
            assembly_context=_context(),
            assembly_provenance=InternalModelAssemblyProvenance(
                method="deterministic",
                implementation_reference=None,
                recipe_reference=None,
                context_fingerprint=None,
            ),
            structure_content_fingerprint=_structure().content_fingerprint,
            internal_model_element_ids=(),
            internal_model_relationship_ids=(),
            review_decision_references=(),
            accepted_exception_references=(exception,),
            created_at="2026-08-13T09:15:00Z",
        )
