"""Human-authorized publication of semantic consensus outcomes.

This module deliberately separates a technically publication-eligible
consensus outcome from the human decision that authorizes publication.
Preparing a request never creates an Information Unit.  Publication is
possible only when a separately supplied authorization is bound to the
exact request fingerprint.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from typing import Protocol, runtime_checkable

from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
)

from .errors import (
    SemanticConsensusError,
    SemanticConsensusIntegrityError,
    SemanticConsensusPublicationError,
    SemanticConsensusPublicationNotAuthorizedError,
    SemanticConsensusReferenceError,
    SemanticConsensusValidationError,
)
from .identifiers import (
    validate_semantic_consensus_candidate_id,
)
from .manifest import validate_semantic_consensus_result
from .types import (
    ConsensusInformationUnitDraft,
    SemanticConsensusOutcome,
    SemanticConsensusResult,
)


SEMANTIC_PUBLICATION_REQUEST_SCHEMA_VERSION = "1.0.0"
SEMANTIC_PUBLICATION_AUTHORIZATION_SCHEMA_VERSION = "1.0.0"
CONFIRM_PUBLISH_DECISION = "confirm_publish"
QUICK_CONFIRMATION_REVIEW_MODE = "quick_confirmation"

_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
_SOURCE_ID_PATTERN = re.compile(r"^SRC-[0-9]{6}$")
_SOURCE_PROJECTION_ID_PATTERN = re.compile(
    r"^SP-[0-9]{6}$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


@dataclass(frozen=True, slots=True)
class SemanticPublicationRequest:
    """One immutable request prepared from a clean consensus outcome."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    consensus_report_id: str
    consensus_candidate_id: str
    required_personas: tuple[str, ...]
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    proposed_information_unit: ConsensusInformationUnitDraft
    confidence: str
    confidence_rationale: str
    confirmation_required: bool
    review_required: bool
    recommended_review_mode: str
    publication_eligible: bool
    consensus_created_at: str
    publication_request_fingerprint: str


@dataclass(frozen=True, slots=True)
class SemanticPublicationAuthorization:
    """Human-review decision bound to one publication request."""

    schema_version: str
    project_id: str
    consensus_report_id: str
    consensus_candidate_id: str
    publication_request_fingerprint: str
    decision: str
    review_mode: str
    review_decision_id: str
    reviewer_id: str
    decided_at: str


@runtime_checkable
class InformationUnitPublisher(Protocol):
    """Minimum repository capability required by this boundary."""

    def create_information_unit(
        self,
        project_id: str,
        source_id: str,
        source_projection_id: str,
        *,
        source_anchors: object,
        source_excerpt: str,
        interpreted_statement: str,
        information_type: str,
        statement_modality: str,
        epistemic_class: str,
        extraction_provenance: (
            InformationUnitExtractionProvenance
        ),
        confidence: str,
        confidence_rationale: str,
        supporting_information_unit_ids: object = (),
        derivation_rationale: str | None = None,
        missing_evidence: str | None = None,
    ) -> InformationUnit:
        """Create and return one repository-allocated Information Unit."""


def prepare_semantic_publication_request(
    consensus_result: SemanticConsensusResult,
    consensus_candidate_id: str,
) -> SemanticPublicationRequest:
    """Prepare, but do not publish, one clean high-confidence outcome."""

    validate_semantic_consensus_result(consensus_result)
    candidate_id = validate_semantic_consensus_candidate_id(
        consensus_candidate_id
    )
    outcome = _find_outcome(
        consensus_result,
        candidate_id,
    )
    _require_quick_confirmation_outcome(outcome)

    draft = outcome.proposed_information_unit
    if draft is None:
        raise SemanticConsensusPublicationError(
            "A publication-eligible outcome must contain a "
            "proposed Information Unit."
        )

    request_without_fingerprint = SemanticPublicationRequest(
        schema_version=(
            SEMANTIC_PUBLICATION_REQUEST_SCHEMA_VERSION
        ),
        project_id=consensus_result.project_id,
        source_id=consensus_result.source_id,
        source_projection_id=(
            consensus_result.source_projection_id
        ),
        team_id=consensus_result.team_id,
        consensus_report_id=(
            consensus_result.consensus_report_id
        ),
        consensus_candidate_id=candidate_id,
        required_personas=consensus_result.required_personas,
        llm_provider=consensus_result.llm_provider,
        llm_model=consensus_result.llm_model,
        prompt_schema_version=(
            consensus_result.prompt_schema_version
        ),
        proposed_information_unit=draft,
        confidence=outcome.confidence,
        confidence_rationale=outcome.confidence_rationale,
        confirmation_required=outcome.confirmation_required,
        review_required=outcome.review_required,
        recommended_review_mode=(
            outcome.recommended_review_mode
        ),
        publication_eligible=outcome.publication_eligible,
        consensus_created_at=consensus_result.created_at,
        publication_request_fingerprint="0" * 64,
    )
    fingerprint = (
        calculate_semantic_publication_request_fingerprint(
            request_without_fingerprint
        )
    )
    request = replace(
        request_without_fingerprint,
        publication_request_fingerprint=fingerprint,
    )
    _validate_publication_request(request)
    return request


def calculate_semantic_publication_request_fingerprint(
    request: SemanticPublicationRequest,
) -> str:
    """Return the canonical SHA-256 binding all publication inputs."""

    if not isinstance(request, SemanticPublicationRequest):
        raise SemanticConsensusValidationError(
            "request must be a SemanticPublicationRequest."
        )

    payload = _publication_request_payload(
        request,
        include_fingerprint=False,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def create_semantic_publication_authorization(
    *,
    project_id: str,
    consensus_report_id: str,
    consensus_candidate_id: str,
    publication_request_fingerprint: str,
    decision: str,
    review_mode: str,
    review_decision_id: str,
    reviewer_id: str,
    decided_at: str,
) -> SemanticPublicationAuthorization:
    """Create the transport record for an external human decision.

    The authoritative decision workflow and reviewer authentication are
    supplied by P4/23.  This function validates and binds the decision;
    it does not infer or manufacture human approval.
    """

    authorization = SemanticPublicationAuthorization(
        schema_version=(
            SEMANTIC_PUBLICATION_AUTHORIZATION_SCHEMA_VERSION
        ),
        project_id=project_id,
        consensus_report_id=consensus_report_id,
        consensus_candidate_id=consensus_candidate_id,
        publication_request_fingerprint=(
            publication_request_fingerprint
        ),
        decision=decision,
        review_mode=review_mode,
        review_decision_id=review_decision_id,
        reviewer_id=reviewer_id,
        decided_at=decided_at,
    )
    _validate_publication_authorization(authorization)
    return authorization


def publish_confirmed_information_unit(
    request: SemanticPublicationRequest,
    authorization: SemanticPublicationAuthorization,
    repository: InformationUnitPublisher,
) -> InformationUnit:
    """Publish only when explicit human authorization matches exactly."""

    _validate_publication_request(request)
    _validate_publication_authorization(authorization)
    _require_matching_authorization(
        request,
        authorization,
    )

    if not isinstance(repository, InformationUnitPublisher):
        raise SemanticConsensusValidationError(
            "repository must provide create_information_unit()."
        )

    draft = request.proposed_information_unit
    provenance = InformationUnitExtractionProvenance(
        team_id=request.team_id,
        persona_ids=request.required_personas,
        llm_provider=request.llm_provider,
        llm_model=request.llm_model,
        prompt_schema_version=request.prompt_schema_version,
        consensus_report_id=request.consensus_report_id,
    )

    try:
        information_unit = repository.create_information_unit(
            request.project_id,
            request.source_id,
            request.source_projection_id,
            source_anchors=draft.source_anchors,
            source_excerpt=draft.source_excerpt,
            interpreted_statement=draft.interpreted_statement,
            information_type=draft.information_type,
            statement_modality=draft.statement_modality,
            epistemic_class=draft.epistemic_class,
            extraction_provenance=provenance,
            confidence=request.confidence,
            confidence_rationale=request.confidence_rationale,
            supporting_information_unit_ids=(
                draft.supporting_information_unit_ids
            ),
            derivation_rationale=draft.derivation_rationale,
            missing_evidence=draft.missing_evidence,
        )
    except SemanticConsensusError:
        raise
    except Exception as exc:
        raise SemanticConsensusPublicationError(
            "Information Unit repository rejected the confirmed "
            "publication request."
        ) from exc

    _validate_published_information_unit(
        request,
        provenance,
        information_unit,
    )
    return information_unit


def _find_outcome(
    result: SemanticConsensusResult,
    candidate_id: str,
) -> SemanticConsensusOutcome:
    matches = tuple(
        outcome
        for outcome in result.outcomes
        if outcome.consensus_candidate_id == candidate_id
    )
    if len(matches) != 1:
        raise SemanticConsensusReferenceError(
            "consensus_candidate_id does not identify exactly one "
            f"outcome: {candidate_id!r}."
        )
    return matches[0]


def _require_quick_confirmation_outcome(
    outcome: SemanticConsensusOutcome,
) -> None:
    violations: list[str] = []

    if outcome.consensus_level != "unanimous":
        violations.append("consensus_level must be unanimous")
    if outcome.variance_level != "low":
        violations.append("variance_level must be low")
    if outcome.confidence != "high":
        violations.append("confidence must be high")
    if outcome.confirmation_required is not True:
        violations.append("confirmation_required must be true")
    if outcome.review_required is not False:
        violations.append("review_required must be false")
    if (
        outcome.recommended_review_mode
        != QUICK_CONFIRMATION_REVIEW_MODE
    ):
        violations.append(
            "recommended_review_mode must be quick_confirmation"
        )
    if outcome.publication_eligible is not True:
        violations.append("publication_eligible must be true")
    if outcome.proposed_information_unit is None:
        violations.append(
            "proposed_information_unit must be present"
        )

    if violations:
        raise SemanticConsensusPublicationNotAuthorizedError(
            "Outcome is not eligible for quick-confirmation "
            "publication: "
            + "; ".join(violations)
            + "."
        )


def _validate_publication_request(
    request: SemanticPublicationRequest,
) -> None:
    if not isinstance(request, SemanticPublicationRequest):
        raise SemanticConsensusValidationError(
            "request must be a SemanticPublicationRequest."
        )
    if (
        request.schema_version
        != SEMANTIC_PUBLICATION_REQUEST_SCHEMA_VERSION
    ):
        raise SemanticConsensusValidationError(
            "Unsupported publication request schema_version."
        )

    _require_project_id(request.project_id)
    _require_source_id(request.source_id)
    _require_source_projection_id(
        request.source_projection_id
    )
    _require_text(request.team_id, "team_id")
    _require_text(
        request.consensus_report_id,
        "consensus_report_id",
    )
    validate_semantic_consensus_candidate_id(
        request.consensus_candidate_id
    )
    _require_personas(request.required_personas)
    _require_text(request.llm_provider, "llm_provider")
    _require_text(request.llm_model, "llm_model")
    _require_semantic_version(
        request.prompt_schema_version,
        "prompt_schema_version",
    )
    if not isinstance(
        request.proposed_information_unit,
        ConsensusInformationUnitDraft,
    ):
        raise SemanticConsensusValidationError(
            "proposed_information_unit must be a "
            "ConsensusInformationUnitDraft."
        )
    _require_text(
        request.confidence_rationale,
        "confidence_rationale",
    )
    _require_utc_timestamp(
        request.consensus_created_at,
        "consensus_created_at",
    )

    synthetic_outcome = SemanticConsensusOutcome(
        consensus_candidate_id=(
            request.consensus_candidate_id
        ),
        source_anchors=(
            request.proposed_information_unit.source_anchors
        ),
        source_excerpt=(
            request.proposed_information_unit.source_excerpt
        ),
        candidate_references=(),
        persona_stability=(),
        field_assessments=(),
        proposed_information_unit=(
            request.proposed_information_unit
        ),
        consensus_level="unanimous",
        variance_level="low",
        confidence=request.confidence,
        total_personas=len(request.required_personas),
        supporting_personas=request.required_personas,
        dissenting_personas=(),
        omitting_personas=(),
        confirmation_required=request.confirmation_required,
        review_required=request.review_required,
        recommended_review_mode=(
            request.recommended_review_mode
        ),
        publication_eligible=request.publication_eligible,
        confidence_rationale=request.confidence_rationale,
    )
    _require_quick_confirmation_outcome(synthetic_outcome)
    _require_sha256(
        request.publication_request_fingerprint,
        "publication_request_fingerprint",
    )

    expected_fingerprint = (
        calculate_semantic_publication_request_fingerprint(
            request
        )
    )
    if (
        request.publication_request_fingerprint
        != expected_fingerprint
    ):
        raise SemanticConsensusIntegrityError(
            "Publication request fingerprint does not match "
            "its bound content."
        )


def _validate_publication_authorization(
    authorization: SemanticPublicationAuthorization,
) -> None:
    if not isinstance(
        authorization,
        SemanticPublicationAuthorization,
    ):
        raise SemanticConsensusValidationError(
            "authorization must be a "
            "SemanticPublicationAuthorization."
        )
    if (
        authorization.schema_version
        != SEMANTIC_PUBLICATION_AUTHORIZATION_SCHEMA_VERSION
    ):
        raise SemanticConsensusValidationError(
            "Unsupported publication authorization "
            "schema_version."
        )

    _require_project_id(authorization.project_id)
    _require_text(
        authorization.consensus_report_id,
        "consensus_report_id",
    )
    validate_semantic_consensus_candidate_id(
        authorization.consensus_candidate_id
    )
    _require_sha256(
        authorization.publication_request_fingerprint,
        "publication_request_fingerprint",
    )
    _require_text(
        authorization.review_decision_id,
        "review_decision_id",
    )
    _require_text(
        authorization.reviewer_id,
        "reviewer_id",
    )
    _require_utc_timestamp(
        authorization.decided_at,
        "decided_at",
    )

    if authorization.decision != CONFIRM_PUBLISH_DECISION:
        raise SemanticConsensusPublicationNotAuthorizedError(
            "Only an explicit confirm_publish decision authorizes "
            "publication."
        )
    if (
        authorization.review_mode
        != QUICK_CONFIRMATION_REVIEW_MODE
    ):
        raise SemanticConsensusPublicationNotAuthorizedError(
            "This publication boundary accepts only a "
            "quick_confirmation decision."
        )


def _require_matching_authorization(
    request: SemanticPublicationRequest,
    authorization: SemanticPublicationAuthorization,
) -> None:
    bindings = (
        (
            "project_id",
            request.project_id,
            authorization.project_id,
        ),
        (
            "consensus_report_id",
            request.consensus_report_id,
            authorization.consensus_report_id,
        ),
        (
            "consensus_candidate_id",
            request.consensus_candidate_id,
            authorization.consensus_candidate_id,
        ),
        (
            "publication_request_fingerprint",
            request.publication_request_fingerprint,
            authorization.publication_request_fingerprint,
        ),
        (
            "review_mode",
            request.recommended_review_mode,
            authorization.review_mode,
        ),
    )
    mismatches = tuple(
        label
        for label, expected, actual in bindings
        if expected != actual
    )

    if mismatches:
        raise SemanticConsensusPublicationNotAuthorizedError(
            "Human authorization is not bound to this "
            "publication request; mismatched fields: "
            + ", ".join(mismatches)
            + "."
        )


def _validate_published_information_unit(
    request: SemanticPublicationRequest,
    provenance: InformationUnitExtractionProvenance,
    information_unit: object,
) -> None:
    if not isinstance(information_unit, InformationUnit):
        raise SemanticConsensusIntegrityError(
            "Repository must return an InformationUnit."
        )

    draft = request.proposed_information_unit
    comparisons = (
        (
            "project_id",
            request.project_id,
            information_unit.project_id,
        ),
        (
            "source_id",
            request.source_id,
            information_unit.source_id,
        ),
        (
            "source_projection_id",
            request.source_projection_id,
            information_unit.source_projection_id,
        ),
        (
            "source_anchors",
            draft.source_anchors,
            information_unit.source_anchors,
        ),
        (
            "source_excerpt",
            draft.source_excerpt,
            information_unit.source_excerpt,
        ),
        (
            "interpreted_statement",
            draft.interpreted_statement,
            information_unit.interpreted_statement,
        ),
        (
            "information_type",
            draft.information_type,
            information_unit.information_type,
        ),
        (
            "statement_modality",
            draft.statement_modality,
            information_unit.statement_modality,
        ),
        (
            "epistemic_class",
            draft.epistemic_class,
            information_unit.epistemic_class,
        ),
        (
            "supporting_information_unit_ids",
            draft.supporting_information_unit_ids,
            information_unit.supporting_information_unit_ids,
        ),
        (
            "derivation_rationale",
            draft.derivation_rationale,
            information_unit.derivation_rationale,
        ),
        (
            "missing_evidence",
            draft.missing_evidence,
            information_unit.missing_evidence,
        ),
        (
            "extraction_provenance",
            provenance,
            information_unit.extraction_provenance,
        ),
        (
            "confidence",
            request.confidence,
            information_unit.confidence,
        ),
        (
            "confidence_rationale",
            request.confidence_rationale,
            information_unit.confidence_rationale,
        ),
    )
    mismatches = tuple(
        label
        for label, expected, actual in comparisons
        if expected != actual
    )

    if mismatches:
        raise SemanticConsensusIntegrityError(
            "Published Information Unit differs from the "
            "authorized request; mismatched fields: "
            + ", ".join(mismatches)
            + "."
        )


def _publication_request_payload(
    request: SemanticPublicationRequest,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    draft = request.proposed_information_unit
    payload: dict[str, object] = {
        "schema_version": request.schema_version,
        "project_id": request.project_id,
        "source_id": request.source_id,
        "source_projection_id": (
            request.source_projection_id
        ),
        "team_id": request.team_id,
        "consensus_report_id": request.consensus_report_id,
        "consensus_candidate_id": (
            request.consensus_candidate_id
        ),
        "required_personas": list(request.required_personas),
        "llm_provider": request.llm_provider,
        "llm_model": request.llm_model,
        "prompt_schema_version": (
            request.prompt_schema_version
        ),
        "proposed_information_unit": {
            "source_anchors": [
                {
                    "segment_id": anchor.segment_id,
                    "start_offset": anchor.start_offset,
                    "end_offset": anchor.end_offset,
                }
                for anchor in draft.source_anchors
            ],
            "source_excerpt": draft.source_excerpt,
            "interpreted_statement": (
                draft.interpreted_statement
            ),
            "information_type": draft.information_type,
            "statement_modality": draft.statement_modality,
            "epistemic_class": draft.epistemic_class,
            "supporting_information_unit_ids": list(
                draft.supporting_information_unit_ids
            ),
            "derivation_rationale": (
                draft.derivation_rationale
            ),
            "missing_evidence": draft.missing_evidence,
        },
        "confidence": request.confidence,
        "confidence_rationale": request.confidence_rationale,
        "confirmation_required": request.confirmation_required,
        "review_required": request.review_required,
        "recommended_review_mode": (
            request.recommended_review_mode
        ),
        "publication_eligible": request.publication_eligible,
        "consensus_created_at": request.consensus_created_at,
    }
    if include_fingerprint:
        payload["publication_request_fingerprint"] = (
            request.publication_request_fingerprint
        )
    return payload


def _require_project_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _PROJECT_ID_PATTERN.fullmatch(value) is None
        or value == "000000"
    ):
        raise SemanticConsensusValidationError(
            "project_id must contain six digits and must not "
            "be 000000."
        )
    return value


def _require_source_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _SOURCE_ID_PATTERN.fullmatch(value) is None
        or value == "SRC-000000"
    ):
        raise SemanticConsensusValidationError(
            "source_id must match SRC-[0-9]{6} and must not "
            "end in 000000."
        )
    return value


def _require_source_projection_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _SOURCE_PROJECTION_ID_PATTERN.fullmatch(value) is None
        or value == "SP-000000"
    ):
        raise SemanticConsensusValidationError(
            "source_projection_id must match SP-[0-9]{6} and "
            "must not end in 000000."
        )
    return value


def _require_text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 32 for character in value)
    ):
        raise SemanticConsensusValidationError(
            f"{label} must be non-empty, trimmed stored text."
        )
    return value


def _require_personas(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or not value
        or any(
            _require_text(persona_id, "required_personas item")
            != persona_id
            for persona_id in value
        )
        or len(value) != len(set(value))
        or value != tuple(sorted(value))
    ):
        raise SemanticConsensusValidationError(
            "required_personas must be a non-empty, unique, "
            "sorted tuple of stored text."
        )
    return value


def _require_semantic_version(
    value: object,
    label: str,
) -> str:
    text = _require_text(value, label)
    if _SEMANTIC_VERSION_PATTERN.fullmatch(text) is None:
        raise SemanticConsensusValidationError(
            f"{label} must be a semantic version."
        )
    return text


def _require_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise SemanticConsensusValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )
    return value


def _require_utc_timestamp(
    value: object,
    label: str,
) -> str:
    text = _require_text(value, label)
    if _UTC_TIMESTAMP_PATTERN.fullmatch(text) is None:
        raise SemanticConsensusValidationError(
            f"{label} must be an ISO 8601 UTC timestamp."
        )
    return text