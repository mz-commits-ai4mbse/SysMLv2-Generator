"""Tests for human-authorized semantic consensus publication."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from hashlib import sha256

import pytest

from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.semantic_consensus.analyzer import (
    analyze_semantic_consensus,
)
from modules.semantic_consensus.errors import (
    SemanticConsensusIntegrityError,
    SemanticConsensusPublicationError,
    SemanticConsensusPublicationNotAuthorizedError,
    SemanticConsensusReferenceError,
    SemanticConsensusValidationError,
)
from modules.semantic_consensus.publication import (
    CONFIRM_PUBLISH_DECISION,
    QUICK_CONFIRMATION_REVIEW_MODE,
    SEMANTIC_PUBLICATION_AUTHORIZATION_SCHEMA_VERSION,
    SEMANTIC_PUBLICATION_REQUEST_SCHEMA_VERSION,
    SemanticPublicationAuthorization,
    SemanticPublicationRequest,
    calculate_semantic_publication_request_fingerprint,
    create_semantic_publication_authorization,
    prepare_semantic_publication_request,
    publish_confirmed_information_unit,
)
from modules.semantic_extraction.manifest import (
    create_information_unit_candidate,
    create_semantic_extraction_agent_result,
)
from modules.source_projection.types import (
    ProjectionSegment,
    SourceProjectionArtifact,
    SourceProjectionManifest,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
CONSENSUS_REPORT_ID = "CONSENSUS-TEST-001"
CONSENSUS_CANDIDATE_ID = "SCC-000001"
TIMESTAMP = "2026-07-24T10:00:00Z"
CONSENSUS_TIMESTAMP = "2026-07-24T11:00:00Z"
DECISION_TIMESTAMP = "2026-07-24T12:00:00Z"


def projection() -> SourceProjectionArtifact:
    return SourceProjectionArtifact(
        manifest=SourceProjectionManifest(
            schema_version="1.0.0",
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_projection_id=SOURCE_PROJECTION_ID,
            source_role="engineering_source",
            source_sha256="a" * 64,
            adapter_id="text",
            adapter_version="1.0.0",
            adapter_configuration=(),
            projection_fingerprint="b" * 64,
            projection_result="available",
            content_sha256="c" * 64,
            content_length=5,
            segments=(
                ProjectionSegment(
                    segment_id="SEG-000001",
                    segment_type="text",
                    start_offset=0,
                    end_offset=5,
                    text_sha256="d" * 64,
                    source_locators=(),
                ),
            ),
            issues=(),
            created_at=TIMESTAMP,
        ),
        content="Alpha",
    )


def candidate(
    *,
    statement: str = "Alpha is present.",
    epistemic_class: str = "explicit",
    missing_evidence: str | None = None,
) -> object:
    return create_information_unit_candidate(
        candidate_id="IUC-000001",
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=5,
            ),
        ),
        source_excerpt="Alpha",
        interpreted_statement=statement,
        information_type="requirement",
        statement_modality="descriptive",
        epistemic_class=epistemic_class,
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=missing_evidence,
        extraction_rationale="Deterministic test candidate.",
        uncertainties=(),
    )


def agent_result(
    persona_id: str,
    *,
    selected_candidate: object | None = None,
) -> object:
    selected = candidate() if selected_candidate is None else selected_candidate
    return create_semantic_extraction_agent_result(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_projection_id=SOURCE_PROJECTION_ID,
        team_id="semantic-team",
        agent_id=f"agent-{persona_id}",
        persona_id=persona_id,
        persona_run_index=1,
        persona_configuration_fingerprint=sha256(
            persona_id.encode("utf-8")
        ).hexdigest(),
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        candidates=(selected,),
        no_candidate_rationale=None,
        timestamp=TIMESTAMP,
    )


def consensus_result(
    *,
    second_statement: str = "Alpha is present.",
    assumption: bool = False,
) -> object:
    first_candidate = candidate(
        epistemic_class=(
            "assumption" if assumption else "explicit"
        ),
        missing_evidence=(
            "Operating context is not stated."
            if assumption
            else None
        ),
    )
    second_candidate = candidate(
        statement=second_statement,
        epistemic_class=(
            "assumption" if assumption else "explicit"
        ),
        missing_evidence=(
            "Operating context is not stated."
            if assumption
            else None
        ),
    )
    return analyze_semantic_consensus(
        agent_results=(
            agent_result(
                "persona-a",
                selected_candidate=first_candidate,
            ),
            agent_result(
                "persona-b",
                selected_candidate=second_candidate,
            ),
        ),
        required_personas=(
            "persona-a",
            "persona-b",
        ),
        expected_runs_per_persona={
            "persona-a": 1,
            "persona-b": 1,
        },
        source_projection=projection(),
        consensus_report_id=CONSENSUS_REPORT_ID,
        timestamp=CONSENSUS_TIMESTAMP,
    )


def prepared_request() -> SemanticPublicationRequest:
    return prepare_semantic_publication_request(
        consensus_result(),
        CONSENSUS_CANDIDATE_ID,
    )


def authorization_for(
    request: SemanticPublicationRequest,
) -> SemanticPublicationAuthorization:
    return create_semantic_publication_authorization(
        project_id=request.project_id,
        consensus_report_id=request.consensus_report_id,
        consensus_candidate_id=(
            request.consensus_candidate_id
        ),
        publication_request_fingerprint=(
            request.publication_request_fingerprint
        ),
        decision=CONFIRM_PUBLISH_DECISION,
        review_mode=QUICK_CONFIRMATION_REVIEW_MODE,
        review_decision_id="REVIEW-DECISION-000001",
        reviewer_id="reviewer-moritz",
        decided_at=DECISION_TIMESTAMP,
    )


class RecordingRepository:
    def __init__(
        self,
        *,
        failure: Exception | None = None,
        mismatch: str | None = None,
    ) -> None:
        self.failure = failure
        self.mismatch = mismatch
        self.calls: list[dict[str, object]] = []

    def create_information_unit(
        self,
        project_id: str,
        source_id: str,
        source_projection_id: str,
        **kwargs: object,
    ) -> InformationUnit:
        self.calls.append(
            {
                "project_id": project_id,
                "source_id": source_id,
                "source_projection_id": source_projection_id,
                **kwargs,
            }
        )
        if self.failure is not None:
            raise self.failure

        values = {
            "schema_version": "1.0.0",
            "project_id": project_id,
            "information_unit_id": "IU-000001",
            "source_id": source_id,
            "source_projection_id": source_projection_id,
            "source_anchors": tuple(
                kwargs["source_anchors"]
            ),
            "source_excerpt": kwargs["source_excerpt"],
            "interpreted_statement": (
                kwargs["interpreted_statement"]
            ),
            "information_type": kwargs["information_type"],
            "statement_modality": (
                kwargs["statement_modality"]
            ),
            "epistemic_class": kwargs["epistemic_class"],
            "supporting_information_unit_ids": tuple(
                kwargs["supporting_information_unit_ids"]
            ),
            "derivation_rationale": (
                kwargs["derivation_rationale"]
            ),
            "missing_evidence": kwargs["missing_evidence"],
            "extraction_provenance": (
                kwargs["extraction_provenance"]
            ),
            "confidence": kwargs["confidence"],
            "confidence_rationale": (
                kwargs["confidence_rationale"]
            ),
            "content_fingerprint": "e" * 64,
            "created_at": DECISION_TIMESTAMP,
        }
        if self.mismatch is not None:
            mismatch_values = {
                "source_anchors": (),
                "supporting_information_unit_ids": (
                    "IU-999999",
                ),
                "extraction_provenance": (),
            }
            values[self.mismatch] = mismatch_values.get(
                self.mismatch,
                "mismatched",
            )
        return InformationUnit(**values)


def test_publication_contract_versions_are_explicit() -> None:
    assert SEMANTIC_PUBLICATION_REQUEST_SCHEMA_VERSION == "1.0.0"
    assert (
        SEMANTIC_PUBLICATION_AUTHORIZATION_SCHEMA_VERSION
        == "1.0.0"
    )


def test_publication_records_are_frozen_and_slotted() -> None:
    assert SemanticPublicationRequest.__dataclass_params__.frozen
    assert SemanticPublicationRequest.__slots__
    assert (
        SemanticPublicationAuthorization.__dataclass_params__.frozen
    )
    assert SemanticPublicationAuthorization.__slots__


def test_preparation_creates_bound_request() -> None:
    request = prepared_request()

    assert request.project_id == PROJECT_ID
    assert request.source_id == SOURCE_ID
    assert request.source_projection_id == SOURCE_PROJECTION_ID
    assert request.consensus_report_id == CONSENSUS_REPORT_ID
    assert (
        request.consensus_candidate_id
        == CONSENSUS_CANDIDATE_ID
    )
    assert request.required_personas == (
        "persona-a",
        "persona-b",
    )
    assert request.confidence == "high"
    assert request.confirmation_required is True
    assert request.review_required is False
    assert request.publication_eligible is True
    assert (
        request.recommended_review_mode
        == QUICK_CONFIRMATION_REVIEW_MODE
    )


def test_request_does_not_contain_final_information_unit_id() -> None:
    request_field_names = {
        field.name for field in fields(SemanticPublicationRequest)
    }
    draft_field_names = {
        field.name
        for field in fields(type(prepared_request().proposed_information_unit))
    }

    assert "information_unit_id" not in request_field_names
    assert "information_unit_id" not in draft_field_names


def test_request_does_not_claim_human_decision() -> None:
    request_field_names = {
        field.name for field in fields(SemanticPublicationRequest)
    }

    assert "decision" not in request_field_names
    assert "reviewer_id" not in request_field_names
    assert "review_decision_id" not in request_field_names
    assert "decided_at" not in request_field_names


def test_preparation_is_deterministic() -> None:
    first = prepared_request()
    second = prepared_request()

    assert first == second
    assert (
        first.publication_request_fingerprint
        == second.publication_request_fingerprint
    )
    assert (
        calculate_semantic_publication_request_fingerprint(first)
        == first.publication_request_fingerprint
    )


def test_changed_professional_content_changes_fingerprint() -> None:
    request = prepared_request()
    changed_draft = replace(
        request.proposed_information_unit,
        interpreted_statement="Changed statement.",
    )
    changed = replace(
        request,
        proposed_information_unit=changed_draft,
    )

    assert (
        calculate_semantic_publication_request_fingerprint(changed)
        != request.publication_request_fingerprint
    )


def test_request_is_immutable() -> None:
    request = prepared_request()

    with pytest.raises(FrozenInstanceError):
        request.confidence = "low"


def test_unknown_candidate_cannot_be_prepared() -> None:
    with pytest.raises(SemanticConsensusReferenceError):
        prepare_semantic_publication_request(
            consensus_result(),
            "SCC-000002",
        )


@pytest.mark.parametrize(
    "candidate_id",
    ["", "SCC-000000", "SCC-1", "IUC-000001"],
)
def test_invalid_candidate_id_cannot_be_prepared(
    candidate_id: str,
) -> None:
    with pytest.raises(SemanticConsensusValidationError):
        prepare_semantic_publication_request(
            consensus_result(),
            candidate_id,
        )


def test_disagreement_cannot_be_prepared() -> None:
    result = consensus_result(
        second_statement="Different statement.",
    )

    with pytest.raises(
        SemanticConsensusPublicationNotAuthorizedError
    ):
        prepare_semantic_publication_request(
            result,
            CONSENSUS_CANDIDATE_ID,
        )


def test_assumption_requiring_review_cannot_be_prepared() -> None:
    result = consensus_result(assumption=True)

    with pytest.raises(
        SemanticConsensusPublicationNotAuthorizedError
    ):
        prepare_semantic_publication_request(
            result,
            CONSENSUS_CANDIDATE_ID,
        )


def test_preparation_performs_no_repository_write() -> None:
    repository = RecordingRepository()

    prepared_request()

    assert repository.calls == []


def test_authorization_is_bound_to_request() -> None:
    request = prepared_request()
    authorization = authorization_for(request)

    assert authorization.project_id == request.project_id
    assert (
        authorization.consensus_report_id
        == request.consensus_report_id
    )
    assert (
        authorization.consensus_candidate_id
        == request.consensus_candidate_id
    )
    assert (
        authorization.publication_request_fingerprint
        == request.publication_request_fingerprint
    )
    assert authorization.decision == "confirm_publish"
    assert authorization.review_mode == "quick_confirmation"
    assert authorization.reviewer_id == "reviewer-moritz"


def test_authorization_is_immutable() -> None:
    authorization = authorization_for(prepared_request())

    with pytest.raises(FrozenInstanceError):
        authorization.decision = "reject"


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("project_id", "000000"),
        ("project_id", "31860"),
        ("consensus_report_id", ""),
        ("consensus_report_id", " report "),
        ("consensus_candidate_id", "SCC-000000"),
        ("publication_request_fingerprint", "A" * 64),
        ("publication_request_fingerprint", "a" * 63),
        ("review_decision_id", ""),
        ("review_decision_id", " decision "),
        ("reviewer_id", ""),
        ("reviewer_id", " reviewer "),
        ("decided_at", "2026-07-24"),
        ("decided_at", "2026-07-24T12:00:00+00:00"),
    ],
)
def test_authorization_rejects_invalid_binding_data(
    field_name: str,
    value: str,
) -> None:
    request = prepared_request()
    values = {
        "project_id": request.project_id,
        "consensus_report_id": request.consensus_report_id,
        "consensus_candidate_id": (
            request.consensus_candidate_id
        ),
        "publication_request_fingerprint": (
            request.publication_request_fingerprint
        ),
        "decision": CONFIRM_PUBLISH_DECISION,
        "review_mode": QUICK_CONFIRMATION_REVIEW_MODE,
        "review_decision_id": "REVIEW-DECISION-000001",
        "reviewer_id": "reviewer-moritz",
        "decided_at": DECISION_TIMESTAMP,
    }
    values[field_name] = value

    with pytest.raises(
        (
            SemanticConsensusValidationError,
            SemanticConsensusPublicationNotAuthorizedError,
        )
    ):
        create_semantic_publication_authorization(**values)


@pytest.mark.parametrize(
    "decision",
    ["reject", "open_detailed_review", "", "confirm"],
)
def test_non_confirmation_decision_never_authorizes(
    decision: str,
) -> None:
    request = prepared_request()

    with pytest.raises(
        SemanticConsensusPublicationNotAuthorizedError
    ):
        create_semantic_publication_authorization(
            project_id=request.project_id,
            consensus_report_id=request.consensus_report_id,
            consensus_candidate_id=(
                request.consensus_candidate_id
            ),
            publication_request_fingerprint=(
                request.publication_request_fingerprint
            ),
            decision=decision,
            review_mode=QUICK_CONFIRMATION_REVIEW_MODE,
            review_decision_id="REVIEW-DECISION-000001",
            reviewer_id="reviewer-moritz",
            decided_at=DECISION_TIMESTAMP,
        )


@pytest.mark.parametrize(
    "review_mode",
    ["detailed_review", "", "automatic"],
)
def test_non_quick_review_mode_never_authorizes(
    review_mode: str,
) -> None:
    request = prepared_request()

    with pytest.raises(
        SemanticConsensusPublicationNotAuthorizedError
    ):
        create_semantic_publication_authorization(
            project_id=request.project_id,
            consensus_report_id=request.consensus_report_id,
            consensus_candidate_id=(
                request.consensus_candidate_id
            ),
            publication_request_fingerprint=(
                request.publication_request_fingerprint
            ),
            decision=CONFIRM_PUBLISH_DECISION,
            review_mode=review_mode,
            review_decision_id="REVIEW-DECISION-000001",
            reviewer_id="reviewer-moritz",
            decided_at=DECISION_TIMESTAMP,
        )


def test_request_without_authorization_cannot_publish() -> None:
    request = prepared_request()
    repository = RecordingRepository()

    with pytest.raises(SemanticConsensusValidationError):
        publish_confirmed_information_unit(
            request,
            None,
            repository,
        )

    assert repository.calls == []


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("project_id", "318605"),
        ("consensus_report_id", "CONSENSUS-OTHER"),
        ("consensus_candidate_id", "SCC-000002"),
        ("publication_request_fingerprint", "f" * 64),
        ("review_mode", "detailed_review"),
    ],
)
def test_mismatched_authorization_cannot_publish(
    field_name: str,
    value: str,
) -> None:
    request = prepared_request()
    authorization = replace(
        authorization_for(request),
        **{field_name: value},
    )
    repository = RecordingRepository()

    with pytest.raises(
        SemanticConsensusPublicationNotAuthorizedError
    ):
        publish_confirmed_information_unit(
            request,
            authorization,
            repository,
        )

    assert repository.calls == []


def test_tampered_request_cannot_publish() -> None:
    request = prepared_request()
    changed = replace(
        request,
        confidence_rationale="Tampered rationale.",
    )
    repository = RecordingRepository()

    with pytest.raises(SemanticConsensusIntegrityError):
        publish_confirmed_information_unit(
            changed,
            authorization_for(request),
            repository,
        )

    assert repository.calls == []


def test_confirmed_request_publishes_exactly_once() -> None:
    request = prepared_request()
    authorization = authorization_for(request)
    repository = RecordingRepository()

    information_unit = publish_confirmed_information_unit(
        request,
        authorization,
        repository,
    )

    assert information_unit.information_unit_id == "IU-000001"
    assert len(repository.calls) == 1


def test_repository_allocates_final_information_unit_id() -> None:
    request = prepared_request()
    repository = RecordingRepository()

    publish_confirmed_information_unit(
        request,
        authorization_for(request),
        repository,
    )

    call = repository.calls[0]
    assert "information_unit_id" not in call


def test_publication_forwards_exact_professional_content() -> None:
    request = prepared_request()
    repository = RecordingRepository()

    publish_confirmed_information_unit(
        request,
        authorization_for(request),
        repository,
    )

    call = repository.calls[0]
    draft = request.proposed_information_unit
    assert call["source_anchors"] == draft.source_anchors
    assert call["source_excerpt"] == draft.source_excerpt
    assert (
        call["interpreted_statement"]
        == draft.interpreted_statement
    )
    assert call["information_type"] == draft.information_type
    assert (
        call["statement_modality"]
        == draft.statement_modality
    )
    assert call["epistemic_class"] == draft.epistemic_class
    assert (
        call["supporting_information_unit_ids"]
        == draft.supporting_information_unit_ids
    )
    assert (
        call["derivation_rationale"]
        == draft.derivation_rationale
    )
    assert call["missing_evidence"] == draft.missing_evidence


def test_publication_builds_exact_extraction_provenance() -> None:
    request = prepared_request()
    repository = RecordingRepository()

    publish_confirmed_information_unit(
        request,
        authorization_for(request),
        repository,
    )

    assert repository.calls[0]["extraction_provenance"] == (
        InformationUnitExtractionProvenance(
            team_id=request.team_id,
            persona_ids=request.required_personas,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            prompt_schema_version=request.prompt_schema_version,
            consensus_report_id=request.consensus_report_id,
        )
    )


def test_repository_failure_is_wrapped() -> None:
    request = prepared_request()
    repository = RecordingRepository(
        failure=RuntimeError("disk failure")
    )

    try:
        publish_confirmed_information_unit(
            request,
            authorization_for(request),
            repository,
        )
    except SemanticConsensusPublicationError as exc:
        assert isinstance(exc.__cause__, RuntimeError)
    else:
        raise AssertionError(
            "Repository failure must be wrapped."
        )


@pytest.mark.parametrize(
    "mismatch",
    [
        "project_id",
        "source_id",
        "source_projection_id",
        "source_anchors",
        "source_excerpt",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "supporting_information_unit_ids",
        "derivation_rationale",
        "missing_evidence",
        "extraction_provenance",
        "confidence",
        "confidence_rationale",
    ],
)
def test_repository_return_value_must_match_authorized_request(
    mismatch: str,
) -> None:
    request = prepared_request()
    repository = RecordingRepository(mismatch=mismatch)

    with pytest.raises(SemanticConsensusIntegrityError):
        publish_confirmed_information_unit(
            request,
            authorization_for(request),
            repository,
        )


def test_non_repository_object_is_rejected() -> None:
    request = prepared_request()

    with pytest.raises(SemanticConsensusValidationError):
        publish_confirmed_information_unit(
            request,
            authorization_for(request),
            object(),
        )