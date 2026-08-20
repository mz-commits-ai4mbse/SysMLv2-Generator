"""Application service for G6 Human Review and Approval."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from modules.framework_assignment import FrameworkAssignmentRepository
from modules.human_review import (
    HUMAN_REVIEW_DECISIONS,
    HumanReviewRepository,
    HumanReviewScanResult,
)
from modules.information_units import InformationUnitRepository
from modules.project_processing import (
    ProjectProcessingRepository,
    ProjectProcessingSummaryService,
    derive_processing_run_state,
    derive_source_processing_summaries,
)
from modules.project_sources import ProjectSourceRegistry
from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)
from modules.terminology_mapping import TerminologyMappingRepository

from .errors import (
    ReviewFinalizationBlockedError,
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
    ReviewWorkspaceError,
)
from .evidence_adapter import select_p9_review_evidence_set
from .open_question_resolution import (
    CreateElementFromOpenQuestionRequest,
    ResolveRelationshipEndpointsRequest,
    create_element_from_open_question_revision,
    create_relationship_endpoint_resolution_revision,
)
from .resolution_candidates import (
    project_relationship_resolution_candidates,
)
from .finalization_authorization import (
    authorize_persisted_review_document_finalization,
)
from .finalization_validation import (
    assess_review_document_finalization,
    create_review_document_finalization_target,
)
from .finalization_workflow import (
    ReviewFinalizationWorkflowPreview,
    build_finalized_review_artifact_set,
    create_review_finalization_workflow_preview,
)
from .workflow_editing import (
    ReviewItemEditRequest,
    create_item_edit_revision,
)
from .proposal_detail import (
    ReviewProposalDetail,
    build_review_proposal_details,
)
from .workflow_lineage import (
    ReviewMergeRequest,
    ReviewProposalActionRequest,
    ReviewSplitRequest,
    create_merge_revision,
    create_proposal_accept_revision,
    create_proposal_reject_revision,
    create_split_revision,
)
from .promotion_workflow import (
    ReviewApprovedInputEventTrace,
    ReviewApprovedInputTrace,
    ReviewApprovalPromotionResult,
)
from .scoped_workflow import (
    ReviewConsensusFilterFact,
    ReviewFilterSpec,
    ReviewItemFilterFact,
    ScopedReviewActionImpactPreview,
    ScopedReviewActionRequest,
    build_review_item_filter_fact,
    create_scoped_review_action_mutation,
    preview_scoped_review_action,
)
from .identifiers import (
    format_review_document_version_id,
    format_review_revision_id,
    next_review_item_id,
)
from .p4_evidence_adapter import select_p4_review_evidence_set
from .p4_evidence_reference_adapter import construct_p4_evidence_references
from .p9_evidence_reference_adapter import (
    construct_p9_evidence_references,
    construct_p9_source_evidence_references,
    load_p9_consensus_evidence_facts,
)
from .p9_review_admissibility_adapter import (
    adapt_p9_agent_proposals_for_review,
)
from .semantic_review_projection import (
    load_semantic_review_consensus_evidence_facts,
    project_p9_proposals_to_semantic_subjects,
    project_p9_review_inputs_to_semantic_subjects,
)
from .repository import DEFAULT_PROJECTS_ROOT, ReviewWorkspaceRepository
from .review_document_assembly import assemble_initial_review_document
from .workflow_types import (
    ReviewApprovalFinalizationResult,
    ReviewApprovalIssue,
    ReviewApprovalProjectView,
    ReviewApprovalQueueItem,
    ReviewApprovalWorkspaceOpenResult,
    ReviewApprovalWorkspaceView,
)


_P4_HUMAN_REVIEW_TARGET_TYPES = frozenset(
    {
        "information_unit_publication",
        "terminology_mapping_candidate",
        "framework_assignment_candidate",
    }
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ReviewApprovalWorkflowService:
    """Compose G2-G5 authority into the G6 application workflow.

    Read operations project the existing immutable authority stores. The G6.2
    creation command may create exactly one initial Review Workspace, but only
    by delegating evidence selection, assembly and persistence to the existing
    G2-G4 contracts.
    """

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository_root: Path | str = Path("."),
        clock: Callable[[], datetime] = _default_clock,
        workspace=None,
        source_registry=None,
        processing_summary_service=None,
        processing_repository=None,
        review_repository=None,
        human_review_repository=None,
        information_unit_repository=None,
        terminology_mapping_repository=None,
        framework_assignment_repository=None,
        approved_input_repository=None,
        promotion_service=None,
        source_summary_deriver: Callable | None = None,
        run_state_deriver: Callable | None = None,
        finalization_assessor: Callable | None = None,
        authority_deriver: Callable | None = None,
        p9_evidence_selector: Callable | None = None,
        p9_proposal_adapter: Callable | None = None,
        p9_evidence_builder: Callable | None = None,
        p9_source_evidence_builder: Callable | None = None,
        p9_review_input_projector: Callable | None = None,
        p9_proposal_projector: Callable | None = None,
        p9_semantic_consensus_loader: Callable | None = None,
        p4_evidence_selector: Callable | None = None,
        p4_evidence_builder: Callable | None = None,
        initial_review_assembler: Callable | None = None,
    ) -> None:
        if not callable(clock):
            raise ReviewValidationError("clock must be callable.")

        self.root = Path(root)
        self.repository_root = Path(repository_root)
        self._clock = clock
        self._workspace = (
            ProjectWorkspace(root=self.root)
            if workspace is None
            else workspace
        )
        self._source_registry = (
            ProjectSourceRegistry(root=self.root)
            if source_registry is None
            else source_registry
        )
        self._processing_summary_service = (
            ProjectProcessingSummaryService(
                root=self.root,
                source_registry=self._source_registry,
            )
            if processing_summary_service is None
            else processing_summary_service
        )
        self._processing_repository = (
            ProjectProcessingRepository(root=self.root)
            if processing_repository is None
            else processing_repository
        )
        self._review_repository = (
            ReviewWorkspaceRepository(root=self.root)
            if review_repository is None
            else review_repository
        )
        self._human_review_repository = (
            HumanReviewRepository(root=self.root)
            if human_review_repository is None
            else human_review_repository
        )
        self._information_unit_repository = (
            InformationUnitRepository(root=self.root)
            if information_unit_repository is None
            else information_unit_repository
        )
        self._terminology_mapping_repository = (
            TerminologyMappingRepository(root=self.root)
            if terminology_mapping_repository is None
            else terminology_mapping_repository
        )
        self._framework_assignment_repository = (
            FrameworkAssignmentRepository(root=self.root)
            if framework_assignment_repository is None
            else framework_assignment_repository
        )

        # Keep the package dependency one-way during import. approved_input
        # itself imports review_workspace contracts, so these imports are
        # deliberately deferred until service construction.
        if approved_input_repository is None:
            from modules.approved_input.repository import ApprovedInputRepository

            approved_input_repository = ApprovedInputRepository(root=self.root)
        self._approved_input_repository = approved_input_repository

        if promotion_service is None:
            from modules.approved_input.promotion_service import (
                ApprovedInputPromotionService,
            )

            promotion_service = ApprovedInputPromotionService(
                root=self.root,
                review_repository=self._review_repository,
                source_registry=self._source_registry,
                processing_repository=self._processing_repository,
                human_review_repository=self._human_review_repository,
                approved_input_repository=self._approved_input_repository,
            )
        self._promotion_service = promotion_service

        if authority_deriver is None:
            from modules.approved_input.lifecycle import (
                derive_approved_input_authority_states,
            )

            authority_deriver = derive_approved_input_authority_states

        self._source_summary_deriver = (
            derive_source_processing_summaries
            if source_summary_deriver is None
            else source_summary_deriver
        )
        self._run_state_deriver = (
            derive_processing_run_state
            if run_state_deriver is None
            else run_state_deriver
        )
        self._finalization_assessor = (
            assess_review_document_finalization
            if finalization_assessor is None
            else finalization_assessor
        )
        self._authority_deriver = authority_deriver
        self._p9_evidence_selector = (
            select_p9_review_evidence_set
            if p9_evidence_selector is None
            else p9_evidence_selector
        )
        self._p9_proposal_adapter = (
            adapt_p9_agent_proposals_for_review
            if p9_proposal_adapter is None
            else p9_proposal_adapter
        )
        self._p9_evidence_builder = (
            construct_p9_evidence_references
            if p9_evidence_builder is None
            else p9_evidence_builder
        )
        self._p9_source_evidence_builder = (
            construct_p9_source_evidence_references
            if p9_source_evidence_builder is None
            else p9_source_evidence_builder
        )
        self._p9_review_input_projector = (
            project_p9_review_inputs_to_semantic_subjects
            if p9_review_input_projector is None
            else p9_review_input_projector
        )
        self._p9_proposal_projector = (
            project_p9_proposals_to_semantic_subjects
            if p9_proposal_projector is None
            else p9_proposal_projector
        )
        self._p9_semantic_consensus_loader = (
            load_semantic_review_consensus_evidence_facts
            if p9_semantic_consensus_loader is None
            else p9_semantic_consensus_loader
        )
        self._p4_evidence_selector = (
            select_p4_review_evidence_set
            if p4_evidence_selector is None
            else p4_evidence_selector
        )
        self._p4_evidence_builder = (
            construct_p4_evidence_references
            if p4_evidence_builder is None
            else p4_evidence_builder
        )
        self._initial_review_assembler = (
            assemble_initial_review_document
            if initial_review_assembler is None
            else initial_review_assembler
        )

    def open_or_create_review(
        self,
        project_id: str,
        processing_run_id: str,
        *,
        opened_by: str,
    ) -> ReviewApprovalWorkspaceOpenResult:
        """Open one existing workspace or atomically create its initial state."""

        self._require_project(project_id)
        reviewer_identity = self._reviewer_identity(opened_by)

        existing = self._documents_for_run(
            project_id,
            processing_run_id,
        )
        if len(existing) > 1:
            raise ReviewIntegrityError(
                "Multiple Review Documents reference the selected "
                "Processing Run. Initial Review creation is blocked."
            )
        if len(existing) == 1:
            return ReviewApprovalWorkspaceOpenResult(
                created=False,
                workspace=self.workspace_view(
                    project_id,
                    existing[0].review_document_id,
                ),
            )

        try:
            history = self._processing_repository.load_run(
                project_id,
                processing_run_id,
            )
            p9_evidence = self._p9_evidence_selector(
                history,
                repository_root=self.repository_root,
            )
            p9_proposals = self._p9_proposal_adapter(
                p9_evidence,
                repository_root=self.repository_root,
            )
            source_only_evidence = (
                self._p9_source_evidence_builder(
                    p9_evidence,
                    p9_proposals,
                    repository_root=self.repository_root,
                )
            )
            semantic_projection = (
                self._p9_review_input_projector(
                    p9_evidence,
                    p9_proposals,
                    source_only_evidence,
                    repository_root=self.repository_root,
                )
            )

            if semantic_projection.used_semantic_projection:
                p9_proposals = semantic_projection.proposals
                p9_structured_evidence = semantic_projection.evidence
            else:
                # Legacy runs without D4 semantic synthesis retain the
                # existing source-wide Derivation Consensus contract.
                p9_structured_evidence = self._p9_evidence_builder(
                    p9_evidence,
                    p9_proposals,
                    repository_root=self.repository_root,
                )

            p4_human_scan = self._p4_human_review_scan(
                self._human_review_repository.scan_decisions(
                    project_id
                )
            )
            p4_evidence = self._p4_evidence_selector(
                p9_evidence,
                information_unit_scan=(
                    self._information_unit_repository
                    .scan_information_units(project_id)
                ),
                terminology_mapping_scan=(
                    self._terminology_mapping_repository
                    .scan_candidates(project_id)
                ),
                framework_assignment_scan=(
                    self._framework_assignment_repository
                    .scan_candidates(project_id)
                ),
                human_review_scan=p4_human_scan,
            )
            p4_evidence_references = self._p4_evidence_builder(
                p4_evidence,
                repository_root=self.repository_root,
            )

            review_document_id = (
                self._review_repository.next_document_id(
                    project_id
                )
            )
            review_document_version_id = (
                format_review_document_version_id(1)
            )
            review_revision_id = format_review_revision_id(1)
            timestamp = self._timestamp()

            occupied_review_item_ids = (
                self._occupied_review_item_ids(project_id)
            )

            assembly = self._initial_review_assembler(
                p9_review_evidence=p9_evidence,
                p9_structured_proposals=p9_proposals,
                p9_structured_evidence=p9_structured_evidence,
                p4_review_evidence=p4_evidence,
                p4_evidence_references=p4_evidence_references,
                review_document_id=review_document_id,
                review_document_version_id=(
                    review_document_version_id
                ),
                review_revision_id=review_revision_id,
                opened_by=reviewer_identity,
                timestamp=timestamp,
                occupied_review_item_ids=(
                    occupied_review_item_ids
                ),
            )
        except (ReviewIntegrityError, ReviewReferenceError, ReviewValidationError):
            raise
        except Exception as exc:
            raise ReviewReferenceError(
                "The exact P4/P9 evidence required for initial "
                "Human Review Workspace creation is unavailable."
            ) from exc

        if not assembly.eligibility.eligible_for_workspace_creation:
            raise ReviewIntegrityError(
                "The assembled Review Document is not eligible "
                "for workspace creation."
            )

        # Recheck the run-to-document cardinality immediately before the
        # repository write. Equivalent retries open the existing workspace.
        existing = self._documents_for_run(
            project_id,
            processing_run_id,
        )
        if len(existing) > 1:
            raise ReviewIntegrityError(
                "Multiple Review Documents reference the selected "
                "Processing Run. Initial Review creation is blocked."
            )
        if len(existing) == 1:
            return ReviewApprovalWorkspaceOpenResult(
                created=False,
                workspace=self.workspace_view(
                    project_id,
                    existing[0].review_document_id,
                ),
            )

        current_occupied_review_item_ids = (
            self._occupied_review_item_ids(project_id)
        )
        if (
            current_occupied_review_item_ids
            != occupied_review_item_ids
        ):
            raise ReviewIntegrityError(
                "Project-wide Review Item identity allocation changed "
                "during initial workspace creation. Retry is required."
            )

        try:
            self._review_repository.create_document_workspace(
                *assembly.repository_bundle
            )
        except ReviewWorkspaceError:
            raise
        except Exception as exc:
            raise ReviewReferenceError(
                "Initial Human Review Workspace persistence did not "
                "complete. No successful workspace state was inferred."
            ) from exc

        return ReviewApprovalWorkspaceOpenResult(
            created=True,
            workspace=self.workspace_view(
                project_id,
                review_document_id,
                review_document_version_id,
            ),
        )






    def promotion_preview(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ):
        """Return a fresh G5 eligibility assessment for exact finalized authority."""

        version = self._review_repository.load_version(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if version.version_state != "finalized":
            raise ReviewValidationError(
                "Approved Input promotion requires a finalized "
                "Review Document Version."
            )

        assessment = self._promotion_service.assess_eligibility(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if (
            assessment.project_id != project_id
            or assessment.review_document_id != review_document_id
            or assessment.review_document_version_id
            != review_document_version_id
            or assessment.review_revision_id
            != version.finalized_revision_id
        ):
            raise ReviewIntegrityError(
                "Promotion eligibility does not bind the exact selected "
                "finalized Review authority."
            )

        return assessment

    def approved_input_traceability(
        self,
        project_id: str,
        review_document_id: str,
    ) -> tuple[ReviewApprovedInputTrace, ...]:
        """Derive complete AIN authority exclusively from manifests and events."""

        self._review_repository.load_document(
            project_id,
            review_document_id,
        )

        scan = self._approved_input_repository.scan_project(
            project_id
        )

        if scan.issues:
            raise ReviewIntegrityError(
                "Approved Input traceability is blocked by repository "
                "integrity or recovery issues."
            )

        authority = tuple(
            self._authority_deriver(
                scan.manifests,
                scan.events,
            )
        )

        events_by_id = defaultdict(list)

        for event in scan.events:
            events_by_id[event.approved_input_id].append(
                ReviewApprovedInputEventTrace(
                    approved_input_event_id=(
                        event.approved_input_event_id
                    ),
                    approved_input_id=event.approved_input_id,
                    event_type=event.event_type,
                    previous_authority_state=(
                        event.previous_authority_state
                    ),
                    next_authority_state=(
                        event.next_authority_state
                    ),
                    reason_code=event.reason_code,
                    rationale=event.rationale,
                    actor_identity=event.actor_identity,
                    successor_approved_input_id=(
                        event.successor_approved_input_id
                    ),
                    causal_review_document_id=(
                        event.causal_review_document_id
                    ),
                    causal_review_document_version_id=(
                        event.causal_review_document_version_id
                    ),
                    causal_review_revision_id=(
                        event.causal_review_revision_id
                    ),
                    causal_finalization_decision_id=(
                        event.causal_finalization_decision_id
                    ),
                    causal_finalization_decision_fingerprint=(
                        event.causal_finalization_decision_fingerprint
                    ),
                    occurred_at=event.occurred_at,
                    previous_event_fingerprint=(
                        event.previous_event_fingerprint
                    ),
                    event_fingerprint=event.event_fingerprint,
                )
            )

        result = []

        for snapshot in authority:
            manifest = snapshot.manifest

            if manifest.review_document_id != review_document_id:
                continue

            result.append(
                ReviewApprovedInputTrace(
                    approved_input_id=manifest.approved_input_id,
                    authority_state=snapshot.authority_state,
                    approved_input_kind=manifest.approved_input_kind,
                    stable_subject_key=manifest.stable_subject_key,
                    canonical_title=(
                        manifest.canonical_content.title
                    ),
                    canonical_primary_text=(
                        manifest.canonical_content.primary_text
                    ),
                    review_document_id=manifest.review_document_id,
                    review_document_version_id=(
                        manifest.review_document_version_id
                    ),
                    review_revision_id=manifest.review_revision_id,
                    review_item_id=manifest.review_item_id,
                    review_item_kind=manifest.review_item_kind,
                    review_item_fingerprint=(
                        manifest.review_item_fingerprint
                    ),
                    finalized_artifact_set_fingerprint=(
                        manifest.finalized_artifact_set_fingerprint
                    ),
                    finalization_decision_id=(
                        manifest.finalization_decision_id
                    ),
                    finalization_decision_fingerprint=(
                        manifest.finalization_decision_fingerprint
                    ),
                    finalization_validation_fingerprint=(
                        manifest.finalization_validation_fingerprint
                    ),
                    source_id=manifest.source_id,
                    source_sha256=manifest.source_sha256,
                    processing_run_id=manifest.processing_run_id,
                    attempt_id=manifest.attempt_id,
                    primary_artifact_id=(
                        manifest.primary_artifact_reference.artifact_id
                    ),
                    supporting_artifact_ids=tuple(
                        reference.artifact_id
                        for reference
                        in manifest.supporting_artifact_references
                    ),
                    proposal_references=manifest.proposal_references,
                    created_at=manifest.created_at,
                    manifest_content_fingerprint=(
                        manifest.content_fingerprint
                    ),
                    latest_event_fingerprint=(
                        snapshot.latest_event_fingerprint
                    ),
                    lifecycle_events=tuple(
                        events_by_id.get(
                            manifest.approved_input_id,
                            (),
                        )
                    ),
                )
            )

        return tuple(
            sorted(
                result,
                key=lambda item: item.approved_input_id,
            )
        )

    def promote_review_version(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ReviewApprovalPromotionResult:
        """Promote exact finalized authority through the existing G5 service."""

        assessment = self.promotion_preview(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if not assessment.eligible_for_promotion:
            from modules.approved_input.errors import (
                ApprovedInputPromotionBlockedError,
            )

            raise ApprovedInputPromotionBlockedError(
                "Approved Input promotion is blocked by the current "
                "eligibility assessment."
            )

        promotion = self._promotion_service.promote_finalized_version(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if (
            promotion.project_id != project_id
            or promotion.review_document_id != review_document_id
            or promotion.review_document_version_id
            != review_document_version_id
            or promotion.finalized_artifact_set_fingerprint
            != assessment.finalized_artifact_set_fingerprint
        ):
            raise ReviewIntegrityError(
                "Approved Input promotion result does not bind the exact "
                "preflight authority snapshot."
            )

        workspace = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        traceability = self.approved_input_traceability(
            project_id,
            review_document_id,
        )

        trace_ids = {
            item.approved_input_id
            for item in traceability
        }
        result_ids = {
            *promotion.created_approved_input_ids,
            *promotion.reused_approved_input_ids,
        }

        if not result_ids.issubset(trace_ids):
            raise ReviewIntegrityError(
                "Promoted Approved Inputs are missing from reloaded "
                "manifest/event authority."
            )

        trace_event_ids = {
            event.approved_input_event_id
            for item in traceability
            for event in item.lifecycle_events
        }

        if not set(
            promotion.lifecycle_event_ids
        ).issubset(trace_event_ids):
            raise ReviewIntegrityError(
                "Promotion lifecycle events are missing from reloaded "
                "Approved Input authority."
            )

        active_from_trace = tuple(
            item.approved_input_id
            for item in traceability
            if item.is_active
        )
        active_from_repository = tuple(
            manifest.approved_input_id
            for manifest
            in self._approved_input_repository
            .list_active_approved_inputs(project_id)
            if manifest.review_document_id == review_document_id
        )

        if active_from_trace != active_from_repository:
            raise ReviewIntegrityError(
                "G6 authority projection differs from the stable Phase H "
                "Approved Input read contract."
            )

        return ReviewApprovalPromotionResult(
            workspace=workspace,
            promotion=promotion,
            traceability=traceability,
        )

    def reopen_review_version(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        *,
        reopen_reason: str,
        actor_identity: str,
    ):
        """Create one documented draft successor of an exact finalized version."""

        predecessor = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if predecessor.version.version_state != "finalized":
            raise ReviewFinalizationBlockedError(
                "Only a finalized Review Document Version can be reopened."
            )

        reviewer = self._reviewer_identity(
            actor_identity
        )

        if not isinstance(reopen_reason, str):
            raise ReviewValidationError(
                "reopen_reason must be a string."
            )

        reason = reopen_reason.strip()

        if (
            not reason
            or reason != reopen_reason
        ):
            raise ReviewValidationError(
                "reopen_reason must be non-empty and must not contain "
                "surrounding whitespace."
            )

        bundle = self._review_repository.reopen_finalized_version(
            project_id,
            review_document_id,
            review_document_version_id,
            reopen_reason=reason,
            opened_by=reviewer,
            timestamp=self._timestamp(),
        )

        if (
            bundle.predecessor_version_id
            != review_document_version_id
            or bundle.version.predecessor_version_id
            != review_document_version_id
            or bundle.version.version_state != "draft"
            or bundle.initial_revision.review_revision_id
            != bundle.version.head_revision_id
        ):
            raise ReviewIntegrityError(
                "Reopened Review Version does not preserve the exact "
                "predecessor and initial-draft bindings."
            )

        reloaded = self.workspace_view(
            project_id,
            review_document_id,
            bundle.version.review_document_version_id,
        )

        if (
            reloaded.version.review_document_version_id
            != bundle.version.review_document_version_id
            or reloaded.version.version_state != "draft"
            or reloaded.version.predecessor_version_id
            != review_document_version_id
            or reloaded.revision.review_revision_id
            != bundle.initial_revision.review_revision_id
        ):
            raise ReviewIntegrityError(
                "Reloaded reopened Review Workspace differs from the "
                "persisted reopening result."
            )

        return bundle

    def finalized_artifact_set(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ):
        """Load the exact persisted finalized three-artifact authority set."""

        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if view.version.version_state != "finalized":
            raise ReviewFinalizationBlockedError(
                "Finalized Review artifacts are available only for a "
                "finalized Review Document Version."
            )

        artifact_set = (
            self._review_repository.load_finalized_artifact_set(
                project_id,
                review_document_id,
                review_document_version_id,
            )
        )

        reviewed_document = artifact_set.reviewed_document

        if (
            reviewed_document.project_id != project_id
            or reviewed_document.review_document_id
            != review_document_id
            or reviewed_document.review_document_version_id
            != review_document_version_id
            or reviewed_document.review_revision_id
            != view.revision.review_revision_id
        ):
            raise ReviewIntegrityError(
                "Finalized Review Artifact Set does not bind the exact "
                "selected finalized Review authority."
            )

        return artifact_set

    def finalization_preview(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ReviewFinalizationWorkflowPreview:
        """Return one fresh G6 finalization assessment and exact HRD state."""

        _, preview = self._finalization_context(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        return preview

    def record_finalization_decision(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        *,
        decision: str,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Persist one detailed HRD against the exact fresh finalization target."""

        if decision not in HUMAN_REVIEW_DECISIONS:
            raise ReviewValidationError(
                "Unsupported Human Review Decision."
            )

        view, preview = self._finalization_context(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if (
            decision == "confirm"
            and not preview.eligible_for_confirmation
        ):
            raise ReviewFinalizationBlockedError(
                "Review Document finalization cannot be confirmed while "
                "blocking finalization findings exist."
            )

        target = create_review_document_finalization_target(
            preview.assessment
        )

        return self._human_review_repository.record_decision(
            project_id,
            target,
            review_mode="detailed_review",
            decision=decision,
            reviewer_identity=self._reviewer_identity(
                reviewer_identity
            ),
            rationale=rationale,
        )

    def finalize_review_version(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ReviewApprovalFinalizationResult:
        """Finalize one exact confirmed draft and publish the artifact set."""

        view, preview = self._finalization_context(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if not preview.can_finalize:
            raise ReviewFinalizationBlockedError(
                "Review Document Version finalization requires one exact "
                "current detailed confirmation and no blocking findings."
            )

        authorized = (
            authorize_persisted_review_document_finalization(
                view.version,
                view.revision,
                preview.assessment,
                self._human_review_repository,
                timestamp=self._timestamp(),
            )
        )

        artifact_set = build_finalized_review_artifact_set(
            view.document,
            view.revision,
            authorized,
        )

        persisted_version = (
            self._review_repository.persist_authorized_finalization(
                authorized
            )
        )

        if persisted_version != authorized.finalized_version:
            raise ReviewIntegrityError(
                "Persisted finalized Review Version differs from the "
                "exact authorized transition."
            )

        persisted_artifact_set = (
            self._review_repository.persist_finalized_artifact_set(
                artifact_set
            )
        )

        if persisted_artifact_set != artifact_set:
            raise ReviewIntegrityError(
                "Persisted Finalized Review Artifact Set differs from "
                "the validated in-memory artifact set."
            )

        reloaded = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if (
            reloaded.version.version_state != "finalized"
            or reloaded.version.finalized_revision_id
            != view.revision.review_revision_id
        ):
            raise ReviewIntegrityError(
                "Reloaded Review Workspace does not expose the exact "
                "finalized Review Revision."
            )

        return ReviewApprovalFinalizationResult(
            workspace=reloaded,
            preview=preview,
            authorization=authorized.authorization,
            artifact_set=persisted_artifact_set,
        )

    def review_filter_facts(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> tuple[ReviewItemFilterFact, ...]:
        """Return exact current facts for every ADR-required G6 filter."""

        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        needs_p9 = any(
            item.proposal_references
            or item.consensus_evidence_references
            for item in view.revision.review_items
        )

        proposals = None
        consensus_by_key = {}

        if needs_p9:
            try:
                history = self._processing_repository.load_run(
                    project_id,
                    view.document.processing_run_id,
                )
                evidence = self._p9_evidence_selector(
                    history,
                    repository_root=self.repository_root,
                )
                raw_proposals = self._p9_proposal_adapter(
                    evidence,
                    repository_root=self.repository_root,
                )
                proposals = self._p9_proposal_projector(
                    evidence,
                    raw_proposals,
                    repository_root=self.repository_root,
                )
                semantic_consensus_facts = (
                    self._p9_semantic_consensus_loader(
                        evidence,
                        raw_proposals,
                        repository_root=self.repository_root,
                    )
                )

                uses_cross_unit_semantic_subjects = any(
                    proposal.stable_subject_key.startswith(
                        (
                            "semantic:element:ses-",
                            "semantic:relationship:srs-",
                        )
                    )
                    for proposal in (
                        *proposals.element_proposals,
                        *proposals.relationship_proposals,
                    )
                )

                if uses_cross_unit_semantic_subjects:
                    # D4 synthesized subjects are the Review authority.
                    # Their exact consensus/evidence facts come from the
                    # cross-unit semantic synthesis artifact. Reconstructing
                    # legacy source-wide P9 consensus here would reintroduce
                    # the pre-SAU single-consensus contract.
                    consensus_facts = semantic_consensus_facts
                else:
                    # Historical/legacy runs without D4 synthesis retain the
                    # original P9 consensus reconstruction path.
                    consensus_facts = load_p9_consensus_evidence_facts(
                        evidence,
                        raw_proposals,
                        repository_root=self.repository_root,
                    )
                consensus_by_key = {
                    (
                        fact.artifact_id,
                        fact.evidence_locator,
                        fact.evidence_content_fingerprint,
                    ): fact
                    for fact in consensus_facts
                }
            except ReviewWorkspaceError:
                raise
            except Exception as exc:
                raise ReviewReferenceError(
                    "Exact P9 filter evidence could not be reconstructed."
                ) from exc

        facts = []

        for item in view.revision.review_items:
            details = (
                ()
                if not item.proposal_references
                else build_review_proposal_details(
                    item,
                    proposals,
                )
            )

            item_consensus = []
            for reference in item.consensus_evidence_references:
                key = (
                    reference.artifact_reference.artifact_id,
                    reference.evidence_locator,
                    reference.evidence_content_fingerprint,
                )
                fact = consensus_by_key.get(key)
                if fact is None:
                    raise ReviewIntegrityError(
                        "Review Item Consensus Evidence cannot be mapped "
                        "to the exact P9 Consensus artifact."
                    )
                item_consensus.append(
                    ReviewConsensusFilterFact(
                        artifact_id=fact.artifact_id,
                        evidence_locator=fact.evidence_locator,
                        evidence_content_fingerprint=(
                            fact.evidence_content_fingerprint
                        ),
                        agreement_level=fact.agreement_level,
                        review_required=fact.review_required,
                    )
                )

            facts.append(
                build_review_item_filter_fact(
                    item,
                    proposal_details=details,
                    source_id=view.document.source_id,
                    consensus_facts=tuple(
                        item_consensus
                    ),
                )
            )

        return tuple(facts)

    def preview_scoped_action(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        *,
        request: ScopedReviewActionRequest,
    ) -> ScopedReviewActionImpactPreview:
        """Return the exact current materialization and precedence impact."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        facts = self.review_filter_facts(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        return preview_scoped_review_action(
            view.revision,
            facts,
            request,
        )

    def apply_scoped_action(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        *,
        request: ScopedReviewActionRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Persist one immutable SRA and its effective successor Revision."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if (
            view.revision.review_revision_id
            != request.expected_revision_id
        ):
            raise ReviewIntegrityError(
                "The Review Workspace changed after impact preview."
            )

        facts = self.review_filter_facts(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        action_id = (
            self._review_repository.next_scoped_action_id(
                project_id,
                review_document_id,
                review_document_version_id,
            )
        )
        revision_id = (
            self._review_repository.next_revision_id(
                project_id,
                review_document_id,
                review_document_version_id,
            )
        )

        mutation = create_scoped_review_action_mutation(
            view.revision,
            facts=facts,
            request=request,
            scoped_review_action_id=action_id,
            new_review_revision_id=revision_id,
            actor_identity=actor_identity,
            timestamp=self._timestamp(),
        )

        self._review_repository.persist_scoped_action(
            mutation.action
        )
        self._review_repository.append_revision(
            mutation.revision
        )

        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )


    def relationship_resolution_candidates(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
    ):
        """Return exact existing element candidates for one unresolved relationship."""

        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        item = self._review_item_from_view(
            view,
            review_item_id,
        )
        if item.review_item_kind != "open_question":
            return ()

        try:
            history = self._processing_repository.load_run(
                project_id,
                view.document.processing_run_id,
            )
            evidence = self._p9_evidence_selector(
                history,
                repository_root=self.repository_root,
            )
            proposals = self._p9_proposal_adapter(
                evidence,
                repository_root=self.repository_root,
            )
        except ReviewWorkspaceError:
            raise
        except Exception as exc:
            raise ReviewReferenceError(
                "Exact P9 uncertainty evidence could not be reconstructed "
                "for relationship resolution."
            ) from exc

        questions = tuple(
            question
            for question in getattr(
                proposals,
                "review_question_proposals",
                (),
            )
            if (
                question.stable_subject_key
                == item.stable_subject_key
                and question.issue_code
                == "unresolved_relationship_endpoint"
            )
        )
        if not questions:
            return ()

        projections = tuple(
            project_relationship_resolution_candidates(
                question,
                view.revision.review_items,
            )
            for question in sorted(
                questions,
                key=lambda value: (
                    value.artifact_reference.artifact_id,
                    value.evidence_locator,
                    value.question_id,
                ),
            )
        )

        identities = {
            (
                projection.source_endpoint.strip().casefold(),
                projection.target_endpoint.strip().casefold(),
                projection.semantic_intent.strip().casefold(),
            )
            for projection in projections
        }
        if len(identities) != 1:
            raise ReviewIntegrityError(
                "One Open Question maps to conflicting unresolved "
                "relationship identities."
            )

        return projections

    def create_element_from_open_question(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        request: CreateElementFromOpenQuestionRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Persist one explicit Human-created element from exact question evidence."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        reviewer = self._reviewer_identity(actor_identity)
        occupied, allocated = self._allocate_project_review_item_ids(
            project_id,
            1,
        )

        revision = create_element_from_open_question_revision(
            view.revision,
            open_question_item_id=review_item_id,
            request=request,
            new_review_item_id=allocated[0],
            new_review_revision_id=(
                self._review_repository.next_revision_id(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            ),
            actor_identity=reviewer,
            timestamp=self._timestamp(),
        )
        self._assert_project_review_item_allocation_unchanged(
            project_id,
            occupied,
        )
        self._review_repository.append_revision(revision)
        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def resolve_relationship_open_question(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        request: ResolveRelationshipEndpointsRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Persist explicit Human endpoint binding as a new relationship Review Item."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        reviewer = self._reviewer_identity(actor_identity)
        occupied, allocated = self._allocate_project_review_item_ids(
            project_id,
            1,
        )

        revision = create_relationship_endpoint_resolution_revision(
            view.revision,
            open_question_item_id=review_item_id,
            request=request,
            new_relationship_review_item_id=allocated[0],
            new_review_revision_id=(
                self._review_repository.next_revision_id(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            ),
            actor_identity=reviewer,
            timestamp=self._timestamp(),
        )
        self._assert_project_review_item_allocation_unchanged(
            project_id,
            occupied,
        )
        self._review_repository.append_revision(revision)
        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def proposal_details(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
    ) -> tuple[ReviewProposalDetail, ...]:
        """Return exact P9 proposal content for one current Review Item."""

        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        item = self._review_item_from_view(
            view,
            review_item_id,
        )

        if not item.proposal_references:
            return ()

        try:
            history = self._processing_repository.load_run(
                project_id,
                view.document.processing_run_id,
            )
            evidence = self._p9_evidence_selector(
                history,
                repository_root=self.repository_root,
            )
            raw_proposals = self._p9_proposal_adapter(
                evidence,
                repository_root=self.repository_root,
            )
            proposals = self._p9_proposal_projector(
                evidence,
                raw_proposals,
                repository_root=self.repository_root,
            )
            return build_review_proposal_details(
                item,
                proposals,
            )
        except ReviewWorkspaceError:
            raise
        except Exception as exc:
            raise ReviewReferenceError(
                "Exact Agent proposal content could not be reconstructed "
                "from the selected Review Document evidence."
            ) from exc

    def accept_proposal(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        request: ReviewProposalActionRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Accept one exact Agent proposal in a new immutable Revision."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        details = self.proposal_details(
            project_id,
            review_document_id,
            review_document_version_id,
            review_item_id,
        )
        matches = tuple(
            detail
            for detail in details
            if detail.proposal_key == request.proposal_key
        )
        if len(matches) != 1:
            raise ReviewReferenceError(
                "The selected Agent proposal is unavailable."
            )

        revision = create_proposal_accept_revision(
            view.revision,
            review_item_id=review_item_id,
            detail=matches[0],
            request=request,
            new_review_revision_id=(
                self._review_repository.next_revision_id(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            ),
            actor_identity=actor_identity,
            timestamp=self._timestamp(),
        )
        self._review_repository.append_revision(
            revision
        )
        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def reject_proposal(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        request: ReviewProposalActionRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Reject one Agent proposal without rejecting the complete item."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        revision = create_proposal_reject_revision(
            view.revision,
            review_item_id=review_item_id,
            request=request,
            new_review_revision_id=(
                self._review_repository.next_revision_id(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            ),
            actor_identity=actor_identity,
            timestamp=self._timestamp(),
        )
        self._review_repository.append_revision(
            revision
        )
        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def split_review_item(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        request: ReviewSplitRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Split one Review Item into explicit lineage-preserving children."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        occupied, allocated = (
            self._allocate_project_review_item_ids(
                project_id,
                len(request.children),
            )
        )
        revision = create_split_revision(
            view.revision,
            review_item_id=review_item_id,
            request=request,
            new_review_item_ids=allocated,
            new_review_revision_id=(
                self._review_repository.next_revision_id(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            ),
            actor_identity=actor_identity,
            timestamp=self._timestamp(),
        )
        self._assert_project_review_item_allocation_unchanged(
            project_id,
            occupied,
        )
        self._review_repository.append_revision(
            revision
        )
        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def merge_review_items(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        *,
        request: ReviewMergeRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Merge explicit Review Items into one new lineage identity."""

        view = self._draft_workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        occupied, allocated = (
            self._allocate_project_review_item_ids(
                project_id,
                1,
            )
        )
        revision = create_merge_revision(
            view.revision,
            request=request,
            new_review_item_id=allocated[0],
            new_review_revision_id=(
                self._review_repository.next_revision_id(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            ),
            actor_identity=actor_identity,
            timestamp=self._timestamp(),
        )
        self._assert_project_review_item_allocation_unchanged(
            project_id,
            occupied,
        )
        self._review_repository.append_revision(
            revision
        )
        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def save_item_review(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        request: ReviewItemEditRequest,
        actor_identity: str,
    ) -> ReviewApprovalWorkspaceView:
        """Persist one item edit as the next immutable Review Revision."""

        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if view.version.version_state != "draft":
            raise ReviewIntegrityError(
                "Item-level Review edits are allowed only on a draft "
                "Review Document Version."
            )

        if (
            view.revision.review_revision_id
            != request.expected_revision_id
        ):
            raise ReviewIntegrityError(
                "The Review Workspace changed after the item edit was opened."
            )

        new_revision_id = (
            self._review_repository.next_revision_id(
                project_id,
                review_document_id,
                review_document_version_id,
            )
        )

        revision = create_item_edit_revision(
            view.revision,
            review_item_id=review_item_id,
            request=request,
            new_review_revision_id=new_revision_id,
            actor_identity=actor_identity,
            timestamp=self._timestamp(),
        )

        try:
            self._review_repository.append_revision(
                revision
            )
        except ReviewWorkspaceError:
            raise
        except Exception as exc:
            raise ReviewReferenceError(
                "The item-level Review Revision could not be persisted. "
                "No successful edit state was inferred."
            ) from exc

        return self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

    def project_view(self, project_id: str) -> ReviewApprovalProjectView:
        """Return the deterministic Human Review work queue."""

        self._require_project(project_id)
        try:
            source_scan, processing_scan = (
                self._processing_summary_service.collect_scans(project_id)
            )
            source_summaries = self._source_summary_deriver(
                project_id,
                source_scan,
                processing_scan,
            )
            review_scan = self._review_repository.scan_project(project_id)
            human_scan = self._human_review_repository.scan_decisions(project_id)
            approved_scan = self._approved_input_repository.scan_project(project_id)
        except Exception as exc:
            raise ReviewReferenceError(
                "The Human Review and Approval read model could not load all "
                "required project-local authority stores."
            ) from exc

        issues = list(
            self._collect_scan_issues(
                project_id,
                source_scan,
                processing_scan,
                review_scan,
                human_scan,
                approved_scan,
            )
        )
        authority = self._derive_authority(project_id, approved_scan, issues)

        sources_by_id = {
            item.source_id: item for item in source_scan.valid_sources
        }
        histories_by_id = {
            item.manifest.processing_run_id: item
            for item in processing_scan.run_histories
        }
        summaries_by_run_id = {
            item.current_processing_run_id: item
            for item in source_summaries
            if item.current_processing_run_id is not None
        }
        documents_by_run_id: dict[str, list] = defaultdict(list)
        for document in review_scan.documents:
            documents_by_run_id[document.processing_run_id].append(document)

        relevant_run_ids = {
            item.current_processing_run_id
            for item in source_summaries
            if item.current_processing_run_id is not None and item.pending_review
        }
        relevant_run_ids.update(documents_by_run_id)

        items = []
        for run_id in sorted(relevant_run_ids):
            item, new_issues = self._queue_item(
                project_id=project_id,
                processing_run_id=run_id,
                sources_by_id=sources_by_id,
                histories_by_id=histories_by_id,
                summaries_by_run_id=summaries_by_run_id,
                review_scan=review_scan,
                documents=tuple(
                    sorted(
                        documents_by_run_id.get(run_id, ()),
                        key=lambda value: value.review_document_id,
                    )
                ),
                authority=authority,
                project_issues=tuple(issues),
            )
            issues.extend(new_issues)
            items.append(item)

        issues_tuple = self._sorted_unique_issues(issues)
        items_tuple = tuple(
            self._with_effective_issue_state(item, issues_tuple)
            for item in sorted(
                items,
                key=lambda value: (value.source_id, value.processing_run_id),
            )
        )
        return ReviewApprovalProjectView(
            project_id=project_id,
            items=items_tuple,
            issues=issues_tuple,
        )

    def workspace_view(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str | None = None,
    ) -> ReviewApprovalWorkspaceView:
        """Return one exact Review Version and all read-side authority."""

        self._require_project(project_id)
        try:
            source_scan, processing_scan = (
                self._processing_summary_service.collect_scans(project_id)
            )
            review_scan = self._review_repository.scan_project(project_id)
            human_scan = self._human_review_repository.scan_decisions(project_id)
            approved_scan = self._approved_input_repository.scan_project(project_id)
            document = self._review_repository.load_document(
                project_id,
                review_document_id,
            )
        except Exception as exc:
            raise ReviewReferenceError(
                "The requested Human Review Workspace could not be loaded "
                "from the selected Project."
            ) from exc

        version = self._select_version(
            project_id,
            document.review_document_id,
            review_document_version_id,
            review_scan,
        )
        revision_id = (
            version.head_revision_id
            if version.version_state == "draft"
            else version.finalized_revision_id
        )
        if revision_id is None:
            raise ReviewIntegrityError(
                "The selected Review Version has no exact revision for its "
                "current state."
            )
        try:
            revision = self._review_repository.load_revision(
                project_id,
                document.review_document_id,
                version.review_document_version_id,
                revision_id,
            )
        except Exception as exc:
            raise ReviewReferenceError(
                "The exact Review Revision for the selected Review Version "
                "could not be loaded."
            ) from exc

        scoped_actions = tuple(
            sorted(
                (
                    item
                    for item in review_scan.scoped_actions
                    if item.review_document_id == document.review_document_id
                    and item.review_document_version_id
                    == version.review_document_version_id
                ),
                key=lambda item: item.scoped_review_action_id,
            )
        )

        issues = list(
            self._collect_scan_issues(
                project_id,
                source_scan,
                processing_scan,
                review_scan,
                human_scan,
                approved_scan,
            )
        )
        finalization_assessment = None
        promotion_assessment = None

        if version.version_state == "draft":
            try:
                finalization_assessment = self._finalization_assessor(
                    document,
                    version,
                    revision,
                )
            except Exception:
                issues.append(
                    self._workflow_issue(
                        project_id,
                        code="workflow.finalization_assessment_unavailable",
                        source_domain="review_workflow",
                        message=(
                            "Finalization assessment is unavailable for the "
                            "selected Review Version."
                        ),
                        review_document_id=document.review_document_id,
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                    )
                )
        elif version.version_state == "finalized":
            try:
                promotion_assessment = self._promotion_service.assess_eligibility(
                    project_id,
                    document.review_document_id,
                    version.review_document_version_id,
                )
            except Exception:
                issues.append(
                    self._workflow_issue(
                        project_id,
                        code="workflow.promotion_assessment_unavailable",
                        source_domain="approved_input",
                        message=(
                            "Promotion eligibility is unavailable for the "
                            "selected finalized Review Version."
                        ),
                        review_document_id=document.review_document_id,
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                    )
                )

        finalization_decisions = tuple(
            sorted(
                (
                    item
                    for item in human_scan.decisions
                    if item.target.target_type == "review_document_finalization"
                    and item.target.target_id
                    == version.review_document_version_id
                ),
                key=lambda item: item.human_review_decision_id,
            )
        )
        authority = self._derive_authority(project_id, approved_scan, issues)
        document_authority = tuple(
            item
            for item in authority
            if item.manifest.review_document_id == document.review_document_id
        )
        approved_ids = tuple(
            item.manifest.approved_input_id for item in document_authority
        )
        relevant_issues = tuple(
            item
            for item in self._sorted_unique_issues(issues)
            if self._issue_applies(
                item,
                source_id=document.source_id,
                processing_run_id=document.processing_run_id,
                review_document_id=document.review_document_id,
                review_document_version_id=version.review_document_version_id,
                approved_input_ids=approved_ids,
            )
        )

        return ReviewApprovalWorkspaceView(
            project_id=project_id,
            document=document,
            version=version,
            revision=revision,
            scoped_actions=scoped_actions,
            finalization_assessment=finalization_assessment,
            promotion_assessment=promotion_assessment,
            finalization_decisions=finalization_decisions,
            approved_input_authority=tuple(
                sorted(
                    document_authority,
                    key=lambda item: item.manifest.approved_input_id,
                )
            ),
            issues=relevant_issues,
        )

    def _queue_item(
        self,
        *,
        project_id,
        processing_run_id,
        sources_by_id,
        histories_by_id,
        summaries_by_run_id,
        review_scan,
        documents,
        authority,
        project_issues,
    ):
        new_issues = []
        history = histories_by_id.get(processing_run_id)
        summary = summaries_by_run_id.get(processing_run_id)
        derived_state = None
        if history is not None:
            try:
                derived_state = self._run_state_deriver(history)
            except Exception:
                new_issues.append(
                    self._workflow_issue(
                        project_id,
                        code="workflow.run_state_unavailable",
                        source_domain="processing",
                        message="Current Processing Run state could not be derived.",
                        source_id=history.manifest.source_id,
                        processing_run_id=processing_run_id,
                    )
                )

        source_id = (
            history.manifest.source_id
            if history is not None
            else (
                documents[0].source_id
                if len(documents) == 1
                else (summary.source_id if summary is not None else "unknown")
            )
        )
        source = sources_by_id.get(source_id)
        filename = source.original_filename if source is not None else source_id
        pending_review = bool(
            summary.pending_review
            if summary is not None
            else (
                derived_state.pending_review
                if derived_state is not None
                else False
            )
        )
        is_current = bool(
            summary is not None
            and summary.current_processing_run_id == processing_run_id
        )
        run_state = (
            derived_state.run_state
            if derived_state is not None
            else (summary.run_state if summary is not None else None)
        )
        attempt_id = (
            derived_state.latest_attempt_id
            if derived_state is not None
            else (
                summary.latest_attempt_id
                if summary is not None
                else (documents[0].attempt_id if len(documents) == 1 else None)
            )
        )
        document_ids = tuple(item.review_document_id for item in documents)

        if len(documents) > 1:
            new_issues.append(
                self._workflow_issue(
                    project_id,
                    code="workflow.multiple_review_documents_for_run",
                    source_domain="review_workspace",
                    message=(
                        "Multiple Review Documents reference the same Processing "
                        "Run. Review selection is blocked."
                    ),
                    source_id=source_id,
                    processing_run_id=processing_run_id,
                )
            )
            return (
                self._empty_queue_item(
                    project_id,
                    source_id,
                    filename,
                    processing_run_id,
                    attempt_id,
                    run_state,
                    pending_review,
                    is_current,
                    document_ids,
                    "attention_required",
                ),
                tuple(new_issues),
            )

        if not documents:
            return (
                self._empty_queue_item(
                    project_id,
                    source_id,
                    filename,
                    processing_run_id,
                    attempt_id,
                    run_state,
                    pending_review,
                    is_current,
                    (),
                    "awaiting_workspace",
                ),
                tuple(new_issues),
            )

        document = documents[0]
        versions = tuple(
            item
            for item in review_scan.versions
            if item.review_document_id == document.review_document_id
        )
        version, version_issue = self._latest_version_or_issue(
            project_id,
            document,
            versions,
        )
        if version_issue is not None:
            new_issues.append(version_issue)
            return (
                self._empty_queue_item(
                    project_id,
                    source_id,
                    filename,
                    processing_run_id,
                    attempt_id,
                    run_state,
                    pending_review,
                    is_current,
                    document_ids,
                    "attention_required",
                    review_document_id=document.review_document_id,
                ),
                tuple(new_issues),
            )

        revision_matches = tuple(
            item
            for item in review_scan.revisions
            if item.review_document_id == document.review_document_id
            and item.review_document_version_id
            == version.review_document_version_id
            and item.review_revision_id == version.head_revision_id
        )
        if len(revision_matches) != 1:
            new_issues.append(
                self._workflow_issue(
                    project_id,
                    code="workflow.head_revision_unavailable",
                    source_domain="review_workspace",
                    message=(
                        "The selected Review Version does not resolve to exactly "
                        "one current head revision."
                    ),
                    source_id=source_id,
                    processing_run_id=processing_run_id,
                    review_document_id=document.review_document_id,
                    review_document_version_id=version.review_document_version_id,
                )
            )
            return (
                self._empty_queue_item(
                    project_id,
                    source_id,
                    filename,
                    processing_run_id,
                    attempt_id,
                    run_state,
                    pending_review,
                    is_current,
                    document_ids,
                    "attention_required",
                    review_document_id=document.review_document_id,
                    review_document_version_id=version.review_document_version_id,
                    version_number=version.version_number,
                    version_state=version.version_state,
                    head_revision_id=version.head_revision_id,
                ),
                tuple(new_issues),
            )

        revision = revision_matches[0]
        outcome_counts = tuple(
            sorted(
                Counter(
                    item.effective_review_outcome
                    for item in revision.review_items
                ).items()
            )
        )
        finalization = None
        promotion = None
        status = "draft_review"

        if version.version_state == "draft":
            try:
                finalization = self._finalization_assessor(
                    document,
                    version,
                    revision,
                )
                if finalization.eligible_for_finalization:
                    status = "ready_to_finalize"
            except Exception:
                new_issues.append(
                    self._workflow_issue(
                        project_id,
                        code="workflow.finalization_assessment_unavailable",
                        source_domain="review_workflow",
                        message="Finalization assessment is unavailable.",
                        source_id=source_id,
                        processing_run_id=processing_run_id,
                        review_document_id=document.review_document_id,
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                    )
                )
                status = "attention_required"
        elif version.version_state == "finalized":
            try:
                promotion = self._promotion_service.assess_eligibility(
                    project_id,
                    document.review_document_id,
                    version.review_document_version_id,
                )
                status = (
                    "ready_to_promote"
                    if promotion.eligible_for_promotion
                    else "promotion_blocked"
                )
            except Exception:
                new_issues.append(
                    self._workflow_issue(
                        project_id,
                        code="workflow.promotion_assessment_unavailable",
                        source_domain="approved_input",
                        message="Promotion eligibility is unavailable.",
                        source_id=source_id,
                        processing_run_id=processing_run_id,
                        review_document_id=document.review_document_id,
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                    )
                )
                status = "attention_required"

        document_authority = tuple(
            item
            for item in authority
            if item.manifest.review_document_id == document.review_document_id
        )
        active_ids = tuple(
            sorted(
                item.manifest.approved_input_id
                for item in document_authority
                if item.authority_state == "active"
            )
        )
        inactive_ids = tuple(
            sorted(
                item.manifest.approved_input_id
                for item in document_authority
                if item.authority_state != "active"
            )
        )
        current_version_active = any(
            item.authority_state == "active"
            and item.manifest.review_document_version_id
            == version.review_document_version_id
            for item in document_authority
        )
        if (
            version.version_state == "finalized"
            and promotion is not None
            and promotion.eligible_for_promotion
            and current_version_active
        ):
            status = "approved_input_available"

        item = ReviewApprovalQueueItem(
            project_id=project_id,
            source_id=source_id,
            original_filename=filename,
            processing_run_id=processing_run_id,
            attempt_id=attempt_id,
            run_state=run_state,
            pending_review=pending_review,
            is_current_processing_run=is_current,
            review_document_ids=document_ids,
            review_document_id=document.review_document_id,
            review_document_version_id=version.review_document_version_id,
            version_number=version.version_number,
            version_state=version.version_state,
            head_revision_id=version.head_revision_id,
            review_item_count=len(revision.review_items),
            review_outcome_counts=outcome_counts,
            finalization_eligible=(
                None if finalization is None else finalization.eligible_for_finalization
            ),
            finalization_blocking_issue_codes=(
                () if finalization is None else tuple(finalization.blocking_issue_codes)
            ),
            promotion_eligible=(
                None if promotion is None else promotion.eligible_for_promotion
            ),
            promotion_blocking_issue_codes=(
                () if promotion is None else tuple(promotion.blocking_issue_codes)
            ),
            promotable_review_item_ids=(
                () if promotion is None else tuple(promotion.promotable_item_ids)
            ),
            active_approved_input_ids=active_ids,
            inactive_approved_input_ids=inactive_ids,
            workflow_status=status,
            issue_codes=(),
        )
        relevant = tuple(
            issue
            for issue in (*project_issues, *new_issues)
            if self._issue_applies(
                issue,
                source_id=source_id,
                processing_run_id=processing_run_id,
                review_document_id=document.review_document_id,
                review_document_version_id=version.review_document_version_id,
                approved_input_ids=active_ids + inactive_ids,
            )
        )
        return self._with_effective_issue_state(item, relevant), tuple(new_issues)

    @staticmethod
    def _empty_queue_item(
        project_id,
        source_id,
        filename,
        processing_run_id,
        attempt_id,
        run_state,
        pending_review,
        is_current,
        document_ids,
        status,
        *,
        review_document_id=None,
        review_document_version_id=None,
        version_number=None,
        version_state=None,
        head_revision_id=None,
    ):
        return ReviewApprovalQueueItem(
            project_id=project_id,
            source_id=source_id,
            original_filename=filename,
            processing_run_id=processing_run_id,
            attempt_id=attempt_id,
            run_state=run_state,
            pending_review=pending_review,
            is_current_processing_run=is_current,
            review_document_ids=document_ids,
            review_document_id=review_document_id,
            review_document_version_id=review_document_version_id,
            version_number=version_number,
            version_state=version_state,
            head_revision_id=head_revision_id,
            review_item_count=0,
            review_outcome_counts=(),
            finalization_eligible=None,
            finalization_blocking_issue_codes=(),
            promotion_eligible=None,
            promotion_blocking_issue_codes=(),
            promotable_review_item_ids=(),
            active_approved_input_ids=(),
            inactive_approved_input_ids=(),
            workflow_status=status,
            issue_codes=(),
        )

    def _select_version(
        self,
        project_id,
        review_document_id,
        requested_version_id,
        review_scan,
    ):
        if requested_version_id is not None:
            try:
                return self._review_repository.load_version(
                    project_id,
                    review_document_id,
                    requested_version_id,
                )
            except Exception as exc:
                raise ReviewReferenceError(
                    "The requested Review Document Version could not be loaded."
                ) from exc

        versions = tuple(
            item
            for item in review_scan.versions
            if item.review_document_id == review_document_id
        )
        if not versions:
            raise ReviewReferenceError(
                "The Review Document has no valid Review Document Version."
            )
        max_number = max(item.version_number for item in versions)
        latest = tuple(
            item for item in versions if item.version_number == max_number
        )
        if len(latest) != 1:
            raise ReviewIntegrityError(
                "The Review Document does not have exactly one latest Review Version."
            )
        return latest[0]

    def _latest_version_or_issue(self, project_id, document, versions):
        if not versions:
            return None, self._workflow_issue(
                project_id,
                code="workflow.review_version_unavailable",
                source_domain="review_workspace",
                message="The Review Document has no valid Review Version.",
                source_id=document.source_id,
                processing_run_id=document.processing_run_id,
                review_document_id=document.review_document_id,
            )
        max_number = max(item.version_number for item in versions)
        latest = tuple(
            item for item in versions if item.version_number == max_number
        )
        if len(latest) != 1:
            return None, self._workflow_issue(
                project_id,
                code="workflow.latest_review_version_ambiguous",
                source_domain="review_workspace",
                message=(
                    "The Review Document does not have exactly one latest "
                    "Review Version."
                ),
                source_id=document.source_id,
                processing_run_id=document.processing_run_id,
                review_document_id=document.review_document_id,
            )
        return latest[0], None

    def _derive_authority(self, project_id, approved_scan, issues):
        if any(
            item.issue_level == "blocking" for item in approved_scan.issues
        ):
            return ()
        try:
            return tuple(
                self._authority_deriver(
                    approved_scan.manifests,
                    approved_scan.events,
                )
            )
        except Exception:
            issues.append(
                self._workflow_issue(
                    project_id,
                    code="workflow.approved_input_authority_unavailable",
                    source_domain="approved_input",
                    message=(
                        "Approved Input authority could not be derived from "
                        "immutable manifests and lifecycle events."
                    ),
                )
            )
            return ()

    def _collect_scan_issues(
        self,
        project_id,
        source_scan,
        processing_scan,
        review_scan,
        human_scan,
        approved_scan,
    ):
        issues = []
        for issue in source_scan.source_issues:
            issues.append(
                self._workflow_issue(
                    project_id,
                    code=f"source.{issue.code}",
                    source_domain="source_registry",
                    message=(
                        "Source Registry integrity requires attention before "
                        "review authority can be trusted."
                    ),
                    source_id=issue.source_id,
                )
            )
        for issue in processing_scan.issues:
            issues.append(
                self._workflow_issue(
                    project_id,
                    code=f"processing.{issue.code}",
                    source_domain="processing",
                    message=(
                        "Processing evidence requires attention before the "
                        "Human Review workflow can trust this state."
                    ),
                    issue_level=issue.issue_level,
                    source_id=issue.source_id,
                    processing_run_id=issue.processing_run_id,
                )
            )
        for issue in review_scan.issues:
            issues.append(
                self._workflow_issue(
                    project_id,
                    code=f"review.{issue.code}",
                    source_domain="review_workspace",
                    message="Review Workspace integrity requires attention.",
                    issue_level=issue.issue_level,
                    review_document_id=issue.review_document_id,
                    review_document_version_id=issue.review_document_version_id,
                )
            )
        for issue in human_scan.issues:
            version_id = (
                issue.target_id
                if issue.target_type == "review_document_finalization"
                else None
            )
            issues.append(
                self._workflow_issue(
                    project_id,
                    code=f"human_review.{issue.code}",
                    source_domain="human_review",
                    message="Human Review Decision integrity requires attention.",
                    issue_level=issue.issue_level,
                    review_document_version_id=version_id,
                )
            )
        manifest_by_id = {
            item.approved_input_id: item for item in approved_scan.manifests
        }
        for issue in approved_scan.issues:
            manifest = (
                manifest_by_id.get(issue.approved_input_id)
                if issue.approved_input_id is not None
                else None
            )
            issues.append(
                self._workflow_issue(
                    project_id,
                    code=f"approved_input.{issue.code}",
                    source_domain="approved_input",
                    message="Approved Input repository integrity requires attention.",
                    issue_level=issue.issue_level,
                    review_document_id=(
                        None if manifest is None else manifest.review_document_id
                    ),
                    review_document_version_id=(
                        None
                        if manifest is None
                        else manifest.review_document_version_id
                    ),
                    approved_input_id=issue.approved_input_id,
                )
            )
        return self._sorted_unique_issues(issues)

    def _with_effective_issue_state(self, item, issues):
        relevant = tuple(
            issue
            for issue in issues
            if self._issue_applies(
                issue,
                source_id=item.source_id,
                processing_run_id=item.processing_run_id,
                review_document_id=item.review_document_id,
                review_document_version_id=item.review_document_version_id,
                approved_input_ids=(
                    item.active_approved_input_ids
                    + item.inactive_approved_input_ids
                ),
            )
        )
        codes = tuple(sorted({issue.code for issue in relevant}))
        blocking = any(issue.issue_level == "blocking" for issue in relevant)
        if not codes:
            return item
        return ReviewApprovalQueueItem(
            project_id=item.project_id,
            source_id=item.source_id,
            original_filename=item.original_filename,
            processing_run_id=item.processing_run_id,
            attempt_id=item.attempt_id,
            run_state=item.run_state,
            pending_review=item.pending_review,
            is_current_processing_run=item.is_current_processing_run,
            review_document_ids=item.review_document_ids,
            review_document_id=item.review_document_id,
            review_document_version_id=item.review_document_version_id,
            version_number=item.version_number,
            version_state=item.version_state,
            head_revision_id=item.head_revision_id,
            review_item_count=item.review_item_count,
            review_outcome_counts=item.review_outcome_counts,
            finalization_eligible=item.finalization_eligible,
            finalization_blocking_issue_codes=(
                item.finalization_blocking_issue_codes
            ),
            promotion_eligible=item.promotion_eligible,
            promotion_blocking_issue_codes=(
                item.promotion_blocking_issue_codes
            ),
            promotable_review_item_ids=item.promotable_review_item_ids,
            active_approved_input_ids=item.active_approved_input_ids,
            inactive_approved_input_ids=item.inactive_approved_input_ids,
            workflow_status=(
                "attention_required" if blocking else item.workflow_status
            ),
            issue_codes=codes,
        )

    @staticmethod
    def _issue_applies(
        issue,
        *,
        source_id,
        processing_run_id,
        review_document_id,
        review_document_version_id,
        approved_input_ids,
    ):
        for issue_value, current_value in (
            (issue.source_id, source_id),
            (issue.processing_run_id, processing_run_id),
            (issue.review_document_id, review_document_id),
            (issue.review_document_version_id, review_document_version_id),
        ):
            if issue_value is not None and issue_value != current_value:
                return False
        if (
            issue.approved_input_id is not None
            and approved_input_ids
            and issue.approved_input_id not in approved_input_ids
        ):
            return False
        return True

    @staticmethod
    def _sorted_unique_issues(issues):
        unique = {}
        for item in issues:
            key = (
                item.project_id,
                item.code,
                item.issue_level,
                item.source_domain,
                item.source_id,
                item.processing_run_id,
                item.review_document_id,
                item.review_document_version_id,
                item.approved_input_id,
            )
            unique[key] = item
        return tuple(
            sorted(
                unique.values(),
                key=lambda item: (
                    item.issue_level,
                    item.code,
                    item.source_id or "",
                    item.processing_run_id or "",
                    item.review_document_id or "",
                    item.review_document_version_id or "",
                    item.approved_input_id or "",
                ),
            )
        )

    @staticmethod
    def _workflow_issue(
        project_id,
        *,
        code,
        source_domain,
        message,
        issue_level="blocking",
        source_id=None,
        processing_run_id=None,
        review_document_id=None,
        review_document_version_id=None,
        approved_input_id=None,
    ):
        return ReviewApprovalIssue(
            project_id=project_id,
            code=code,
            issue_level=issue_level,
            source_domain=source_domain,
            message=message,
            source_id=source_id,
            processing_run_id=processing_run_id,
            review_document_id=review_document_id,
            review_document_version_id=review_document_version_id,
            approved_input_id=approved_input_id,
        )



    def _finalization_context(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> tuple[
        ReviewApprovalWorkspaceView,
        ReviewFinalizationWorkflowPreview,
    ]:
        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        if view.version.version_state != "draft":
            raise ReviewFinalizationBlockedError(
                "Only a draft Review Document Version can enter "
                "finalization."
            )

        blocking_issue_codes = tuple(
            issue.code
            for issue in view.issues
            if issue.issue_level == "blocking"
        )

        preview = create_review_finalization_workflow_preview(
            view.document,
            view.version,
            view.revision,
            view.finalization_decisions,
            workflow_blocking_issue_codes=(
                blocking_issue_codes
            ),
        )

        return view, preview

    def _draft_workspace_view(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ReviewApprovalWorkspaceView:
        view = self.workspace_view(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        if view.version.version_state != "draft":
            raise ReviewIntegrityError(
                "Review structure mutations are allowed only on a draft "
                "Review Document Version."
            )
        return view

    @staticmethod
    def _review_item_from_view(
        view: ReviewApprovalWorkspaceView,
        review_item_id: str,
    ):
        matches = tuple(
            item
            for item in view.revision.review_items
            if item.review_item_id == review_item_id
        )
        if len(matches) != 1:
            raise ReviewReferenceError(
                "The selected Review Item is unavailable in the current "
                "Review Revision."
            )
        return matches[0]

    def _allocate_project_review_item_ids(
        self,
        project_id: str,
        count: int,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ReviewValidationError(
                "Review Item allocation count must be a positive integer."
            )

        occupied = self._occupied_review_item_ids(
            project_id
        )
        allocated = []
        working = list(occupied)

        for _ in range(count):
            selected = next_review_item_id(
                working
            )
            allocated.append(selected)
            working.append(selected)

        return occupied, tuple(allocated)

    def _assert_project_review_item_allocation_unchanged(
        self,
        project_id: str,
        expected_occupied_ids: tuple[str, ...],
    ) -> None:
        if (
            self._occupied_review_item_ids(project_id)
            != expected_occupied_ids
        ):
            raise ReviewIntegrityError(
                "Project-wide Review Item identity allocation changed "
                "during the Review structure mutation. Retry is required."
            )

    def _occupied_review_item_ids(
        self,
        project_id: str,
    ) -> tuple[str, ...]:
        """Return all project-local RIT identities ever persisted."""

        try:
            scan = self._review_repository.scan_project(project_id)
        except Exception as exc:
            raise ReviewReferenceError(
                "Review Workspace state could not be inspected for "
                "project-wide Review Item identity allocation."
            ) from exc

        blocking = tuple(
            issue
            for issue in scan.issues
            if getattr(issue, "issue_level", "blocking") == "blocking"
        )
        if blocking:
            raise ReviewIntegrityError(
                "Review Workspace integrity issues block project-wide "
                "Review Item identity allocation."
            )

        identities: dict[str, tuple[str, str]] = {}

        for revision in scan.revisions:
            for item in revision.review_items:
                identity = (
                    item.review_document_id,
                    item.stable_subject_key,
                )
                previous = identities.get(
                    item.review_item_id
                )
                if previous is None:
                    identities[
                        item.review_item_id
                    ] = identity
                    continue

                if previous != identity:
                    raise ReviewIntegrityError(
                        "One project-local Review Item ID is bound to "
                        "multiple Review Item identities."
                    )

        return tuple(sorted(identities))

    def _documents_for_run(
        self,
        project_id: str,
        processing_run_id: str,
    ) -> tuple:
        try:
            scan = self._review_repository.scan_project(project_id)
        except ReviewWorkspaceError:
            raise
        except Exception as exc:
            raise ReviewReferenceError(
                "Review Workspace state could not be inspected "
                "before initial creation."
            ) from exc

        blocking = tuple(
            issue
            for issue in scan.issues
            if getattr(issue, "issue_level", "blocking") == "blocking"
        )
        if blocking:
            raise ReviewIntegrityError(
                "Review Workspace integrity issues block initial "
                "workspace creation."
            )

        return tuple(
            sorted(
                (
                    document
                    for document in scan.documents
                    if (
                        document.processing_run_id
                        == processing_run_id
                    )
                ),
                key=lambda item: item.review_document_id,
            )
        )

    @staticmethod
    def _p4_human_review_scan(scan) -> HumanReviewScanResult:
        """Exclude Review-finalization HRDs from the earlier P4 evidence view."""

        decisions = tuple(
            decision
            for decision in scan.decisions
            if (
                decision.target.target_type
                in _P4_HUMAN_REVIEW_TARGET_TYPES
            )
        )
        issues = tuple(
            issue
            for issue in scan.issues
            if (
                getattr(issue, "target_type", None) is None
                or getattr(issue, "target_type", None)
                in _P4_HUMAN_REVIEW_TARGET_TYPES
            )
        )
        return HumanReviewScanResult(
            decisions=decisions,
            issues=issues,
        )

    @staticmethod
    def _reviewer_identity(value: object) -> str:
        if not isinstance(value, str):
            raise ReviewValidationError(
                "opened_by must be a reviewer identity string."
            )
        selected = value.strip()
        if (
            not selected
            or len(selected) > 240
            or "\n" in selected
            or "\r" in selected
        ):
            raise ReviewValidationError(
                "opened_by must be a non-empty single-line reviewer identity."
            )
        return selected

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise ReviewValidationError(
                "clock must return a datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise ReviewValidationError(
                "clock must return a timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

    def _require_project(self, project_id):
        try:
            self._workspace.load_project(project_id)
        except ProjectWorkspaceError as exc:
            raise ReviewReferenceError(
                "The selected Project is unavailable for Human Review and Approval."
            ) from exc
        except Exception as exc:
            raise ReviewReferenceError(
                "The selected Project could not be validated for Human Review "
                "and Approval."
            ) from exc
