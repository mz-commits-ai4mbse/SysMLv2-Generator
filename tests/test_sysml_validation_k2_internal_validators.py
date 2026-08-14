"""Focused K2 tests for deterministic generated-artifact validators."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib

from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
)
from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_profile,
    load_artifact_structure_reference,
)
from modules.sysml_generation.generation_profile import load_generation_profile_reference
from modules.sysml_generation.generator_rules import load_generator_rules_reference
from modules.sysml_generation.target_notation import load_target_notation_reference
from modules.sysml_generation.types import (
    GeneratedSysMLArtifactSet,
    GeneratedSysMLLocation,
    GeneratedSysMLTraceabilityEntry,
    GeneratedSysMLUnit,
    SysMLGenerationContext,
    SysMLGenerationProvenance,
)
from modules.sysml_validation import (
    calculate_received_artifact_set_fingerprint,
    calculate_received_generation_input_fingerprint,
    validate_artifact_set_integrity,
    validate_artifact_structure,
    validate_generation_context,
    validate_target_notation_subset,
    validate_traceability,
)


def _valid_artifact() -> GeneratedSysMLArtifactSet:
    profile = load_artifact_structure_profile()
    root = profile["root_package"]["package_name"]
    mappings = profile["framework_package_mappings"]
    children = {}
    for item in mappings:
        children.setdefault(item["parent_framework_node_id"], []).append(item)
    for items in children.values():
        items.sort(key=lambda item: (item["order"], item["framework_node_id"]))

    element_symbol = "IME_000001"
    relationship_symbol = "IMR_000001"
    content_lines = [f"package {root} {{"]

    def emit(parent, depth):
        for item in children.get(parent, []):
            content_lines.append("    " * depth + f"package {item['package_name']} {{")
            if item["mapping_key"] == "system.requirements":
                content_lines.extend(
                    [
                        "    " * (depth + 1) + f"requirement {element_symbol} {{",
                        "    " * (depth + 2) + "doc /* Engineering name: Requirement */",
                        "    " * (depth + 1) + "}",
                    ]
                )
            emit(item["framework_node_id"], depth + 1)
            content_lines.append("    " * depth + "}")

    emit(None, 1)
    relationship_line = f"dependency from SystemLevel::Requirements::{element_symbol} to SystemLevel::Requirements::{element_symbol};"
    content_lines.append("    " + relationship_line)
    content_lines.append("}")
    content = "\n".join(content_lines) + "\n"

    element_start = next(
        line_number
        for line_number, line in enumerate(content_lines, start=1)
        if line.strip() == f"requirement {element_symbol} {{"
    )
    element_location = GeneratedSysMLLocation(element_start, element_start + 2)
    relationship_start = content_lines.index("    " + relationship_line) + 1
    relationship_location = GeneratedSysMLLocation(relationship_start, relationship_start)

    approved = ModelCandidateApprovedInputReference(
        approved_input_id="AI-000001",
        content_fingerprint="1" * 64,
        stable_subject_key="subject:1",
        provenance_role="primary",
    )
    element_review = ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCRD-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        decision_fingerprint="2" * 64,
    )
    relationship_review = ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCRD-000002",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="accepted",
        decision_fingerprint="3" * 64,
    )

    context = SysMLGenerationContext(
        target_notation_reference=load_target_notation_reference(),
        generation_profile_reference=load_generation_profile_reference(),
        artifact_structure_reference=load_artifact_structure_reference(),
        generator_rules_reference=load_generator_rules_reference(),
    )
    unit = GeneratedSysMLUnit(
        unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content=content,
        content_fingerprint=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        generated_symbol_ids=(element_symbol, relationship_symbol),
        source_internal_model_element_ids=("IME-000001",),
        source_internal_model_relationship_ids=("IMR-000001",),
    )
    traces = (
        GeneratedSysMLTraceabilityEntry(
            generated_unit_id=unit.unit_id,
            generated_symbol_id=element_symbol,
            generated_location=element_location,
            source_internal_engineering_model_id="IEM-000001",
            source_internal_model_element_id="IME-000001",
            source_internal_model_relationship_id=None,
            source_model_candidate_id="MCE-000001",
            approved_input_references=(approved,),
            review_decision_reference=element_review,
            accepted_exception_reference=None,
        ),
        GeneratedSysMLTraceabilityEntry(
            generated_unit_id=unit.unit_id,
            generated_symbol_id=relationship_symbol,
            generated_location=relationship_location,
            source_internal_engineering_model_id="IEM-000001",
            source_internal_model_element_id=None,
            source_internal_model_relationship_id="IMR-000001",
            source_model_candidate_id="MCR-000001",
            approved_input_references=(approved,),
            review_decision_reference=relationship_review,
            accepted_exception_reference=None,
        ),
    )
    draft = GeneratedSysMLArtifactSet(
        schema_version="1.0.0",
        project_id="PROJECT-001",
        source_internal_engineering_model_id="IEM-000001",
        source_iem_content_fingerprint="4" * 64,
        generation_context=context,
        generation_input_fingerprint="0" * 64,
        generation_provenance=SysMLGenerationProvenance(
            method="deterministic_sysml_v2_generation",
            implementation_reference="tests",
            context_fingerprint="5" * 64,
        ),
        units=(unit,),
        traceability_entries=traces,
        nonblocking_diagnostics=(),
        content_fingerprint="0" * 64,
    )
    with_input = replace(
        draft,
        generation_input_fingerprint=calculate_received_generation_input_fingerprint(draft),
    )
    return replace(
        with_input,
        content_fingerprint=calculate_received_artifact_set_fingerprint(with_input),
    )


def _codes(findings):
    return {item.code for item in findings}


def test_valid_fixture_passes_all_k2_validators():
    artifact = _valid_artifact()
    assert validate_artifact_set_integrity(artifact) == ()
    assert validate_generation_context(artifact) == ()
    assert validate_target_notation_subset(artifact) == ()
    assert validate_artifact_structure(artifact) == ()
    assert validate_traceability(artifact) == ()


def test_artifact_integrity_detects_changed_unit_bytes_and_set_identity():
    artifact = _valid_artifact()
    unit = replace(artifact.units[0], content=artifact.units[0].content + "\n")
    changed = replace(artifact, units=(unit,))
    codes = _codes(validate_artifact_set_integrity(changed))
    assert "K2_UNIT_FINGERPRINT_MISMATCH" in codes
    assert "K2_ARTIFACT_FINGERPRINT_MISMATCH" in codes


def test_artifact_integrity_detects_generation_input_identity_mismatch():
    artifact = _valid_artifact()
    changed = replace(artifact, generation_input_fingerprint="f" * 64)
    assert "K2_GENERATION_INPUT_FINGERPRINT_MISMATCH" in _codes(
        validate_artifact_set_integrity(changed)
    )


def test_generation_context_detects_pinned_target_notation_mismatch():
    artifact = _valid_artifact()
    bad_ref = replace(
        artifact.generation_context.target_notation_reference,
        content_fingerprint="f" * 64,
    )
    changed = replace(
        artifact,
        generation_context=replace(
            artifact.generation_context,
            target_notation_reference=bad_ref,
        ),
    )
    assert "K2_TARGET_NOTATION_REFERENCE_MISMATCH" in _codes(
        validate_generation_context(changed)
    )


def test_target_notation_rejects_unapproved_element_form():
    artifact = _valid_artifact()
    unit = artifact.units[0]
    content = unit.content.replace("requirement IME_000001 {", "item IME_000001 {")
    changed = replace(artifact, units=(replace(unit, content=content),))
    assert "K2_TARGET_ELEMENT_FORM_INVALID" in _codes(
        validate_target_notation_subset(changed)
    )


def test_structure_detects_missing_profile_package():
    artifact = _valid_artifact()
    unit = artifact.units[0]
    content = unit.content.replace("    package StakeholderLevel {\n", "", 1).replace(
        "    }\n    package SystemLevel {\n",
        "    package SystemLevel {\n",
        1,
    )
    changed = replace(artifact, units=(replace(unit, content=content),))
    assert "K2_STRUCTURE_PACKAGE_HIERARCHY_MISMATCH" in _codes(
        validate_artifact_structure(changed)
    )


def test_traceability_detects_missing_generated_symbol_coverage():
    artifact = _valid_artifact()
    changed = replace(artifact, traceability_entries=artifact.traceability_entries[:1])
    codes = _codes(validate_traceability(changed))
    assert "K2_TRACE_SYMBOL_COVERAGE_MISMATCH" in codes
    assert "K2_TRACE_IMR_COVERAGE_MISMATCH" in codes


def test_findings_are_blocking_errors_for_k2_contract_failures():
    artifact = _valid_artifact()
    changed = replace(artifact, generation_input_fingerprint="f" * 64)
    findings = validate_artifact_set_integrity(changed)
    assert findings
    assert all(item.blocking is True for item in findings)
    assert all(item.severity == "error" for item in findings)
