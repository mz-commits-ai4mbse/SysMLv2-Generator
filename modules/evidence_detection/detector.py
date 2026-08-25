"""Specialized persona-independent Evidence Detection Agent."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
import re
from typing import Any

from modules.llm.factory import create_llm_client
from modules.llm.progress import (
    LLMRequestProgressObserver,
    notify_llm_progress,
)
from modules.llm.types import LLMRequest
from modules.source_analysis_units.types import SourceAnalysisUnit
from modules.source_evidence.types import SourceEvidenceAnchor

from .candidate_spans import (
    build_candidate_spans,
    resolve_candidate_span_selection,
)
from .errors import (
    EvidenceDetectionGroundingError,
    EvidenceDetectionValidationError,
)
from .prompt import (
    EVIDENCE_DETECTION_INSTRUCTIONS,
    EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION,
    build_evidence_detection_input,
)
from .types import (
    EVIDENCE_RELEVANCE_VALUES,
    DetectedEvidenceSpan,
    EvidenceCandidateSpan,
    EvidenceDetectionResult,
)


ClientFactory = Callable[[str], Any]
_RESULT_FIELDS = frozenset({"detections", "no_detection_rationale"})
_DETECTION_FIELDS = frozenset(
    {"candidate_span_ids", "relevance", "rationale"}
)
_JSON_FENCE = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)


class EvidenceDetectionAgent:
    """Execute one specialized detector task without persona branching."""

    def __init__(
        self,
        *,
        client_factory: ClientFactory = create_llm_client,
    ) -> None:
        self._client_factory = client_factory

    def detect(
        self,
        *,
        source_analysis_unit: SourceAnalysisUnit,
        reference_examples: str,
        provider: str,
        model: str,
        api_key: str | None = None,
        dry_run: bool = False,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> EvidenceDetectionResult:
        """Detect exact source evidence through deterministic candidate IDs."""

        if not isinstance(source_analysis_unit, SourceAnalysisUnit):
            raise EvidenceDetectionValidationError(
                "source_analysis_unit must be a SourceAnalysisUnit instance."
            )
        if not isinstance(reference_examples, str) or not reference_examples:
            raise EvidenceDetectionValidationError(
                "reference_examples must be non-empty text."
            )
        if not isinstance(provider, str) or not provider.strip():
            raise EvidenceDetectionValidationError(
                "provider must be non-empty."
            )
        if not isinstance(model, str) or not model.strip():
            raise EvidenceDetectionValidationError(
                "model must be non-empty."
            )

        reference_sha = sha256(
            reference_examples.encode("utf-8")
        ).hexdigest()

        if dry_run:
            return EvidenceDetectionResult(
                source_analysis_unit_id=(
                    source_analysis_unit.source_analysis_unit_id
                ),
                provider=provider,
                model=model,
                prompt_schema_version=(
                    EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION
                ),
                reference_examples_sha256=reference_sha,
                detections=(),
                response_id=None,
                raw_status="dry_run",
            )

        candidate_spans = build_candidate_spans(
            source_analysis_unit
        )

        client = self._client_factory(provider)
        result = client.generate(
            LLMRequest(
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=EVIDENCE_DETECTION_INSTRUCTIONS,
                input_text=build_evidence_detection_input(
                    source_analysis_unit=source_analysis_unit,
                    reference_examples=reference_examples,
                    candidate_spans=candidate_spans,
                ),
                metadata={
                    "task": "source_grounded_evidence_detection",
                    "source_analysis_unit_id": (
                        source_analysis_unit.source_analysis_unit_id
                    ),
                    "prompt_schema_version": (
                        EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION
                    ),
                    "reference_examples_sha256": reference_sha,
                },
            )
        )
        notify_llm_progress(
            llm_progress_observer,
            event_type="completed",
            stage="evidence_detection",
            detail=source_analysis_unit.source_analysis_unit_id,
        )

        detections = parse_detection_response(
            getattr(result, "text", ""),
            source_analysis_unit=source_analysis_unit,
            candidate_spans=candidate_spans,
        )
        for detection in detections:
            resolve_detection_anchors(
                source_analysis_unit=source_analysis_unit,
                detected_excerpt=detection.source_excerpt,
                source_start_offset=detection.source_start_offset,
                source_end_offset=detection.source_end_offset,
            )

        return EvidenceDetectionResult(
            source_analysis_unit_id=(
                source_analysis_unit.source_analysis_unit_id
            ),
            provider=provider,
            model=model,
            prompt_schema_version=(
                EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION
            ),
            reference_examples_sha256=reference_sha,
            detections=detections,
            response_id=getattr(result, "response_id", None),
            raw_status=getattr(result, "raw_status", None),
        )


def parse_detection_response(
    text: str,
    *,
    source_analysis_unit: SourceAnalysisUnit,
    candidate_spans: tuple[EvidenceCandidateSpan, ...],
) -> tuple[DetectedEvidenceSpan, ...]:
    """Parse strict detector JSON and resolve IDs to exact source slices."""

    if not isinstance(text, str) or not text.strip():
        raise EvidenceDetectionValidationError(
            "Evidence Detection returned empty output."
        )

    match = _JSON_FENCE.fullmatch(text)
    normalized = match.group(1) if match else text.strip()

    try:
        payload = json.loads(
            normalized,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except EvidenceDetectionValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise EvidenceDetectionValidationError(
            f"Evidence Detection output is not valid JSON: {exc}."
        ) from exc

    item = _require_exact_object(
        payload,
        _RESULT_FIELDS,
        "Evidence Detection result",
    )
    raw = item["detections"]
    if not isinstance(raw, list):
        raise EvidenceDetectionValidationError(
            "detections must be a JSON array."
        )

    no_detection_rationale = item["no_detection_rationale"]
    if no_detection_rationale is not None and (
        not isinstance(no_detection_rationale, str)
        or not no_detection_rationale.strip()
        or no_detection_rationale != no_detection_rationale.strip()
    ):
        raise EvidenceDetectionValidationError(
            "no_detection_rationale must be null or trimmed text."
        )

    detections: list[DetectedEvidenceSpan] = []
    seen_source_ranges: set[tuple[int, int]] = set()
    used_candidate_ids: set[str] = set()

    for value in raw:
        detection = _parse_detection(
            value,
            source_analysis_unit=source_analysis_unit,
            candidate_spans=candidate_spans,
        )
        source_range = (
            detection.source_start_offset,
            detection.source_end_offset,
        )
        if source_range in seen_source_ranges:
            raise EvidenceDetectionValidationError(
                "Duplicate detector source ranges are not allowed."
            )
        overlap = used_candidate_ids.intersection(
            detection.candidate_span_ids
        )
        if overlap:
            raise EvidenceDetectionValidationError(
                "Candidate span IDs may not be reused across detections."
            )
        seen_source_ranges.add(source_range)
        used_candidate_ids.update(detection.candidate_span_ids)
        detections.append(detection)

    if detections and no_detection_rationale is not None:
        raise EvidenceDetectionValidationError(
            "no_detection_rationale must be null when detections exist."
        )
    if not detections and no_detection_rationale is None:
        raise EvidenceDetectionValidationError(
            "Empty detections require no_detection_rationale."
        )
    return tuple(detections)


def resolve_detection_anchors(
    *,
    source_analysis_unit: SourceAnalysisUnit,
    detected_excerpt: str,
    source_start_offset: int | None = None,
    source_end_offset: int | None = None,
) -> tuple[SourceEvidenceAnchor, ...]:
    """Resolve one exact source range onto Source Projection anchors."""

    if not isinstance(source_analysis_unit, SourceAnalysisUnit):
        raise EvidenceDetectionGroundingError(
            "source_analysis_unit must be a SourceAnalysisUnit instance."
        )
    if not isinstance(detected_excerpt, str) or not detected_excerpt:
        raise EvidenceDetectionGroundingError(
            "detected_excerpt must be non-empty exact source text."
        )

    if source_start_offset is None and source_end_offset is None:
        count = source_analysis_unit.source_excerpt.count(
            detected_excerpt
        )
        if count == 0:
            raise EvidenceDetectionGroundingError(
                "Detector excerpt is not present exactly in the source scope."
            )
        if count > 1:
            raise EvidenceDetectionGroundingError(
                "Detector excerpt is ambiguous in the source scope; "
                "explicit deterministic offsets are required."
            )
        start = source_analysis_unit.source_excerpt.index(
            detected_excerpt
        )
        end = start + len(detected_excerpt)
    else:
        if (
            not isinstance(source_start_offset, int)
            or isinstance(source_start_offset, bool)
            or not isinstance(source_end_offset, int)
            or isinstance(source_end_offset, bool)
        ):
            raise EvidenceDetectionGroundingError(
                "Explicit source offsets must both be integers."
            )
        start = source_start_offset
        end = source_end_offset
        if (
            start < 0
            or end <= start
            or end > len(source_analysis_unit.source_excerpt)
        ):
            raise EvidenceDetectionGroundingError(
                "Explicit source offsets are outside the Source Analysis Unit."
            )
        if (
            source_analysis_unit.source_excerpt[start:end]
            != detected_excerpt
        ):
            raise EvidenceDetectionGroundingError(
                "Deterministic source offsets do not reproduce exact source text."
            )

    result: list[SourceEvidenceAnchor] = []
    concatenated_start = 0
    for scope_anchor in source_analysis_unit.source_anchors:
        scope_length = (
            scope_anchor.end_offset - scope_anchor.start_offset
        )
        concatenated_end = concatenated_start + scope_length
        overlap_start = max(start, concatenated_start)
        overlap_end = min(end, concatenated_end)

        if overlap_start < overlap_end:
            result.append(
                SourceEvidenceAnchor(
                    segment_id=scope_anchor.segment_id,
                    start_offset=(
                        scope_anchor.start_offset
                        + overlap_start
                        - concatenated_start
                    ),
                    end_offset=(
                        scope_anchor.start_offset
                        + overlap_end
                        - concatenated_start
                    ),
                )
            )
        concatenated_start = concatenated_end

    if not result:
        raise EvidenceDetectionGroundingError(
            "Detector source range could not be mapped to source anchors."
        )
    return tuple(result)


def _parse_detection(
    value: Any,
    *,
    source_analysis_unit: SourceAnalysisUnit,
    candidate_spans: tuple[EvidenceCandidateSpan, ...],
) -> DetectedEvidenceSpan:
    item = _require_exact_object(
        value,
        _DETECTION_FIELDS,
        "Evidence Detection item",
    )

    raw_candidate_ids = item["candidate_span_ids"]
    if not isinstance(raw_candidate_ids, list) or not raw_candidate_ids:
        raise EvidenceDetectionValidationError(
            "candidate_span_ids must be a non-empty JSON array."
        )
    candidate_span_ids = tuple(raw_candidate_ids)
    if any(
        not isinstance(candidate_span_id, str)
        for candidate_span_id in candidate_span_ids
    ):
        raise EvidenceDetectionValidationError(
            "candidate_span_ids must contain strings only."
        )

    relevance = item["relevance"]
    if relevance not in EVIDENCE_RELEVANCE_VALUES:
        raise EvidenceDetectionValidationError(
            "relevance must be relevant, uncertain or not_relevant."
        )

    rationale = item["rationale"]
    if (
        not isinstance(rationale, str)
        or not rationale.strip()
        or rationale != rationale.strip()
    ):
        raise EvidenceDetectionValidationError(
            "rationale must be non-empty trimmed text."
        )

    source_excerpt, start, end = resolve_candidate_span_selection(
        source_analysis_unit=source_analysis_unit,
        candidate_spans=candidate_spans,
        candidate_span_ids=candidate_span_ids,
    )

    return DetectedEvidenceSpan(
        candidate_span_ids=candidate_span_ids,
        source_excerpt=source_excerpt,
        source_start_offset=start,
        source_end_offset=end,
        relevance=relevance,
        rationale=rationale,
    )


def _require_exact_object(
    value: Any,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceDetectionValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected:
        raise EvidenceDetectionValidationError(
            f"{label} fields do not match the schema. "
            f"Missing: {sorted(expected - actual)}; "
            f"unexpected: {sorted(actual - expected)}."
        )
    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceDetectionValidationError(
                f"Duplicate JSON field is not allowed: {key!r}."
            )
        result[key] = value
    return result
