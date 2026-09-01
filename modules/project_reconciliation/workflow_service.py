"""Human-authority write workflow for ADR-032 Project Reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Callable

from modules.approved_input import ApprovedInputRepository
from modules.project_engineering_authority import (
    PROJECT_AUTHORITY_DECISION_OUTCOMES,
    build_project_engineering_authority_state,
    create_project_authority_decision,
    prepare_project_authority_bindings,
)

from .case_persistence import (
    PROJECT_RECONCILIATION_CASE_CYCLE_MODE,
    PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION,
)
from .repository import ProjectReconciliationRepository


_IEM = re.compile(r"^IEM-[0-9]{6}$")


class ProjectReconciliationWorkflowError(RuntimeError):
    """Fail-closed project-level Human Authority workflow error."""


@dataclass(frozen=True, slots=True)
class ProjectAuthorityRelationReview:
    """One exact S3 relation and its immutable Human Authority disposition."""

    left_subject_ref: str
    right_subject_ref: str
    left_source_id: str
    right_source_id: str
    left_label: str
    right_label: str
    machine_outcome: str
    machine_rationale: str
    shared_concepts: tuple[str, ...]
    material_differences: tuple[str, ...]
    left_approved_input_id: str | None
    right_approved_input_id: str | None
    human_decision_id: str | None
    human_outcome: str | None
    authority_concern_id: str | None
    retained_approved_input_ids: tuple[str, ...]
    project_superseded_approved_input_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectAuthorityClaimGroupReview:
    """Read-only non-authoritative claim variant inside one Case."""

    claim_group_id: str
    summary: str
    supported_by_subject_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectAuthorityCaseReview:
    """Read-only ADR-033 Reconciliation Case projection."""

    case_id: str
    group_label: str
    outcome: str
    summary: str
    source_ids: tuple[str, ...]
    member_subject_refs: tuple[str, ...]
    shared_concepts: tuple[str, ...]
    material_differences: tuple[str, ...]
    claim_groups: tuple[ProjectAuthorityClaimGroupReview, ...]
    human_review_required: bool


@dataclass(frozen=True, slots=True)
class ProjectAuthorityReviewView:
    """Read projection for one immutable Project Reconciliation cycle."""

    project_id: str
    cycle_id: str | None
    source_ids: tuple[str, ...]
    relation_reviews: tuple[ProjectAuthorityRelationReview, ...]
    unmatched_subject_count: int
    bindings_ready: bool
    decision_count: int
    required_decision_count: int
    authority_state_ready: bool
    model_impact_ready: bool
    model_impact_persisted: bool
    workflow_status: str
    blocking_reason: str | None
    reconciliation_mode: str = "legacy_relations"
    case_reviews: tuple[ProjectAuthorityCaseReview, ...] = ()
    case_count: int = 0
    unique_case_count: int = 0
    potential_conflicts_present: bool = False
    uncertainties_present: bool = False
    regrouping_required: bool = False
    case_authority_ready: bool = True

    @property
    def open_decision_count(self) -> int:
        return self.required_decision_count - self.decision_count


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ProjectAuthorityWorkflowService:
    """Delegate Human Project Authority to S4/S5 without owning new authority."""

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        reconciliation_repository=None,
        approved_input_repository=None,
        review_workflow_service=None,
        accepted_model_loader: Callable[[str], object | None] | None = None,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        if not callable(clock):
            raise ProjectReconciliationWorkflowError(
                "clock must be callable."
            )

        self.project_root = Path(project_root)
        self.projects_root = self.project_root / "data" / "projects"
        self._clock = clock

        self._reconciliation = (
            ProjectReconciliationRepository(root=self.projects_root)
            if reconciliation_repository is None
            else reconciliation_repository
        )
        self._approved_inputs = (
            ApprovedInputRepository(root=self.projects_root)
            if approved_input_repository is None
            else approved_input_repository
        )
        self._review_workflow_service = review_workflow_service
        self._accepted_model_loader = (
            self._load_unique_accepted_model_head
            if accepted_model_loader is None
            else accepted_model_loader
        )

    def load_review(
        self,
        project_id: str,
        *,
        cycle_id: str | None = None,
    ) -> ProjectAuthorityReviewView:
        """Load one non-authoritative review projection of persisted S3/S4/S5."""

        try:
            cycle = (
                self._reconciliation.latest_cycle(project_id)
                if cycle_id is None
                else self._reconciliation.load_cycle(project_id, cycle_id)
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Project Reconciliation cycle state is unavailable."
            ) from exc

        if cycle is None:
            return ProjectAuthorityReviewView(
                project_id=project_id,
                cycle_id=None,
                source_ids=(),
                relation_reviews=(),
                unmatched_subject_count=0,
                bindings_ready=False,
                decision_count=0,
                required_decision_count=0,
                authority_state_ready=False,
                model_impact_ready=False,
                model_impact_persisted=False,
                workflow_status="not_started",
                blocking_reason=None,
            )

        cycle_id = cycle.reconciliation_cycle_id
        if self._is_concern_centric_cycle(cycle):
            return self._load_concern_centric_review(
                project_id,
                cycle_id,
            )

        try:
            reconciliation = (
                self._reconciliation.load_semantic_reconciliation(
                    project_id,
                    cycle_id,
                )
            )
            bindings_snapshot = (
                self._reconciliation.load_authority_bindings_if_available(
                    project_id,
                    cycle_id,
                )
            )
            decisions = self._reconciliation.list_authority_decisions(
                project_id,
                cycle_id,
            )
            authority_state = (
                self._reconciliation.load_authority_state_if_available(
                    project_id,
                    cycle_id,
                )
            )
            model_impact = (
                self._reconciliation.load_model_impact_if_available(
                    project_id,
                    cycle_id,
                )
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Persisted Project Reconciliation evidence cannot be "
                "reconstructed safely."
            ) from exc

        subject_by_ref = {
            item.subject_ref: item
            for item in reconciliation.subjects
        }
        binding_by_ref = (
            {}
            if bindings_snapshot is None
            else {
                item.subject_ref: item
                for item in bindings_snapshot.bindings
            }
        )
        decision_by_pair = {
            (item.left_subject_ref, item.right_subject_ref): item
            for item in decisions
        }

        rows = []
        for relation in sorted(
            reconciliation.relations,
            key=lambda item: (
                item.left_subject_ref,
                item.right_subject_ref,
            ),
        ):
            left_ref, right_ref = sorted(
                (relation.left_subject_ref, relation.right_subject_ref)
            )
            left = subject_by_ref[left_ref]
            right = subject_by_ref[right_ref]
            decision = decision_by_pair.get((left_ref, right_ref))
            left_binding = binding_by_ref.get(left_ref)
            right_binding = binding_by_ref.get(right_ref)
            rows.append(
                ProjectAuthorityRelationReview(
                    left_subject_ref=left_ref,
                    right_subject_ref=right_ref,
                    left_source_id=left.source_id,
                    right_source_id=right.source_id,
                    left_label=left.canonical_label,
                    right_label=right.canonical_label,
                    machine_outcome=relation.outcome,
                    machine_rationale=relation.rationale,
                    shared_concepts=tuple(relation.shared_concepts),
                    material_differences=tuple(
                        relation.material_differences
                    ),
                    left_approved_input_id=(
                        None
                        if left_binding is None
                        else left_binding.approved_input_id
                    ),
                    right_approved_input_id=(
                        None
                        if right_binding is None
                        else right_binding.approved_input_id
                    ),
                    human_decision_id=(
                        None if decision is None else decision.decision_id
                    ),
                    human_outcome=(
                        None if decision is None else decision.outcome
                    ),
                    authority_concern_id=(
                        None
                        if decision is None
                        else decision.authority_concern_id
                    ),
                    retained_approved_input_ids=(
                        ()
                        if decision is None
                        else decision.retained_approved_input_ids
                    ),
                    project_superseded_approved_input_ids=(
                        ()
                        if decision is None
                        else (
                            decision
                            .project_superseded_approved_input_ids
                        )
                    ),
                )
            )

        required = len(reconciliation.relations)
        decided = len(decisions)
        bindings_ready = bindings_snapshot is not None

        if not bindings_ready:
            status = "bindings_required"
            blocking = None
        elif decided < required:
            status = "human_decision_required"
            blocking = None
        elif authority_state is None:
            status = "authority_finalization_required"
            blocking = None
        elif not authority_state.model_impact_ready:
            status = "authority_unresolved"
            blocking = (
                "Human Project Authority contains unresolved decisions."
            )
        elif model_impact is None:
            status = "model_impact_required"
            blocking = None
        else:
            status = "complete"
            blocking = None

        return ProjectAuthorityReviewView(
            project_id=project_id,
            cycle_id=cycle_id,
            source_ids=tuple(reconciliation.source_ids),
            relation_reviews=tuple(rows),
            unmatched_subject_count=len(
                reconciliation.unmatched_subject_refs
            ),
            bindings_ready=bindings_ready,
            decision_count=decided,
            required_decision_count=required,
            authority_state_ready=authority_state is not None,
            model_impact_ready=(
                False
                if authority_state is None
                else authority_state.model_impact_ready
            ),
            model_impact_persisted=model_impact is not None,
            workflow_status=status,
            blocking_reason=blocking,
        )

    @staticmethod
    def _is_concern_centric_cycle(cycle) -> bool:
        return (
            getattr(cycle, "schema_version", None)
            == PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION
            and getattr(cycle, "reconciliation_mode", None)
            == PROJECT_RECONCILIATION_CASE_CYCLE_MODE
        )

    def _load_concern_centric_review(
        self,
        project_id: str,
        cycle_id: str,
    ) -> ProjectAuthorityReviewView:
        try:
            semantic_index = self._reconciliation.load_semantic_index(
                project_id,
                cycle_id,
            )
            assessments = self._reconciliation.load_case_assessments(
                project_id,
                cycle_id,
            )
            summary = (
                self._reconciliation.load_reconciliation_summary(
                    project_id,
                    cycle_id,
                )
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Persisted concern-centric Project Reconciliation "
                "evidence cannot be reconstructed safely."
            ) from exc

        cases_by_id = {
            case.case_id: case
            for case in semantic_index.cases
        }
        if (
            len(cases_by_id) != len(semantic_index.cases)
            or len(assessments) != len(semantic_index.cases)
        ):
            raise ProjectReconciliationWorkflowError(
                "Concern-centric Case population is inconsistent."
            )

        rows = []
        for assessment in assessments:
            case = cases_by_id.get(assessment.case_id)
            if case is None:
                raise ProjectReconciliationWorkflowError(
                    "Case assessment references an unknown indexed Case."
                )
            rows.append(
                ProjectAuthorityCaseReview(
                    case_id=case.case_id,
                    group_label=case.group_label,
                    outcome=assessment.outcome,
                    summary=assessment.summary,
                    source_ids=case.source_ids,
                    member_subject_refs=case.member_subject_refs,
                    shared_concepts=assessment.shared_concepts,
                    material_differences=(
                        assessment.material_differences
                    ),
                    claim_groups=tuple(
                        ProjectAuthorityClaimGroupReview(
                            claim_group_id=group.claim_group_id,
                            summary=group.summary,
                            supported_by_subject_refs=(
                                group.supported_by_subject_refs
                            ),
                        )
                        for group in assessment.claim_groups
                    ),
                    human_review_required=(
                        assessment.human_review_required
                    ),
                )
            )

        rows = tuple(
            sorted(rows, key=lambda item: item.case_id)
        )
        unique_count = sum(
            1 for item in rows if item.outcome == "unique"
        )

        if summary.regrouping_required:
            status = "regrouping_required"
            blocking = (
                "S3B identified at least one over-grouped "
                "Reconciliation Case. Semantic regrouping is required "
                "before Human Project Authority."
            )
        else:
            status = "case_review_ready"
            blocking = (
                "Concern-centric S3 evidence is persisted and "
                "reviewable. The case-aware Human Project Authority "
                "workflow is required before any project-level "
                "authority decision can be made."
            )

        return ProjectAuthorityReviewView(
            project_id=project_id,
            cycle_id=cycle_id,
            source_ids=tuple(semantic_index.source_ids),
            relation_reviews=(),
            unmatched_subject_count=0,
            bindings_ready=False,
            decision_count=0,
            required_decision_count=0,
            authority_state_ready=False,
            model_impact_ready=False,
            model_impact_persisted=False,
            workflow_status=status,
            blocking_reason=blocking,
            reconciliation_mode=(
                PROJECT_RECONCILIATION_CASE_CYCLE_MODE
            ),
            case_reviews=rows,
            case_count=summary.case_count,
            unique_case_count=unique_count,
            potential_conflicts_present=(
                summary.potential_conflicts_present
            ),
            uncertainties_present=(
                summary.uncertainties_present
            ),
            regrouping_required=summary.regrouping_required,
            case_authority_ready=False,
        )

    def _require_legacy_relation_authority_cycle(
        self,
        project_id: str,
        cycle_id: str,
    ) -> None:
        try:
            cycle = self._reconciliation.load_cycle(
                project_id,
                cycle_id,
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Project Reconciliation cycle state is unavailable."
            ) from exc

        if self._is_concern_centric_cycle(cycle):
            raise ProjectReconciliationWorkflowError(
                "Concern-centric Reconciliation Cases require the "
                "case-aware Human Project Authority workflow. Legacy "
                "pairwise relation authority is not permitted."
            )

    def prepare_authority_bindings(
        self,
        project_id: str,
        cycle_id: str,
    ):
        """Freeze exact current source-local Human Authority for one S3 cycle."""

        self._require_legacy_relation_authority_cycle(
            project_id,
            cycle_id,
        )

        existing = (
            self._reconciliation.load_authority_bindings_if_available(
                project_id,
                cycle_id,
            )
        )
        if existing is not None:
            return existing

        reconciliation = (
            self._reconciliation.load_semantic_reconciliation(
                project_id,
                cycle_id,
            )
        )
        manifests, events, aeis = self._current_authority_material(
            project_id,
            reconciliation=reconciliation,
            bindings=None,
        )
        try:
            bindings = prepare_project_authority_bindings(
                reconciliation,
                manifests,
                events,
                aeis,
            )
            return self._reconciliation.publish_authority_bindings(
                project_id,
                cycle_id,
                bindings,
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Current source-local Human Authority cannot be frozen "
                "for this exact S3 cycle."
            ) from exc

    def record_authority_decision(
        self,
        project_id: str,
        cycle_id: str,
        *,
        left_subject_ref: str,
        right_subject_ref: str,
        outcome: str,
        reviewer_identity: str,
        rationale: str,
        retained_approved_input_id: str | None = None,
        authority_concern_id: str | None = None,
    ):
        """Persist one immutable Human S4 decision for one exact S3 relation."""

        self._require_legacy_relation_authority_cycle(
            project_id,
            cycle_id,
        )

        if outcome not in PROJECT_AUTHORITY_DECISION_OUTCOMES:
            raise ProjectReconciliationWorkflowError(
                "Unsupported Human Project Authority outcome."
            )
        if not isinstance(reviewer_identity, str) or not reviewer_identity.strip():
            raise ProjectReconciliationWorkflowError(
                "Reviewer identity is required."
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise ProjectReconciliationWorkflowError(
                "Human rationale is required."
            )
        if (
            self._reconciliation.load_authority_state_if_available(
                project_id,
                cycle_id,
            )
            is not None
        ):
            raise ProjectReconciliationWorkflowError(
                "Project Authority State is already finalized and immutable."
            )

        reconciliation = (
            self._reconciliation.load_semantic_reconciliation(
                project_id,
                cycle_id,
            )
        )
        binding_snapshot = self._reconciliation.load_authority_bindings(
            project_id,
            cycle_id,
        )

        concern = authority_concern_id
        if outcome in {"coexist", "supersede"} and concern is None:
            concern = self._reconciliation.next_authority_concern_id(
                project_id,
                cycle_id,
            )

        try:
            decision = create_project_authority_decision(
                reconciliation,
                binding_snapshot.bindings,
                decision_id=(
                    self._reconciliation.next_authority_decision_id(
                        project_id,
                        cycle_id,
                    )
                ),
                left_subject_ref=left_subject_ref,
                right_subject_ref=right_subject_ref,
                outcome=outcome,
                reviewer_identity=reviewer_identity.strip(),
                rationale=rationale.strip(),
                decided_at=self._timestamp(),
                authority_concern_id=concern,
                retained_approved_input_id=retained_approved_input_id,
            )
            return self._reconciliation.record_authority_decision(
                project_id,
                cycle_id,
                decision,
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Human Project Authority decision was rejected by the "
                "exact S3/S4 authority contract."
            ) from exc

    def finalize_authority(
        self,
        project_id: str,
        cycle_id: str,
    ):
        """Derive immutable S4 state from exact persisted decisions and live authority."""

        self._require_legacy_relation_authority_cycle(
            project_id,
            cycle_id,
        )

        existing = self._reconciliation.load_authority_state_if_available(
            project_id,
            cycle_id,
        )
        if existing is not None:
            return existing

        reconciliation = (
            self._reconciliation.load_semantic_reconciliation(
                project_id,
                cycle_id,
            )
        )
        binding_snapshot = self._reconciliation.load_authority_bindings(
            project_id,
            cycle_id,
        )
        decisions = self._reconciliation.list_authority_decisions(
            project_id,
            cycle_id,
        )
        if len(decisions) != len(reconciliation.relations):
            raise ProjectReconciliationWorkflowError(
                "Every S3 relation requires exactly one immutable Human "
                "Project Authority decision before S4 finalization."
            )

        manifests, events, aeis = self._current_authority_material(
            project_id,
            reconciliation=reconciliation,
            bindings=binding_snapshot.bindings,
        )
        try:
            state = build_project_engineering_authority_state(
                reconciliation,
                manifests,
                events,
                aeis,
                decisions,
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Project Engineering Authority could not be finalized. "
                "Current source-local authority may have changed since the "
                "frozen S4 binding snapshot."
            ) from exc

        if state.bindings != binding_snapshot.bindings:
            raise ProjectReconciliationWorkflowError(
                "Current source-local authority differs from the frozen "
                "S4 binding snapshot. Start a new reconciliation cycle."
            )

        try:
            return self._reconciliation.publish_authority_state(
                project_id,
                cycle_id,
                state,
            )
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Project Engineering Authority State could not be persisted."
            ) from exc

    def reconcile_model_impact(
        self,
        project_id: str,
        cycle_id: str,
    ):
        """Persist deterministic S5 impact against the unique accepted-model head."""

        existing = self._reconciliation.load_model_impact_if_available(
            project_id,
            cycle_id,
        )
        if existing is not None:
            return existing

        state = self._reconciliation.load_authority_state(
            project_id,
            cycle_id,
        )
        if not state.model_impact_ready:
            raise ProjectReconciliationWorkflowError(
                "Model Impact Reconciliation is blocked while Project "
                "Engineering Authority remains unresolved."
            )

        try:
            accepted_model = self._accepted_model_loader(project_id)
            from modules.model_impact_reconciliation import (
                reconcile_model_impact,
            )

            artifact = reconcile_model_impact(
                state,
                accepted_model,
            )
            return self._reconciliation.publish_model_impact(
                project_id,
                cycle_id,
                artifact,
            )
        except ProjectReconciliationWorkflowError:
            raise
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Model Impact Reconciliation could not be derived safely."
            ) from exc

    def _current_authority_material(
        self,
        project_id: str,
        *,
        reconciliation,
        bindings,
    ):
        try:
            manifests = tuple(
                self._approved_inputs.list_manifests(project_id)
            )
            events = tuple(
                self._approved_inputs.list_events(project_id)
            )
            if bindings is None:
                active = tuple(
                    self._approved_inputs.list_active_approved_inputs(
                        project_id
                    )
                )
                relevant = tuple(
                    item
                    for item in active
                    if item.source_id in set(reconciliation.source_ids)
                )
                review_refs = {
                    (
                        item.review_document_id,
                        item.review_document_version_id,
                    )
                    for item in relevant
                }
            else:
                review_refs = {
                    (
                        item.review_document_id,
                        item.review_document_version_id,
                    )
                    for item in bindings
                }

            if not review_refs:
                raise ProjectReconciliationWorkflowError(
                    "No source-local finalized Review authority is available."
                )

            service = self._review_service()
            aeis = tuple(
                service.approved_engineering_information(
                    project_id,
                    document_id,
                    version_id,
                )
                for document_id, version_id in sorted(review_refs)
            )
            return manifests, events, aeis
        except ProjectReconciliationWorkflowError:
            raise
        except Exception as exc:
            raise ProjectReconciliationWorkflowError(
                "Source-local Approved Input / AEI authority cannot be "
                "reconstructed safely."
            ) from exc

    def _review_service(self):
        if self._review_workflow_service is None:
            from modules.review_workspace.workflow_service import (
                ReviewApprovalWorkflowService,
            )

            self._review_workflow_service = ReviewApprovalWorkflowService(
                root=self.projects_root,
                repository_root=self.project_root,
                approved_input_repository=self._approved_inputs,
            )
        return self._review_workflow_service

    def _load_unique_accepted_model_head(self, project_id: str):
        from modules.internal_model.authority_backed import (
            AuthorityBackedInternalModelRepository,
        )

        root = (
            self.projects_root
            / project_id
            / "internal_models_v2"
        )
        if not root.exists():
            return None
        if root.is_symlink() or not root.is_dir():
            raise ProjectReconciliationWorkflowError(
                "Authority-backed Internal Model repository is unsafe."
            )

        repository = AuthorityBackedInternalModelRepository(
            root=self.projects_root
        )
        snapshots = []
        for entry in sorted(root.iterdir(), key=lambda item: item.name):
            if (
                entry.is_symlink()
                or not entry.is_dir()
                or _IEM.fullmatch(entry.name) is None
            ):
                raise ProjectReconciliationWorkflowError(
                    "Unexpected Authority-backed Internal Model entry."
                )
            snapshots.append(repository.load(project_id, entry.name))

        if not snapshots:
            return None

        predecessor_ids = {
            item.source_internal_engineering_model_id
            for item in snapshots
            if item.source_internal_engineering_model_id is not None
        }
        heads = tuple(
            item
            for item in snapshots
            if item.internal_engineering_model_id not in predecessor_ids
        )
        if len(heads) != 1:
            raise ProjectReconciliationWorkflowError(
                "S5 requires exactly one accepted authority-backed "
                "Internal Model head."
            )
        return heads[0]

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise ProjectReconciliationWorkflowError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise ProjectReconciliationWorkflowError(
                "clock must return timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
