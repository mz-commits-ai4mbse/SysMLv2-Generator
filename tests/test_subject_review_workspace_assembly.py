"""R4c.5b.2 Subject Review Workspace assembly tests."""

from pathlib import Path
from types import SimpleNamespace
import hashlib
import json

from modules.project_processing import create_processing_artifact_reference
from modules.project_processing import create_semantic_reference_version
from modules.project_workspace.types import FrameworkTemplateReference
from modules.review_workspace.subject_review_artifact_adapter import (
    SubjectReviewPublishedArtifacts,
    assemble_subject_review_initial_review,
)


def _write_ref(
    repo_root,
    name,
    artifact_type,
    payload,
    *,
    artifact_index,
):
    artifact_root = (
        repo_root
        / "data"
        / "projects"
        / "396272"
        / "processing"
        / "test_subject_review"
    )
    artifact_root.mkdir(parents=True, exist_ok=True)
    path = artifact_root / name
    content = (
        json.dumps(payload, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    path.write_bytes(content)
    return create_processing_artifact_reference(
        artifact_type=artifact_type,
        artifact_id=f"CONS-ATT-000003-{artifact_index:04d}",
        content_fingerprint=hashlib.sha256(content).hexdigest(),
        repository_relative_path=path.relative_to(repo_root).as_posix(),
    )


def test_subject_workspace_uses_canonical_subject_identity_and_open_state(
    tmp_path,
):
    repo_root = tmp_path

    card = {
        "canonical_subject_id": "SUBJ-000001",
        "canonical_label": "Microscope Operator",
        "mentions": [
            {
                "mention_id": "MNT-000001",
                "exact_text": "the microscope operator",
                "source_evidence_ids": ["EVD-000001"],
            }
        ],
        "information_type": {
            "selected_value": "actor",
            "confidence": "high",
            "consensus_level": "unanimous",
            "value_distribution": [
                {"value": "actor", "supporting_personas": ["P1", "P2", "P3"]}
            ],
        },
        "statement_modality": {
            "selected_value": "descriptive",
            "confidence": "high",
            "consensus_level": "unanimous",
            "value_distribution": [
                {
                    "value": "descriptive",
                    "supporting_personas": ["P1", "P2", "P3"],
                }
            ],
        },
        "epistemic_class": {
            "selected_value": "explicit",
            "confidence": "high",
            "consensus_level": "unanimous",
            "value_distribution": [
                {
                    "value": "explicit",
                    "supporting_personas": ["P1", "P2", "P3"],
                }
            ],
        },
        "persona_interpretations": [
            {
                "persona_id": "P1",
                "interpreted_statements": [
                    "The microscope operator is the local actor."
                ],
            }
        ],
        "relationships": [],
        "classification_review_attention_required": False,
        "relationship_review_attention_required": False,
        "review_attention_required": False,
        "content_fingerprint": "1" * 64,
    }

    payload = {
        "schema_version": "1.0.0",
        "project_id": "396272",
        "source_id": "SRC-000001",
        "source_projection_id": "SP-000001",
        "canonical_subject_ids": ["SUBJ-000001"],
        "cards": [card],
        "human_review_required": True,
        "content_fingerprint": "2" * 64,
    }

    authority = {
        "project_id": "396272",
        "source_id": "SRC-000001",
        "source_sha256": "a" * 64,
        "source_projection_id": "SP-000001",
        "processing_run_id": "RUN-000001",
        "attempt_id": "ATT-000003",
    }
    body = {
        "schema_version": "1.0.0",
        "artifact_kind": "subject_review_bundle",
        "authority": authority,
        "payload": payload,
    }
    envelope = {
        **body,
        "content_fingerprint": hashlib.sha256(
            json.dumps(
                body,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }

    canonical_ref = _write_ref(
        repo_root,
        "canonical_subject_set.json",
        "consensus_reports",
        {"kind": "canonical_subject_set"},
        artifact_index=1,
    )
    interpretations_ref = _write_ref(
        repo_root,
        "subject_interpretations.json",
        "consensus_reports",
        {"kind": "subject_interpretations"},
        artifact_index=2,
    )
    consensus_ref = _write_ref(
        repo_root,
        "subject_consensus.json",
        "consensus_reports",
        {"kind": "subject_consensus"},
        artifact_index=3,
    )
    bundle_ref = _write_ref(
        repo_root,
        "subject_review_bundle.json",
        "consensus_reports",
        envelope,
        artifact_index=4,
    )
    report_root = (
        repo_root
        / "data"
        / "projects"
        / "396272"
        / "processing"
        / "test_subject_review"
    )
    report_root.mkdir(parents=True, exist_ok=True)
    report_path = report_root / "ingestion_review_report.md"
    report_path.write_text("Review report\n", encoding="utf-8")
    report_content = report_path.read_bytes()
    report_ref = create_processing_artifact_reference(
        artifact_type="review_reports",
        artifact_id="REVIEW-ATT-000003-0001",
        content_fingerprint=hashlib.sha256(report_content).hexdigest(),
        repository_relative_path=report_path.relative_to(repo_root).as_posix(),
    )

    artifacts = SubjectReviewPublishedArtifacts(
        primary_review_report=report_ref,
        canonical_subject_set=canonical_ref,
        subject_interpretations=interpretations_ref,
        subject_consensus=consensus_ref,
        subject_review_bundle=bundle_ref,
        attempt_id="ATT-000003",
    )

    history = SimpleNamespace(
        manifest=SimpleNamespace(
            project_id="396272",
            source_id="SRC-000001",
            source_sha256="a" * 64,
            processing_run_id="RUN-000001",
            semantic_reference_versions=(
                create_semantic_reference_version(
                    reference_system_id="SYSML_V2",
                    reference_version="1.0.0",
                ),
            ),
        )
    )
    source = SimpleNamespace(
        source_id="SRC-000001",
        sha256="a" * 64,
    )
    project = SimpleNamespace(
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        )
    )

    assembly = assemble_subject_review_initial_review(
        history=history,
        source_manifest=source,
        project_manifest=project,
        artifacts=artifacts,
        repository_root=repo_root,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        opened_by="reviewer",
        timestamp="2026-08-24T06:00:00Z",
        occupied_review_item_ids=(),
    )

    item = assembly.initial_revision.review_items[0]
    assert item.stable_subject_key == "subject:subj-000001"
    assert item.original_report_locator == "subject_review:SUBJ-000001"
    assert item.current_content.title == "Microscope Operator"
    assert item.current_content.information_type == "actor"
    assert item.effective_review_outcome == "open"
    assert item.proposal_references == ()
    assert assembly.review_document.attempt_id == "ATT-000003"
