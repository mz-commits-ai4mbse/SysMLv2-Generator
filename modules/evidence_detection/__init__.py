"""Public API for specialized source-grounded Evidence Detection."""

from .candidate_spans import (
    build_candidate_spans,
    resolve_candidate_span_selection,
)
from .detector import (
    EvidenceDetectionAgent,
    parse_detection_response,
    resolve_detection_anchors,
)
from .errors import (
    EvidenceDetectionError,
    EvidenceDetectionGroundingError,
    EvidenceDetectionReferenceError,
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


__all__ = [
    "EVIDENCE_DETECTION_INSTRUCTIONS",
    "EVIDENCE_DETECTION_PROMPT_SCHEMA_VERSION",
    "EVIDENCE_RELEVANCE_VALUES",
    "DetectedEvidenceSpan",
    "EvidenceCandidateSpan",
    "EvidenceDetectionAgent",
    "EvidenceDetectionError",
    "EvidenceDetectionGroundingError",
    "EvidenceDetectionReferenceError",
    "EvidenceDetectionResult",
    "EvidenceDetectionValidationError",
    "build_candidate_spans",
    "build_evidence_detection_input",
    "parse_detection_response",
    "resolve_candidate_span_selection",
    "resolve_detection_anchors",
]
