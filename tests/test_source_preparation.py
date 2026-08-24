"""Integration tests for reusable Source Preparation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from modules.evidence_detection import EvidenceDetectionAgent
from modules.llm.types import LLMResult
from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.source_preparation import SourcePreparationService


PROJECT_ID = "318604"


def fixed_clock() -> datetime:
    return datetime(
        2026, 8, 21, 10, 0, 0, tzinfo=timezone.utc
    )


class AdaptiveFakeClient:
    def __init__(self) -> None:
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if "temporary control" in request.input_text:
            output = """{
              "detections": [{
                "candidate_span_ids": ["CAND-001"],
                "relevance": "relevant",
                "rationale": "Concrete control information."
              }],
              "no_detection_rationale": null
            }"""
        else:
            output = """{
              "detections": [],
              "no_detection_rationale": "No engineering passage in this scope."
            }"""
        return LLMResult(
            text=output,
            provider="openai",
            model=request.model,
            response_id=f"resp_{len(self.requests):03d}",
            raw_status="completed",
        )


def environment(
    tmp_path: Path,
    source_role: str,
) -> tuple[Path, str, Path]:
    projects_root = tmp_path / "data" / "projects"
    inputs = tmp_path / "inputs"
    inputs.mkdir(parents=True)

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Source Preparation Test")

    source_path = inputs / "source.md"
    source_path.write_text(
        "# Demo\n\n"
        "The operator may grant temporary control to the remote expert.\n",
        encoding="utf-8",
    )

    registry = ProjectSourceRegistry(
        root=projects_root,
        clock=fixed_clock,
    )
    source = registry.register_source(
        PROJECT_ID,
        source_path,
        source_role=source_role,
    )

    examples = tmp_path / "examples.md"
    examples.write_text(
        "REFERENCE EXAMPLE ONLY — never project evidence.",
        encoding="utf-8",
    )
    return projects_root, source.source_id, examples


def service_for(
    projects_root: Path,
    examples: Path,
    fake: AdaptiveFakeClient,
) -> SourcePreparationService:
    return SourcePreparationService(
        root=projects_root,
        repository_root=projects_root.parent.parent,
        clock=fixed_clock,
        detector=EvidenceDetectionAgent(
            client_factory=lambda provider: fake
        ),
        reference_examples_path=examples,
    )


def test_live_preparation_persists_evidence(
    tmp_path: Path,
) -> None:
    projects_root, source_id, examples = environment(
        tmp_path,
        ENGINEERING_SOURCE_ROLE,
    )
    fake = AdaptiveFakeClient()
    service = service_for(projects_root, examples, fake)

    result = service.prepare_registered_source(
        PROJECT_ID,
        source_id,
        provider="openai",
        model="gpt-test",
    )

    assert result.status == "prepared"
    assert result.source_evidence_ids == ("EVD-000001",)
    assert (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_evidence"
        / "EVD-000001.json"
    ).is_file()
    assert (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_preparation"
        / result.source_projection_id
        / f"{result.preparation_fingerprint}.json"
    ).is_file()


def test_same_preparation_is_reused_without_second_llm_pass(
    tmp_path: Path,
) -> None:
    projects_root, source_id, examples = environment(
        tmp_path,
        ENGINEERING_SOURCE_ROLE,
    )
    fake = AdaptiveFakeClient()
    service = service_for(projects_root, examples, fake)

    first = service.prepare_registered_source(
        PROJECT_ID,
        source_id,
        provider="openai",
        model="gpt-test",
    )
    calls = len(fake.requests)
    second = service.prepare_registered_source(
        PROJECT_ID,
        source_id,
        provider="openai",
        model="gpt-test",
    )

    assert second == first
    assert len(fake.requests) == calls


def test_context_only_source_never_calls_detector(
    tmp_path: Path,
) -> None:
    projects_root, source_id, examples = environment(
        tmp_path,
        CONTEXT_ONLY_SOURCE_ROLE,
    )
    fake = AdaptiveFakeClient()
    service = service_for(projects_root, examples, fake)

    result = service.prepare_registered_source(
        PROJECT_ID,
        source_id,
        provider="openai",
        model="gpt-test",
    )

    assert result.status == "skipped_context_only"
    assert result.source_evidence_ids == ()
    assert fake.requests == []
