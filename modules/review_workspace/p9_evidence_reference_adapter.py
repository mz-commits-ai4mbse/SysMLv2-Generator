"""Construct exact P9 source and consensus evidence references."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from modules.project_processing import (
    ProcessingArtifactReference,
    ProcessingValidationError,
    validate_processing_artifact_reference,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .evidence_adapter import (
    AGENTIC_INGESTION_STAGE,
    P9ReviewEvidenceSet,
)
from .p9_proposal_adapter import (
    DERIVATION_STAGE_DIRECTORY,
    DERIVATION_TEAM_ID,
    P9ElementProposal,
    P9RelationshipProposal,
    P9StructuredProposalSet,
)
from .types import ReviewEvidenceReference


CONSENSUS_EVIDENCE_ROLE = "agent_consensus"
SOURCE_EVIDENCE_ROLE = "agent_source_evidence"

_CONSENSUS_REPORT_FIELDS = frozenset(
    {
        "consensus_report_id",
        "team_id",
        "task_name",
        "created_at",
        "total_agents",
        "agent_ids",
        "agent_labels",
        "summary",
        "groups",
    }
)

_CONSENSUS_SUMMARY_FIELDS = frozenset(
    {
        "total_groups",
        "full_agreement",
        "majority_agreement",
        "majority_with_disagreement",
        "minority_interpretation",
        "conflict",
        "review_required",
    }
)

_CONSENSUS_GROUP_FIELDS = frozenset(
    {
        "group_key",
        "item_type",
        "agreement_level",
        "total_agents",
        "supporting_agents",
        "value_distribution",
        "representative_value",
        "review_required",
        "reason",
        "agent_values",
    }
)

_CONSENSUS_AGREEMENT_LEVELS = frozenset(
    {
        "full_agreement",
        "majority_agreement",
        "majority_with_disagreement",
        "minority_interpretation",
        "conflict",
    }
)

_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,239}$"
)


@dataclass(frozen=True, slots=True)
class P9ConsensusEvidenceFact:
    """Exact filter fact for one structured Consensus evidence fragment."""

    artifact_id: str
    evidence_locator: str
    evidence_content_fingerprint: str
    agreement_level: str
    review_required: bool


@dataclass(frozen=True, slots=True)
class P9SubjectEvidence:
    """Exact P9 evidence associated with one stable review subject."""

    stable_subject_key: str
    review_item_kind: str
    source_evidence_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]
    consensus_evidence_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]


@dataclass(frozen=True, slots=True)
class P9StructuredEvidenceSet:
    """All P9 evidence references required for Review Item construction."""

    project_id: str
    source_id: str
    processing_run_id: str
    attempt_id: str
    subject_evidence: tuple[P9SubjectEvidence, ...]

    def evidence_for_subject(
        self,
        stable_subject_key: str,
    ) -> P9SubjectEvidence:
        """Return evidence for one exact stable subject."""

        matches = tuple(
            record
            for record in self.subject_evidence
            if record.stable_subject_key
            == stable_subject_key
        )

        if not matches:
            raise ReviewReferenceError(
                "No P9 evidence exists for stable subject: "
                f"{stable_subject_key!r}."
            )

        if len(matches) != 1:
            raise ReviewIntegrityError(
                "P9 subject evidence identities must be unique."
            )

        return matches[0]


def construct_p9_evidence_references(
    p9_evidence: object,
    structured_proposals: object,
    *,
    repository_root: Path | str,
) -> P9StructuredEvidenceSet:
    """Construct source and consensus evidence for P9 proposals.

    Relationships currently receive no Consensus Evidence because the
    existing Consensus Analyzer does not create explicit-link groups.
    """

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )

    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a "
            "P9StructuredProposalSet."
        )

    root = _validated_repository_root(repository_root)

    _validate_proposal_set_identity(
        p9_evidence,
        structured_proposals,
    )
    _validate_proposal_artifact_membership(
        p9_evidence,
        structured_proposals,
    )

    consensus_reference = (
        _select_derivation_consensus_reference(
            p9_evidence
        )
    )

    consensus_report = _load_consensus_report(
        consensus_reference,
        repository_root=root,
        p9_evidence=p9_evidence,
    )

    _validate_consensus_agents(
        consensus_report,
        structured_proposals,
    )

    source_references = _construct_source_references(
        structured_proposals
    )
    consensus_references = (
        _construct_consensus_references(
            consensus_report,
            consensus_reference=consensus_reference,
            structured_proposals=structured_proposals,
        )
    )

    item_kinds: dict[str, str] = {}

    for proposal in (
        structured_proposals.element_proposals
    ):
        _register_subject_kind(
            item_kinds,
            proposal.stable_subject_key,
            "element",
        )

    for proposal in (
        structured_proposals.relationship_proposals
    ):
        _register_subject_kind(
            item_kinds,
            proposal.stable_subject_key,
            "relationship",
        )

    records = tuple(
        P9SubjectEvidence(
            stable_subject_key=stable_subject_key,
            review_item_kind=item_kinds[
                stable_subject_key
            ],
            source_evidence_references=tuple(
                sorted(
                    source_references.get(
                        stable_subject_key,
                        (),
                    ),
                    key=_evidence_reference_key,
                )
            ),
            consensus_evidence_references=tuple(
                sorted(
                    consensus_references.get(
                        stable_subject_key,
                        (),
                    ),
                    key=_evidence_reference_key,
                )
            ),
        )
        for stable_subject_key in sorted(item_kinds)
    )

    for record in records:
        if not record.source_evidence_references:
            raise ReviewIntegrityError(
                "Every structured P9 subject requires "
                "at least one Source Evidence Reference."
            )

        if (
            record.review_item_kind == "element"
            and len(
                record.consensus_evidence_references
            )
            != 1
        ):
            raise ReviewIntegrityError(
                "Every P9 element subject requires exactly "
                "one Consensus Evidence Reference."
            )

        if (
            record.review_item_kind == "relationship"
            and record.consensus_evidence_references
        ):
            raise ReviewIntegrityError(
                "Relationship Consensus Evidence must not "
                "be invented while explicit links are absent "
                "from the Consensus Analyzer."
            )

    return P9StructuredEvidenceSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        processing_run_id=(
            p9_evidence.processing_run_id
        ),
        attempt_id=p9_evidence.attempt_id,
        subject_evidence=records,
    )



def load_p9_consensus_evidence_facts(
    p9_evidence: object,
    structured_proposals: object,
    *,
    repository_root: Path | str,
) -> tuple[P9ConsensusEvidenceFact, ...]:
    """Load exact candidate-element Consensus facts for G6 filtering."""

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )
    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a P9StructuredProposalSet."
        )

    root = _validated_repository_root(
        repository_root
    )
    _validate_proposal_set_identity(
        p9_evidence,
        structured_proposals,
    )
    _validate_proposal_artifact_membership(
        p9_evidence,
        structured_proposals,
    )

    reference = _select_derivation_consensus_reference(
        p9_evidence
    )
    report = _load_consensus_report(
        reference,
        repository_root=root,
        p9_evidence=p9_evidence,
    )
    _validate_consensus_agents(
        report,
        structured_proposals,
    )

    facts = []
    seen = set()

    for index, raw_group in enumerate(
        report["groups"]
    ):
        group = _validate_consensus_group(
            raw_group,
            expected_total_agents=report["total_agents"],
            report_agent_ids=tuple(
                report["agent_ids"]
            ),
        )
        if group["item_type"] != "candidate_model_element":
            continue

        key = group["group_key"]
        if key in seen:
            raise ReviewIntegrityError(
                "Derivation Consensus Report contains duplicate "
                "candidate-model-element groups."
            )
        seen.add(key)

        facts.append(
            P9ConsensusEvidenceFact(
                artifact_id=reference.artifact_id,
                evidence_locator=f"/groups/{index}",
                evidence_content_fingerprint=(
                    _canonical_fingerprint(group)
                ),
                agreement_level=group["agreement_level"],
                review_required=group["review_required"],
            )
        )

    return tuple(facts)

def _construct_source_references(
    proposals: P9StructuredProposalSet,
) -> dict[
    str,
    list[ReviewEvidenceReference],
]:
    result: dict[
        str,
        list[ReviewEvidenceReference],
    ] = {}

    for proposal in proposals.element_proposals:
        payload = {
            "source_basis": list(
                proposal.source_basis
            ),
            "source_assignments": [
                {
                    "source_info_id": (
                        assignment.source_info_id
                    ),
                    "source_statement": (
                        assignment.source_statement
                    ),
                    "assignment_type": (
                        assignment.assignment_type
                    ),
                    "confidence": (
                        assignment.confidence
                    ),
                }
                for assignment
                in proposal.source_assignments
            ],
        }

        reference = ReviewEvidenceReference(
            artifact_reference=(
                proposal.proposal_reference
                .artifact_reference
            ),
            evidence_role=SOURCE_EVIDENCE_ROLE,
            evidence_locator=(
                "output_text:/candidate_model_elements/"
                f"{proposal.candidate_id}/source_evidence"
            ),
            evidence_content_fingerprint=(
                _canonical_fingerprint(payload)
            ),
        )

        result.setdefault(
            proposal.stable_subject_key,
            [],
        ).append(reference)

    for proposal in proposals.relationship_proposals:
        payload = {
            "source_basis": list(
                proposal.source_basis
            ),
            "source_statement": (
                proposal.source_statement
            ),
        }

        reference = ReviewEvidenceReference(
            artifact_reference=(
                proposal.proposal_reference
                .artifact_reference
            ),
            evidence_role=SOURCE_EVIDENCE_ROLE,
            evidence_locator=(
                "output_text:/explicit_source_links/"
                f"{proposal.link_id}/source_evidence"
            ),
            evidence_content_fingerprint=(
                _canonical_fingerprint(payload)
            ),
        )

        result.setdefault(
            proposal.stable_subject_key,
            [],
        ).append(reference)

    _require_unique_evidence_references(result)

    return result


def _construct_consensus_references(
    report: dict[str, Any],
    *,
    consensus_reference: ProcessingArtifactReference,
    structured_proposals: P9StructuredProposalSet,
) -> dict[
    str,
    list[ReviewEvidenceReference],
]:
    expected_subjects: dict[str, str] = {}

    for proposal in (
        structured_proposals.element_proposals
    ):
        group_key = _element_consensus_group_key(
            proposal
        )
        previous = expected_subjects.get(group_key)

        if (
            previous is not None
            and previous
            != proposal.stable_subject_key
        ):
            raise ReviewIntegrityError(
                "Distinct stable element subjects collapse "
                "to the same Consensus group key."
            )

        expected_subjects[group_key] = (
            proposal.stable_subject_key
        )

    result: dict[
        str,
        list[ReviewEvidenceReference],
    ] = {}
    seen_group_keys: set[str] = set()

    groups = report["groups"]

    for index, raw_group in enumerate(groups):
        group = _validate_consensus_group(
            raw_group,
            expected_total_agents=(
                report["total_agents"]
            ),
            report_agent_ids=tuple(
                report["agent_ids"]
            ),
        )

        if group["item_type"] != (
            "candidate_model_element"
        ):
            continue

        group_key = group["group_key"]

        if group_key in seen_group_keys:
            raise ReviewIntegrityError(
                "Derivation Consensus Report contains "
                "a duplicate candidate-model-element group."
            )

        seen_group_keys.add(group_key)

        stable_subject_key = (
            expected_subjects.get(group_key)
        )

        if stable_subject_key is None:
            raise ReviewReferenceError(
                "Derivation Consensus Report contains "
                "a candidate group without a matching "
                f"structured proposal: {group_key!r}."
            )

        reference = ReviewEvidenceReference(
            artifact_reference=consensus_reference,
            evidence_role=CONSENSUS_EVIDENCE_ROLE,
            evidence_locator=f"/groups/{index}",
            evidence_content_fingerprint=(
                _canonical_fingerprint(group)
            ),
        )

        result.setdefault(
            stable_subject_key,
            [],
        ).append(reference)

    missing = sorted(
        set(expected_subjects) - seen_group_keys
    )

    if missing:
        raise ReviewReferenceError(
            "Derivation Consensus Report is missing "
            "candidate groups required by structured "
            f"proposals: {missing!r}."
        )

    _require_unique_evidence_references(result)

    return result


def _select_derivation_consensus_reference(
    p9_evidence: P9ReviewEvidenceSet,
) -> ProcessingArtifactReference:
    references = tuple(
        reference
        for reference
        in p9_evidence.consensus_report_references
        if (
            reference.artifact_type
            == "consensus_reports"
            and DERIVATION_STAGE_DIRECTORY
            in PurePosixPath(
                reference.repository_relative_path
            ).parts
            and PurePosixPath(
                reference.repository_relative_path
            ).suffix
            == ".json"
        )
    )

    if not references:
        raise ReviewReferenceError(
            "P9 Review Evidence contains no structured "
            "Derivation Consensus JSON artifact."
        )

    if len(references) != 1:
        raise ReviewIntegrityError(
            "P9 Review Evidence requires exactly one "
            "structured Derivation Consensus JSON artifact."
        )

    return references[0]


def _load_consensus_report(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
    p9_evidence: P9ReviewEvidenceSet,
) -> dict[str, Any]:
    content = _read_verified_consensus_artifact(
        reference,
        repository_root=repository_root,
        p9_evidence=p9_evidence,
    )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewReferenceError(
            "Derivation Consensus JSON is not valid UTF-8."
        ) from exc

    try:
        value = json.loads(
            text,
            object_pairs_hook=(
                _object_without_duplicate_keys
            ),
        )
    except ReviewIntegrityError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "Derivation Consensus artifact is not "
            "valid JSON."
        ) from exc

    report = _exact_object(
        value,
        expected_fields=_CONSENSUS_REPORT_FIELDS,
        label="Derivation Consensus Report",
    )

    _identifier(
        report["consensus_report_id"],
        "consensus_report_id",
    )

    if report["team_id"] != DERIVATION_TEAM_ID:
        raise ReviewIntegrityError(
            "Consensus artifact does not identify the "
            "Derivation Assessment Team."
        )

    _text(report["task_name"], "task_name")
    _text(report["created_at"], "created_at")

    total_agents = _positive_integer(
        report["total_agents"],
        "total_agents",
    )

    agent_ids = _identifier_list(
        report["agent_ids"],
        "agent_ids",
        require_nonempty=True,
    )

    if len(agent_ids) != total_agents:
        raise ReviewIntegrityError(
            "Consensus total_agents must equal the "
            "number of unique agent_ids."
        )

    labels = report["agent_labels"]

    if not isinstance(labels, dict):
        raise ReviewValidationError(
            "agent_labels must be a JSON object."
        )

    if set(labels) != set(agent_ids):
        raise ReviewIntegrityError(
            "agent_labels must bind every and only "
            "the declared agent_ids."
        )

    for agent_id, persona_id in labels.items():
        _identifier(agent_id, "agent_labels key")
        _identifier(persona_id, "persona_id")

    groups = report["groups"]

    if not isinstance(groups, list):
        raise ReviewValidationError(
            "groups must be a JSON array."
        )

    summary = _validate_consensus_summary(
        report["summary"],
        groups=groups,
    )

    report["agent_ids"] = list(agent_ids)
    report["summary"] = summary

    return report


def _validate_consensus_summary(
    value: object,
    *,
    groups: list[object],
) -> dict[str, int]:
    summary = _exact_object(
        value,
        expected_fields=_CONSENSUS_SUMMARY_FIELDS,
        label="Consensus summary",
    )

    validated = {
        field_name: _nonnegative_integer(
            summary[field_name],
            f"summary.{field_name}",
        )
        for field_name
        in _CONSENSUS_SUMMARY_FIELDS
    }

    if validated["total_groups"] != len(groups):
        raise ReviewIntegrityError(
            "Consensus summary total_groups does not "
            "match the groups array."
        )

    calculated = {
        agreement_level: 0
        for agreement_level
        in _CONSENSUS_AGREEMENT_LEVELS
    }
    review_required_count = 0

    for raw_group in groups:
        if not isinstance(raw_group, dict):
            raise ReviewValidationError(
                "Consensus groups must be JSON objects."
            )

        agreement_level = raw_group.get(
            "agreement_level"
        )

        if (
            agreement_level
            in _CONSENSUS_AGREEMENT_LEVELS
        ):
            calculated[agreement_level] += 1

        if raw_group.get("review_required") is True:
            review_required_count += 1

    for agreement_level, count in calculated.items():
        if validated[agreement_level] != count:
            raise ReviewIntegrityError(
                "Consensus summary disagrees with "
                f"group count for {agreement_level!r}."
            )

    if (
        validated["review_required"]
        != review_required_count
    ):
        raise ReviewIntegrityError(
            "Consensus summary review_required does "
            "not match the groups array."
        )

    return validated


def _validate_consensus_group(
    value: object,
    *,
    expected_total_agents: int,
    report_agent_ids: tuple[str, ...],
) -> dict[str, Any]:
    group = _exact_object(
        value,
        expected_fields=_CONSENSUS_GROUP_FIELDS,
        label="Consensus group",
    )

    _text(group["group_key"], "group_key")
    _identifier(group["item_type"], "item_type")

    if (
        group["agreement_level"]
        not in _CONSENSUS_AGREEMENT_LEVELS
    ):
        raise ReviewValidationError(
            "agreement_level is unsupported."
        )

    if (
        _positive_integer(
            group["total_agents"],
            "group total_agents",
        )
        != expected_total_agents
    ):
        raise ReviewIntegrityError(
            "Consensus group total_agents does not "
            "match the report."
        )

    supporting_agents = _identifier_list(
        group["supporting_agents"],
        "supporting_agents",
        require_nonempty=True,
    )

    if not set(supporting_agents) <= set(
        report_agent_ids
    ):
        raise ReviewReferenceError(
            "Consensus group references an unknown "
            "supporting Agent."
        )

    value_distribution = group[
        "value_distribution"
    ]

    if (
        not isinstance(value_distribution, dict)
        or not value_distribution
    ):
        raise ReviewValidationError(
            "value_distribution must be a "
            "non-empty JSON object."
        )

    for distribution_key, agent_values in (
        value_distribution.items()
    ):
        _text(
            distribution_key,
            "value_distribution key",
        )
        distributed_agents = _identifier_list(
            agent_values,
            "value_distribution agents",
            require_nonempty=True,
        )

        if not set(distributed_agents) <= set(
            report_agent_ids
        ):
            raise ReviewReferenceError(
                "value_distribution references an "
                "unknown Agent."
            )

    _text(
        group["representative_value"],
        "representative_value",
    )

    if not isinstance(
        group["review_required"],
        bool,
    ):
        raise ReviewValidationError(
            "review_required must be Boolean."
        )

    _text(group["reason"], "reason")

    agent_values = group["agent_values"]

    if not isinstance(agent_values, dict):
        raise ReviewValidationError(
            "agent_values must be a JSON object."
        )

    if not set(agent_values) <= set(
        report_agent_ids
    ):
        raise ReviewReferenceError(
            "agent_values references an unknown Agent."
        )

    for agent_id, display_value in (
        agent_values.items()
    ):
        _identifier(agent_id, "agent_values key")
        _text(display_value, "agent display value")

    return group


def _validate_consensus_agents(
    report: dict[str, Any],
    proposals: P9StructuredProposalSet,
) -> None:
    proposal_agents: dict[str, str] = {}

    for proposal in (
        proposals.element_proposals
        + proposals.relationship_proposals
    ):
        reference = proposal.proposal_reference
        previous_persona = proposal_agents.get(
            reference.agent_id
        )

        if (
            previous_persona is not None
            and previous_persona
            != reference.persona_id
        ):
            raise ReviewIntegrityError(
                "One P9 Agent ID is associated with "
                "multiple Persona IDs."
            )

        proposal_agents[reference.agent_id] = (
            reference.persona_id
        )

    if set(proposal_agents) != set(
        report["agent_ids"]
    ):
        raise ReviewIntegrityError(
            "Derivation Consensus Agents do not match "
            "the structured proposal Agents."
        )

    for agent_id, persona_id in (
        proposal_agents.items()
    ):
        if (
            report["agent_labels"][agent_id]
            != persona_id
        ):
            raise ReviewIntegrityError(
                "Derivation Consensus Agent/Persona "
                "mapping does not match proposals."
            )


def _validate_proposal_set_identity(
    evidence: P9ReviewEvidenceSet,
    proposals: P9StructuredProposalSet,
) -> None:
    for field_name in (
        "project_id",
        "source_id",
        "processing_run_id",
        "attempt_id",
    ):
        if getattr(evidence, field_name) != getattr(
            proposals,
            field_name,
        ):
            raise ReviewIntegrityError(
                "P9 Evidence and structured proposals "
                f"disagree on {field_name}."
            )


def _validate_proposal_artifact_membership(
    evidence: P9ReviewEvidenceSet,
    proposals: P9StructuredProposalSet,
) -> None:
    selected_references = {
        _artifact_reference_key(reference)
        for reference
        in evidence.agent_output_references
    }

    for proposal in (
        proposals.element_proposals
        + proposals.relationship_proposals
    ):
        reference = (
            proposal.proposal_reference
            .artifact_reference
        )

        if (
            _artifact_reference_key(reference)
            not in selected_references
        ):
            raise ReviewReferenceError(
                "Structured proposal references an "
                "Agent Output outside the selected "
                "P9 Evidence Set."
            )


def _read_verified_consensus_artifact(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
    p9_evidence: P9ReviewEvidenceSet,
) -> bytes:
    try:
        validate_processing_artifact_reference(
            reference
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "P9 contains an invalid Consensus "
            "Artifact Reference."
        ) from exc

    relative_path = PurePosixPath(
        reference.repository_relative_path
    )

    expected_prefix = (
        "data",
        "projects",
        p9_evidence.project_id,
        "runs",
        p9_evidence.processing_run_id,
        "artifacts",
        "consensus_reports",
        AGENTIC_INGESTION_STAGE,
        p9_evidence.attempt_id,
    )

    if (
        relative_path.parts[: len(expected_prefix)]
        != expected_prefix
    ):
        raise ReviewIntegrityError(
            "Consensus artifact path does not match "
            "the selected Project, Run and Attempt."
        )

    target = repository_root.joinpath(
        *relative_path.parts
    )

    current = repository_root

    for part in relative_path.parts:
        current = current / part

        if current.is_symlink():
            raise ReviewReferenceError(
                "Consensus artifact path must not "
                "contain symbolic links."
            )

    try:
        resolved_root = repository_root.resolve(
            strict=True
        )
        resolved_target = target.resolve(
            strict=True
        )
        resolved_target.relative_to(resolved_root)
    except FileNotFoundError as exc:
        raise ReviewReferenceError(
            "Referenced Consensus artifact does not exist."
        ) from exc
    except ValueError as exc:
        raise ReviewReferenceError(
            "Referenced Consensus artifact escapes "
            "repository_root."
        ) from exc
    except OSError as exc:
        raise ReviewReferenceError(
            "Referenced Consensus artifact cannot "
            "be resolved."
        ) from exc

    if not target.is_file():
        raise ReviewReferenceError(
            "Referenced Consensus artifact is not "
            "a regular file."
        )

    try:
        content = target.read_bytes()
    except OSError as exc:
        raise ReviewReferenceError(
            "Referenced Consensus artifact cannot be read."
        ) from exc

    actual_fingerprint = hashlib.sha256(
        content
    ).hexdigest()

    if (
        actual_fingerprint
        != reference.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Consensus artifact fingerprint does not "
            "match persisted content."
        )

    return content


def _element_consensus_group_key(
    proposal: P9ElementProposal,
) -> str:
    return (
        "candidate_model_element::"
        f"{_normalize_consensus_text(proposal.element_type)}::"
        f"{_normalize_consensus_text(proposal.candidate_name)}"
    )


def _normalize_consensus_text(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(
        r"[^a-z0-9äöüß]+",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _register_subject_kind(
    kinds: dict[str, str],
    stable_subject_key: str,
    review_item_kind: str,
) -> None:
    existing = kinds.get(stable_subject_key)

    if (
        existing is not None
        and existing != review_item_kind
    ):
        raise ReviewIntegrityError(
            "One stable subject is associated with "
            "multiple Review Item kinds."
        )

    kinds[stable_subject_key] = review_item_kind


def _require_unique_evidence_references(
    references: dict[
        str,
        list[ReviewEvidenceReference],
    ],
) -> None:
    for stable_subject_key, values in (
        references.items()
    ):
        keys = [
            _evidence_reference_key(value)
            for value in values
        ]

        if len(keys) != len(set(keys)):
            raise ReviewIntegrityError(
                "Evidence references must be unique "
                f"for subject {stable_subject_key!r}."
            )


def _validated_repository_root(
    repository_root: Path | str,
) -> Path:
    try:
        root = Path(repository_root)
    except TypeError as exc:
        raise ReviewValidationError(
            "repository_root must be a filesystem path."
        ) from exc

    if root.is_symlink():
        raise ReviewReferenceError(
            "repository_root must not be a symbolic link."
        )

    if not root.exists() or not root.is_dir():
        raise ReviewReferenceError(
            "repository_root must be an existing directory."
        )

    return root


def _exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewValidationError(
            f"{label} must be a JSON object."
        )

    if set(value) != expected_fields:
        missing = sorted(
            expected_fields - set(value)
        )
        unknown = sorted(
            set(value) - expected_fields
        )

        raise ReviewValidationError(
            f"{label} fields do not match the contract; "
            f"missing={missing!r}, unknown={unknown!r}."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewIntegrityError(
                "Duplicate JSON key is not permitted: "
                f"{key!r}."
            )

        result[key] = value

    return result


def _identifier(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _IDENTIFIER_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a supported identifier."
        )

    return value


def _text(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\x00" in value
        or "\r" in value
    ):
        raise ReviewValidationError(
            f"{label} must be non-empty normalized text."
        )

    return value


def _identifier_list(
    value: object,
    label: str,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ReviewValidationError(
            f"{label} must be a JSON array."
        )

    if require_nonempty and not value:
        raise ReviewIntegrityError(
            f"{label} must not be empty."
        )

    result = tuple(
        _identifier(item, label)
        for item in value
    )

    if len(result) != len(set(result)):
        raise ReviewIntegrityError(
            f"{label} must not contain duplicates."
        )

    return result


def _positive_integer(
    value: object,
    label: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise ReviewValidationError(
            f"{label} must be a positive integer."
        )

    return value


def _nonnegative_integer(
    value: object,
    label: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise ReviewValidationError(
            f"{label} must be a non-negative integer."
        )

    return value


def _canonical_fingerprint(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def _artifact_reference_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )


def _evidence_reference_key(
    reference: ReviewEvidenceReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_reference.artifact_id,
        reference.evidence_role,
        reference.evidence_locator,
        reference.evidence_content_fingerprint,
    )
