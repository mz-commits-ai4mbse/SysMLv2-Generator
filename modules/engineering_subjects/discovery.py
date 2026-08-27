"""Execute one shared LLM call for canonical subject discovery."""

from __future__ import annotations

from collections.abc import Callable

from modules.llm.factory import create_llm_client
from modules.llm.progress import (
    LLMRequestProgressObserver,
    notify_llm_progress,
)
from modules.llm.types import LLMRequest
from modules.source_evidence.types import SourceEvidence
from modules.source_projection.types import SourceProjectionArtifact

from .context import (
    build_context_preserving_source_input,
    build_discovery_source_spans,
)
from .contract import (
    materialize_canonical_subject_set,
    parse_subject_discovery_output,
)
from .errors import EngineeringSubjectGroundingError
from .grounding import (
    ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION,
    build_engineering_subject_grounding_repair_instructions,
)
from .prompt import (
    ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION,
    build_engineering_subject_discovery_instructions,
)
from .types import EngineeringSubjectDiscoveryResult


ClientFactory = Callable[[str], object]
RawResponseObserver = Callable[[str, object], None]


class EngineeringSubjectDiscoveryAgent:
    """Discover one shared subject population before Persona interpretation."""

    def __init__(
        self,
        *,
        client_factory: ClientFactory = create_llm_client,
    ) -> None:
        self._client_factory = client_factory

    def discover(
        self,
        *,
        source_projection: SourceProjectionArtifact,
        source_evidence: tuple[SourceEvidence, ...],
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
        raw_response_observer: RawResponseObserver | None = None,
    ) -> EngineeringSubjectDiscoveryResult:
        spans = build_discovery_source_spans(
            source_projection,
            source_evidence,
        )
        input_text = build_context_preserving_source_input(
            source_projection,
            spans,
        )
        instructions = (
            build_engineering_subject_discovery_instructions()
        )

        client = self._client_factory(provider)
        result = self._generate(
            client=client,
            provider=provider,
            model=model,
            api_key=api_key,
            instructions=instructions,
            input_text=input_text,
            retry=False,
        )
        self._observe_raw_response(
            raw_response_observer,
            response_kind="initial",
            result=result,
        )
        notify_llm_progress(
            llm_progress_observer,
            event_type="completed",
            stage="subject_discovery",
            detail="canonical subject discovery",
        )

        try:
            proposals = parse_subject_discovery_output(result.text)
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
        except EngineeringSubjectGroundingError as exc:
            correction_instructions = (
                build_engineering_subject_grounding_repair_instructions(
                    base_instructions=instructions,
                    error=exc,
                )
            )
            correction_input = (
                input_text
                + "\n\nPREVIOUS_INVALID_DISCOVERY_OUTPUT\n"
                + result.text
                + "\nEND_PREVIOUS_INVALID_DISCOVERY_OUTPUT"
            )

            notify_llm_progress(
                llm_progress_observer,
                event_type="planned",
                stage="subject_discovery",
                detail="grounding correction retry",
            )
            result = self._generate(
                client=client,
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=correction_instructions,
                input_text=correction_input,
                retry=True,
            )
            self._observe_raw_response(
                raw_response_observer,
                response_kind="grounding_correction",
                result=result,
            )
            notify_llm_progress(
                llm_progress_observer,
                event_type="completed",
                stage="subject_discovery",
                detail="grounding correction retry",
            )

            proposals = parse_subject_discovery_output(result.text)
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

        return EngineeringSubjectDiscoveryResult(
            source_spans=spans,
            canonical_subject_set=subject_set,
            provider=result.provider,
            model=result.model,
            response_id=result.response_id,
        )

    @staticmethod
    def _observe_raw_response(
        observer: RawResponseObserver | None,
        *,
        response_kind: str,
        result,
    ) -> None:
        """Expose one completed raw response before semantic validation."""

        if observer is None:
            return
        observer(response_kind, result)

    def _generate(
        self,
        *,
        client,
        provider: str,
        model: str,
        api_key: str | None,
        instructions: str,
        input_text: str,
        retry: bool,
    ):
        return client.generate(
            LLMRequest(
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=instructions,
                input_text=input_text,
                metadata={
                    "task_name": "canonical_engineering_subject_discovery",
                    "prompt_schema_version": (
                        ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION
                    ),
                    "grounding_correction_retry": retry,
                    **(
                        {
                            "grounding_repair_schema_version": (
                                ENGINEERING_SUBJECT_GROUNDING_REPAIR_SCHEMA_VERSION
                            )
                        }
                        if retry
                        else {}
                    ),
                },
            )
        )
