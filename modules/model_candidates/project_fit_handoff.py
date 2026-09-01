"""Project-Fit-based multi-source Phase-H handoff for the thesis MVP.

The handoff binds exact admitted Project Fit evidence to existing immutable
source-local Approved Inputs and Approved Engineering Information.

It creates no cross-source semantic identity, performs no supersession,
owns no Engineering Authority and does not synthesize a merged AEI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json

from modules.approved_input.manifest import (
    validate_approved_input_manifest,
)
from modules.project_fit import (
    derive_project_fit_gate_state,
    validate_project_fit_assessment,
)

from .types import ModelCandidateGenerationProvenance


PROJECT_FIT_PHASE_H_HANDOFF_SCHEMA_VERSION = "1.0.0"


class ProjectFitPhaseHHandoffError(RuntimeError):
    """Fail-closed Project-Fit Phase-H handoff error."""


@dataclass(frozen=True, slots=True)
class ProjectFitPhaseHSourceBinding:
    """Exact admitted source-local authority population for one Source."""

    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    project_fit_fingerprint: str
    approved_input_ids: tuple[str, ...]
    approved_input_fingerprints: tuple[str, ...]
    approved_engineering_information_fingerprints: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectFitPhaseHHandoff:
    """Transient provenance-preserving multi-source Phase-H handoff."""

    schema_version: str
    project_id: str
    source_bindings: tuple[ProjectFitPhaseHSourceBinding, ...]
    approved_engineering_information_sets: tuple[object, ...]
    content_fingerprint: str

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(
            item.source_id
            for item in self.source_bindings
        )

    @property
    def project_fit_fingerprints(self) -> tuple[str, ...]:
        return tuple(
            item.project_fit_fingerprint
            for item in self.source_bindings
        )


def _fingerprint(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectFitPhaseHHandoffError(
            f"{label} must be a non-empty string."
        )
    return value


def _review_ref(item) -> tuple[str, str]:
    return (
        _require_text(
            getattr(item, "review_document_id", None),
            "Approved Input review_document_id",
        ),
        _require_text(
            getattr(item, "review_document_version_id", None),
            "Approved Input review_document_version_id",
        ),
    )


def create_project_fit_phase_h_handoff(
    *,
    project_fit_assessments: tuple,
    approved_input_manifests: tuple,
    approved_engineering_information_sets: tuple,
) -> ProjectFitPhaseHHandoff:
    """Create an exact non-authoring Phase-H handoff for admitted Sources."""

    if not isinstance(project_fit_assessments, tuple):
        raise ProjectFitPhaseHHandoffError(
            "project_fit_assessments must be a tuple."
        )
    if not isinstance(approved_input_manifests, tuple):
        raise ProjectFitPhaseHHandoffError(
            "approved_input_manifests must be a tuple."
        )
    if not isinstance(
        approved_engineering_information_sets,
        tuple,
    ):
        raise ProjectFitPhaseHHandoffError(
            "approved_engineering_information_sets must be a tuple."
        )
    if not approved_input_manifests:
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H handoff requires Approved Inputs."
        )

    for item in approved_input_manifests:
        try:
            validate_approved_input_manifest(item)
        except Exception as exc:
            raise ProjectFitPhaseHHandoffError(
                "Approved Input validation failed."
            ) from exc

        if getattr(item, "authority_state", None) != "active":
            raise ProjectFitPhaseHHandoffError(
                "Project-Fit Phase-H handoff accepts only active "
                "Approved Inputs."
            )

    project_ids = {
        getattr(item, "project_id", None)
        for item in approved_input_manifests
    }
    if len(project_ids) != 1:
        raise ProjectFitPhaseHHandoffError(
            "Approved Inputs must belong to exactly one Project."
        )
    project_id = _require_text(
        next(iter(project_ids)),
        "project_id",
    )

    source_ids = {
        getattr(item, "source_id", None)
        for item in approved_input_manifests
    }
    if len(source_ids) < 2:
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H handoff is only valid for a genuine "
            "multi-source active snapshot."
        )
    if None in source_ids:
        raise ProjectFitPhaseHHandoffError(
            "Approved Input source_id is invalid."
        )

    exact_fits = {}
    for source_id in sorted(source_ids):
        inputs = tuple(
            item
            for item in approved_input_manifests
            if item.source_id == source_id
        )

        source_sha256s = {
            item.source_sha256
            for item in inputs
        }
        processing_run_ids = {
            item.processing_run_id
            for item in inputs
        }
        attempt_ids = {
            item.attempt_id
            for item in inputs
        }

        if (
            len(source_sha256s) != 1
            or len(processing_run_ids) != 1
            or len(attempt_ids) != 1
        ):
            raise ProjectFitPhaseHHandoffError(
                "Active Approved Inputs for one Source must bind one exact "
                "Source / Processing Run / Attempt snapshot."
            )

        source_sha256 = next(iter(source_sha256s))
        processing_run_id = next(iter(processing_run_ids))
        attempt_id = next(iter(attempt_ids))

        matches = []
        for fit in project_fit_assessments:
            try:
                validate_project_fit_assessment(fit)
            except Exception as exc:
                raise ProjectFitPhaseHHandoffError(
                    "Project Fit validation failed."
                ) from exc

            if (
                fit.project_id == project_id
                and fit.source_id == source_id
                and fit.source_sha256 == source_sha256
                and fit.processing_run_id == processing_run_id
                and fit.attempt_id == attempt_id
            ):
                matches.append(fit)

        if len(matches) != 1:
            raise ProjectFitPhaseHHandoffError(
                "Exactly one admitted Project Fit assessment must bind "
                "each active Source / Run / Attempt snapshot."
            )

        fit = matches[0]
        try:
            gate_state = derive_project_fit_gate_state(fit)
        except Exception as exc:
            raise ProjectFitPhaseHHandoffError(
                "Project Fit gate state cannot be derived safely."
            ) from exc

        if gate_state != "admitted":
            raise ProjectFitPhaseHHandoffError(
                f"Project Fit does not admit Source {source_id}."
            )

        exact_fits[source_id] = fit

    expected_review_refs = {
        _review_ref(item)
        for item in approved_input_manifests
    }

    aei_by_review_ref = {}
    for aei in approved_engineering_information_sets:
        if getattr(aei, "project_id", None) != project_id:
            raise ProjectFitPhaseHHandoffError(
                "Approved Engineering Information belongs to another Project."
            )

        ref = (
            _require_text(
                getattr(aei, "review_document_id", None),
                "AEI review_document_id",
            ),
            _require_text(
                getattr(aei, "review_document_version_id", None),
                "AEI review_document_version_id",
            ),
        )
        if ref in aei_by_review_ref:
            raise ProjectFitPhaseHHandoffError(
                "More than one AEI set binds the same Review Workspace."
            )
        aei_by_review_ref[ref] = aei

    if set(aei_by_review_ref) != expected_review_refs:
        raise ProjectFitPhaseHHandoffError(
            "Source-local AEI coverage must exactly match the active "
            "Approved Input Review Workspaces."
        )

    active_by_id = {
        item.approved_input_id: item
        for item in approved_input_manifests
    }
    if len(active_by_id) != len(approved_input_manifests):
        raise ProjectFitPhaseHHandoffError(
            "Active Approved Input IDs must be unique."
        )

    for ref, aei in aei_by_review_ref.items():
        allowed_ids = {
            item.approved_input_id
            for item in approved_input_manifests
            if _review_ref(item) == ref
        }

        subject_ids = set()
        for subject in getattr(aei, "subjects", ()):
            approved_input_id = getattr(
                subject,
                "approved_input_id",
                None,
            )
            if approved_input_id not in allowed_ids:
                raise ProjectFitPhaseHHandoffError(
                    "AEI Subject does not bind an active Approved Input "
                    "from its exact source-local Review Workspace."
                )

            canonical_subject_id = _require_text(
                getattr(
                    subject,
                    "canonical_subject_id",
                    None,
                ),
                "AEI canonical_subject_id",
            )
            if canonical_subject_id in subject_ids:
                raise ProjectFitPhaseHHandoffError(
                    "AEI canonical Subject IDs must be unique within one "
                    "source-local Review Workspace."
                )
            subject_ids.add(canonical_subject_id)

        for relationship in getattr(aei, "relationships", ()):
            if (
                relationship.source_subject_id not in subject_ids
                or relationship.target_subject_id not in subject_ids
            ):
                raise ProjectFitPhaseHHandoffError(
                    "AEI Relationship must bind two Subjects from the same "
                    "source-local AEI set."
                )

    bindings = []
    for source_id in sorted(source_ids):
        inputs = tuple(
            sorted(
                (
                    item
                    for item in approved_input_manifests
                    if item.source_id == source_id
                ),
                key=lambda item: item.approved_input_id,
            )
        )
        fit = exact_fits[source_id]

        review_refs = {
            _review_ref(item)
            for item in inputs
        }
        aeis = tuple(
            aei_by_review_ref[ref]
            for ref in sorted(review_refs)
        )

        bindings.append(
            ProjectFitPhaseHSourceBinding(
                source_id=source_id,
                source_sha256=inputs[0].source_sha256,
                processing_run_id=inputs[0].processing_run_id,
                attempt_id=inputs[0].attempt_id,
                project_fit_fingerprint=(
                    fit.assessment_fingerprint
                ),
                approved_input_ids=tuple(
                    item.approved_input_id
                    for item in inputs
                ),
                approved_input_fingerprints=tuple(
                    item.content_fingerprint
                    for item in inputs
                ),
                approved_engineering_information_fingerprints=tuple(
                    sorted(
                        aei.content_fingerprint
                        for aei in aeis
                    )
                ),
            )
        )

    body = {
        "schema_version": PROJECT_FIT_PHASE_H_HANDOFF_SCHEMA_VERSION,
        "project_id": project_id,
        "source_bindings": [
            asdict(item)
            for item in bindings
        ],
    }

    return ProjectFitPhaseHHandoff(
        schema_version=PROJECT_FIT_PHASE_H_HANDOFF_SCHEMA_VERSION,
        project_id=project_id,
        source_bindings=tuple(bindings),
        approved_engineering_information_sets=tuple(
            aei_by_review_ref[ref]
            for ref in sorted(aei_by_review_ref)
        ),
        content_fingerprint=_fingerprint(body),
    )


def validate_project_fit_phase_h_handoff(
    handoff: ProjectFitPhaseHHandoff,
) -> None:
    if not isinstance(handoff, ProjectFitPhaseHHandoff):
        raise ProjectFitPhaseHHandoffError(
            "handoff must be a ProjectFitPhaseHHandoff."
        )

    if (
        handoff.schema_version
        != PROJECT_FIT_PHASE_H_HANDOFF_SCHEMA_VERSION
    ):
        raise ProjectFitPhaseHHandoffError(
            "Unsupported Project-Fit Phase-H handoff schema."
        )

    if len(handoff.source_bindings) < 2:
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H handoff must bind at least two Sources."
        )

    source_ids = tuple(
        item.source_id
        for item in handoff.source_bindings
    )
    if (
        source_ids != tuple(sorted(source_ids))
        or len(source_ids) != len(set(source_ids))
    ):
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H source bindings must be sorted and unique."
        )

    body = {
        "schema_version": handoff.schema_version,
        "project_id": handoff.project_id,
        "source_bindings": [
            asdict(item)
            for item in handoff.source_bindings
        ],
    }
    if _fingerprint(body) != handoff.content_fingerprint:
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H handoff fingerprint is invalid."
        )


def select_project_fit_active_inputs(
    approved_inputs: tuple,
    handoff: ProjectFitPhaseHHandoff,
) -> tuple:
    """Verify exact population; Project Fit never supersedes/filter inputs."""

    validate_project_fit_phase_h_handoff(handoff)

    expected = {
        (
            approved_input_id,
            approved_input_fingerprint,
        )
        for binding in handoff.source_bindings
        for approved_input_id, approved_input_fingerprint in zip(
            binding.approved_input_ids,
            binding.approved_input_fingerprints,
            strict=True,
        )
    }

    actual = {
        (
            item.approved_input_id,
            item.content_fingerprint,
        )
        for item in approved_inputs
    }

    if expected != actual:
        raise ProjectFitPhaseHHandoffError(
            "Current active Approved Inputs do not match the exact "
            "Project-Fit Phase-H handoff population."
        )

    return tuple(
        sorted(
            approved_inputs,
            key=lambda item: item.approved_input_id,
        )
    )


def validate_project_fit_phase_h_request(request) -> None:
    """Validate mutual exclusivity and exact active-input binding."""

    handoff = getattr(request, "project_fit_handoff", None)
    if handoff is None:
        return

    validate_project_fit_phase_h_handoff(handoff)

    if getattr(request, "project_authority_handoff", None) is not None:
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit and Project-Authority Phase-H handoffs are "
            "mutually exclusive."
        )

    if (
        getattr(
            request,
            "approved_engineering_information",
            None,
        )
        is not None
    ):
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H handoff must not be combined with one "
            "synthetic ApprovedEngineeringInformationSet."
        )

    if getattr(request, "project_id", None) != handoff.project_id:
        raise ProjectFitPhaseHHandoffError(
            "Phase-H request Project does not match Project-Fit handoff."
        )

    inputs = tuple(
        getattr(request, "approved_inputs", ())
    )
    if len({item.source_id for item in inputs}) < 2:
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Phase-H handoff requires a genuine multi-source "
            "request."
        )

    select_project_fit_active_inputs(inputs, handoff)

def project_fit_phase_h_subject_key(
    request,
    approved_input,
) -> str:
    """Return source-scoped identity for one Project-Fit multi-source input."""

    handoff = getattr(request, "project_fit_handoff", None)
    if handoff is None:
        return approved_input.stable_subject_key

    validate_project_fit_phase_h_request(request)

    approved_input_id = _require_text(
        getattr(approved_input, "approved_input_id", None),
        "Approved Input ID",
    )
    source_id = _require_text(
        getattr(approved_input, "source_id", None),
        "Approved Input source_id",
    )
    stable_subject_key = _require_text(
        getattr(approved_input, "stable_subject_key", None),
        "Approved Input stable_subject_key",
    )

    matches = tuple(
        binding
        for binding in handoff.source_bindings
        if (
            binding.source_id == source_id
            and approved_input_id in binding.approved_input_ids
        )
    )
    if len(matches) != 1:
        raise ProjectFitPhaseHHandoffError(
            "Approved Input has no unique Project-Fit Source binding."
        )

    binding = matches[0]
    by_id = dict(
        zip(
            binding.approved_input_ids,
            binding.approved_input_fingerprints,
            strict=True,
        )
    )
    if (
        by_id.get(approved_input_id)
        != getattr(approved_input, "content_fingerprint", None)
    ):
        raise ProjectFitPhaseHHandoffError(
            "Project-Fit Approved Input binding is stale."
        )

    return (
        "project_subject:"
        f"{source_id.lower()}:"
        f"{stable_subject_key}"
    )


def project_fit_phase_h_subject_key_for_source(
    request,
    *,
    source_id: str,
    stable_subject_key: str,
) -> str:
    """Resolve one source-local Subject key in a Project-Fit request."""

    handoff = getattr(request, "project_fit_handoff", None)
    if handoff is None:
        return stable_subject_key

    validate_project_fit_phase_h_request(request)

    source_id = _require_text(source_id, "source_id")
    stable_subject_key = _require_text(
        stable_subject_key,
        "stable_subject_key",
    )

    matches = tuple(
        item
        for item in request.approved_inputs
        if (
            item.source_id == source_id
            and item.stable_subject_key == stable_subject_key
        )
    )
    if len(matches) != 1:
        raise ProjectFitPhaseHHandoffError(
            "Source-local Subject key is not uniquely Project-Fit resolvable."
        )

    return project_fit_phase_h_subject_key(
        request,
        matches[0],
    )


def bind_generation_provenance_to_project_fit_handoff(
    provenance: ModelCandidateGenerationProvenance,
    handoff: ProjectFitPhaseHHandoff | None,
) -> ModelCandidateGenerationProvenance:
    """Bind exact Project-Fit multi-source provenance to Phase-H generation."""

    if handoff is None:
        return provenance

    validate_project_fit_phase_h_handoff(handoff)

    if not isinstance(
        provenance,
        ModelCandidateGenerationProvenance,
    ):
        raise ProjectFitPhaseHHandoffError(
            "Generation provenance has invalid type."
        )

    body = {
        "base_context_fingerprint": provenance.context_fingerprint,
        "project_fit_handoff_fingerprint": (
            handoff.content_fingerprint
        ),
        "project_fit_fingerprints": list(
            handoff.project_fit_fingerprints
        ),
        "source_approved_engineering_information_fingerprints": [
            fingerprint
            for binding in handoff.source_bindings
            for fingerprint in (
                binding.approved_engineering_information_fingerprints
            )
        ],
    }

    return replace(
        provenance,
        context_fingerprint=_fingerprint(body),
    )
