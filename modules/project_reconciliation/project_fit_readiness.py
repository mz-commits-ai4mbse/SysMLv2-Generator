"""Read-only Project Fit readiness projection for the BLK-002 thesis MVP.

This module deliberately owns no Engineering Authority. It only projects
current source-local Human Review state together with immutable Project Fit
evidence into the active multi-source admissibility gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.project_fit import derive_project_fit_gate_state


class ProjectFitReadinessError(RuntimeError):
    """Fail-closed Project Fit readiness reconstruction error."""


@dataclass(frozen=True, slots=True)
class ProjectFitSourceReadiness:
    source_id: str
    processing_run_id: str
    attempt_id: str | None
    workflow_status: str
    gate_state: str
    outcome: str | None
    assessment_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class ProjectFitReadiness:
    project_id: str
    sources: tuple[ProjectFitSourceReadiness, ...]

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(item.source_id for item in self.sources)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def admitted_source_ids(self) -> tuple[str, ...]:
        return tuple(
            item.source_id
            for item in self.sources
            if item.gate_state == "admitted"
        )

    @property
    def assessment_required_source_ids(self) -> tuple[str, ...]:
        return tuple(
            item.source_id
            for item in self.sources
            if item.gate_state == "assessment_required"
        )

    @property
    def source_review_required_source_ids(self) -> tuple[str, ...]:
        return tuple(
            item.source_id
            for item in self.sources
            if item.gate_state == "source_review_required"
        )

    @property
    def human_resolution_source_ids(self) -> tuple[str, ...]:
        return tuple(
            item.source_id
            for item in self.sources
            if item.gate_state in {
                "human_resolution_required",
                "context_only",
            }
        )

    @property
    def project_fit_fingerprints(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.assessment_fingerprint
                for item in self.sources
                if item.assessment_fingerprint is not None
            )
        )

    @property
    def all_admitted(self) -> bool:
        return (
            self.source_count > 1
            and len(self.admitted_source_ids) == self.source_count
        )


def derive_project_fit_readiness(
    *,
    project_id: str,
    review_items: tuple,
    project_fit_assessments: tuple,
) -> ProjectFitReadiness:
    """Project exact current source/run/attempt Project Fit readiness."""

    if not isinstance(project_id, str) or not project_id.strip():
        raise ProjectFitReadinessError("project_id must be non-empty.")
    if not isinstance(review_items, tuple):
        raise ProjectFitReadinessError("review_items must be a tuple.")
    if not isinstance(project_fit_assessments, tuple):
        raise ProjectFitReadinessError(
            "project_fit_assessments must be a tuple."
        )

    current = tuple(
        sorted(
            (
                item
                for item in review_items
                if getattr(item, "is_current_processing_run", False)
            ),
            key=lambda item: item.source_id,
        )
    )

    source_ids = tuple(item.source_id for item in current)
    if len(source_ids) != len(set(source_ids)):
        raise ProjectFitReadinessError(
            "Current Human Review contains more than one item for the same "
            "Engineering Source."
        )

    states = []
    for item in current:
        source_id = getattr(item, "source_id", None)
        processing_run_id = getattr(item, "processing_run_id", None)
        attempt_id = getattr(item, "attempt_id", None)
        workflow_status = getattr(item, "workflow_status", None)

        if not isinstance(source_id, str) or not source_id:
            raise ProjectFitReadinessError(
                "Current Human Review item has no valid source_id."
            )
        if not isinstance(processing_run_id, str) or not processing_run_id:
            raise ProjectFitReadinessError(
                f"{source_id} has no valid current Processing Run."
            )
        if not isinstance(workflow_status, str) or not workflow_status:
            raise ProjectFitReadinessError(
                f"{source_id} has no valid Human Review workflow status."
            )

        if workflow_status != "approved_input_available":
            states.append(
                ProjectFitSourceReadiness(
                    source_id=source_id,
                    processing_run_id=processing_run_id,
                    attempt_id=attempt_id,
                    workflow_status=workflow_status,
                    gate_state="source_review_required",
                    outcome=None,
                    assessment_fingerprint=None,
                )
            )
            continue

        if not isinstance(attempt_id, str) or not attempt_id:
            raise ProjectFitReadinessError(
                f"{source_id} has approved input but no exact Processing Attempt."
            )

        matches = tuple(
            fit
            for fit in project_fit_assessments
            if (
                getattr(fit, "project_id", None) == project_id
                and getattr(fit, "source_id", None) == source_id
                and getattr(fit, "processing_run_id", None)
                == processing_run_id
                and getattr(fit, "attempt_id", None) == attempt_id
            )
        )

        if len(matches) > 1:
            raise ProjectFitReadinessError(
                "More than one Project Fit assessment binds the same exact "
                f"current source/run/attempt: {source_id} / "
                f"{processing_run_id} / {attempt_id}."
            )

        if not matches:
            states.append(
                ProjectFitSourceReadiness(
                    source_id=source_id,
                    processing_run_id=processing_run_id,
                    attempt_id=attempt_id,
                    workflow_status=workflow_status,
                    gate_state="assessment_required",
                    outcome=None,
                    assessment_fingerprint=None,
                )
            )
            continue

        fit = matches[0]
        try:
            gate_state = derive_project_fit_gate_state(fit)
        except Exception as exc:
            raise ProjectFitReadinessError(
                f"Project Fit evidence for {source_id} is invalid."
            ) from exc

        assessment_fingerprint = getattr(
            fit,
            "assessment_fingerprint",
            None,
        )
        if (
            not isinstance(assessment_fingerprint, str)
            or not assessment_fingerprint
        ):
            raise ProjectFitReadinessError(
                f"Project Fit evidence for {source_id} has no fingerprint."
            )

        states.append(
            ProjectFitSourceReadiness(
                source_id=source_id,
                processing_run_id=processing_run_id,
                attempt_id=attempt_id,
                workflow_status=workflow_status,
                gate_state=gate_state,
                outcome=getattr(fit, "outcome", None),
                assessment_fingerprint=assessment_fingerprint,
            )
        )

    return ProjectFitReadiness(
        project_id=project_id,
        sources=tuple(states),
    )
