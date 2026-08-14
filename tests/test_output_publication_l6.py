from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import pytest

from modules.final_model_review import (
    create_final_model_review_decision,
    create_final_model_review_decision_target,
    create_final_model_review_revision,
    create_generated_unit_reference,
)
from modules.final_model_review.types import FinalModelReviewRevisionBundle
from modules.output_publication import (
    OutputPublicationIntegrityError,
    OutputPublicationPersistenceError,
    OutputPublicationRepository,
    OutputPublicationValidationError,
    OutputWriter,
    calculate_publication_input_fingerprint,
    create_published_output_file_reference,
    create_published_output_manifest,
    format_output_package_id,
    load_output_publication_profile,
    next_output_package_id,
    output_publication_profile_reference,
    published_output_manifest_from_json,
    published_output_manifest_to_json,
    validate_manifest_against_profile,
    validate_output_package_id,
)


FP_ART = "a" * 64
FP_VAL = "b" * 64
FP_GATE = "c" * 64
FP_META = "d" * 64


@dataclass(frozen=True)
class FakePolicyReference:
    profile_id: str
    profile_version: str
    profile_fingerprint: str


@dataclass(frozen=True)
class FakeTargetNotationReference:
    context_id: str
    version: str
    content_fingerprint: str


@dataclass(frozen=True)
class FakeGeneratorRulesReference:
    rules_id: str
    rules_version: str
    rules_fingerprint: str


@dataclass(frozen=True)
class FakeGenerationContext:
    target_notation_reference: FakeTargetNotationReference
    generation_profile_reference: FakePolicyReference
    artifact_structure_reference: FakePolicyReference
    generator_rules_reference: FakeGeneratorRulesReference


@dataclass(frozen=True)
class FakeGenerationProvenance:
    method: str
    implementation_reference: str | None
    context_fingerprint: str | None


@dataclass(frozen=True)
class FakeApprovedInputReference:
    approved_input_id: str
    content_fingerprint: str
    stable_subject_key: str
    provenance_role: str


@dataclass(frozen=True)
class FakeReviewDecisionReference:
    model_candidate_review_decision_id: str
    target_type: str
    candidate_id: str
    decision: str
    decision_fingerprint: str


@dataclass(frozen=True)
class FakeLocation:
    start_line: int
    end_line: int


@dataclass(frozen=True)
class FakeTraceabilityEntry:
    generated_unit_id: str
    generated_symbol_id: str
    generated_location: FakeLocation | None
    source_internal_engineering_model_id: str
    source_internal_model_element_id: str | None
    source_internal_model_relationship_id: str | None
    source_model_candidate_id: str
    approved_input_references: tuple[FakeApprovedInputReference, ...]
    review_decision_reference: FakeReviewDecisionReference
    accepted_exception_reference: FakeReviewDecisionReference | None


@dataclass(frozen=True)
class FakeGenerationFinding:
    code: str
    message: str
    issue_level: str
    blocking: bool
    target_type: str | None = None
    target_id: str | None = None
    profile_rule_id: str | None = None


@dataclass(frozen=True)
class FakeUnit:
    unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str
    generated_symbol_ids: tuple[str, ...]
    source_internal_model_element_ids: tuple[str, ...]
    source_internal_model_relationship_ids: tuple[str, ...]


@dataclass(frozen=True)
class FakeArtifactSet:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_iem_content_fingerprint: str
    generation_context: FakeGenerationContext
    generation_input_fingerprint: str
    generation_provenance: FakeGenerationProvenance
    units: tuple[FakeUnit, ...]
    traceability_entries: tuple[FakeTraceabilityEntry, ...]
    nonblocking_diagnostics: tuple[FakeGenerationFinding, ...]
    content_fingerprint: str


@dataclass(frozen=True)
class FakeValidationLocation:
    start_line: int
    end_line: int
    start_column: int | None = None
    end_column: int | None = None


@dataclass(frozen=True)
class FakeValidatorIdentity:
    validator_id: str
    tool_name: str
    tool_version: str | None
    command_contract_id: str
    configuration_fingerprint: str


@dataclass(frozen=True)
class FakeExternalEvidence:
    validator_identity: FakeValidatorIdentity
    execution_status: str
    exit_code: int | None
    normalized_diagnostic_count: int


@dataclass(frozen=True)
class FakeValidationFinding:
    code: str
    category: str
    severity: str
    blocking: bool
    message: str
    generated_unit_id: str | None = None
    generated_symbol_id: str | None = None
    generated_location: FakeValidationLocation | None = None
    validator_id: str | None = None
    validator_rule_id: str | None = None


@dataclass(frozen=True)
class FakeValidationResult:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str
    validation_profile_reference: FakePolicyReference
    validation_input_fingerprint: str
    external_validator_evidence: tuple[FakeExternalEvidence, ...]
    findings: tuple[FakeValidationFinding, ...]
    validation_status: str
    publication_gate: str
    content_fingerprint: str


class ReviewRepositoryStub:
    def __init__(self, revision, decision):
        self.bundle = FinalModelReviewRevisionBundle(
            revision=revision,
            storage_manifest=None,
            artifact_set_snapshot={},
            validation_result_snapshot={},
            generated_units=(),
        )
        self.decision = decision
        self.items = ()
        self.proposals = ()
        self.extra_revisions = ()

    def load_decision(self, project_id, review_id, decision_id):
        if decision_id != self.decision.final_model_review_decision_id:
            raise OutputPublicationIntegrityError("missing decision")
        return self.decision

    def load_revision(self, project_id, review_id, revision_id):
        if revision_id == self.bundle.revision.final_model_review_revision_id:
            return self.bundle
        for item in self.extra_revisions:
            if item.revision.final_model_review_revision_id == revision_id:
                return item
        raise OutputPublicationIntegrityError("missing revision")

    def list_revisions(self, project_id, review_id):
        return (self.bundle,) + tuple(self.extra_revisions)

    def list_items(self, project_id, review_id, revision_id):
        return tuple(
            item
            for item in self.items
            if item.final_model_review_revision_id == revision_id
        )

    def list_change_proposals(self, project_id, review_id=None, revision_id=None):
        return tuple(
            item
            for item in self.proposals
            if revision_id is None
            or item.final_model_review_revision_id == revision_id
        )

    def list_decisions(self, project_id, review_id):
        return (self.decision,)


def _clock():
    return datetime(2026, 8, 14, 13, 0, 0, tzinfo=timezone.utc)


def _artifact(content="package GeneratedModel {}\n", *, fingerprint=FP_ART):
    unit_fp = hashlib.sha256(content.encode("utf-8")).hexdigest()
    unit = FakeUnit(
        unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content=content,
        content_fingerprint=unit_fp,
        generated_symbol_ids=("IME_000001",),
        source_internal_model_element_ids=("IME-000001",),
        source_internal_model_relationship_ids=(),
    )
    review_ref = FakeReviewDecisionReference(
        model_candidate_review_decision_id="MCD-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        decision_fingerprint="1" * 64,
    )
    trace = FakeTraceabilityEntry(
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
        generated_location=FakeLocation(start_line=1, end_line=1),
        source_internal_engineering_model_id="IEM-000001",
        source_internal_model_element_id="IME-000001",
        source_internal_model_relationship_id=None,
        source_model_candidate_id="MCE-000001",
        approved_input_references=(
            FakeApprovedInputReference(
                approved_input_id="AI-000001",
                content_fingerprint="2" * 64,
                stable_subject_key="subject-1",
                provenance_role="primary",
            ),
        ),
        review_decision_reference=review_ref,
        accepted_exception_reference=None,
    )
    return FakeArtifactSet(
        schema_version="1.0.0",
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        source_iem_content_fingerprint="3" * 64,
        generation_context=FakeGenerationContext(
            target_notation_reference=FakeTargetNotationReference(
                context_id="CTX_SYSML_V2_TARGET_NOTATION",
                version="0.2.0",
                content_fingerprint="4" * 64,
            ),
            generation_profile_reference=FakePolicyReference(
                profile_id="TURING_SYSML_V2_GENERATION",
                profile_version="1.0.0",
                profile_fingerprint="5" * 64,
            ),
            artifact_structure_reference=FakePolicyReference(
                profile_id="TURING_SYSML_V2_ARTIFACT_STRUCTURE",
                profile_version="1.0.0",
                profile_fingerprint="6" * 64,
            ),
            generator_rules_reference=FakeGeneratorRulesReference(
                rules_id="TURING_SYSML_V2_GENERATOR_RULES",
                rules_version="1.0.0",
                rules_fingerprint="7" * 64,
            ),
        ),
        generation_input_fingerprint="8" * 64,
        generation_provenance=FakeGenerationProvenance(
            method="deterministic",
            implementation_reference="modules.sysml_generation",
            context_fingerprint="9" * 64,
        ),
        units=(unit,),
        traceability_entries=(trace,),
        nonblocking_diagnostics=(),
        content_fingerprint=fingerprint,
    )


def _validation(*, artifact_fp=FP_ART, fingerprint=FP_VAL):
    return FakeValidationResult(
        schema_version="1.0.0",
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        source_artifact_set_fingerprint=artifact_fp,
        validation_profile_reference=FakePolicyReference(
            profile_id="TURING_SYSML_V2_VALIDATION",
            profile_version="1.0.0",
            profile_fingerprint="a" * 64,
        ),
        validation_input_fingerprint="b" * 64,
        external_validator_evidence=(
            FakeExternalEvidence(
                validator_identity=FakeValidatorIdentity(
                    validator_id="SYSIDE_CLI",
                    tool_name="SYSIDE",
                    tool_version="1.0",
                    command_contract_id="SYSIDE_VALIDATE_V1",
                    configuration_fingerprint="c" * 64,
                ),
                execution_status="completed",
                exit_code=0,
                normalized_diagnostic_count=1,
            ),
        ),
        findings=(
            FakeValidationFinding(
                code="K4_WARNING",
                category="external_warning",
                severity="warning",
                blocking=False,
                message="Example warning.",
                generated_unit_id="GSU-000001",
                generated_symbol_id="IME_000001",
                generated_location=FakeValidationLocation(1, 1, 1, 10),
                validator_id="SYSIDE_CLI",
                validator_rule_id="warning-rule",
            ),
        ),
        validation_status="valid",
        publication_gate="passed",
        content_fingerprint=fingerprint,
    )


def _revision(artifact=_artifact(), validation=_validation()):
    return create_final_model_review_revision(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        predecessor_revision_id=None,
        source_internal_engineering_model_id="IEM-000001",
        generated_artifact_set_fingerprint=artifact.content_fingerprint,
        validation_result_fingerprint=validation.content_fingerprint,
        validation_status="valid",
        publication_gate="passed",
        generated_units=(
            create_generated_unit_reference(
                generated_unit_id=artifact.units[0].unit_id,
                relative_path=artifact.units[0].relative_path,
                content_fingerprint=artifact.units[0].content_fingerprint,
            ),
        ),
        created_at="2026-08-14T12:00:00Z",
    )


def _decision(revision):
    return create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=create_final_model_review_decision_target(revision),
        decision="approved_for_publication",
        reviewer_identity="moritz",
        rationale="Final model reviewed and approved.",
        reviewed_at="2026-08-14T12:30:00Z",
    )


def _profile_path():
    return Path(__file__).parents[1] / "context/sysml/turing_sysml_v2_output_profile.json"


def _writer(tmp_path, review_repo, *, gate=lambda a, v: None, rename=None):
    output_repo = OutputPublicationRepository(
        tmp_path / "output",
        **({"rename": rename} if rename is not None else {}),
    )
    return OutputWriter(
        output_root=tmp_path / "output",
        project_root=tmp_path / "projects",
        profile_path=_profile_path(),
        output_repository=output_repo,
        final_review_repository=review_repo,
        phase_l_gate=gate,
        clock=_clock,
    )


def _metadata_files():
    data = {
        "generation_summary.json": b"{}\n",
        "traceability.json": b"{}\n",
        "validation_report.md": b"ok\n",
        "validation_result.json": b"{}\n",
        "generated_model.sysml": b"package GeneratedModel {}\n",
    }
    roles = {
        "generation_summary.json": "generation_summary",
        "traceability.json": "traceability",
        "validation_report.md": "validation_report",
        "validation_result.json": "validation_result",
        "generated_model.sysml": "sysml_unit",
    }
    refs = tuple(
        sorted(
            (
                create_published_output_file_reference(
                    relative_path=path,
                    role=roles[path],
                    content_fingerprint=hashlib.sha256(content).hexdigest(),
                    source_generated_unit_id=(
                        "GSU-000001" if roles[path] == "sysml_unit" else None
                    ),
                )
                for path, content in data.items()
            ),
            key=lambda item: item.relative_path,
        )
    )
    return data, refs


def _manifest(output_id="OUT-000001", publication_fp=FP_META):
    profile = load_output_publication_profile(_profile_path())
    _, refs = _metadata_files()
    return create_published_output_manifest(
        project_id="000001",
        output_package_id=output_id,
        source_internal_engineering_model_id="IEM-000001",
        source_artifact_set_fingerprint=FP_ART,
        validation_result_fingerprint=FP_VAL,
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_review_revision_fingerprint="e" * 64,
        final_review_decision_id="FRD-000001",
        final_review_decision_fingerprint="f" * 64,
        final_release_gate_fingerprint=FP_GATE,
        output_profile_reference=output_publication_profile_reference(profile),
        publication_input_fingerprint=publication_fp,
        files=refs,
        published_at="2026-08-14T13:00:00Z",
    )


def test_l6_output_profile_loads_and_is_fingerprint_bound():
    profile = load_output_publication_profile(_profile_path())
    assert profile.profile_id == "TURING_SYSML_V2_OUTPUT"
    assert profile.profile_version == "1.0.0"
    assert profile.output_root == "data/output"
    assert len(profile.profile_fingerprint) == 64


def test_l6_tampered_output_profile_is_rejected(tmp_path):
    payload = json.loads(_profile_path().read_text(encoding="utf-8"))
    payload["archive_policy"] = "authoritative"
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OutputPublicationIntegrityError):
        load_output_publication_profile(path)


def test_l6_output_id_contract():
    assert validate_output_package_id("OUT-000001") == "OUT-000001"
    assert format_output_package_id(42) == "OUT-000042"
    assert next_output_package_id(("OUT-000001", "OUT-000003")) == "OUT-000004"


@pytest.mark.parametrize("value", ["OUT-000000", "OUT-1", "FMR-000001", None])
def test_l6_invalid_output_ids_are_rejected(value):
    with pytest.raises(OutputPublicationValidationError):
        validate_output_package_id(value)


def test_l6_published_file_reference_rejects_unsafe_path():
    with pytest.raises(OutputPublicationValidationError):
        create_published_output_file_reference(
            relative_path="../model.sysml",
            role="sysml_unit",
            content_fingerprint=FP_META,
            source_generated_unit_id="GSU-000001",
        )


def test_l6_manifest_round_trips_and_matches_profile():
    manifest = _manifest()
    parsed = published_output_manifest_from_json(
        published_output_manifest_to_json(manifest),
        expected_project_id="000001",
        expected_output_package_id="OUT-000001",
    )
    assert parsed == manifest
    validate_manifest_against_profile(
        parsed, load_output_publication_profile(_profile_path())
    )


def test_l6_publication_input_fingerprint_is_identity_not_out_id_or_time():
    profile = load_output_publication_profile(_profile_path())
    ref = output_publication_profile_reference(profile)
    first = calculate_publication_input_fingerprint(
        source_artifact_set_fingerprint=FP_ART,
        validation_result_fingerprint=FP_VAL,
        final_review_decision_fingerprint="f" * 64,
        final_review_revision_fingerprint="e" * 64,
        output_profile_reference=ref,
    )
    second = calculate_publication_input_fingerprint(
        source_artifact_set_fingerprint=FP_ART,
        validation_result_fingerprint=FP_VAL,
        final_review_decision_fingerprint="f" * 64,
        final_review_revision_fingerprint="e" * 64,
        output_profile_reference=ref,
    )
    assert first == second


def test_l6_repository_publishes_and_loads_atomic_package(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    data, _ = _metadata_files()
    package = repo.publish_package(_manifest(), data)
    assert package.manifest.output_package_id == "OUT-000001"
    assert (package.package_path / "manifest.json").is_file()
    assert repo.load_output("000001", "OUT-000001") == package


def test_l6_repository_detects_tampered_published_sysml(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    data, _ = _metadata_files()
    package = repo.publish_package(_manifest(), data)
    (package.package_path / "generated_model.sysml").write_text(
        "tampered\n", encoding="utf-8"
    )
    with pytest.raises(OutputPublicationIntegrityError):
        repo.load_output("000001", "OUT-000001")


def test_l6_repository_detects_unexpected_package_file(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    data, _ = _metadata_files()
    package = repo.publish_package(_manifest(), data)
    (package.package_path / "surprise.txt").write_text("x", encoding="utf-8")
    with pytest.raises(OutputPublicationIntegrityError):
        repo.load_output("000001", "OUT-000001")


def test_l6_scan_flags_unexpected_project_output_entry(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    project = tmp_path / "output" / "000001"
    project.mkdir(parents=True)
    (project / "README.txt").write_text("unexpected", encoding="utf-8")
    scan = repo.scan_project("000001")
    assert scan.issues[0].code == "unexpected_output_entry"


def test_l6_scan_flags_interrupted_publication(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    project = tmp_path / "output" / "000001"
    project.mkdir(parents=True)
    (project / ".OUT-000001.tmp-deadbeef").mkdir()
    scan = repo.scan_project("000001")
    assert scan.issues[0].code == "interrupted_output_publication"


def test_l6_publish_rejects_symlinked_output_root(tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    output = tmp_path / "output"
    output.symlink_to(target, target_is_directory=True)
    repo = OutputPublicationRepository(output)
    data, _ = _metadata_files()
    with pytest.raises(OutputPublicationPersistenceError):
        repo.publish_package(_manifest(), data)


def test_l6_duplicate_publication_input_is_repository_issue(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    data, _ = _metadata_files()
    repo.publish_package(_manifest("OUT-000001", FP_META), data)
    repo.publish_package(_manifest("OUT-000002", FP_META), data)
    scan = repo.scan_project("000001")
    assert any(item.code == "duplicate_publication_input" for item in scan.issues)


def test_l6_writer_creates_first_authoritative_out_package(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    writer = _writer(tmp_path, ReviewRepositoryStub(revision, decision))
    package = writer.publish(artifact, validation, decision)
    assert package.manifest.output_package_id == "OUT-000001"
    assert package.manifest.final_review_decision_id == "FRD-000001"
    assert package.manifest.final_release_gate_fingerprint
    assert package.package_path == tmp_path / "output" / "000001" / "OUT-000001"


def test_l6_writer_preserves_exact_sysml_bytes(tmp_path):
    artifact = _artifact(content="package GeneratedModel {\n}\n")
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    writer = _writer(tmp_path, ReviewRepositoryStub(revision, decision))
    package = writer.publish(artifact, validation, decision)
    assert (package.package_path / "generated_model.sysml").read_bytes() == (
        artifact.units[0].content.encode("utf-8")
    )


def test_l6_writer_package_contains_required_authoritative_roles(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    package = _writer(
        tmp_path, ReviewRepositoryStub(revision, decision)
    ).publish(artifact, validation, decision)
    assert {item.role for item in package.manifest.files} == {
        "generation_summary",
        "sysml_unit",
        "traceability",
        "validation_report",
        "validation_result",
    }


def test_l6_writer_validation_report_is_human_readable_projection(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    package = _writer(
        tmp_path, ReviewRepositoryStub(revision, decision)
    ).publish(artifact, validation, decision)
    report = (package.package_path / "validation_report.md").read_text(
        encoding="utf-8"
    )
    assert "Validation status: **valid**" in report
    assert "`K4_WARNING`" in report
    assert "SYSIDE" in report


def test_l6_writer_traceability_package_preserves_generated_trace(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    package = _writer(
        tmp_path, ReviewRepositoryStub(revision, decision)
    ).publish(artifact, validation, decision)
    trace = json.loads(
        (package.package_path / "traceability.json").read_text(encoding="utf-8")
    )
    assert trace["entries"][0]["generated_symbol_id"] == "IME_000001"
    assert trace["entries"][0]["source_model_candidate_id"] == "MCE-000001"


def test_l6_writer_is_idempotent_for_exact_same_publication_input(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    reviews = ReviewRepositoryStub(revision, decision)
    writer = _writer(tmp_path, reviews)
    first = writer.publish(artifact, validation, decision)
    # Later review evidence may block new publication, but cannot erase an already
    # published immutable OUT package. Identical re-publication returns the same OUT.
    reviews.proposals = (object(),)
    second = writer.publish(artifact, validation, decision)
    assert second.manifest.output_package_id == first.manifest.output_package_id
    assert len(writer._outputs.scan_project("000001").packages) == 1


def test_l6_writer_rejects_nonapproval_decision(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000001",
        target=create_final_model_review_decision_target(revision),
        decision="changes_requested",
        reviewer_identity="moritz",
        rationale="change it",
        reviewed_at="2026-08-14T12:30:00Z",
    )
    with pytest.raises(OutputPublicationValidationError):
        _writer(
            tmp_path, ReviewRepositoryStub(revision, decision)
        ).publish(artifact, validation, decision)


def test_l6_writer_rejects_k_gate_failure(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)

    def blocked(a, v):
        raise RuntimeError("K blocked")

    with pytest.raises(OutputPublicationIntegrityError):
        _writer(
            tmp_path, ReviewRepositoryStub(revision, decision), gate=blocked
        ).publish(artifact, validation, decision)


def test_l6_writer_rejects_unpersisted_or_changed_human_decision(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    persisted = _decision(revision)
    supplied = replace(persisted, reviewer_identity="someone_else")
    with pytest.raises(OutputPublicationIntegrityError):
        _writer(
            tmp_path, ReviewRepositoryStub(revision, persisted)
        ).publish(artifact, validation, supplied)


def test_l6_writer_rejects_artifact_not_authorized_by_decision(tmp_path):
    artifact = _artifact(fingerprint="e" * 64)
    validation = _validation(artifact_fp="e" * 64)
    authorized_artifact = _artifact()
    authorized_validation = _validation()
    revision = _revision(authorized_artifact, authorized_validation)
    decision = _decision(revision)
    with pytest.raises(OutputPublicationIntegrityError):
        _writer(
            tmp_path, ReviewRepositoryStub(revision, decision)
        ).publish(artifact, validation, decision)


def test_l6_new_publication_is_blocked_when_current_l5_gate_is_stale(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    reviews = ReviewRepositoryStub(revision, decision)

    @dataclass(frozen=True)
    class Proposal:
        final_model_review_revision_id: str = "FRV-000001"
        final_model_review_change_proposal_id: str = "FCP-000001"

    reviews.proposals = (Proposal(),)
    with pytest.raises(Exception):
        _writer(tmp_path, reviews).publish(artifact, validation, decision)
    assert not (tmp_path / "output" / "000001" / "OUT-000001").exists()


def test_l6_output_repository_issue_blocks_new_writer_publication(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)
    project = tmp_path / "output" / "000001"
    project.mkdir(parents=True)
    (project / "unexpected.txt").write_text("x", encoding="utf-8")
    with pytest.raises(OutputPublicationIntegrityError):
        _writer(
            tmp_path, ReviewRepositoryStub(revision, decision)
        ).publish(artifact, validation, decision)


def test_l6_failed_atomic_rename_leaves_recovery_evidence(tmp_path):
    artifact = _artifact()
    validation = _validation()
    revision = _revision(artifact, validation)
    decision = _decision(revision)

    def fail_rename(src, dst):
        raise OSError("simulated rename failure")

    writer = _writer(
        tmp_path,
        ReviewRepositoryStub(revision, decision),
        rename=fail_rename,
    )
    with pytest.raises(OSError):
        writer.publish(artifact, validation, decision)
    scan = writer._outputs.scan_project("000001")
    assert any(item.code == "interrupted_output_publication" for item in scan.issues)


def test_l6_read_file_only_allows_manifest_declared_files(tmp_path):
    repo = OutputPublicationRepository(tmp_path / "output")
    data, _ = _metadata_files()
    repo.publish_package(_manifest(), data)
    assert repo.read_file(
        "000001", "OUT-000001", "generated_model.sysml"
    ) == data["generated_model.sysml"]
    with pytest.raises(Exception):
        repo.read_file("000001", "OUT-000001", "manifest.json")
