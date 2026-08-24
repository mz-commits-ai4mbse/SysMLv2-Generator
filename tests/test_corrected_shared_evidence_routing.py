"""R4b integration test for corrected Processing-to-Review routing."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from modules.agents.types import AgentRunResult
from modules.evidence_detection import EvidenceDetectionAgent
from modules.evidence_interpretation import (
    SharedEvidenceInterpretationPipeline,
)
from modules.llm.types import LLMResult
from modules.project_ingestion import (
    CORRECTED_PIPELINE_CONFIGURATION_VERSION,
    ProjectBoundIngestionService,
    ProjectIngestionConfiguration,
)
from modules.project_sources import ENGINEERING_SOURCE_ROLE
from modules.project_workspace import ProjectWorkspace
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)
from modules.source_preparation import SourcePreparationService


PROJECT_ID = "318604"


def fixed_clock() -> datetime:
    return datetime(
        2026,
        8,
        21,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )


class DetectionClient:
    def generate(self, request):
        if "temporary control" in request.input_text:
            text = """
            {
              "detections": [
                {
                  "candidate_span_ids": ["CAND-001"],
                  "relevance": "relevant",
                  "rationale": "Concrete permissioned control behavior."
                }
              ],
              "no_detection_rationale": null
            }
            """
        else:
            text = """
            {
              "detections": [],
              "no_detection_rationale": "No relevant engineering content."
            }
            """
        return LLMResult(
            text=text,
            provider="openai",
            model=request.model,
            response_id="resp_detection",
            raw_status="completed",
        )


def interpretation_runner(**kwargs):
    agent_ids = (
        "AGENT_LEGACY_LITERAL_INTERPRETER",
        "AGENT_LEGACY_SYSTEMS_ENGINEERING_INTERPRETER",
        "AGENT_LEGACY_SKEPTICAL_AMBIGUITY_INTERPRETER",
    )
    results = []
    for index, agent_id in enumerate(agent_ids, start=1):
        payload = {
            "interpretations": [
                {
                    "source_evidence_id": "EVD-000001",
                    "interpreted_statement": (
                        "The remote expert may receive temporary control "
                        "when the operator permits it."
                    ),
                    "information_type": "function",
                    "statement_modality": "descriptive",
                    "epistemic_class": "explicit",
                    "missing_evidence": None,
                    "extraction_rationale": "Direct source wording.",
                    "uncertainties": [],
                },
            ]
        }
        results.append(
            AgentRunResult(
                agent_id=agent_id,
                task_name="Interpret fixed source-grounded Evidence",
                run_index=1,
                provider="openai",
                model="gpt-test",
                output_text=json.dumps(payload),
                output_path=Path(f"/tmp/raw-{index}.json"),
                response_id=f"resp_interp_{index}",
                status="completed",
            )
        )
    return results


def test_v2_bypasses_legacy_derivation_and_opens_evidence_review(
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace
    import re

    from modules.agents.team_config import load_team_config
    from modules.agents.team_runner import select_team_members
    from modules.engineering_subjects import (
        build_discovery_source_spans,
        materialize_canonical_subject_set,
        parse_subject_discovery_output,
    )
    from modules.subject_interpretation import SubjectInterpretationPipeline

    repo_root = tmp_path / "repo"
    projects_root = repo_root / "data" / "projects"
    repo_root.mkdir()

    examples_path = tmp_path / "examples.md"
    examples_path.write_text(
        "REFERENCE EXAMPLE ONLY.",
        encoding="utf-8",
    )

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Corrected Routing Test")

    detector = EvidenceDetectionAgent(
        client_factory=lambda provider: DetectionClient()
    )
    source_preparation = SourcePreparationService(
        root=projects_root,
        repository_root=repo_root,
        clock=fixed_clock,
        detector=detector,
        reference_examples_path=examples_path,
    )
    interpretation = SharedEvidenceInterpretationPipeline(
        project_root=Path("."),
        team_runner=interpretation_runner,
        clock=fixed_clock,
    )

    class DeterministicSubjectDiscovery:
        def discover(
            self,
            *,
            source_projection,
            source_evidence,
            **_kwargs,
        ):
            spans = build_discovery_source_spans(
                source_projection,
                source_evidence,
            )

            def token_range(*expected_words):
                expected = tuple(
                    word.casefold() for word in expected_words
                )
                for span in spans:
                    tokens = span.source_tokens
                    values = tuple(
                        token.exact_text.casefold()
                        for token in tokens
                    )
                    width = len(expected)
                    for index in range(
                        0,
                        len(values) - width + 1,
                    ):
                        if values[index : index + width] != expected:
                            continue
                        if not span.source_evidence_ids:
                            raise AssertionError(
                                "Test Subject mention resolved to a "
                                "context-only Source Span."
                            )
                        return (
                            span.span_id,
                            tokens[index].token_id,
                            tokens[index + width - 1].token_id,
                        )
                raise AssertionError(
                    "Required deterministic Subject phrase was "
                    f"not found: {expected_words!r}"
                )

            temporary = token_range("temporary", "control")
            permission = token_range(
                "operator",
                "permits",
                "it",
            )

            payload = {
                "subjects": [
                    {
                        "canonical_label": "Temporary Control",
                        "subject_form": "behavior",
                        "identity_status": "resolved",
                        "mentions": [
                            {
                                "source_span_id": temporary[0],
                                "start_token_id": temporary[1],
                                "end_token_id": temporary[2],
                            }
                        ],
                    },
                    {
                        "canonical_label": "Operator Permission",
                        "subject_form": "condition",
                        "identity_status": "resolved",
                        "mentions": [
                            {
                                "source_span_id": permission[0],
                                "start_token_id": permission[1],
                                "end_token_id": permission[2],
                            }
                        ],
                    },
                ]
            }
            proposals = parse_subject_discovery_output(
                json.dumps(payload)
            )
            subject_set = materialize_canonical_subject_set(
                project_id=source_projection.manifest.project_id,
                source_id=source_projection.manifest.source_id,
                source_projection_id=(
                    source_projection.manifest.source_projection_id
                ),
                source_projection_fingerprint=(
                    source_projection.manifest.projection_fingerprint
                ),
                source_spans=spans,
                proposals=proposals,
            )
            return SimpleNamespace(
                canonical_subject_set=subject_set
            )

    def subject_interpretation_runner(**kwargs):
        subject_ids = tuple(
            re.findall(
                r"^## (SUBJ-[0-9]{6})$",
                kwargs["input_text"],
                flags=re.MULTILINE,
            )
        )
        assert subject_ids == (
            "SUBJ-000001",
            "SUBJ-000002",
        )

        payload = {
            "interpretations": [
                {
                    "canonical_subject_id": subject_ids[0],
                    "interpreted_statement": (
                        "Temporary microscope control is an "
                        "operational function."
                    ),
                    "information_type": "function",
                    "statement_modality": "descriptive",
                    "epistemic_class": "explicit",
                    "missing_evidence": None,
                    "rationale": (
                        "The Source explicitly describes temporary "
                        "control."
                    ),
                    "uncertainties": [],
                },
                {
                    "canonical_subject_id": subject_ids[1],
                    "interpreted_statement": (
                        "Operator permission constrains temporary "
                        "control."
                    ),
                    "information_type": "constraint",
                    "statement_modality": "descriptive",
                    "epistemic_class": "explicit",
                    "missing_evidence": None,
                    "rationale": (
                        "The Source explicitly makes control "
                        "conditional on operator permission."
                    ),
                    "uncertainties": [],
                },
            ],
            "relationships": [],
        }

        team = load_team_config(
            project_root=kwargs["project_root"],
            team_file=kwargs["team_file"],
        )
        members = tuple(
            select_team_members(
                team_config=team,
                max_members=kwargs["max_members"],
                include_alternative_members=False,
            )
        )
        return tuple(
            SimpleNamespace(
                agent_id=member.agent_id,
                run_index=run_index,
                output_text=json.dumps(payload),
            )
            for member in members
            for run_index in range(
                1,
                kwargs["runs_per_member"] + 1,
            )
        )

    subject_interpretation = SubjectInterpretationPipeline(
        project_root=Path("."),
        team_runner=subject_interpretation_runner,
    )

    def legacy_pipeline_must_not_run(**kwargs):
        raise AssertionError(
            "Legacy Phase-F pipeline must be bypassed for v2."
        )

    service = ProjectBoundIngestionService(
        root=projects_root,
        repository_root=repo_root,
        project_workspace=workspace,
        source_preparation_service=source_preparation,
        shared_evidence_interpretation_pipeline=interpretation,
        engineering_subject_discovery_agent=(
            DeterministicSubjectDiscovery()
        ),
        subject_interpretation_pipeline=subject_interpretation,
        pipeline_runner=legacy_pipeline_must_not_run,
        clock=fixed_clock,
    )

    source = service.register_uploaded_source(
        PROJECT_ID,
        original_filename="source.md",
        content=(
            b"# Demo\n\nThe remote expert may take temporary control "
            b"when the operator permits it.\n"
        ),
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(
            provider="openai",
            model="gpt-test",
            runs_per_member=1,
            max_members_per_team=None,
            dry_run=False,
            pipeline_configuration_version=(
                CORRECTED_PIPELINE_CONFIGURATION_VERSION
            ),
        ),
    )

    assert result.run_state == "awaiting_review"
    assert result.failure_reason is None

    published_paths = {
        reference.repository_relative_path
        for reference in result.artifact_references
    }
    for filename in (
        "canonical_subject_set.json",
        "subject_interpretations.json",
        "subject_consensus.json",
        "subject_review_bundle.json",
    ):
        assert any(
            path.endswith(filename)
            for path in published_paths
        )

    assert any(
        path.endswith("shared_evidence_review_input.json")
        for path in published_paths
    )
    assert not any(
        "semantic_consolidation" in path
        for path in published_paths
    )

    review_service = ReviewApprovalWorkflowService(
        root=projects_root,
        repository_root=repo_root,
        clock=fixed_clock,
    )
    opened = review_service.open_or_create_review(
        PROJECT_ID,
        result.processing_run_id,
        opened_by="reviewer@example.test",
    )

    assert opened.created is True
    items = opened.workspace.revision.review_items
    assert len(items) == 2
    assert {
        item.stable_subject_key for item in items
    } == {
        "subject:subj-000001",
        "subject:subj-000002",
    }
    assert {
        item.original_report_locator for item in items
    } == {
        "subject_review:SUBJ-000001",
        "subject_review:SUBJ-000002",
    }
    assert all(not item.proposal_references for item in items)
