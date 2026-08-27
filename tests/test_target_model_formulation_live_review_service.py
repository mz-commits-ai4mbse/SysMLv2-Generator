from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

from modules.target_model_formulation.live_review import (
    TargetModelFormulationLiveReviewService,
)
from modules.target_model_formulation.repository import (
    TargetModelFormulationAuthorityRepository,
)


def _clock():
    return datetime(
        2026,
        8,
        25,
        14,
        30,
        0,
        tzinfo=timezone.utc,
    )


def _snapshot():
    elements = (
        SimpleNamespace(
            internal_model_element_id="IME-000001",
            element_type="stakeholder",
            name="microscope operator",
        ),
        SimpleNamespace(
            internal_model_element_id="IME-000002",
            element_type="system_requirement",
            name="other",
        ),
        SimpleNamespace(
            internal_model_element_id="IME-000003",
            element_type="stakeholder",
            name="separate client application user",
        ),
    )
    relationships = (
        SimpleNamespace(
            internal_model_relationship_id="IMR-000001",
            semantic_intent="traces_to",
        ),
        SimpleNamespace(
            internal_model_relationship_id="IMR-000002",
            semantic_intent="dependency",
        ),
        SimpleNamespace(
            internal_model_relationship_id="IMR-000003",
            semantic_intent="traces_to",
        ),
    )
    return SimpleNamespace(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        comparison_fingerprint="a" * 64,
        content_fingerprint="1" * 64,
        final_model_review_decision_id="FAD-000001",
        final_model_review_decision_fingerprint="2" * 64,
        elements=elements,
        relationships=relationships,
    )


class _IEMRepo:
    def load(self, project_id, iem_id):
        assert project_id == "120412"
        assert iem_id == "IEM-000001"
        return _snapshot()


class _FADRepo:
    def latest_decision(self, project_id, comparison_fingerprint):
        assert project_id == "120412"
        assert comparison_fingerprint == "a" * 64
        return SimpleNamespace(
            decision="approved",
            final_assembly_decision_id="FAD-000001",
            decision_fingerprint="2" * 64,
        )


def _repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "context/sysml").mkdir(parents=True)
    (root / "external/sysml-v2-release").mkdir(parents=True)

    (root / "context/sysml/sysml_v2_target_model_profile.json").write_text(
        json.dumps(
            {
                "profile_id": "TURING_SYSML_V2_TARGET_MODEL",
                "profile_version": "0.1.0-draft",
            }
        ),
        encoding="utf-8",
    )
    generation_profile_source = (
        Path(__file__).resolve().parents[1]
        / "context/sysml/turing_sysml_v2_generation_profile.json"
    )
    (
        root
        / "context/sysml/turing_sysml_v2_generation_profile.json"
    ).write_text(
        generation_profile_source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    (root / "context/sysml/sysml_v2_target_notation.json").write_text(
        json.dumps(
            {
                "constructs": [
                    {
                        "construct_id": "TN_003",
                        "name": "Part definition",
                        "usage_rules": [
                            (
                                "Use part definitions for Human-reviewed standalone "
                                "reusable stakeholder-role types."
                            )
                        ],
                        "syntax_evidence": {
                            "fixture_id": "SFX-C6C3-001",
                            "fixture_path": (
                                "context/sysml/fixtures/c6c3/"
                                "stakeholder_role_part_definition.sysml"
                            ),
                            "validation_status": (
                                "passed_with_nonblocking_warning"
                            ),
                        },
                    },
                    {
                        "construct_id": "TN_004",
                        "name": "Part usage",
                        "usage_rules": [
                            "Use part usages for logical components."
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (
        root
        / "external/sysml-v2-release/SysML.sysml"
    ).write_text(
        (
            "metadata def StakeholderMembership {\n"
            "  derived item ownedStakeholderParameter : PartUsage[1..1];\n"
            "}\n"
        ),
        encoding="utf-8",
    )
    return root


def test_prepare_review_persists_and_resumes_same_tfr(tmp_path):
    authority_repo = TargetModelFormulationAuthorityRepository(
        tmp_path / "projects"
    )
    service = TargetModelFormulationLiveReviewService(
        projects_root=tmp_path / "projects",
        repo_root=_repo_root(tmp_path),
        authority_repository=authority_repo,
        internal_model_repository=_IEMRepo(),
        final_model_review_repository=_FADRepo(),
        clock=_clock,
    )

    first = service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )
    second = service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )

    assert first == second
    assert first.review_id == "TFR-000001"
    assert len(first.items) == 4
    assert [
        item.candidates[0].relevance_outcome
        for item in first.items
    ] == [
        "materialize_formally",
        "materialize_formally",
        "intentionally_not_materialized",
        "intentionally_not_materialized",
    ]


def test_four_explicit_selections_then_finalize_is_idempotent(tmp_path):
    authority_repo = TargetModelFormulationAuthorityRepository(
        tmp_path / "projects"
    )
    service = TargetModelFormulationLiveReviewService(
        projects_root=tmp_path / "projects",
        repo_root=_repo_root(tmp_path),
        authority_repository=authority_repo,
        internal_model_repository=_IEMRepo(),
        final_model_review_repository=_FADRepo(),
        clock=_clock,
    )
    review = service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )

    for item in review.items:
        candidate = item.candidates[0]
        service.record_selection(
            review=review,
            authority_subject_id=item.authority_subject_id,
            selected_candidate_id=candidate.candidate_id,
            reviewer_identity="MZ",
            rationale=(
                f"Explicit Human authorization for "
                f"{item.authority_subject_id}."
            ),
        )

    first = service.finalize(review)
    second = service.finalize(review)

    assert first == second
    assert first.authority_set_id == "TFA-000001"
    assert len(first.effective_decisions) == 4


def test_prepare_review_can_create_explicit_immutable_revision(tmp_path):
    authority_repo = TargetModelFormulationAuthorityRepository(
        tmp_path / "projects"
    )
    service = TargetModelFormulationLiveReviewService(
        projects_root=tmp_path / "projects",
        repo_root=_repo_root(tmp_path),
        authority_repository=authority_repo,
        internal_model_repository=_IEMRepo(),
        final_model_review_repository=_FADRepo(),
        clock=_clock,
    )

    first = service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )

    revised = service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
        force_revision=True,
    )

    assert first.review_id == "TFR-000001"
    assert revised.review_id == "TFR-000002"
    assert revised.source_internal_engineering_model_id == (
        first.source_internal_engineering_model_id
    )
    assert revised.source_internal_engineering_model_fingerprint == (
        first.source_internal_engineering_model_fingerprint
    )

    # Normal resume now resolves the newest immutable review.
    resumed = service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )
    assert resumed == revised

    # Old history remains available.
    assert authority_repo.load_review(
        "120412",
        "TFR-000001",
    ) == first



def test_prepare_review_resolves_generation_profile_from_repo_root(
    tmp_path,
    monkeypatch,
):
    import modules.target_model_formulation.live_review as live_review_module

    repo_root = _repo_root(tmp_path)
    expected = (
        repo_root
        / "context/sysml/turing_sysml_v2_generation_profile.json"
    )
    captured = {}

    def fake_load_generation_profile(path):
        captured["path"] = Path(path)
        return {}

    monkeypatch.setattr(
        live_review_module,
        "load_generation_profile",
        fake_load_generation_profile,
    )

    authority_repo = TargetModelFormulationAuthorityRepository(
        tmp_path / "projects"
    )
    service = TargetModelFormulationLiveReviewService(
        projects_root=tmp_path / "projects",
        repo_root=repo_root,
        authority_repository=authority_repo,
        internal_model_repository=_IEMRepo(),
        final_model_review_repository=_FADRepo(),
        clock=_clock,
    )

    service.prepare_review(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )

    assert captured["path"] == expected
