"""LLM-assisted Project Fit assessment service."""

from __future__ import annotations

from modules.llm.factory import create_llm_client
from modules.llm.progress import notify_llm_progress
from modules.llm.types import LLMRequest
from modules.project_processing.types import ProcessingRunManifest
from modules.project_workspace.types import ProjectManifest
from modules.source_projection.types import SourceProjectionArtifact

from .contract import (
    create_project_fit_assessment,
    parse_project_fit_response,
    prepare_project_fit_context,
)
from .prompt import (
    PROJECT_FIT_PROMPT_SCHEMA_VERSION,
    build_project_fit_input,
    build_project_fit_instructions,
)
from .types import ProjectFitAssessment


class ProjectFitAssessmentService:
    """Assess source-to-project plausibility without granting authority."""

    def __init__(self, *, client_factory=create_llm_client) -> None:
        self._client_factory = client_factory

    def assess(
        self,
        project: ProjectManifest,
        run_manifest: ProcessingRunManifest,
        candidate: SourceProjectionArtifact,
        available_projections: tuple[SourceProjectionArtifact, ...],
        *,
        attempt_id: str,
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
    ) -> ProjectFitAssessment:
        context_references, content_by_ref, input_fingerprint = (
            prepare_project_fit_context(
                project,
                run_manifest,
                candidate,
                available_projections,
                attempt_id=attempt_id,
            )
        )

        candidate_manifest = candidate.manifest
        input_text = build_project_fit_input(
            project_id=project.project_id,
            display_name=project.display_name,
            description=project.description,
            candidate_metadata={
                "reference_id": (
                    "candidate_source_projection:"
                    f"{candidate_manifest.source_projection_id}"
                ),
                "source_id": candidate_manifest.source_id,
                "source_role": candidate_manifest.source_role,
                "source_projection_id": candidate_manifest.source_projection_id,
                "projection_result": candidate_manifest.projection_result,
            },
            candidate_content=candidate.content,
            context_references=context_references,
            context_content_by_ref=content_by_ref,
        )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="planned",
                stage="project_fit_assessment",
                request_count=1,
            )

        result = self._client_factory(provider).generate(
            LLMRequest(
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=build_project_fit_instructions(),
                input_text=input_text,
                metadata={
                    "task_name": "project_fit_assessment",
                    "prompt_schema_version": PROJECT_FIT_PROMPT_SCHEMA_VERSION,
                    "project_id": project.project_id,
                    "source_id": candidate_manifest.source_id,
                    "source_projection_id": (
                        candidate_manifest.source_projection_id
                    ),
                    "processing_run_id": run_manifest.processing_run_id,
                    "attempt_id": attempt_id,
                    "context_reference_count": len(context_references),
                },
            )
        )

        if llm_progress_observer is not None:
            notify_llm_progress(
                llm_progress_observer,
                event_type="completed",
                stage="project_fit_assessment",
                request_count=1,
            )

        parsed = parse_project_fit_response(
            result.text,
            allowed_context_refs=tuple(
                reference.reference_id
                for reference in context_references
            ),
        )

        return create_project_fit_assessment(
            project=project,
            run_manifest=run_manifest,
            candidate=candidate,
            attempt_id=attempt_id,
            context_references=context_references,
            input_fingerprint=input_fingerprint,
            parsed_response=parsed,
            llm_provider=result.provider,
            llm_model=result.model,
            llm_response_id=result.response_id,
        )
