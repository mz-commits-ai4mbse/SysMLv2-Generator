"""Human-controlled Phase-H derivation orchestration for Guided Workflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from typing import Callable

from modules.approved_input import ApprovedInputRepository
from modules.project_workspace import ProjectWorkspace

from .approved_engineering_deriver import (
    ApprovedEngineeringInformationDeriver,
)
from .candidate_review_repository import ModelCandidateReviewRepository
from .derivation_context import load_model_derivation_rules_reference
from .derivation_strategy import (
    ECO_DETERMINISTIC_MODE,
    LLM_ASSISTED_MODE,
    ModelDerivationStrategyAssessment,
    assess_model_derivation_strategy,
    build_review_escalation_reason,
    validate_model_derivation_mode,
)
from .errors import (
    ModelCandidateGenerationBlockedError,
    ModelCandidateValidationError,
)
from .generation import ModelCandidateGenerationService
from .hybrid_deriver import HybridModelCandidateDeriver
from .modeling_persona_executor import ModelingPersonaProjectionExecutor
from .profile_deriver import ProfileDrivenModelCandidateDeriver
from .repository import ModelCandidateRepository
from .semantic_relationship_projection import (
    SemanticRelationshipProjectionExecutor,
)
from .structure_profile import (
    load_model_structure_profile,
    model_structure_profile_reference,
)
from .types import (
    ModelCandidateDerivationRequest,
    ModelCandidateGenerationProvenance,
)


DEFAULT_MODELING_PROVIDER = "openai"
DEFAULT_MODELING_MODEL = "gpt-5.4-mini"


class ModelDerivationWorkflowService:
    """Compose existing Phase-H authorities behind explicit Human choices."""

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        approved_input_repository=None,
        candidate_repository=None,
        candidate_review_repository=None,
        generation_service=None,
        workspace=None,
        review_workflow_service=None,
        modeling_executor_factory: Callable[..., object] | None = None,
        semantic_relationship_executor_factory: (
            Callable[..., object] | None
        ) = None,
        model_placement_review_repository=None,
        model_placement_executor_factory: Callable[..., object] | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.projects_root = self.project_root / "data" / "projects"

        self._approved_inputs = (
            ApprovedInputRepository(root=self.projects_root)
            if approved_input_repository is None
            else approved_input_repository
        )
        self._candidates = (
            ModelCandidateRepository(root=self.projects_root)
            if candidate_repository is None
            else candidate_repository
        )
        self._candidate_reviews = (
            ModelCandidateReviewRepository(
                root=self.projects_root,
                candidate_repository=self._candidates,
            )
            if candidate_review_repository is None
            else candidate_review_repository
        )
        self._workspace = (
            ProjectWorkspace(root=self.projects_root)
            if workspace is None
            else workspace
        )
        self._generation = (
            ModelCandidateGenerationService(
                root=self.projects_root,
                approved_input_repository=self._approved_inputs,
                candidate_repository=self._candidates,
                workspace=self._workspace,
            )
            if generation_service is None
            else generation_service
        )
        self._review_workflow_service = review_workflow_service
        self._modeling_executor_factory = (
            self._default_modeling_executor
            if modeling_executor_factory is None
            else modeling_executor_factory
        )
        self._semantic_relationship_executor_factory = (
            self._default_semantic_relationship_executor
            if semantic_relationship_executor_factory is None
            else semantic_relationship_executor_factory
        )
        if model_placement_review_repository is None:
            # Lazy import preserves the package boundary because
            # model_placement comparison contracts depend on model_candidates
            # LLM projection contracts.
            from modules.model_placement.review_repository import (
                ModelPlacementReviewRepository,
            )

            self._model_placement_reviews = ModelPlacementReviewRepository(
                root=self.projects_root,
            )
        else:
            self._model_placement_reviews = (
                model_placement_review_repository
            )
        self._model_placement_executor_factory = (
            self._default_model_placement_executor
            if model_placement_executor_factory is None
            else model_placement_executor_factory
        )

    def assess(
        self,
        project_id: str,
        *,
        predecessor_candidate_set_id: str | None = None,
    ) -> ModelDerivationStrategyAssessment:
        """Assess deterministic coverage and advisory derivation strategy."""

        request, strict_deriver, predecessor = self._assessment_request(
            project_id,
            predecessor_candidate_set_id=predecessor_candidate_set_id,
        )
        coverage = strict_deriver.assess_projection_coverage(request)
        decisions = (
            ()
            if predecessor is None
            else self._candidate_reviews.list_decisions(
                project_id,
                candidate_set_id=predecessor.manifest.candidate_set_id,
            )
        )

        return assess_model_derivation_strategy(
            coverage=coverage,
            predecessor_candidate_set=predecessor,
            predecessor_review_decisions=decisions,
        )

    def prepare_model_placement_review(
        self,
        project_id: str,
        *,
        mode: str,
        provider: str = DEFAULT_MODELING_PROVIDER,
        model: str = DEFAULT_MODELING_MODEL,
        api_key: str | None = None,
    ):
        """Generate and persist placement proposals before any model assembly."""

        from modules.model_placement.request_builder import (
            build_deterministic_model_placement_comparison,
            build_model_placement_request,
        )

        selected_mode = validate_model_derivation_mode(mode)
        request, strict_deriver, _predecessor = self._assessment_request(
            project_id,
            predecessor_candidate_set_id=None,
        )
        coverage = strict_deriver.assess_projection_coverage(request)
        profile = load_model_structure_profile()
        placement_request = build_model_placement_request(
            request=request,
            coverage=coverage,
            profile=profile,
        )

        if selected_mode == ECO_DETERMINISTIC_MODE:
            comparison = build_deterministic_model_placement_comparison(
                placement_request=placement_request,
                coverage=coverage,
            )
        else:
            output_dir = self._new_model_placement_execution_directory(
                project_id
            )
            executor = self._model_placement_executor_factory(
                project_root=self.project_root,
                provider=provider,
                model=model,
                api_key=api_key,
            )
            comparison = executor.execute(
                request=placement_request,
                output_dir=output_dir,
            )

        return self._model_placement_reviews.publish_comparison(
            comparison
        )

    def assemble_model_draft(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        provider: str = DEFAULT_MODELING_PROVIDER,
        model: str = DEFAULT_MODELING_MODEL,
        api_key: str | None = None,
    ):
        """Assemble a reviewable draft; Human Final Review resolves non-exact Relationships."""

        from modules.model_assembly import (
            ModelAssemblyRepository,
            build_model_assembly_draft,
        )

        placement_set = (
            self._model_placement_reviews.load_approved_placement_set(
                project_id,
                comparison_fingerprint,
            )
        )
        request, _strict_deriver, _predecessor = self._assessment_request(
            project_id,
            predecessor_candidate_set_id=None,
        )
        if request.approved_engineering_information is None:
            raise ModelCandidateGenerationBlockedError(
                "Model Assembly requires Approved Engineering Information."
            )

        profile = load_model_structure_profile()

        # BLK-007:
        # Model Placement personas are not authorized to decide target
        # Relationship representation during Assembly. The Assembly builder
        # already preserves exact profile matches deterministically and can
        # carry every non-exact accepted engineering Relationship forward as
        # unresolved. Human Final Model Review is the authority that resolves
        # those remaining representation choices.
        draft = build_model_assembly_draft(
            request=request,
            approved_placement_set=placement_set,
            profile=profile,
            relationship_executor=None,
            output_dir=None,
            provider=provider,
            model=model,
        )
        repository = ModelAssemblyRepository(root=self.projects_root)
        return repository.persist(draft)

    def generate(
        self,
        project_id: str,
        *,
        mode: str,
        provider: str = DEFAULT_MODELING_PROVIDER,
        model: str = DEFAULT_MODELING_MODEL,
        api_key: str | None = None,
        predecessor_candidate_set_id: str | None = None,
        human_regeneration_reason: str | None = None,
    ):
        """Generate one Candidate Set using the explicit Human-selected mode."""

        selected_mode = validate_model_derivation_mode(mode)
        assessment = self.assess(
            project_id,
            predecessor_candidate_set_id=predecessor_candidate_set_id,
        )

        total = (
            assessment.mapped_count
            + assessment.ambiguous_count
            + assessment.unmapped_count
            + assessment.intentionally_not_projected_count
        )
        if total == 0:
            raise ModelCandidateGenerationBlockedError(
                "Model derivation requires active Approved Engineering Information."
            )

        regeneration_reason = None
        if predecessor_candidate_set_id is not None:
            if not assessment.rejected_predecessor_candidate_ids:
                raise ModelCandidateGenerationBlockedError(
                    "Regeneration requires at least one currently rejected "
                    "predecessor Candidate."
                )
            if selected_mode != LLM_ASSISTED_MODE:
                raise ModelCandidateGenerationBlockedError(
                    "Review-driven regeneration currently requires "
                    "llm_assisted mode."
                )
            regeneration_reason = build_review_escalation_reason(
                assessment=assessment,
                human_reason=human_regeneration_reason,
            )
        elif human_regeneration_reason is not None:
            raise ModelCandidateValidationError(
                "human_regeneration_reason requires a predecessor Candidate Set."
            )

        profile = load_model_structure_profile()
        rules = load_model_derivation_rules_reference()
        profile_reference = model_structure_profile_reference(profile)

        active_inputs = tuple(
            self._approved_inputs.list_active_approved_inputs(project_id)
        )
        approved_engineering_information = (
            self._approved_engineering_information_for_inputs(
                project_id, active_inputs
            )
        )

        if selected_mode == ECO_DETERMINISTIC_MODE:
            base_deriver = ProfileDrivenModelCandidateDeriver(
                profile=profile,
                derivation_rules_reference=rules,
            )
            deriver = ApprovedEngineeringInformationDeriver(
                base_deriver=base_deriver,
                profile=profile,
            )
            provenance = self._eco_provenance(
                profile_reference=profile_reference,
                rules_reference=rules,
            )
        else:
            execution_dir = self._new_execution_directory(project_id)
            executor = self._modeling_executor_factory(
                project_root=self.project_root,
                provider=provider,
                model=model,
                api_key=api_key,
            )
            base_deriver = HybridModelCandidateDeriver(
                profile=profile,
                derivation_rules_reference=rules,
                executor=executor,
                output_dir=execution_dir,
                review_escalation_approved_input_ids=(
                    assessment.escalated_approved_input_ids
                ),
            )
            relationship_executor = (
                self._semantic_relationship_executor_factory(
                    project_root=self.project_root,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                )
            )
            deriver = ApprovedEngineeringInformationDeriver(
                base_deriver=base_deriver,
                profile=profile,
                relationship_executor=relationship_executor,
                output_dir=execution_dir,
            )
            provenance = None

        generation_kwargs = {
            "deriver": deriver,
            "model_structure_profile_reference": profile_reference,
            "derivation_rules_reference": rules,
            "generation_provenance": provenance,
            "predecessor_candidate_set_id": predecessor_candidate_set_id,
            "regeneration_reason": regeneration_reason,
        }
        if approved_engineering_information is not None:
            generation_kwargs["approved_engineering_information"] = (
                approved_engineering_information
            )
        return self._generation.generate_candidate_set(
            project_id,
            **generation_kwargs,
        )

    def _assessment_request(
        self,
        project_id: str,
        *,
        predecessor_candidate_set_id: str | None,
    ):
        project = self._workspace.load_project(project_id)
        approved_inputs = tuple(
            self._approved_inputs.list_active_approved_inputs(project_id)
        )
        predecessor = (
            None
            if predecessor_candidate_set_id is None
            else self._candidates.load_candidate_set(
                project_id,
                predecessor_candidate_set_id,
            )
        )

        profile = load_model_structure_profile()
        rules = load_model_derivation_rules_reference()
        base_strict_deriver = ProfileDrivenModelCandidateDeriver(
            profile=profile,
            derivation_rules_reference=rules,
        )
        approved_engineering_information = (
            self._approved_engineering_information_for_inputs(
                project_id, approved_inputs
            )
        )
        strict_deriver = ApprovedEngineeringInformationDeriver(
            base_deriver=base_strict_deriver,
            profile=profile,
        )
        request = ModelCandidateDerivationRequest(
            project_id=project_id,
            approved_inputs=approved_inputs,
            framework_template_reference=project.framework_template,
            model_structure_profile_reference=model_structure_profile_reference(
                profile
            ),
            derivation_rules_reference=rules,
            predecessor_candidate_set=predecessor,
            approved_engineering_information=approved_engineering_information,
        )
        return request, strict_deriver, predecessor

    def _approved_engineering_information_for_inputs(
        self,
        project_id: str,
        approved_inputs,
    ):
        if not approved_inputs:
            return None
        r4c_flags = tuple(
            isinstance(item.stable_subject_key, str)
            and item.stable_subject_key.startswith("subject:subj-")
            for item in approved_inputs
        )
        if not any(r4c_flags):
            return None
        if not all(r4c_flags):
            raise ModelCandidateGenerationBlockedError(
                "Phase-H active input snapshot mixes R4c canonical Subjects "
                "with legacy Approved Input authority."
            )
        review_refs = {
            (item.review_document_id, item.review_document_version_id)
            for item in approved_inputs
        }
        if len(review_refs) != 1:
            raise ModelCandidateGenerationBlockedError(
                "R4c Phase-H derivation requires one exact finalized Review "
                "Version for all active Approved Inputs."
            )
        review_document_id, review_document_version_id = next(iter(review_refs))
        if self._review_workflow_service is None:
            from modules.review_workspace.workflow_service import (
                ReviewApprovalWorkflowService,
            )
            self._review_workflow_service = ReviewApprovalWorkflowService(
                root=self.projects_root,
                repository_root=self.project_root,
                workspace=self._workspace,
                approved_input_repository=self._approved_inputs,
            )
        try:
            return self._review_workflow_service.approved_engineering_information(
                project_id,
                review_document_id,
                review_document_version_id,
            )
        except Exception as exc:
            raise ModelCandidateGenerationBlockedError(
                "Finalized R4c Approved Engineering Information authority is "
                "unavailable for Phase-H derivation."
            ) from exc

    def _default_model_placement_executor(
        self,
        *,
        project_root: Path,
        provider: str,
        model: str,
        api_key: str | None,
    ):
        from modules.model_placement.persona_executor import (
            ModelPlacementPersonaExecutor,
        )

        return ModelPlacementPersonaExecutor(
            project_root=project_root,
            provider=provider,
            model=model,
            api_key=api_key,
        )

    def _new_model_assembly_execution_directory(
        self,
        project_id: str,
    ) -> Path:
        root = (
            self.projects_root
            / project_id
            / "work"
            / "model_assembly_generation"
        )
        root.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(
                prefix="assembly_",
                dir=root,
            )
        )

    def _new_model_placement_execution_directory(
        self,
        project_id: str,
    ) -> Path:
        root = (
            self.projects_root
            / project_id
            / "work"
            / "model_placement_generation"
        )
        root.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(
                prefix="placement_",
                dir=root,
            )
        )

    def _default_semantic_relationship_executor(
        self,
        *,
        project_root: Path,
        provider: str,
        model: str,
        api_key: str | None,
    ):
        return SemanticRelationshipProjectionExecutor(
            project_root=project_root,
            provider=provider,
            model=model,
            api_key=api_key,
        )

    def _default_modeling_executor(
        self,
        *,
        project_root: Path,
        provider: str,
        model: str,
        api_key: str | None,
    ):
        return ModelingPersonaProjectionExecutor(
            project_root=project_root,
            provider=provider,
            model=model,
            api_key=api_key,
        )

    def _new_execution_directory(self, project_id: str) -> Path:
        root = (
            self.projects_root
            / project_id
            / "work"
            / "model_candidate_generation"
        )
        root.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(
                prefix="llm_assisted_",
                dir=root,
            )
        )

    def _eco_provenance(
        self,
        *,
        profile_reference,
        rules_reference,
    ) -> ModelCandidateGenerationProvenance:
        payload = {
            "mode": ECO_DETERMINISTIC_MODE,
            "profile_id": profile_reference.profile_id,
            "profile_version": profile_reference.profile_version,
            "profile_fingerprint": profile_reference.profile_fingerprint,
            "rules_context_id": rules_reference.context_id,
            "rules_context_version": rules_reference.context_version,
            "rules_context_fingerprint": rules_reference.context_fingerprint,
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        fingerprint = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return ModelCandidateGenerationProvenance(
            method="deterministic_profile_projection",
            recipe_reference="ADR-028:R5-01",
            agent_reference=None,
            model_reference=None,
            context_fingerprint=fingerprint,
        )
