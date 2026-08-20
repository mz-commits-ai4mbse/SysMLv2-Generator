"""Lossless Human-Review admissibility over structured P9 Agent outputs.

This adapter preserves strict artifact/integrity validation while converting
reviewable semantic contract deviations into explicit open questions.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .evidence_adapter import P9ReviewEvidenceSet
from .p9_proposal_adapter import (
    P9_ELEMENT_TYPES,
    P9_SOURCE_ASSIGNMENT_TYPES,
    P9ElementProposal,
    P9ReviewQuestionProposal,
    P9StructuredProposalSet,
    _adapt_element_proposals,
    _adapt_relationship_proposals,
    _canonical_fingerprint,
    _identifier,
    _is_derivation_reference,
    _load_agent_wrapper,
    _parse_derivation_output,
    _reference_key,
    _validated_repository_root,
)


def _derivation_execution_identity(
    wrapper: dict[str, object],
) -> tuple[str | None, str, str, int]:
    """Return one derivation execution identity within a Processing Run.

    Source-anchored execution intentionally reuses the same Agent/persona/run
    identity for different Source Analysis Units. The SAU dimension therefore
    participates in execution identity. Legacy non-SAU outputs retain the old
    behavior through a ``None`` SAU component.
    """

    source_analysis_unit_id = wrapper.get(
        "source_analysis_unit_id"
    )
    if (
        source_analysis_unit_id is not None
        and not isinstance(source_analysis_unit_id, str)
    ):
        raise ReviewValidationError(
            "source_analysis_unit_id must be a string when present."
        )

    agent_id = wrapper["agent_id"]
    persona_id = wrapper["persona_id"]
    run_index = wrapper["run_index"]

    if not isinstance(agent_id, str):
        raise ReviewValidationError("agent_id must be a string.")
    if not isinstance(persona_id, str):
        raise ReviewValidationError("persona_id must be a string.")
    if not isinstance(run_index, int):
        raise ReviewValidationError("run_index must be an integer.")

    return (
        source_analysis_unit_id,
        agent_id,
        persona_id,
        run_index,
    )


def adapt_p9_agent_proposals_for_review(
    p9_evidence: object,
    *,
    repository_root: Path | str,
) -> P9StructuredProposalSet:
    """Adapt P9 outputs without turning semantic uncertainty into a hard stop."""

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )

    root = _validated_repository_root(repository_root)

    derivation_references = tuple(
        reference
        for reference in p9_evidence.agent_output_references
        if _is_derivation_reference(reference)
    )

    if not derivation_references:
        raise ReviewReferenceError(
            "P9 Review Evidence contains no structured "
            "derivation-assessment Agent Outputs."
        )

    execution_keys: set[
        tuple[str | None, str, str, int]
    ] = set()
    element_proposals: list[P9ElementProposal] = []
    relationship_proposals = []
    review_questions: list[P9ReviewQuestionProposal] = []

    for reference in sorted(
        derivation_references,
        key=_reference_key,
    ):
        wrapper = _load_agent_wrapper(
            reference,
            repository_root=root,
            p9_evidence=p9_evidence,
        )

        execution_key = _derivation_execution_identity(
            wrapper
        )
        if execution_key in execution_keys:
            raise ReviewIntegrityError(
                "P9 contains duplicate derivation Agent "
                "execution identity."
            )
        execution_keys.add(execution_key)

        output = _parse_derivation_output(
            wrapper["output_text"]
        )

        (
            artifact_elements,
            element_questions,
        ) = _adapt_elements_for_review(
            output["candidate_model_elements"],
            reference=reference,
            agent_id=wrapper["agent_id"],
            persona_id=wrapper["persona_id"],
        )

        (
            artifact_relationships,
            relationship_questions,
        ) = _adapt_relationships_for_review(
            output["explicit_source_links"],
            reference=reference,
            agent_id=wrapper["agent_id"],
            persona_id=wrapper["persona_id"],
            element_proposals=artifact_elements,
        )

        element_proposals.extend(artifact_elements)
        relationship_proposals.extend(
            artifact_relationships
        )
        review_questions.extend(element_questions)
        review_questions.extend(relationship_questions)

    if not element_proposals and not review_questions:
        raise ReviewIntegrityError(
            "Structured P9 derivation evidence contains "
            "neither candidate model elements nor reviewable "
            "semantic uncertainty."
        )

    return P9StructuredProposalSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        processing_run_id=p9_evidence.processing_run_id,
        attempt_id=p9_evidence.attempt_id,
        element_proposals=tuple(
            sorted(
                element_proposals,
                key=lambda item: (
                    item.stable_subject_key,
                    item.proposal_reference
                    .artifact_reference.artifact_id,
                    item.candidate_id,
                ),
            )
        ),
        relationship_proposals=tuple(
            sorted(
                relationship_proposals,
                key=lambda item: (
                    item.stable_subject_key,
                    item.proposal_reference
                    .artifact_reference.artifact_id,
                    item.link_id,
                ),
            )
        ),
        review_question_proposals=tuple(
            sorted(
                review_questions,
                key=lambda item: (
                    item.stable_subject_key,
                    item.artifact_reference.artifact_id,
                    item.evidence_locator,
                    item.question_id,
                ),
            )
        ),
    )


def _adapt_elements_for_review(
    values: object,
    *,
    reference,
    agent_id: str,
    persona_id: str,
) -> tuple[
    tuple[P9ElementProposal, ...],
    tuple[P9ReviewQuestionProposal, ...],
]:
    """Normalize only enumerated semantic labels that Human Review can resolve."""

    if not isinstance(values, list):
        raise ReviewValidationError(
            "candidate_model_elements must be a JSON array."
        )

    normalized_values = deepcopy(values)
    issue_specs: list[dict[str, object]] = []

    for candidate_index, (
        raw_candidate,
        normalized_candidate,
    ) in enumerate(zip(values, normalized_values)):
        if not isinstance(raw_candidate, dict):
            # The strict adapter remains authoritative for structural shape.
            continue

        candidate_id = raw_candidate.get("candidate_id")
        candidate_name = raw_candidate.get("candidate_name")
        raw_element_type = raw_candidate.get("element_type")

        if (
            isinstance(raw_element_type, str)
            and raw_element_type
            and raw_element_type not in P9_ELEMENT_TYPES
        ):
            normalized_candidate["element_type"] = "other"
            issue_specs.append(
                {
                    "kind": "unsupported_element_type",
                    "candidate_index": candidate_index,
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "raw_value": raw_element_type,
                    "normalized_value": "other",
                    "assignment_index": None,
                }
            )

        raw_assignments = raw_candidate.get(
            "assigned_source_information"
        )
        normalized_assignments = normalized_candidate.get(
            "assigned_source_information"
        )
        if not (
            isinstance(raw_assignments, list)
            and isinstance(normalized_assignments, list)
        ):
            continue

        for assignment_index, (
            raw_assignment,
            normalized_assignment,
        ) in enumerate(
            zip(raw_assignments, normalized_assignments)
        ):
            if not isinstance(raw_assignment, dict):
                continue

            raw_assignment_type = raw_assignment.get(
                "assignment_type"
            )
            if (
                isinstance(raw_assignment_type, str)
                and raw_assignment_type
                and raw_assignment_type
                not in P9_SOURCE_ASSIGNMENT_TYPES
            ):
                normalized_assignment[
                    "assignment_type"
                ] = "unclear_assignment"
                issue_specs.append(
                    {
                        "kind": "unsupported_assignment_type",
                        "candidate_index": candidate_index,
                        "candidate_id": candidate_id,
                        "candidate_name": candidate_name,
                        "raw_value": raw_assignment_type,
                        "normalized_value": "unclear_assignment",
                        "assignment_index": assignment_index,
                    }
                )

    proposals = _adapt_element_proposals(
        normalized_values,
        reference=reference,
        agent_id=agent_id,
        persona_id=persona_id,
    )

    raw_by_id = {}
    for raw_candidate in values:
        if isinstance(raw_candidate, dict):
            candidate_id = raw_candidate.get("candidate_id")
            if isinstance(candidate_id, str):
                raw_by_id[candidate_id] = raw_candidate

    restored: list[P9ElementProposal] = []
    by_id: dict[str, P9ElementProposal] = {}

    for proposal in proposals:
        raw_candidate = raw_by_id.get(
            proposal.candidate_id
        )
        if raw_candidate is None:
            raise ReviewIntegrityError(
                "Normalized P9 element proposal cannot be "
                "rebound to its exact raw candidate."
            )

        professional_content = {
            key: raw_candidate[key]
            for key in sorted(raw_candidate)
            if key != "candidate_id"
        }
        raw_element_type = raw_candidate.get(
            "element_type"
        )
        raw_type_for_consensus = (
            raw_element_type
            if (
                isinstance(raw_element_type, str)
                and raw_element_type
                != proposal.element_type
            )
            else None
        )

        restored_proposal = replace(
            proposal,
            proposal_reference=replace(
                proposal.proposal_reference,
                proposal_content_fingerprint=(
                    _canonical_fingerprint(
                        professional_content
                    )
                ),
            ),
            raw_element_type=raw_type_for_consensus,
        )
        restored.append(restored_proposal)
        by_id[proposal.candidate_id] = (
            restored_proposal
        )

    questions = []
    for spec in issue_specs:
        candidate_id = spec["candidate_id"]
        if (
            not isinstance(candidate_id, str)
            or candidate_id not in by_id
        ):
            # Structural candidate identity is not review-normalizable.
            # The strict adapter above will already have raised in this case.
            raise ReviewIntegrityError(
                "Reviewable enum uncertainty lacks a valid "
                "candidate identity."
            )

        proposal = by_id[candidate_id]
        raw_candidate = raw_by_id[candidate_id]
        kind = str(spec["kind"])
        raw_value = str(spec["raw_value"])
        normalized_value = str(
            spec["normalized_value"]
        )

        if kind == "unsupported_element_type":
            source_statement = _first_source_statement(
                raw_candidate,
                fallback=proposal.description,
            )
            evidence_locator = (
                "output_text:/candidate_model_elements/"
                f"{candidate_id}/element_type"
            )
            evidence_payload = {
                "candidate_id": candidate_id,
                "element_type": raw_value,
            }
            title = (
                "Review element classification: "
                f"{proposal.candidate_name}"
            )
            review_question = (
                "The Agent used unsupported element_type "
                f"{raw_value!r}. The entity remains reviewable "
                "with the neutral draft classification 'other'. "
                "Which engineering classification should be used?"
            )
            rationale = (
                "Entity existence remains source-supported; only "
                "its model classification requires Human Review."
            )
            anchor = proposal.candidate_name
        else:
            assignment_index = spec["assignment_index"]
            if not isinstance(assignment_index, int):
                raise ReviewIntegrityError(
                    "Assignment review uncertainty lacks "
                    "its exact assignment index."
                )
            raw_assignments = raw_candidate[
                "assigned_source_information"
            ]
            raw_assignment = raw_assignments[
                assignment_index
            ]
            source_statement = str(
                raw_assignment["source_statement"]
            )
            source_info_id = str(
                raw_assignment["source_info_id"]
            )
            evidence_locator = (
                "output_text:/candidate_model_elements/"
                f"{candidate_id}/assigned_source_information/"
                f"{assignment_index}/assignment_type"
            )
            evidence_payload = {
                "candidate_id": candidate_id,
                "source_info_id": source_info_id,
                "source_statement": source_statement,
                "assignment_type": raw_value,
            }
            title = (
                "Review source assignment: "
                f"{proposal.candidate_name}"
            )
            review_question = (
                "The Agent used unsupported assignment_type "
                f"{raw_value!r}. The review draft uses "
                "'unclear_assignment' without treating that "
                "normalization as Human approval. Which source "
                "assignment classification is correct?"
            )
            rationale = (
                "The exact Agent value is preserved as review "
                "evidence while the admissible draft remains "
                "explicitly uncertain."
            )
            anchor = (
                f"{proposal.candidate_name}|"
                f"{source_statement}"
            )

        questions.append(
            _create_review_question(
                reference=reference,
                agent_id=agent_id,
                persona_id=persona_id,
                issue_code=kind,
                subject_anchor=anchor,
                raw_value=raw_value,
                normalized_value=normalized_value,
                title=title,
                review_question=review_question,
                source_basis=proposal.source_basis,
                source_statement=source_statement,
                raw_fragment=raw_candidate,
                evidence_locator=evidence_locator,
                evidence_payload=evidence_payload,
                rationale_summary=rationale,
            )
        )

    return tuple(restored), tuple(questions)


def _adapt_relationships_for_review(
    values: object,
    *,
    reference,
    agent_id: str,
    persona_id: str,
    element_proposals: tuple[P9ElementProposal, ...],
):
    """Preserve unresolved source-supported links as Human Review questions."""

    if not isinstance(values, list):
        raise ReviewValidationError(
            "explicit_source_links must be a JSON array."
        )

    relationships = []
    questions = []
    link_ids: set[str] = set()

    for raw_link in values:
        if isinstance(raw_link, dict):
            link_id_value = raw_link.get("link_id")
        else:
            link_id_value = None

        # Validate ID before the per-link strict adapter so duplicate IDs
        # remain a hard integrity failure even though each link is adapted
        # independently.
        link_id = _identifier(
            link_id_value,
            "link_id",
        )
        if link_id in link_ids:
            raise ReviewIntegrityError(
                "Link IDs must be unique within one "
                "derivation Agent Output."
            )
        link_ids.add(link_id)

        try:
            adapted = _adapt_relationship_proposals(
                [raw_link],
                reference=reference,
                agent_id=agent_id,
                persona_id=persona_id,
                element_proposals=element_proposals,
            )
        except ReviewReferenceError as exc:
            questions.append(
                _relationship_question(
                    raw_link,
                    reference=reference,
                    agent_id=agent_id,
                    persona_id=persona_id,
                    reason=str(exc),
                )
            )
            continue
        except ReviewIntegrityError as exc:
            if not str(exc).startswith(
                "Explicit source link candidate name is ambiguous"
            ):
                raise
            questions.append(
                _relationship_question(
                    raw_link,
                    reference=reference,
                    agent_id=agent_id,
                    persona_id=persona_id,
                    reason=str(exc),
                )
            )
            continue

        relationships.extend(adapted)

    return tuple(relationships), tuple(questions)


def _relationship_question(
    raw_link: object,
    *,
    reference,
    agent_id: str,
    persona_id: str,
    reason: str,
) -> P9ReviewQuestionProposal:
    if not isinstance(raw_link, dict):
        raise ReviewValidationError(
            "explicit source link must be a JSON object."
        )

    link_id = str(raw_link["link_id"])
    source_value = str(
        raw_link["source_element_candidate"]
    )
    target_value = str(
        raw_link["target_element_candidate"]
    )
    link_type = str(raw_link["link_type"])
    source_statement = str(
        raw_link["source_statement"]
    )
    source_basis = tuple(raw_link["source_basis"])

    raw_value = (
        f"{source_value} --{link_type}--> {target_value}"
    )
    evidence_locator = (
        "output_text:/explicit_source_links/"
        f"{link_id}"
    )

    return _create_review_question(
        reference=reference,
        agent_id=agent_id,
        persona_id=persona_id,
        issue_code="unresolved_relationship_endpoint",
        subject_anchor=(
            f"{source_value}|{link_type}|"
            f"{target_value}|{source_statement}"
        ),
        raw_value=raw_value,
        normalized_value="unresolved",
        title=(
            "Resolve relationship endpoints: "
            f"{source_value} {link_type} {target_value}"
        ),
        review_question=(
            "This source-supported relationship cannot be "
            "bound unambiguously to the current element "
            "candidates. Which element(s) should the endpoints "
            "refer to, or should an explicit source-supported "
            "element be created during Human Review?"
        ),
        source_basis=source_basis,
        source_statement=source_statement,
        raw_fragment=raw_link,
        evidence_locator=evidence_locator,
        evidence_payload=raw_link,
        rationale_summary=(
            "The relationship evidence is retained for Human "
            f"Review instead of being discarded. Adapter detail: {reason}"
        ),
    )


def _create_review_question(
    *,
    reference,
    agent_id: str,
    persona_id: str,
    issue_code: str,
    subject_anchor: str,
    raw_value: str,
    normalized_value: str,
    title: str,
    review_question: str,
    source_basis: tuple[str, ...],
    source_statement: str,
    raw_fragment: object,
    evidence_locator: str,
    evidence_payload: object,
    rationale_summary: str,
) -> P9ReviewQuestionProposal:
    stable_subject_key = _question_stable_subject_key(
        issue_code=issue_code,
        subject_anchor=subject_anchor,
        raw_value=raw_value,
    )

    occurrence_identity = "|".join(
        (
            reference.artifact_id,
            evidence_locator,
            stable_subject_key,
        )
    )
    question_digest = hashlib.sha256(
        occurrence_identity.encode("utf-8")
    ).hexdigest()[:16].upper()

    return P9ReviewQuestionProposal(
        stable_subject_key=stable_subject_key,
        question_id=f"RQ_{question_digest}",
        issue_code=issue_code,
        title=title,
        review_question=review_question,
        raw_value=raw_value,
        normalized_value=normalized_value,
        source_basis=tuple(source_basis),
        source_statement=source_statement,
        raw_fragment_json=_canonical_json(
            raw_fragment
        ),
        artifact_reference=reference,
        agent_id=agent_id,
        persona_id=persona_id,
        evidence_locator=evidence_locator,
        evidence_content_fingerprint=(
            _canonical_fingerprint(
                evidence_payload
            )
        ),
        rationale_summary=rationale_summary,
    )


def _question_stable_subject_key(
    *,
    issue_code: str,
    subject_anchor: str,
    raw_value: str,
) -> str:
    normalized_issue = _stable_fragment(issue_code)
    normalized_anchor = _stable_fragment(
        subject_anchor
    )
    normalized_raw = _stable_fragment(raw_value)

    semantic_identity = "|".join(
        (
            normalized_issue,
            normalized_anchor,
            normalized_raw,
        )
    )
    digest = hashlib.sha256(
        semantic_identity.encode("utf-8")
    ).hexdigest()[:20]

    return (
        f"open_question:{normalized_issue}:"
        f"{normalized_anchor[:80]}:{digest}"
    )


def _stable_fragment(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(value),
    )
    normalized = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(
        r"[^a-z0-9._:-]+",
        "-",
        normalized,
    )
    normalized = re.sub(r"-+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "unknown"


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _first_source_statement(
    raw_candidate: dict,
    *,
    fallback: str,
) -> str:
    assignments = raw_candidate.get(
        "assigned_source_information"
    )
    if isinstance(assignments, list):
        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue
            statement = assignment.get(
                "source_statement"
            )
            if isinstance(statement, str) and statement:
                return statement
    return fallback
