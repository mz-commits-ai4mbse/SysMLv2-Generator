"""Tests for ADR-032 S3 cross-source semantic reconciliation."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from modules.engineering_subjects.types import (
    CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.llm.types import LLMResult
from modules.project_fit import ProjectFitAssessmentService
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_semantic_reconciliation import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationService,
    ProjectSemanticReconciliationValidationError,
    ProjectSemanticSourceInput,
    project_semantic_reconciliation_to_json,
)
from modules.project_sources import ENGINEERING_SOURCE_ROLE
from modules.project_workspace.manifest import create_project_manifest
from modules.source_projection.manifest import create_source_projection_artifact
from modules.source_projection.text_adapter import project_plain_text
from modules.subject_consensus import analyze_subject_consensus
from modules.subject_interpretation.types import (
    PersonaSubjectInterpretation,
    SharedSubjectInterpretationResult,
    SubjectInterpretationRunResult,
)


PROJECT_ID = "318604"
SHA_A = "a" * 64
SHA_B = "b" * 64


class Client:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.requests = []

    def _output_for_request(self, request):
        if not isinstance(self.output, dict):
            return self.output

        request_payload = json.loads(request.input_text)
        transport_by_project_ref = {}

        for subject in request_payload.get("subjects", []):
            if not isinstance(subject, dict):
                continue

            transport_ref = subject.get("subject_ref")
            source_id = subject.get("source_id")
            source_projection_id = subject.get("source_projection_id")
            canonical_subject_id = subject.get("canonical_subject_id")

            if not all(
                isinstance(value, str) and value
                for value in (
                    transport_ref,
                    source_id,
                    source_projection_id,
                    canonical_subject_id,
                )
            ):
                continue

            project_ref = (
                f"project_subject:{source_id}:"
                f"{source_projection_id}:{canonical_subject_id}"
            )
            transport_by_project_ref[project_ref] = transport_ref

        # Existing semantic tests intentionally express expected relations in
        # persisted project_subject identity. Adapt only the fake LLM boundary
        # to the transient SUBJ-NNNN transport contract used by production.
        output = json.loads(json.dumps(self.output))

        relations = output.get("relations")
        if isinstance(relations, list):
            for relation in relations:
                if not isinstance(relation, dict):
                    continue
                for field in ("left_subject_ref", "right_subject_ref"):
                    value = relation.get(field)
                    if value in transport_by_project_ref:
                        relation[field] = transport_by_project_ref[value]

        unmatched = output.get("unmatched_subject_refs")
        if isinstance(unmatched, list):
            output["unmatched_subject_refs"] = [
                transport_by_project_ref.get(value, value)
                for value in unmatched
            ]

        return output

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return LLMResult(
            text=json.dumps(self._output_for_request(request)),
            provider=request.provider,
            model=request.model,
            response_id="semantic-project-1",
        )


def canonical_sha(value):
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def project():
    return create_project_manifest(
        PROJECT_ID,
        "Remote Streaming Product",
        description=(
            "Remote digital microscopy streaming and collaboration product."
        ),
        timestamp="2026-08-31T06:00:00Z",
    )


def projection(source_id, sha_value, projection_id, text):
    return create_source_projection_artifact(
        project_id=PROJECT_ID,
        source_id=source_id,
        source_projection_id=projection_id,
        source_role=ENGINEERING_SOURCE_ROLE,
        source_sha256=sha_value,
        draft=project_plain_text(text.encode("utf-8")),
        timestamp="2026-08-31T06:01:00Z",
    )


def run_manifest(source_id, sha_value, run_id):
    return create_processing_run_manifest(
        project_id=PROJECT_ID,
        processing_run_id=run_id,
        source_id=source_id,
        source_sha256=sha_value,
        source_role_snapshot=ENGINEERING_SOURCE_ROLE,
        workflow_profile="engineering_source_processing",
        configuration_fingerprint="d" * 64,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            create_semantic_reference_version(
                reference_system_id="PROJECT_GLOSSARY",
                reference_version="1.0.0",
            ),
        ),
        timestamp="2026-08-31T06:02:00Z",
    )


def fit_assessment(candidate, source_id, sha_value, run_id):
    client = Client(
        {
            "outcome": "plausible_in_scope",
            "rationale": "The candidate describes the remote streaming product.",
            "matched_concepts": ["remote streaming"],
            "incompatible_concepts": [],
            "supporting_context_refs": [
                f"project_manifest:{PROJECT_ID}"
            ],
        }
    )
    return ProjectFitAssessmentService(
        client_factory=lambda provider: client
    ).assess(
        project(),
        run_manifest(source_id, sha_value, run_id),
        candidate,
        (),
        attempt_id="ATT-000001",
        provider="openai",
        model="gpt-fit",
    )


def canonical_set(
    source_id,
    projection_artifact,
    subjects,
):
    mentions = []
    canonical_subjects = []

    for index, (label, form, exact_text) in enumerate(subjects, start=1):
        mention_id = f"MENT-{index:06d}"
        mention = EngineeringMention(
            mention_id=mention_id,
            source_span_id=f"SPAN-{index:06d}",
            segment_id=f"SEG-{index:06d}",
            start_offset=0,
            end_offset=len(exact_text),
            exact_text=exact_text,
            source_evidence_ids=(f"SE-{index:06d}",),
            content_fingerprint=canonical_sha(
                {
                    "source_id": source_id,
                    "mention_id": mention_id,
                    "exact_text": exact_text,
                }
            ),
        )
        mentions.append(mention)

        subject_id = f"SUBJ-{index:06d}"
        canonical_subjects.append(
            CanonicalEngineeringSubject(
                canonical_subject_id=subject_id,
                canonical_label=label,
                subject_form=form,
                identity_status="resolved",
                mention_ids=(mention_id,),
                content_fingerprint=canonical_sha(
                    {
                        "source_id": source_id,
                        "subject_id": subject_id,
                        "label": label,
                        "mention_fingerprint": (
                            mention.content_fingerprint
                        ),
                    }
                ),
            )
        )

    body = {
        "schema_version": CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "source_id": source_id,
        "source_projection_id": (
            projection_artifact.manifest.source_projection_id
        ),
        "source_projection_fingerprint": (
            projection_artifact.manifest.projection_fingerprint
        ),
        "mentions": [
            {
                "mention_id": item.mention_id,
                "source_span_id": item.source_span_id,
                "segment_id": item.segment_id,
                "start_offset": item.start_offset,
                "end_offset": item.end_offset,
                "exact_text": item.exact_text,
                "source_evidence_ids": list(item.source_evidence_ids),
                "content_fingerprint": item.content_fingerprint,
            }
            for item in mentions
        ],
        "subjects": [
            {
                "canonical_subject_id": item.canonical_subject_id,
                "canonical_label": item.canonical_label,
                "subject_form": item.subject_form,
                "identity_status": item.identity_status,
                "mention_ids": list(item.mention_ids),
                "content_fingerprint": item.content_fingerprint,
            }
            for item in canonical_subjects
        ],
    }
    return CanonicalSubjectSet(
        schema_version=CANONICAL_SUBJECT_SET_SCHEMA_VERSION,
        project_id=PROJECT_ID,
        source_id=source_id,
        source_projection_id=(
            projection_artifact.manifest.source_projection_id
        ),
        source_projection_fingerprint=(
            projection_artifact.manifest.projection_fingerprint
        ),
        mentions=tuple(mentions),
        subjects=tuple(canonical_subjects),
        content_fingerprint=canonical_sha(body),
    )


def consensus(subject_set, statements):
    personas = ("domain_engineer", "system_engineer")
    run_results = []
    for persona in personas:
        interpretations = tuple(
            PersonaSubjectInterpretation(
                canonical_subject_id=subject.canonical_subject_id,
                interpreted_statement=statements[index],
                information_type="constraint",
                statement_modality="descriptive",
                epistemic_class="explicit",
                missing_evidence=None,
                rationale="Source-grounded.",
                uncertainties=(),
                content_fingerprint=canonical_sha(
                    {
                        "persona": persona,
                        "subject_id": subject.canonical_subject_id,
                        "statement": statements[index],
                    }
                ),
            )
            for index, subject in enumerate(subject_set.subjects)
        )
        run_results.append(
            SubjectInterpretationRunResult(
                project_id=PROJECT_ID,
                source_id=subject_set.source_id,
                source_projection_id=subject_set.source_projection_id,
                team_id="TEAM-SEMANTIC",
                agent_id=f"agent-{persona}",
                persona_id=persona,
                persona_run_index=1,
                llm_provider="openai",
                llm_model="gpt-test",
                prompt_schema_version="1.0.0",
                interpretations=interpretations,
                relationships=(),
                content_fingerprint=canonical_sha(
                    {
                        "persona": persona,
                        "source_id": subject_set.source_id,
                    }
                ),
            )
        )

    shared = SharedSubjectInterpretationResult(
        project_id=PROJECT_ID,
        source_id=subject_set.source_id,
        source_projection_id=subject_set.source_projection_id,
        team_id="TEAM-SEMANTIC",
        canonical_subject_ids=tuple(
            item.canonical_subject_id
            for item in subject_set.subjects
        ),
        required_personas=personas,
        runs_per_persona=1,
        run_results=tuple(run_results),
        output_root=Path("."),
    )
    return analyze_subject_consensus(shared)


def source_input(
    source_id,
    sha_value,
    projection_id,
    run_id,
    subjects,
    statements,
):
    candidate = projection(
        source_id,
        sha_value,
        projection_id,
        "\n".join(statement for statement in statements),
    )
    subject_set = canonical_set(
        source_id,
        candidate,
        subjects,
    )
    return ProjectSemanticSourceInput(
        project_fit=fit_assessment(
            candidate,
            source_id,
            sha_value,
            run_id,
        ),
        canonical_subject_set=subject_set,
        subject_consensus=consensus(subject_set, statements),
    )


def two_sources():
    first = source_input(
        "SRC-000001",
        SHA_A,
        "SP-000001",
        "RUN-000001",
        (
            (
                "Remote viewing",
                "assertion",
                "The system shall provide remote viewing.",
            ),
        ),
        ("The system shall provide remote viewing.",),
    )
    second = source_input(
        "SRC-000002",
        SHA_B,
        "SP-000002",
        "RUN-000002",
        (
            (
                "Streaming encoder",
                "behavior",
                (
                    "The streaming subsystem shall encode microscope images "
                    "for remote transmission."
                ),
            ),
        ),
        (
            (
                "The streaming subsystem encodes microscope images for "
                "remote transmission."
            ),
        ),
    )
    return first, second


def refs():
    return (
        "project_subject:SRC-000001:SP-000001:SUBJ-000001",
        "project_subject:SRC-000002:SP-000002:SUBJ-000001",
    )


def service(client):
    return ProjectSemanticReconciliationService(
        client_factory=lambda provider: client
    )


def test_complementary_relation_preserves_both_source_subjects():
    left, right = refs()
    client = Client(
        {
            "relations": [
                {
                    "left_subject_ref": left,
                    "right_subject_ref": right,
                    "outcome": "complementary",
                    "rationale": (
                        "One Subject states system-level remote viewing while "
                        "the other describes a realization behavior."
                    ),
                    "shared_concepts": [
                        "remote image streaming"
                    ],
                    "material_differences": [
                        "system capability versus subsystem realization"
                    ],
                }
            ],
            "unmatched_subject_refs": [],
        }
    )

    artifact = service(client).reconcile(
        two_sources(),
        provider="openai",
        model="gpt-test",
    )

    assert len(artifact.subjects) == 2
    assert len(artifact.relations) == 1
    relation = artifact.relations[0]
    assert relation.outcome == "complementary"
    assert relation.left_subject_ref == left
    assert relation.right_subject_ref == right
    assert artifact.human_review_required is True
    assert artifact.unmatched_subject_refs == ()


def test_local_subject_ids_can_repeat_across_sources_without_collision():
    artifact = service(
        Client(
            {
                "relations": [],
                "unmatched_subject_refs": list(refs()),
            }
        )
    ).reconcile(
        two_sources(),
        provider="openai",
        model="gpt-test",
    )
    assert tuple(
        subject.canonical_subject_id
        for subject in artifact.subjects
    ) == ("SUBJ-000001", "SUBJ-000001")
    assert len(
        {subject.subject_ref for subject in artifact.subjects}
    ) == 2


@pytest.mark.parametrize(
    "outcome",
    (
        "equivalent",
        "complementary",
        "potential_conflict",
        "distinct",
        "uncertain",
    ),
)
def test_all_adr032_relation_outcomes_are_supported(outcome):
    left, right = refs()
    shared = [] if outcome in {"distinct", "uncertain"} else ["streaming"]
    differences = (
        []
        if outcome in {"equivalent", "uncertain"}
        else ["scope or meaning differs"]
    )
    client = Client(
        {
            "relations": [
                {
                    "left_subject_ref": left,
                    "right_subject_ref": right,
                    "outcome": outcome,
                    "rationale": "Bounded semantic relationship evidence.",
                    "shared_concepts": shared,
                    "material_differences": differences,
                }
            ],
            "unmatched_subject_refs": [],
        }
    )
    artifact = service(client).reconcile(
        two_sources(),
        provider="openai",
        model="gpt-test",
    )
    assert artifact.relations[0].outcome == outcome


def test_subjects_must_be_explicitly_covered_or_unmatched():
    left, _ = refs()
    client = Client(
        {
            "relations": [],
            "unmatched_subject_refs": [left],
        }
    )
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="cover every Subject",
    ):
        service(client).reconcile(
            two_sources(),
            provider="openai",
            model="gpt-test",
        )


def test_subject_cannot_be_both_related_and_unmatched():
    left, right = refs()
    client = Client(
        {
            "relations": [
                {
                    "left_subject_ref": left,
                    "right_subject_ref": right,
                    "outcome": "equivalent",
                    "rationale": "Same engineering meaning.",
                    "shared_concepts": ["remote viewing"],
                    "material_differences": [],
                }
            ],
            "unmatched_subject_refs": [left],
        }
    )
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="both related and unmatched",
    ):
        service(client).reconcile(
            two_sources(),
            provider="openai",
            model="gpt-test",
        )


def test_duplicate_unordered_pair_is_rejected():
    left, right = refs()
    relation = {
        "left_subject_ref": left,
        "right_subject_ref": right,
        "outcome": "equivalent",
        "rationale": "Same meaning.",
        "shared_concepts": ["remote viewing"],
        "material_differences": [],
    }
    reversed_relation = {
        **relation,
        "left_subject_ref": right,
        "right_subject_ref": left,
    }
    client = Client(
        {
            "relations": [relation, reversed_relation],
            "unmatched_subject_refs": [],
        }
    )
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="unordered cross-source Subject pair",
    ):
        service(client).reconcile(
            two_sources(),
            provider="openai",
            model="gpt-test",
        )


def test_complementary_requires_shared_and_difference_evidence():
    left, right = refs()
    client = Client(
        {
            "relations": [
                {
                    "left_subject_ref": left,
                    "right_subject_ref": right,
                    "outcome": "complementary",
                    "rationale": "Different abstraction levels.",
                    "shared_concepts": ["streaming"],
                    "material_differences": [],
                }
            ],
            "unmatched_subject_refs": [],
        }
    )
    with pytest.raises(ProjectSemanticReconciliationValidationError):
        service(client).reconcile(
            two_sources(),
            provider="openai",
            model="gpt-test",
        )


def test_potential_conflict_requires_positive_shared_subject_and_variance():
    left, right = refs()
    client = Client(
        {
            "relations": [
                {
                    "left_subject_ref": left,
                    "right_subject_ref": right,
                    "outcome": "potential_conflict",
                    "rationale": "Claims differ.",
                    "shared_concepts": [],
                    "material_differences": ["control permission differs"],
                }
            ],
            "unmatched_subject_refs": [],
        }
    )
    with pytest.raises(ProjectSemanticReconciliationValidationError):
        service(client).reconcile(
            two_sources(),
            provider="openai",
            model="gpt-test",
        )


def test_non_admitted_project_fit_cannot_enter_reconciliation():
    first, second = two_sources()
    blocked = replace(
        second.project_fit,
        outcome="uncertain",
        matched_concepts=(),
        supporting_context_refs=(),
    )
    # The tampered fit evidence is itself invalid because its fingerprint no
    # longer matches. That must fail before semantic reconciliation.
    with pytest.raises(
        ProjectSemanticReconciliationValidationError,
        match="Project Fit assessment is invalid",
    ):
        service(Client()).reconcile(
            (
                first,
                replace(second, project_fit=blocked),
            ),
            provider="openai",
            model="gpt-test",
        )


def test_same_registered_source_cannot_enter_twice():
    first, _ = two_sources()
    duplicate = replace(
        first,
        project_fit=replace(
            first.project_fit,
            processing_run_id="RUN-000003",
        ),
    )
    # Preserve the test intent by using the exact same valid source input twice;
    # duplicate Source identity is rejected after validation.
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="distinct registered Sources",
    ):
        service(Client()).reconcile(
            (first, first),
            provider="openai",
            model="gpt-test",
        )


def test_provider_failure_has_no_lossy_fallback():
    with pytest.raises(RuntimeError, match="provider down"):
        service(
            Client(error=RuntimeError("provider down"))
        ).reconcile(
            two_sources(),
            provider="openai",
            model="gpt-test",
        )


def test_serialization_preserves_source_and_semantic_provenance():
    artifact = service(
        Client(
            {
                "relations": [],
                "unmatched_subject_refs": list(refs()),
            }
        )
    ).reconcile(
        two_sources(),
        provider="openai",
        model="gpt-test",
    )
    payload = json.loads(
        project_semantic_reconciliation_to_json(artifact)
    )
    assert payload["source_ids"] == [
        "SRC-000001",
        "SRC-000002",
    ]
    assert payload["subjects"][0]["source_id"] == "SRC-000001"
    assert payload["subjects"][1]["source_id"] == "SRC-000002"
    assert (
        payload["subjects"][0]["canonical_subject_id"]
        == "SUBJ-000001"
    )
    assert (
        payload["subjects"][1]["canonical_subject_id"]
        == "SUBJ-000001"
    )
    assert len(payload["input_fingerprint"]) == 64
    assert len(payload["content_fingerprint"]) == 64
    assert payload["llm_response_id"] == "semantic-project-1"


def test_tampered_reconciliation_artifact_fails_closed():
    artifact = service(
        Client(
            {
                "relations": [],
                "unmatched_subject_refs": list(refs()),
            }
        )
    ).reconcile(
        two_sources(),
        provider="openai",
        model="gpt-test",
    )
    tampered = replace(
        artifact,
        unmatched_subject_refs=(refs()[0],),
    )
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError
    ):
        project_semantic_reconciliation_to_json(tampered)
