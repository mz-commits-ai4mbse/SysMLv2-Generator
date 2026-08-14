"""Human change-proposal routing and optional bounded agent re-proposal handoff."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .change_proposal import create_final_model_review_change_proposal
from .errors import FinalModelReviewIntegrityError, FinalModelReviewValidationError
from .identifiers import next_final_model_review_change_proposal_id
from .repository import FinalModelReviewRepository
from .types import (
    FinalModelReviewAgentReproposalRequest,
    FinalModelReviewChangeRoute,
    FinalModelReviewChangeSubmission,
    FinalModelReviewChangeTarget,
)


class FinalModelReviewAgentReproposalAdapter(Protocol):
    """Optional orchestration boundary; agents may propose but never mutate authority."""

    def submit_reproposal_request(
        self,
        request: FinalModelReviewAgentReproposalRequest,
    ) -> None:
        ...


_ROUTE_POLICIES = {
    "engineering_semantics": FinalModelReviewChangeRoute(
        classification="engineering_semantics",
        authority_route="phase_h_candidate_review",
        required_action="Create or regenerate Model Candidates and require Candidate Human Review before IEM reassembly.",
        requires_candidate_review=True,
        requires_regeneration=True,
        requires_revalidation=True,
        requires_new_review_revision=True,
    ),
    "generated_representation": FinalModelReviewChangeRoute(
        classification="generated_representation",
        authority_route="phase_j_generation",
        required_action="Correct the Phase-J generation policy or generator, then deterministically regenerate and revalidate.",
        requires_candidate_review=False,
        requires_regeneration=True,
        requires_revalidation=True,
        requires_new_review_revision=True,
    ),
    "validation_policy_or_tool": FinalModelReviewChangeRoute(
        classification="validation_policy_or_tool",
        authority_route="phase_k_validation",
        required_action="Investigate the Phase-K validation policy or validator, then revalidate the exact generated artifact.",
        requires_candidate_review=False,
        requires_regeneration=False,
        requires_revalidation=True,
        requires_new_review_revision=True,
    ),
    "review_presentation_only": FinalModelReviewChangeRoute(
        classification="review_presentation_only",
        authority_route="phase_l_presentation",
        required_action="Correct only the Phase-L read model or UI projection; do not alter engineering or generated authority.",
        requires_candidate_review=False,
        requires_regeneration=False,
        requires_revalidation=False,
        requires_new_review_revision=False,
    ),
}


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class FinalModelReviewChangeService:
    """Record an immutable Human proposal and return its deterministic route."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository: FinalModelReviewRepository | None = None,
        clock: Callable[[], datetime] = _default_clock,
        agent_reproposal_adapter: FinalModelReviewAgentReproposalAdapter | None = None,
    ) -> None:
        self.root = Path(root)
        self._repository = repository or FinalModelReviewRepository(root=self.root)
        self._clock = clock
        self._agent_adapter = agent_reproposal_adapter

    def submit_change(
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
    ) -> FinalModelReviewChangeSubmission:
        bundle = self._repository.load_revision(
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        route = self.route_for_classification(classification)
        target = self._target(
            bundle,
            generated_unit_id=generated_unit_id,
            generated_symbol_id=generated_symbol_id,
            internal_model_element_id=internal_model_element_id,
            internal_model_relationship_id=internal_model_relationship_id,
            validation_finding_code=validation_finding_code,
        )
        if route.authority_route == "phase_l_presentation" and request_agent_reproposal:
            raise FinalModelReviewValidationError(
                "presentation-only changes must not invoke an engineering agent re-proposal loop."
            )
        existing = self._repository.list_change_proposals(project_id)
        proposal_id = next_final_model_review_change_proposal_id(
            item.final_model_review_change_proposal_id for item in existing
        )
        proposal = create_final_model_review_change_proposal(
            project_id=project_id,
            final_model_review_id=final_model_review_id,
            final_model_review_revision_id=final_model_review_revision_id,
            final_model_review_change_proposal_id=proposal_id,
            base_revision_content_fingerprint=bundle.revision.content_fingerprint,
            base_review_subject_fingerprint=bundle.revision.review_subject_fingerprint,
            surface=surface,
            classification=classification,
            target=target,
            original_text=original_text,
            proposed_text=proposed_text,
            reviewer_feedback=reviewer_feedback,
            request_agent_reproposal=request_agent_reproposal,
            requested_agent_personalities=requested_agent_personalities,
            created_by=created_by,
            created_at=self._timestamp(),
        )
        saved = self._repository.persist_change_proposal(proposal)
        agent_request = None
        if request_agent_reproposal:
            agent_request = FinalModelReviewAgentReproposalRequest(
                project_id=project_id,
                final_model_review_id=final_model_review_id,
                final_model_review_revision_id=final_model_review_revision_id,
                final_model_review_change_proposal_id=(
                    saved.final_model_review_change_proposal_id
                ),
                change_proposal_fingerprint=saved.content_fingerprint,
                authority_route=saved.authority_route,
                reviewer_feedback=saved.reviewer_feedback,
                requested_agent_personalities=saved.requested_agent_personalities,
                source_model_candidate_ids=self._candidate_ids(
                    bundle.artifact_set_snapshot,
                    generated_symbol_id=generated_symbol_id,
                    internal_model_element_id=internal_model_element_id,
                    internal_model_relationship_id=internal_model_relationship_id,
                ),
            )
            if self._agent_adapter is not None:
                self._agent_adapter.submit_reproposal_request(agent_request)
        return FinalModelReviewChangeSubmission(saved, route, agent_request)

    @staticmethod
    def route_for_classification(classification: str) -> FinalModelReviewChangeRoute:
        try:
            return _ROUTE_POLICIES[classification]
        except KeyError as exc:
            raise FinalModelReviewValidationError(
                "change classification is unsupported."
            ) from exc

    def _target(
        self,
        bundle,
        *,
        generated_unit_id,
        generated_symbol_id,
        internal_model_element_id,
        internal_model_relationship_id,
        validation_finding_code,
    ) -> FinalModelReviewChangeTarget:
        unit_fingerprint = None
        if generated_unit_id is not None:
            matches = tuple(
                item for item in bundle.revision.generated_units
                if item.generated_unit_id == generated_unit_id
            )
            if len(matches) != 1:
                raise FinalModelReviewIntegrityError(
                    "change target generated unit does not resolve exactly once in the review revision."
                )
            unit_fingerprint = matches[0].content_fingerprint
        if generated_symbol_id is not None:
            if generated_unit_id is None:
                raise FinalModelReviewValidationError(
                    "generated_symbol_id requires generated_unit_id."
                )
            units = bundle.artifact_set_snapshot.get("units")
            matches = [
                item for item in units or []
                if isinstance(item, dict) and item.get("unit_id") == generated_unit_id
            ]
            if len(matches) != 1 or generated_symbol_id not in matches[0].get("generated_symbol_ids", []):
                raise FinalModelReviewIntegrityError(
                    "change target generated symbol is outside the exact review subject."
                )
        traceability_entries = bundle.artifact_set_snapshot.get("traceability_entries")
        if (
            internal_model_element_id is not None
            or internal_model_relationship_id is not None
        ):
            if not isinstance(traceability_entries, list):
                raise FinalModelReviewIntegrityError(
                    "review subject lacks traceability needed to resolve the model target."
                )
            if internal_model_element_id is not None and not any(
                isinstance(item, dict)
                and item.get("source_internal_model_element_id")
                == internal_model_element_id
                for item in traceability_entries
            ):
                raise FinalModelReviewIntegrityError(
                    "change target internal model element is outside the exact review subject."
                )
            if internal_model_relationship_id is not None and not any(
                isinstance(item, dict)
                and item.get("source_internal_model_relationship_id")
                == internal_model_relationship_id
                for item in traceability_entries
            ):
                raise FinalModelReviewIntegrityError(
                    "change target internal model relationship is outside the exact review subject."
                )
        if validation_finding_code is not None:
            findings = bundle.validation_result_snapshot.get("findings")
            if not isinstance(findings, list) or not any(
                isinstance(item, dict) and item.get("code") == validation_finding_code
                for item in findings
            ):
                raise FinalModelReviewIntegrityError(
                    "change target validation finding is outside the exact review subject."
                )
        return FinalModelReviewChangeTarget(
            generated_unit_id=generated_unit_id,
            generated_unit_content_fingerprint=unit_fingerprint,
            generated_symbol_id=generated_symbol_id,
            internal_model_element_id=internal_model_element_id,
            internal_model_relationship_id=internal_model_relationship_id,
            validation_finding_code=validation_finding_code,
        )

    def _candidate_ids(
        self,
        artifact_snapshot,
        *,
        generated_symbol_id,
        internal_model_element_id,
        internal_model_relationship_id,
    ) -> tuple[str, ...]:
        entries = artifact_snapshot.get("traceability_entries")
        if not isinstance(entries, list):
            return ()
        result = set()
        for item in entries:
            if not isinstance(item, dict):
                continue
            if generated_symbol_id is not None and item.get("generated_symbol_id") != generated_symbol_id:
                continue
            if internal_model_element_id is not None and item.get("source_internal_model_element_id") != internal_model_element_id:
                continue
            if internal_model_relationship_id is not None and item.get("source_internal_model_relationship_id") != internal_model_relationship_id:
                continue
            candidate_id = item.get("source_model_candidate_id")
            if isinstance(candidate_id, str):
                result.add(candidate_id)
        return tuple(sorted(result))

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise FinalModelReviewValidationError(
                "clock must return a timezone-aware datetime."
            )
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
