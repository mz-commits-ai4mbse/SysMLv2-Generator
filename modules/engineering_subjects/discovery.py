"""Execute one shared LLM call for canonical subject discovery."""

from __future__ import annotations

from collections.abc import Callable

from modules.llm.factory import create_llm_client
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
from .errors import EngineeringSubjectIntegrityError
from .prompt import (
    ENGINEERING_SUBJECT_DISCOVERY_PROMPT_SCHEMA_VERSION,
    build_engineering_subject_discovery_instructions,
)
from .types import EngineeringSubjectDiscoveryResult


ClientFactory = Callable[[str], object]


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
        except EngineeringSubjectIntegrityError as exc:
            correction_instructions = (
                instructions
                + "\n\nCORRECTION RETRY:\n"
                + "The previous JSON contained at least one mention whose "
                + "TOK-* range did not belong to the claimed SPAN-* or "
                + "otherwise violated system-owned source grounding. Return "
                + "the COMPLETE JSON again. Preserve the discovered subject "
                + "population unless grounding requires a correction. "
                + "Re-check every source_span_id and TOK-* range against the "
                + "visible TOKEN MAP before returning. Do not invent token "
                + "IDs or move a mention to another span without source "
                + "support.\n"
                + f"Validation error: {exc}"
            )
            correction_input = (
                input_text
                + "\n\nPREVIOUS_INVALID_DISCOVERY_OUTPUT\n"
                + result.text
                + "\nEND_PREVIOUS_INVALID_DISCOVERY_OUTPUT"
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
                },
            )
        )
