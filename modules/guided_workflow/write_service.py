"""Authority-preserving write delegation for Guided Engineering Workflow."""

from __future__ import annotations

from pathlib import Path

from modules.final_model_review.change_workflow import (
    FinalModelReviewChangeService,
)
from modules.final_model_review.release_service import (
    FinalModelReviewReleaseService,
)
from modules.final_model_review.repository import (
    FinalModelReviewRepository,
)
from modules.model_candidates.candidate_review_repository import (
    ModelCandidateReviewRepository,
)
from modules.model_candidates.derivation_workflow import (
    ModelDerivationWorkflowService,
)
from modules.model_placement import (
    ModelPlacementReviewRepository,
)
from modules.output_publication.final_review_publication import (
    FinalReviewPublicationService,
)

from .errors import GuidedWorkflowWriteError


class GuidedWorkflowWriteService:
    """Delegate explicit Human actions to existing normative domain authority.

    This service owns no engineering, review, release or publication authority.
    It does not select implicit targets and does not maintain authoritative UI
    state.
    """

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        candidate_review_repository=None,
        model_derivation_service=None,
        model_placement_review_repository=None,
        model_assembly_repository=None,
        model_assembly_final_review_repository=None,
        authority_backed_internal_model_repository=None,
        authority_backed_sysml_repository=None,
        authority_backed_sysml_validation_repository=None,
        final_review_repository=None,
        final_change_service=None,
        final_release_service=None,
        final_publication_service=None,
    ) -> None:
        self.project_root = Path(project_root)
        projects_root = self.project_root / "data" / "projects"

        self._candidate_reviews = (
            ModelCandidateReviewRepository(
                root=projects_root,
            )
            if candidate_review_repository is None
            else candidate_review_repository
        )
        self._model_derivation = (
            ModelDerivationWorkflowService(
                project_root=self.project_root,
            )
            if model_derivation_service is None
            else model_derivation_service
        )
        self._model_placement_reviews = (
            ModelPlacementReviewRepository(root=projects_root)
            if model_placement_review_repository is None
            else model_placement_review_repository
        )
        if model_assembly_repository is None:
            from modules.model_assembly import ModelAssemblyRepository

            self._model_assemblies = ModelAssemblyRepository(
                root=projects_root
            )
        else:
            self._model_assemblies = model_assembly_repository

        if model_assembly_final_review_repository is None:
            from modules.model_assembly.final_review import (
                ModelAssemblyFinalReviewRepository,
            )

            self._model_assembly_final_reviews = (
                ModelAssemblyFinalReviewRepository(root=projects_root)
            )
        else:
            self._model_assembly_final_reviews = (
                model_assembly_final_review_repository
            )

        if authority_backed_internal_model_repository is None:
            from modules.internal_model.authority_backed import (
                AuthorityBackedInternalModelRepository,
            )

            self._authority_backed_internal_models = (
                AuthorityBackedInternalModelRepository(
                    root=projects_root
                )
            )
        else:
            self._authority_backed_internal_models = (
                authority_backed_internal_model_repository
            )

        if authority_backed_sysml_repository is None:
            from modules.sysml_generation.authority_backed import (
                AuthorityBackedSysMLArtifactRepository,
            )

            self._authority_backed_sysml = (
                AuthorityBackedSysMLArtifactRepository(
                    root=projects_root
                )
            )
        else:
            self._authority_backed_sysml = (
                authority_backed_sysml_repository
            )

        if authority_backed_sysml_validation_repository is None:
            from modules.sysml_validation.authority_backed import (
                AuthorityBackedSysMLValidationRepository,
            )

            self._authority_backed_sysml_validation = (
                AuthorityBackedSysMLValidationRepository(
                    root=projects_root
                )
            )
        else:
            self._authority_backed_sysml_validation = (
                authority_backed_sysml_validation_repository
            )

        if final_review_repository is None:
            final_review_repository = FinalModelReviewRepository(
                root=projects_root,
            )

        self._final_reviews = final_review_repository

        self._final_changes = (
            FinalModelReviewChangeService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_change_service is None
            else final_change_service
        )

        self._final_release = (
            FinalModelReviewReleaseService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_release_service is None
            else final_release_service
        )

        self._final_publication = (
            FinalReviewPublicationService(
                self.project_root,
                final_review_repository=self._final_reviews,
            )
            if final_publication_service is None
            else final_publication_service
        )

    def assess_model_derivation(
        self,
        project_id: str,
        *,
        predecessor_candidate_set_id: str | None = None,
    ):
        """Return advisory Phase-H strategy without making a Human choice."""

        try:
            return self._model_derivation.assess(
                project_id,
                predecessor_candidate_set_id=predecessor_candidate_set_id,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model derivation strategy could not be assessed safely."
            ) from exc

    def generate_model_placement_review(
        self,
        project_id: str,
        *,
        mode: str,
        provider: str = "openai",
        model: str = "gpt-5.4-mini",
        api_key: str | None = None,
    ):
        """Generate one reviewable Model Placement bundle, not a Candidate Set."""

        try:
            return self._model_derivation.prepare_model_placement_review(
                project_id,
                mode=mode,
                provider=provider,
                model=model,
                api_key=api_key,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Placement generation could not be completed safely."
            ) from exc

    def load_authority_backed_sysml_validation(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ):
        """Return persisted Phase-K result for authority-backed SysML."""

        try:
            return (
                self._authority_backed_sysml_validation
                .load_if_available(
                    project_id,
                    internal_engineering_model_id,
                )
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Authority-backed SysML validation could not be loaded safely."
            ) from exc

    def validate_authority_backed_sysml(
        self,
        project_id: str,
        *,
        artifact,
    ):
        """Run strict Phase-K validation on authority-backed SysML."""

        if artifact.project_id != project_id:
            raise GuidedWorkflowWriteError(
                "Authority-backed validation Project binding is invalid."
            )
        try:
            return self._authority_backed_sysml_validation.validate(
                artifact
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Authority-backed SysML validation failed safely."
            ) from exc

    def load_authority_backed_sysml(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ):
        """Return generated SysML v2 for an authority-backed Internal Model."""

        try:
            return self._authority_backed_sysml.load_if_available(
                project_id,
                internal_engineering_model_id,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Authority-backed SysML artifact could not be loaded safely."
            ) from exc

    def generate_authority_backed_sysml(
        self,
        project_id: str,
        *,
        snapshot,
    ):
        """Generate SysML v2 without Candidate Review traceability."""

        if snapshot.project_id != project_id:
            raise GuidedWorkflowWriteError(
                "Authority-backed SysML Project binding is invalid."
            )
        try:
            return self._authority_backed_sysml.generate(snapshot)
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Authority-backed SysML generation failed safely."
            ) from exc

    def list_refined_internal_models(
        self,
        project_id: str,
        source_internal_engineering_model_id: str,
    ):
        """Return Human-authorized refined successors for one exact source IEM."""

        return self.list_sem015_successor_internal_models(
            project_id,
            source_internal_engineering_model_id,
        )

    def materialize_refined_internal_model(
        self,
        project_id: str,
        *,
        source_snapshot,
        target_model_formulation_authority,
        model_quality_authority,
    ):
        """Materialize the exact Human-authorized refined Internal Model."""

        if source_snapshot.project_id != project_id:
            raise GuidedWorkflowWriteError(
                "Refined Internal Model Project binding is invalid."
            )
        try:
            from dataclasses import asdict, is_dataclass
            import json
            from pathlib import Path

            from modules.internal_model.semantic_successor import (
                SEM015InternalModelSuccessorRepository,
            )

            def payload(value):
                if isinstance(value, dict):
                    raw = dict(value)
                elif is_dataclass(value):
                    raw = asdict(value)
                else:
                    raise TypeError("Authority must be a dataclass or dict.")

                return json.loads(json.dumps(raw))

            repository = SEM015InternalModelSuccessorRepository(
                Path(self.project_root) / "data" / "projects"
            )
            return repository.materialize(
                source=source_snapshot,
                target_model_formulation_authority=payload(
                    target_model_formulation_authority
                ),
                model_quality_authority=payload(model_quality_authority),
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Refined Internal Model materialization failed safely."
            ) from exc

    def list_sem015_successor_internal_models(
        self,
        project_id: str,
        source_internal_engineering_model_id: str,
    ):
        """Return exact SEM-015 successors for one explicit source IEM."""

        try:
            from pathlib import Path
            import json

            root = (
                Path(self.project_root)
                / "data"
                / "projects"
                / project_id
                / "internal_models_v2"
            )
            if not root.exists():
                return ()
            result = []
            for entry in sorted(root.iterdir(), key=lambda item: item.name):
                if entry.is_symlink() or not entry.is_dir():
                    continue
                sidecar = entry / "semantic_authority.json"
                if sidecar.is_symlink() or not sidecar.is_file():
                    continue
                raw = json.loads(sidecar.read_text(encoding="utf-8"))
                binding = raw.get("authority_binding", {})
                if (
                    binding.get("source_internal_engineering_model_id")
                    != source_internal_engineering_model_id
                ):
                    continue
                model = self._authority_backed_internal_models.load(
                    project_id,
                    entry.name,
                )
                result.append(
                    {
                        "internal_engineering_model_id": (
                            model.internal_engineering_model_id
                        ),
                        "model": model,
                        "target_model_formulation_authority_set_id": (
                            binding.get(
                                "target_model_formulation_authority_set_id"
                            )
                        ),
                        "model_quality_authority_set_id": (
                            binding.get("model_quality_authority_set_id")
                        ),
                        "intentionally_not_materialized_relationship_ids": (
                            tuple(
                                binding.get(
                                    "intentionally_not_materialized_relationship_ids",
                                    (),
                                )
                            )
                        ),
                    }
                )
            return tuple(result)
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "SEM-015 successor Internal Models could not be loaded safely."
            ) from exc

    def preview_authority_backed_sysml_validation(
        self,
        project_id: str,
        *,
        artifact,
    ):
        """Run current Phase-K validation without persisting a new result."""

        if artifact.project_id != project_id:
            raise GuidedWorkflowWriteError(
                "Authority-backed validation Project binding is invalid."
            )
        try:
            from modules.sysml_validation.authority_backed import (
                AuthorityBackedSysMLValidationService,
            )

            return AuthorityBackedSysMLValidationService().validate(
                artifact
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Current SysML validation preview failed safely."
            ) from exc

    def load_authority_backed_internal_model(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return the v2 Internal Model for this exact placement comparison."""

        try:
            return (
                self._authority_backed_internal_models
                .find_by_comparison(
                    project_id,
                    comparison_fingerprint,
                )
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Authority-backed Internal Model could not be loaded safely."
            ) from exc

    def materialize_authority_backed_internal_model(
        self,
        project_id: str,
        *,
        draft,
        final_decision,
        profile,
        framework_template,
    ):
        """Materialize approved Assembly authority without Candidate Review."""

        if (
            draft.project_id != project_id
            or final_decision.project_id != project_id
        ):
            raise GuidedWorkflowWriteError(
                "Internal Model authority Project binding is invalid."
            )
        try:
            return self._authority_backed_internal_models.materialize(
                draft=draft,
                final_decision=final_decision,
                profile=profile,
                framework_template=framework_template,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Authority-backed Internal Model could not be materialized safely."
            ) from exc

    def load_model_final_review_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return the immutable whole-model Final Review decision, if any."""

        try:
            return self._model_assembly_final_reviews.latest_decision(
                project_id,
                comparison_fingerprint,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final Model Review decision could not be loaded safely."
            ) from exc

    def model_final_review_options(
        self,
        draft,
        *,
        profile,
    ):
        """Build exact Human-selectable Relationship representation options."""

        try:
            from modules.model_assembly.final_review import (
                build_final_model_review_options,
            )

            return build_final_model_review_options(
                draft=draft,
                profile=profile,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final Model Review options could not be built safely."
            ) from exc

    def record_model_final_review_decision(
        self,
        project_id: str,
        *,
        draft,
        profile,
        decision: str,
        selected_relationship_rules,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Persist one explicit Human decision over the exact Assembly Draft."""

        if draft.project_id != project_id:
            raise GuidedWorkflowWriteError(
                "Final Model Review Project binding is invalid."
            )
        try:
            return self._model_assembly_final_reviews.record(
                draft=draft,
                profile=profile,
                decision=decision,
                selected_relationship_rules=selected_relationship_rules,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final Model Review decision could not be recorded safely."
            ) from exc

    def assemble_model_draft(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        provider: str = "openai",
        model: str = "gpt-5.4-mini",
        api_key: str | None = None,
    ):
        """Assemble Human-approved placements without creating new authority."""

        try:
            return self._model_derivation.assemble_model_draft(
                project_id,
                comparison_fingerprint,
                provider=provider,
                model=model,
                api_key=api_key,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Assembly could not be completed safely."
            ) from exc

    def generate_model_proposal(
        self,
        project_id: str,
        *,
        mode: str,
        provider: str = "openai",
        model: str = "gpt-5.4-mini",
        api_key: str | None = None,
        predecessor_candidate_set_id: str | None = None,
        human_regeneration_reason: str | None = None,
    ):
        """Generate one explicit Phase-H Candidate Set."""

        try:
            return self._model_derivation.generate(
                project_id,
                mode=mode,
                provider=provider,
                model=model,
                api_key=api_key,
                predecessor_candidate_set_id=predecessor_candidate_set_id,
                human_regeneration_reason=human_regeneration_reason,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Proposal generation could not be completed safely."
            ) from exc

    def list_model_placement_comparisons(
        self,
        project_id: str,
    ):
        """Return persisted Human Model Placement review bundles."""

        try:
            return self._model_placement_reviews.list_comparisons(
                project_id
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Placement comparisons could not be loaded safely."
            ) from exc

    def model_placement_review_state(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return effective Human Model Placement Review state."""

        try:
            return self._model_placement_reviews.review_state(
                project_id,
                comparison_fingerprint,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Placement Review state could not be loaded safely."
            ) from exc

    def load_finalized_model_placement_set(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return finalized placement authority when available."""

        try:
            return (
                self._model_placement_reviews
                .load_approved_placement_set_if_available(
                    project_id,
                    comparison_fingerprint,
                )
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Finalized Model Placement authority could not be loaded safely."
            ) from exc

    def load_model_assembly_draft(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return persisted Model Assembly Draft when available."""

        try:
            return self._model_assemblies.load_if_available(
                project_id,
                comparison_fingerprint,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Assembly Draft could not be loaded safely."
            ) from exc

    def finalize_model_placement_review(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        profile,
    ):
        """Finalize Human-resolved placement authority for later assembly."""

        try:
            return self._model_placement_reviews.finalize_approved_placement_set(
                project_id,
                comparison_fingerprint,
                profile=profile,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Placement Review could not be finalized safely."
            ) from exc

    def record_model_placement_review_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        approved_input_id: str,
        outcome: str,
        selected_rule_id: str | None,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Record one explicit Human Model Placement decision."""

        try:
            return self._model_placement_reviews.record_decision(
                project_id,
                comparison_fingerprint,
                approved_input_id=approved_input_id,
                outcome=outcome,
                selected_rule_id=selected_rule_id,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Placement decision could not be recorded safely."
            ) from exc

    def reopen_model_placement_review_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        approved_input_id: str,
        reviewer_identity: str,
        rationale: str,
    ):
        """Reopen one decided placement without mutating its history."""

        try:
            return self._model_placement_reviews.reopen_decision(
                project_id,
                comparison_fingerprint,
                approved_input_id=approved_input_id,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Placement decision could not be reopened safely."
            ) from exc

    def record_candidate_review_decision(
        self,
        project_id: str,
        candidate_set_id: str,
        *,
        target_type: str,
        candidate_id: str,
        decision: str,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Record one Human decision against one explicit Candidate snapshot."""

        try:
            return self._candidate_reviews.record_decision(
                project_id,
                candidate_set_id,
                target_type=target_type,
                candidate_id=candidate_id,
                decision=decision,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Candidate Review decision could not be recorded safely."
            ) from exc

    def submit_final_model_change(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
        *,
        surface: str,
        classification: str,
        reviewer_feedback: str,
        created_by: str,
        generated_unit_id: str | None = None,
        generated_symbol_id: str | None = None,
        internal_model_element_id: str | None = None,
        internal_model_relationship_id: str | None = None,
        validation_finding_code: str | None = None,
        original_text: str | None = None,
        proposed_text: str | None = None,
        request_agent_reproposal: bool = False,
        requested_agent_personalities: tuple[str, ...] = (),
    ):
        """Submit one immutable Human change proposal for one exact FRV."""

        try:
            return self._final_changes.submit_change(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
                surface=surface,
                classification=classification,
                reviewer_feedback=reviewer_feedback,
                created_by=created_by,
                generated_unit_id=generated_unit_id,
                generated_symbol_id=generated_symbol_id,
                internal_model_element_id=internal_model_element_id,
                internal_model_relationship_id=(
                    internal_model_relationship_id
                ),
                validation_finding_code=validation_finding_code,
                original_text=original_text,
                proposed_text=proposed_text,
                request_agent_reproposal=request_agent_reproposal,
                requested_agent_personalities=(
                    requested_agent_personalities
                ),
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final Model Review change request could not be recorded safely."
            ) from exc

    def list_phase_l_review_subject_candidates(
        self,
        project_id: str,
    ):
        # Discovery only: never selects an implicit latest artifact.
        generated_root = (
            self.project_root
            / "data"
            / "projects"
            / project_id
            / "generated_sysml_v2"
        )
        if not generated_root.exists():
            return ()
        if generated_root.is_symlink() or not generated_root.is_dir():
            raise GuidedWorkflowWriteError(
                "Generated SysML review-subject root is unsafe."
            )

        result = []
        for entry in sorted(generated_root.iterdir(), key=lambda item: item.name):
            if entry.is_symlink() or not entry.is_dir():
                continue
            artifact_file = entry / "artifact_set.json"
            if artifact_file.is_symlink() or not artifact_file.is_file():
                continue
            try:
                artifact = self._authority_backed_sysml.load(
                    project_id,
                    entry.name,
                )
            except Exception as exc:
                raise GuidedWorkflowWriteError(
                    "Generated SysML review-subject candidate could not "
                    "be reconstructed safely."
                ) from exc
            result.append(
                {
                    "internal_engineering_model_id": (
                        artifact.source_internal_engineering_model_id
                    ),
                    "artifact_fingerprint": artifact.content_fingerprint,
                    "unit_count": len(artifact.units),
                }
            )
        return tuple(result)

    def create_phase_l_final_model_review(
        self,
        project_id: str,
        internal_engineering_model_id: str,
        *,
        validation_result=None,
    ):
        # Create/reuse only the exact Phase-L review subject.
        # No Human release or publication authority is inferred.
        try:
            artifact = self._authority_backed_sysml.load(
                project_id,
                internal_engineering_model_id,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Generated SysML artifact could not be loaded for "
                "Final Model Review."
            ) from exc

        if validation_result is None:
            validation_result = (
                self.preview_authority_backed_sysml_validation(
                    project_id,
                    artifact=artifact,
                )
            )

        if validation_result.project_id != project_id:
            raise GuidedWorkflowWriteError(
                "Validation result Project binding is invalid."
            )
        if (
            validation_result.source_internal_engineering_model_id
            != artifact.source_internal_engineering_model_id
        ):
            raise GuidedWorkflowWriteError(
                "Validation result does not target the selected Internal Model."
            )
        if (
            validation_result.source_artifact_set_fingerprint
            != artifact.content_fingerprint
        ):
            raise GuidedWorkflowWriteError(
                "Validation result does not cover the exact generated artifact."
            )

        try:
            scan = self._final_reviews.scan(project_id)
            if scan.issues:
                raise GuidedWorkflowWriteError(
                    "Final Model Review repository contains integrity issues."
                )

            reviews = tuple(scan.review_manifests)
            if len(reviews) > 1:
                raise GuidedWorkflowWriteError(
                    "Multiple Final Model Review containers exist; "
                    "an explicit target is required."
                )

            review = (
                reviews[0]
                if reviews
                else self._final_reviews.create_review(project_id)
            )

            existing = self._final_reviews.list_revisions(
                project_id,
                review.final_model_review_id,
            )
            for bundle in existing:
                revision = bundle.revision
                if (
                    revision.source_internal_engineering_model_id
                    == artifact.source_internal_engineering_model_id
                    and revision.generated_artifact_set_fingerprint
                    == artifact.content_fingerprint
                    and revision.validation_result_fingerprint
                    == validation_result.content_fingerprint
                ):
                    return bundle

            return self._final_reviews.append_revision(
                project_id,
                review.final_model_review_id,
                artifact_set=artifact,
                validation_result=validation_result,
            )
        except GuidedWorkflowWriteError:
            raise
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final Model Review subject could not be created safely."
            ) from exc

    def approve_final_model_for_publication(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
        *,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Record Human publication approval for one exact validated FRV."""

        try:
            return self._final_release.approve_for_publication(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final publication approval could not be recorded safely."
            ) from exc


    def publish_final_model_review_revision(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
    ):
        """Publish one explicit already-approved Final Model Review revision."""

        try:
            return self._final_publication.publish_revision(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Approved Final Model Review revision could not be "
                "published safely."
            ) from exc
