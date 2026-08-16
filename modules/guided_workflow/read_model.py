
"""Deterministic read-side projection for the Guided Engineering Workflow."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from modules.final_model_review.release_service import (
    FinalModelReviewReleaseService,
)
from modules.final_model_review.repository import (
    FinalModelReviewRepository,
)
from modules.model_candidates.model_proposal import (
    ModelProposalReadService,
)
from modules.model_candidates.repository import ModelCandidateRepository
from modules.output_publication.repository import (
    OutputPublicationRepository,
)
from modules.project_dashboard.service import ProjectDashboardService
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)

from .errors import GuidedWorkflowValidationError
from .presentation import (
    build_guided_workflow_view,
    create_stage_view,
)


_DISAGREEMENT_STATES = frozenset(
    {
        "majority_with_disagreement",
        "minority_interpretation",
        "conflict",
    }
)

_HUMAN_RELEASE_ATTENTION_BLOCKERS = frozenset(
    {
        "mandatory_review_items_unresolved",
        "change_proposals_unresolved",
    }
)


class GuidedWorkflowReadService:
    """Project existing authority into one engineer-centered workflow view.

    This service owns no engineering or workflow authority. Every stage is
    reconstructed from existing read-side services and immutable repositories.
    """

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        dashboard_service=None,
        review_service=None,
        candidate_repository=None,
        model_proposal_service=None,
        final_review_repository=None,
        final_release_service=None,
        output_repository=None,
    ) -> None:
        self.project_root = Path(project_root)
        projects_root = self.project_root / "data" / "projects"

        self._dashboard = (
            ProjectDashboardService(
                root=projects_root,
                repository_root=self.project_root,
            )
            if dashboard_service is None
            else dashboard_service
        )
        self._review = (
            ReviewApprovalWorkflowService(
                root=projects_root,
                repository_root=self.project_root,
            )
            if review_service is None
            else review_service
        )
        self._candidates = (
            ModelCandidateRepository(root=projects_root)
            if candidate_repository is None
            else candidate_repository
        )
        self._model_proposals = (
            ModelProposalReadService(
                root=projects_root,
                candidate_repository=self._candidates,
            )
            if model_proposal_service is None
            else model_proposal_service
        )
        self._final_reviews = (
            FinalModelReviewRepository(root=projects_root)
            if final_review_repository is None
            else final_review_repository
        )
        self._final_release = (
            FinalModelReviewReleaseService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_release_service is None
            else final_release_service
        )
        self._outputs = (
            OutputPublicationRepository(
                output_root=self.project_root / "data" / "output"
            )
            if output_repository is None
            else output_repository
        )

    def load_view(self, project_id: str):
        """Load one complete non-authoritative project workflow projection."""

        try:
            # Validate the exact Project through the established P7 read side.
            self._dashboard.project_overview(project_id)
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "The selected Project cannot be projected safely."
            ) from exc

        source_stage, processing_stage = (
            self._source_and_processing_stages(project_id)
        )
        human_stage, confirmed_result_count = (
            self._human_review_stage(project_id)
        )
        model_stage = self._model_proposal_stage(
            project_id,
            human_stage=human_stage,
        )
        final_stage, final_approved = self._final_review_stage(
            project_id,
            model_stage=model_stage,
        )
        output_stage = self._output_stage(
            project_id,
            final_approved=final_approved,
        )

        return build_guided_workflow_view(
            project_id=project_id,
            stages=(
                source_stage,
                processing_stage,
                human_stage,
                model_stage,
                final_stage,
                output_stage,
            ),
            confirmed_result_count=confirmed_result_count,
        )

    def _source_and_processing_stages(self, project_id: str):
        try:
            view = self._dashboard.source_processing_view(project_id)
        except Exception:
            unavailable = create_stage_view(
                stage_id="project_sources",
                presentation_status="unavailable",
                semantic="blocking",
                summary="Source information is currently unavailable.",
                blocking_issue_count=1,
                action_label="Inspect Project state",
            )
            processing = create_stage_view(
                stage_id="processing",
                presentation_status="unavailable",
                semantic="blocking",
                summary="Processing state cannot be reconstructed safely.",
                blocking_issue_count=1,
                action_label="Inspect processing state",
            )
            return unavailable, processing

        source_count = len(view.sources)

        if source_count:
            source_status = "complete"
            source_semantic = "positive"
            source_action = "Manage sources"
            source_summary = (
                f"{source_count} source"
                + ("" if source_count == 1 else "s")
                + " provided."
            )
        else:
            source_status = "action_required"
            source_semantic = "attention"
            source_action = "Add first source"
            source_summary = "No engineering source has been provided yet."

        source_stage = create_stage_view(
            stage_id="project_sources",
            presentation_status=source_status,
            semantic=source_semantic,
            summary=source_summary,
            action_label=source_action,
        )

        running = 0
        awaiting_review = 0
        completed = 0
        attention = 0

        for row in view.sources:
            if row.run_state in {"created", "running"}:
                running += 1
            elif row.run_state == "awaiting_review":
                awaiting_review += 1
            elif row.run_state in {"completed", "superseded"}:
                completed += 1

            if (
                row.run_state in {"blocked", "failed"}
                or row.blocking_issue_codes
                or row.failure_issue_codes
            ):
                attention += 1

        repository_blockers = sum(
            1
            for issue in view.issues
            if getattr(issue, "issue_level", None) == "blocking"
        )
        blockers = attention + repository_blockers

        if source_count == 0:
            processing_status = "not_started"
            processing_semantic = "neutral"
            processing_action = None
        elif blockers:
            processing_status = "blocked"
            processing_semantic = "blocking"
            processing_action = "Resolve processing issues"
        elif running:
            processing_status = "in_progress"
            processing_semantic = "informational"
            processing_action = "Open processing"
        elif awaiting_review or completed == source_count:
            processing_status = "complete"
            processing_semantic = "positive"
            processing_action = "Inspect processing results"
        else:
            processing_status = "ready"
            processing_semantic = "informational"
            processing_action = "Process sources"

        processing_summary = (
            f"{completed} complete · "
            f"{running} running · "
            f"{awaiting_review} awaiting review · "
            f"{attention} need attention"
        )

        processing_stage = create_stage_view(
            stage_id="processing",
            presentation_status=processing_status,
            semantic=processing_semantic,
            summary=processing_summary,
            blocking_issue_count=blockers,
            action_label=processing_action,
        )

        return source_stage, processing_stage

    def _human_review_stage(self, project_id: str):
        try:
            view = self._review.project_view(project_id)
        except Exception:
            return (
                create_stage_view(
                    stage_id="human_review",
                    presentation_status="unavailable",
                    semantic="blocking",
                    summary="Human Review state cannot be reconstructed safely.",
                    blocking_issue_count=1,
                    action_label="Inspect Human Review",
                ),
                0,
            )

        blockers = sum(
            1
            for issue in view.issues
            if getattr(issue, "issue_level", None) == "blocking"
        )

        decisions = 0
        active_approved_inputs: set[str] = set()
        variance_attention = 0
        variance_read_failures = 0
        actionable_document_ids: list[str] = []

        for item in view.items:
            decisions += self._outcome_count(item, "open")
            decisions += self._outcome_count(item, "unresolved")

            active_approved_inputs.update(
                item.active_approved_input_ids
            )

            if (
                item.workflow_status != "approved_input_available"
                and item.review_document_id is not None
            ):
                actionable_document_ids.append(
                    item.review_document_id
                )

            if (
                item.review_document_id is not None
                and item.review_document_version_id is not None
            ):
                try:
                    facts = self._review.review_filter_facts(
                        project_id,
                        item.review_document_id,
                        item.review_document_version_id,
                    )
                except Exception:
                    variance_read_failures += 1
                else:
                    variance_attention += sum(
                        1
                        for fact in facts
                        if fact.agent_disagreement_state
                        in _DISAGREEMENT_STATES
                    )

        blockers += variance_read_failures

        statuses = {
            item.workflow_status
            for item in view.items
        }

        if blockers:
            status = "blocked"
            semantic = "blocking"
        elif not view.items:
            status = "not_started"
            semantic = "neutral"
        elif statuses == {"approved_input_available"}:
            status = "complete"
            semantic = "positive"
        else:
            status = "action_required"
            semantic = "attention"

        if decisions:
            action = (
                f"Resolve {decisions} Human decision"
                + ("" if decisions == 1 else "s")
            )
        elif view.items and status != "complete":
            action = "Continue Human Review"
        else:
            action = None

        summary = (
            f"{len(view.items)} source workflow"
            + ("" if len(view.items) == 1 else "s")
            + f" · {decisions} open decisions"
            + f" · {len(active_approved_inputs)} active approved inputs"
        )

        if variance_read_failures:
            summary += " · variance evidence unavailable"

        unique_targets = tuple(sorted(set(actionable_document_ids)))

        stage = create_stage_view(
            stage_id="human_review",
            presentation_status=status,
            semantic=semantic,
            summary=summary,
            decision_count=decisions,
            variance_attention_count=variance_attention,
            blocking_issue_count=blockers,
            action_label=action,
            target_entity_id=(
                unique_targets[0]
                if len(unique_targets) == 1
                else None
            ),
        )
        return stage, len(active_approved_inputs)

    def _model_proposal_stage(
        self,
        project_id: str,
        *,
        human_stage,
    ):
        try:
            scan = self._candidates.scan_project(project_id)
        except Exception:
            return create_stage_view(
                stage_id="model_proposal",
                presentation_status="unavailable",
                semantic="blocking",
                summary="Model Proposal state is unavailable.",
                blocking_issue_count=1,
                action_label="Inspect Model Proposal state",
            )

        blockers = len(scan.issues)
        heads = self._candidate_heads(scan.candidate_sets)

        if scan.candidate_sets and not heads:
            blockers += 1

        decision_count = 0
        proposal_blockers = 0
        gate_statuses: list[str] = []

        for snapshot in heads:
            candidate_set_id = snapshot.manifest.candidate_set_id
            try:
                proposal = self._model_proposals.load_model_proposal(
                    project_id,
                    candidate_set_id,
                )
            except Exception:
                proposal_blockers += 1
                continue

            decision_count += len(
                proposal.required_human_decisions
            )
            proposal_blockers += len(
                proposal.blocking_issues
            )
            gate_statuses.append(
                proposal.phase_i_gate_status
            )

        blockers += proposal_blockers

        if not scan.candidate_sets:
            if human_stage.presentation_status == "complete":
                status = "ready"
                semantic = "informational"
                action = "Create model proposal"
                summary = (
                    "Approved engineering input is available; "
                    "no Model Proposal has been created yet."
                )
            else:
                status = "not_started"
                semantic = "neutral"
                action = None
                summary = "No Model Proposal is available yet."
        elif blockers:
            status = "blocked"
            semantic = "blocking"
            action = "Inspect Model Proposal issues"
            summary = (
                f"{len(heads)} current proposal"
                + ("" if len(heads) == 1 else "s")
                + f" · {decision_count} decisions · "
                f"{blockers} blocking issues"
            )
        elif decision_count:
            status = "action_required"
            semantic = "attention"
            action = "Review model proposal"
            summary = (
                f"{len(heads)} current proposal"
                + ("" if len(heads) == 1 else "s")
                + f" · {decision_count} Human decisions required"
            )
        elif gate_statuses and all(
            value == "ready"
            for value in gate_statuses
        ):
            status = "complete"
            semantic = "positive"
            action = "Inspect accepted proposal"
            summary = (
                f"{len(heads)} current proposal"
                + ("" if len(heads) == 1 else "s")
                + " ready for engineering-model assembly."
            )
        else:
            status = "in_progress"
            semantic = "informational"
            action = "Review model proposal"
            summary = (
                f"{len(heads)} current proposal"
                + ("" if len(heads) == 1 else "s")
                + " under engineering review."
            )

        return create_stage_view(
            stage_id="model_proposal",
            presentation_status=status,
            semantic=semantic,
            summary=summary,
            decision_count=decision_count,
            blocking_issue_count=blockers,
            action_label=action,
            target_entity_id=(
                heads[0].manifest.candidate_set_id
                if len(heads) == 1
                else None
            ),
        )

    def _final_review_stage(
        self,
        project_id: str,
        *,
        model_stage,
    ):
        try:
            scan = self._final_reviews.scan(project_id)
        except Exception:
            return (
                create_stage_view(
                    stage_id="final_model_review",
                    presentation_status="unavailable",
                    semantic="blocking",
                    summary="Final Model Review state is unavailable.",
                    blocking_issue_count=1,
                    action_label="Inspect Final Model Review state",
                ),
                False,
            )

        repository_blockers = sum(
            1
            for issue in scan.issues
            if getattr(issue, "issue_level", "blocking")
            == "blocking"
        )

        heads, lineage_blockers = self._final_review_heads(
            scan.revisions
        )
        hard_blockers = repository_blockers + lineage_blockers
        attention_blockers = 0
        decision_count = 0
        approved_count = 0

        for bundle in heads:
            revision = bundle.revision
            try:
                gate = self._final_release.evaluate(
                    project_id,
                    revision.final_model_review_id,
                    revision.final_model_review_revision_id,
                )
            except Exception:
                hard_blockers += 1
                continue

            if gate.release_status == "approved_for_publication":
                approved_count += 1
                continue

            if gate.release_status == "ready_for_approval":
                decision_count += 1
                continue

            blocker_codes = {
                blocker.code
                for blocker in gate.blockers
            }
            attention_codes = (
                blocker_codes
                & _HUMAN_RELEASE_ATTENTION_BLOCKERS
            )
            hard_codes = (
                blocker_codes
                - _HUMAN_RELEASE_ATTENTION_BLOCKERS
            )

            attention_blockers += len(attention_codes)
            hard_blockers += len(hard_codes)

        if not scan.revisions:
            if model_stage.presentation_status == "complete":
                status = "ready"
                semantic = "informational"
                action = "Generate and review final model"
                summary = (
                    "The accepted Model Proposal is ready for "
                    "generation and Final Model Review."
                )
            else:
                status = "not_started"
                semantic = "neutral"
                action = None
                summary = "No Final Model Review revision exists yet."
        elif hard_blockers:
            status = "blocked"
            semantic = "blocking"
            action = "Inspect Final Model Review blockers"
            summary = (
                f"{len(heads)} current review revision"
                + ("" if len(heads) == 1 else "s")
                + f" · {hard_blockers} blocking issues"
            )
        elif decision_count or attention_blockers:
            status = "action_required"
            semantic = "attention"
            action = "Review final model"
            summary = (
                f"{len(heads)} current review revision"
                + ("" if len(heads) == 1 else "s")
                + f" · {decision_count} release decisions"
                + f" · {attention_blockers} review actions"
            )
        elif heads and approved_count == len(heads):
            status = "complete"
            semantic = "positive"
            action = "Inspect approved final model"
            summary = (
                f"{approved_count} final review revision"
                + ("" if approved_count == 1 else "s")
                + " approved for publication."
            )
        else:
            status = "in_progress"
            semantic = "informational"
            action = "Review final model"
            summary = "Final Model Review is in progress."

        stage = create_stage_view(
            stage_id="final_model_review",
            presentation_status=status,
            semantic=semantic,
            summary=summary,
            decision_count=decision_count,
            blocking_issue_count=(
                hard_blockers + attention_blockers
            ),
            action_label=action,
        )
        return stage, approved_count > 0

    def _output_stage(
        self,
        project_id: str,
        *,
        final_approved: bool,
    ):
        try:
            scan = self._outputs.scan_project(project_id)
        except Exception:
            return create_stage_view(
                stage_id="published_output",
                presentation_status="unavailable",
                semantic="blocking",
                summary="Published Output state is unavailable.",
                blocking_issue_count=1,
                action_label="Inspect publication state",
            )

        blockers = sum(
            1
            for issue in scan.issues
            if getattr(issue, "issue_level", "blocking")
            == "blocking"
        )

        if blockers:
            status = "blocked"
            semantic = "blocking"
            action = "Inspect publication issues"
        elif scan.packages:
            status = "complete"
            semantic = "positive"
            action = "Open published output"
        elif final_approved:
            status = "ready"
            semantic = "informational"
            action = "Publish approved model"
        else:
            status = "not_started"
            semantic = "neutral"
            action = None

        if scan.packages:
            summary = (
                f"{len(scan.packages)} immutable output package"
                + ("" if len(scan.packages) == 1 else "s")
                + " published."
            )
        elif final_approved:
            summary = (
                "A Human-approved final model is eligible "
                "for controlled publication."
            )
        else:
            summary = "No final output package has been published yet."

        return create_stage_view(
            stage_id="published_output",
            presentation_status=status,
            semantic=semantic,
            summary=summary,
            blocking_issue_count=blockers,
            action_label=action,
            target_entity_id=(
                scan.packages[0].manifest.output_package_id
                if len(scan.packages) == 1
                else None
            ),
        )

    @staticmethod
    def _outcome_count(item, outcome: str) -> int:
        method = getattr(item, "review_outcome_count", None)
        if callable(method):
            return int(method(outcome))
        return int(
            dict(
                getattr(
                    item,
                    "review_outcome_counts",
                    (),
                )
            ).get(outcome, 0)
        )

    @staticmethod
    def _candidate_heads(candidate_sets):
        sets = tuple(candidate_sets)
        predecessor_ids = {
            snapshot.manifest.predecessor_candidate_set_id
            for snapshot in sets
            if snapshot.manifest.predecessor_candidate_set_id
            is not None
        }
        return tuple(
            snapshot
            for snapshot in sets
            if snapshot.manifest.candidate_set_id
            not in predecessor_ids
        )

    @staticmethod
    def _final_review_heads(revision_bundles):
        bundles = tuple(revision_bundles)
        by_review = defaultdict(list)

        for bundle in bundles:
            by_review[
                bundle.revision.final_model_review_id
            ].append(bundle)

        heads = []
        blockers = 0

        for review_id in sorted(by_review):
            review_bundles = by_review[review_id]
            predecessor_ids = {
                bundle.revision.predecessor_revision_id
                for bundle in review_bundles
                if bundle.revision.predecessor_revision_id
                is not None
            }
            review_heads = [
                bundle
                for bundle in review_bundles
                if bundle.revision.final_model_review_revision_id
                not in predecessor_ids
            ]

            if len(review_heads) != 1:
                blockers += 1
                continue

            heads.append(review_heads[0])

        return tuple(heads), blockers
