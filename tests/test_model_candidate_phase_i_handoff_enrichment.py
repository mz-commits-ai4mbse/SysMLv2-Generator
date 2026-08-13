from __future__ import annotations

from modules.model_candidates import ModelCandidateReadService
from modules.model_candidates.types import (
    ModelCandidateGenerationProvenance,
    ModelCandidateReviewScanResult,
    ModelCandidateSetManifest,
    ModelCandidateSetSnapshot,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.project_workspace.types import FrameworkTemplateReference


class _CandidateRepository:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def load_candidate_set(self, project_id, candidate_set_id):
        return self.snapshot


class _ReviewRepository:
    def scan_decisions(self, project_id):
        return ModelCandidateReviewScanResult()


class _ApprovedInputRepository:
    def list_active_approved_inputs(self, project_id):
        return ()


def test_phase_i_handoff_carries_pinned_template_and_derivation_rules():
    manifest = ModelCandidateSetManifest(
        schema_version="1.0.0",
        project_id="000001",
        candidate_set_id="MCS-000001",
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=(),
        approved_input_snapshot_fingerprint="a" * 64,
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint="b" * 64,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="c" * 64,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="profile_driven",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        element_candidate_ids=(),
        relationship_candidate_ids=(),
        created_at="2026-08-13T09:00:00Z",
        content_fingerprint="d" * 64,
    )
    snapshot = ModelCandidateSetSnapshot(
        manifest=manifest,
        element_candidates=(),
        relationship_candidates=(),
    )
    service = ModelCandidateReadService(
        candidate_repository=_CandidateRepository(snapshot),
        review_repository=_ReviewRepository(),
        approved_input_repository=_ApprovedInputRepository(),
    )

    result = service.load_phase_i_input("000001", "MCS-000001")

    assert result.framework_template_reference == manifest.framework_template_reference
    assert result.derivation_rules_reference == manifest.derivation_rules_reference
    assert result.model_structure_profile_reference == manifest.model_structure_profile_reference
