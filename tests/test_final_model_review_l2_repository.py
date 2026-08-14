from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path

import pytest

from modules.final_model_review import (
    FinalModelReviewIntegrityError,
    FinalModelReviewRepository,
    create_final_model_review_decision,
    create_final_model_review_decision_target,
    create_final_model_review_item,
)
from modules.final_model_review.paths import (
    final_model_review_revision_path,
    final_model_reviews_path,
)

FP_C = "c" * 64
FP_D = "d" * 64


class WorkspaceStub:
    def load_project(self, project_id):
        if project_id != "000001":
            raise RuntimeError("Project not found.")
        return object()


@dataclass(frozen=True)
class FakeUnit:
    unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str
    generated_symbol_ids: tuple[str, ...] = ("IME_000001",)


@dataclass(frozen=True)
class FakeArtifact:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    content_fingerprint: str
    units: tuple[FakeUnit, ...]


@dataclass(frozen=True)
class FakeValidation:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str
    validation_status: str
    publication_gate: str
    content_fingerprint: str


def _clock():
    return datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)


def _artifact(*, project="000001", content="package X {}\n", fp=FP_C):
    unit = FakeUnit(
        "GSU-000001",
        "generated_model.sysml",
        content,
        hashlib.sha256(content.encode()).hexdigest(),
    )
    return FakeArtifact("1.0.0", project, "IEM-000001", fp, (unit,))


def _validation(*, project="000001", status="valid", gate="passed", artifact_fp=FP_C):
    return FakeValidation("1.0.0", project, "IEM-000001", artifact_fp, status, gate, FP_D)


def _repo(tmp_path, **kwargs):
    return FinalModelReviewRepository(
        root=tmp_path,
        workspace=WorkspaceStub(),
        clock=_clock,
        artifact_validator=lambda value: None,
        validation_result_validator=lambda value: None,
        **kwargs,
    )


def test_l2_create_review_round_trips_project_local_manifest(tmp_path):
    repo=_repo(tmp_path)
    value=repo.create_review("000001")
    assert value.final_model_review_id == "FMR-000001"
    assert repo.load_review("000001","FMR-000001") == value


def test_l2_review_ids_follow_highest_persisted_sequence(tmp_path):
    repo=_repo(tmp_path)
    assert repo.create_review("000001").final_model_review_id == "FMR-000001"
    assert repo.create_review("000001").final_model_review_id == "FMR-000002"


def test_l2_revision_bundle_persists_exact_sysml_and_jk_snapshots(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    artifact=_artifact()
    bundle=repo.append_revision("000001","FMR-000001",artifact_set=artifact,validation_result=_validation())
    assert bundle.revision.final_model_review_revision_id == "FRV-000001"
    assert bundle.generated_units[0].content == artifact.units[0].content
    assert bundle.artifact_set_snapshot["content_fingerprint"] == FP_C
    assert bundle.validation_result_snapshot["content_fingerprint"] == FP_D


@pytest.mark.parametrize(("status","gate"), [("invalid","blocked"),("incomplete","blocked")])
def test_l2_blocked_k_result_is_still_persistable_for_review(tmp_path,status,gate):
    repo=_repo(tmp_path); repo.create_review("000001")
    bundle=repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation(status=status,gate=gate))
    assert bundle.revision.validation_status == status


def test_l2_revision_successor_preserves_predecessor(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    first=repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    second=repo.append_revision("000001","FMR-000001",artifact_set=_artifact(content="package Y {}\n"),validation_result=_validation())
    assert second.revision.final_model_review_revision_id == "FRV-000002"
    assert second.revision.predecessor_revision_id == "FRV-000001"
    assert repo.load_revision("000001","FMR-000001","FRV-000001") == first


def test_l2_rejects_cross_project_subject(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    with pytest.raises(FinalModelReviewIntegrityError):
        repo.append_revision("000001","FMR-000001",artifact_set=_artifact(project="000002"),validation_result=_validation(project="000002"))


def test_l2_rejects_validation_for_other_artifact(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    with pytest.raises(FinalModelReviewIntegrityError):
        repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation(artifact_fp="e"*64))


def test_l2_detects_tampered_sysml_bytes(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    d=final_model_review_revision_path(tmp_path,"000001","FMR-000001","FRV-000001")
    (d/"generated"/"generated_model.sysml").write_text("tampered\n")
    with pytest.raises(FinalModelReviewIntegrityError): repo.load_revision("000001","FMR-000001","FRV-000001")


def test_l2_detects_tampered_validation_snapshot(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    d=final_model_review_revision_path(tmp_path,"000001","FMR-000001","FRV-000001")
    (d/"validation_result.json").write_text("{}\n")
    with pytest.raises(FinalModelReviewIntegrityError): repo.load_revision("000001","FMR-000001","FRV-000001")


def test_l2_detects_unexpected_revision_file(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    d=final_model_review_revision_path(tmp_path,"000001","FMR-000001","FRV-000001")
    (d/"surprise.txt").write_text("x")
    with pytest.raises(FinalModelReviewIntegrityError): repo.load_revision("000001","FMR-000001","FRV-000001")


def test_l2_item_round_trip(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    item=create_final_model_review_item(
        project_id="000001", final_model_review_id="FMR-000001", final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001", item_kind="generated_symbol", summary="Review symbol.", detail=None,
        mandatory=True, generated_unit_id="GSU-000001", generated_symbol_id="IME_000001"
    )
    assert repo.persist_item(item) == item


def test_l2_decision_round_trip_and_duplicate_rejection(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    bundle=repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    target=create_final_model_review_decision_target(bundle.revision)
    first=create_final_model_review_decision(project_id="000001",final_model_review_decision_id="FRD-000001",target=target,decision="changes_requested",reviewer_identity="moritz",rationale="revise",reviewed_at="2026-08-14T12:05:00Z")
    second=create_final_model_review_decision(project_id="000001",final_model_review_decision_id="FRD-000002",target=target,decision="changes_requested",reviewer_identity="moritz",rationale="revise",reviewed_at="2026-08-14T13:05:00Z")
    assert repo.persist_decision(first) == first
    with pytest.raises(FinalModelReviewIntegrityError): repo.persist_decision(second)



def test_l2_item_rejects_symbol_outside_persisted_revision(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    item=create_final_model_review_item(
        project_id="000001", final_model_review_id="FMR-000001", final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001", item_kind="generated_symbol", summary="Review symbol.", detail=None,
        mandatory=True, generated_unit_id="GSU-000001", generated_symbol_id="IME_999999"
    )
    with pytest.raises(FinalModelReviewIntegrityError): repo.persist_item(item)


def test_l2_decision_rejects_partial_stale_target_even_with_revision_fingerprint(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    bundle=repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    target=create_final_model_review_decision_target(bundle.revision)
    stale=replace(target, validation_result_fingerprint="e"*64)
    decision=create_final_model_review_decision(
        project_id="000001", final_model_review_decision_id="FRD-000001", target=stale, decision="changes_requested",
        reviewer_identity="moritz", rationale="revise", reviewed_at="2026-08-14T12:05:00Z"
    )
    with pytest.raises(FinalModelReviewIntegrityError): repo.persist_decision(decision)

def test_l2_scan_returns_clean_valid_evidence(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    scan=repo.scan("000001")
    assert len(scan.review_manifests)==1 and len(scan.revisions)==1 and scan.issues==()


def test_l2_scan_flags_unexpected_root_entry(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    (final_model_reviews_path(tmp_path,"000001")/"README.txt").write_text("x")
    assert any(i.code=="unexpected_final_model_review_entry" for i in repo.scan("000001").issues)


def test_l2_scan_flags_interrupted_review(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    (final_model_reviews_path(tmp_path,"000001")/".FMR-000002.tmp-deadbeef").mkdir()
    assert any(i.code=="interrupted_final_model_review_publication" for i in repo.scan("000001").issues)


def test_l2_scan_flags_interrupted_revision(tmp_path):
    repo=_repo(tmp_path); repo.create_review("000001")
    d=tmp_path/"000001"/"final_model_reviews"/"FMR-000001"/"revisions"
    (d/".FRV-000001.tmp-deadbeef").mkdir()
    assert any(i.code=="interrupted_final_model_review_revision" for i in repo.scan("000001").issues)


def test_l2_scan_rejects_symlinked_review_root(tmp_path):
    (tmp_path/"outside").mkdir(); (tmp_path/"000001").mkdir()
    (tmp_path/"000001"/"final_model_reviews").symlink_to(tmp_path/"outside",target_is_directory=True)
    scan=_repo(tmp_path).scan("000001")
    assert scan.issues[0].code == "unsafe_final_model_review_root"


def test_l2_failed_revision_rename_leaves_recovery_evidence(tmp_path):
    def rename(src,dst):
        if "FRV-" in Path(src).name: raise OSError("simulated")
        os.rename(src,dst)
    repo=_repo(tmp_path,rename=rename); repo.create_review("000001")
    with pytest.raises(OSError):
        repo.append_revision("000001","FMR-000001",artifact_set=_artifact(),validation_result=_validation())
    assert any(i.code=="interrupted_final_model_review_revision" for i in repo.scan("000001").issues)
