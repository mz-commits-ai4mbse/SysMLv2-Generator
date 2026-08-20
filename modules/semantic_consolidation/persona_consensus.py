"""Persona-aware consensus projection over element semantic subjects."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from .element_clustering import ElementSemanticProposal
from .types import SemanticConsolidationArtifact


@dataclass(frozen=True)
class PersonaElementPerspective:
    """One Persona perspective independent of raw run count."""

    persona_id: str
    proposal_refs: tuple[str, ...]
    run_indexes: tuple[int, ...]
    classification_options: tuple[str, ...]
    stable_classification: str | None
    intra_persona_instability: bool


@dataclass(frozen=True)
class ElementClassificationSupport:
    """Stable Persona support for one proposed classification."""

    classification: str
    persona_ids: tuple[str, ...]


@dataclass(frozen=True)
class ElementPersonaConsensus:
    """Read-only consensus evidence for one semantic element subject."""

    semantic_subject_id: str
    member_proposal_refs: tuple[str, ...]
    expected_persona_ids: tuple[str, ...]
    recognized_persona_ids: tuple[str, ...]
    recognition_count: int
    expected_persona_count: int
    full_recognition: bool
    perspectives: tuple[PersonaElementPerspective, ...]
    classification_support: tuple[ElementClassificationSupport, ...]
    classification_variance: bool
    intra_persona_instability: bool
    unanimous_stable_classification: str | None
    human_approval: bool


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticConsolidationValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise SemanticConsolidationValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _expected_personas(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise SemanticConsolidationIntegrityError(
            "expected_persona_ids must contain at least one Persona."
        )
    checked = tuple(_text(value, label="persona_id") for value in values)
    if checked != tuple(sorted(checked)):
        raise SemanticConsolidationValidationError(
            "expected_persona_ids must use deterministic sorted order."
        )
    if len(checked) != len(set(checked)):
        raise SemanticConsolidationIntegrityError(
            "expected_persona_ids must be unique."
        )
    return checked


def project_element_persona_consensus(
    *,
    artifact: SemanticConsolidationArtifact,
    proposals: tuple[ElementSemanticProposal, ...],
    expected_persona_ids: tuple[str, ...],
) -> tuple[ElementPersonaConsensus, ...]:
    """Project Persona-level recognition/classification evidence.

    Repeated runs from one Persona never create additional votes. Divergent
    classifications inside one Persona are retained as intra-Persona instability.
    The projection is processing evidence only and therefore hard-codes
    ``human_approval=False``.
    """

    expected = _expected_personas(expected_persona_ids)
    expected_set = set(expected)

    proposal_by_ref: dict[str, ElementSemanticProposal] = {}
    for proposal in proposals:
        if not isinstance(proposal, ElementSemanticProposal):
            raise SemanticConsolidationValidationError(
                "proposals contains an invalid element proposal."
            )
        if proposal.proposal_ref in proposal_by_ref:
            raise SemanticConsolidationIntegrityError(
                "proposals must not repeat a proposal_ref."
            )
        proposal_by_ref[proposal.proposal_ref] = proposal

    artifact_bindings = {
        proposal.proposal_ref: proposal for proposal in artifact.proposals
    }
    if set(artifact_bindings) != set(proposal_by_ref):
        raise SemanticConsolidationIntegrityError(
            "Consensus proposal content must match the exact consolidation "
            "artifact proposal set."
        )

    for proposal_ref, binding in artifact_bindings.items():
        proposal = proposal_by_ref[proposal_ref]
        if binding.proposal_kind != "element":
            raise SemanticConsolidationIntegrityError(
                "Element Persona consensus cannot consume relationship proposals."
            )
        exact_tuple = (
            binding.agent_id,
            binding.persona_id,
            binding.run_index,
            binding.upstream_artifact_ref,
            binding.evidence_refs,
        )
        content_tuple = (
            proposal.agent_id,
            proposal.persona_id,
            proposal.run_index,
            proposal.upstream_artifact_ref,
            proposal.evidence_refs,
        )
        if exact_tuple != content_tuple:
            raise SemanticConsolidationIntegrityError(
                "Consensus proposal provenance does not match the exact "
                f"artifact binding: {proposal_ref!r}."
            )
        if proposal.persona_id not in expected_set:
            raise SemanticConsolidationIntegrityError(
                "Proposal references a Persona outside expected_persona_ids: "
                f"{proposal.persona_id!r}."
            )

    results: list[ElementPersonaConsensus] = []
    for subject in artifact.subjects:
        if subject.proposal_kind != "element":
            continue
        subject_proposals = tuple(
            proposal_by_ref[proposal_ref]
            for proposal_ref in subject.member_proposal_refs
        )

        by_persona: dict[str, list[ElementSemanticProposal]] = {}
        for proposal in subject_proposals:
            by_persona.setdefault(proposal.persona_id, []).append(proposal)

        perspectives: list[PersonaElementPerspective] = []
        stable_support: dict[str, list[str]] = {}
        any_instability = False

        for persona_id in sorted(by_persona):
            persona_proposals = sorted(
                by_persona[persona_id],
                key=lambda item: (item.run_index, item.proposal_ref),
            )
            classifications = tuple(
                sorted(
                    {
                        proposal.proposed_element_type
                        for proposal in persona_proposals
                    }
                )
            )
            unstable = len(classifications) > 1
            any_instability = any_instability or unstable
            stable = classifications[0] if len(classifications) == 1 else None
            if stable is not None:
                stable_support.setdefault(stable, []).append(persona_id)
            perspectives.append(
                PersonaElementPerspective(
                    persona_id=persona_id,
                    proposal_refs=tuple(
                        sorted(proposal.proposal_ref for proposal in persona_proposals)
                    ),
                    run_indexes=tuple(
                        sorted({proposal.run_index for proposal in persona_proposals})
                    ),
                    classification_options=classifications,
                    stable_classification=stable,
                    intra_persona_instability=unstable,
                )
            )

        support = tuple(
            ElementClassificationSupport(
                classification=classification,
                persona_ids=tuple(sorted(persona_ids)),
            )
            for classification, persona_ids in sorted(stable_support.items())
        )
        recognized = tuple(sorted(by_persona))
        stable_classifications = tuple(item.classification for item in support)
        classification_variance = len(stable_classifications) > 1

        unanimous_stable: str | None = None
        if (
            len(recognized) == len(expected)
            and not any_instability
            and len(stable_classifications) == 1
        ):
            unanimous_stable = stable_classifications[0]

        results.append(
            ElementPersonaConsensus(
                semantic_subject_id=subject.semantic_subject_id,
                member_proposal_refs=subject.member_proposal_refs,
                expected_persona_ids=expected,
                recognized_persona_ids=recognized,
                recognition_count=len(recognized),
                expected_persona_count=len(expected),
                full_recognition=(len(recognized) == len(expected)),
                perspectives=tuple(perspectives),
                classification_support=support,
                classification_variance=classification_variance,
                intra_persona_instability=any_instability,
                unanimous_stable_classification=unanimous_stable,
                human_approval=False,
            )
        )

    return tuple(sorted(results, key=lambda item: item.semantic_subject_id))
