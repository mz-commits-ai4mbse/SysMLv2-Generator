"""Exact JSON reconstruction for persisted SEM-015 model-quality artifacts."""

from __future__ import annotations

import hashlib
import json

from .contract import create_refinement_bundle
from .errors import ModelQualityError
from .types import (
    ModelQualityInputElement,
    ModelQualityRefinementProposal,
    ModelQualityRefinementRequest,
)


def request_from_json(text: str):
    try:
        payload = json.loads(text)
        elements = []
        for item in payload["elements"]:
            element_body = {
                "internal_model_element_id": item["internal_model_element_id"],
                "approved_input_id": item["approved_input_id"],
                "model_subject_key": item["model_subject_key"],
                "original_name": item["original_name"],
                "original_description": item["original_description"],
                "element_type": item["element_type"],
                "model_area": item["model_area"],
                "framework_assignment": item["framework_assignment"],
                "source_element_fingerprint": item["source_element_fingerprint"],
                "classification_fingerprint": item["classification_fingerprint"],
                "quality_rule_ids": list(item["quality_rule_ids"]),
                "quality_rule_texts": list(item["quality_rule_texts"]),
            }
            if _fingerprint(element_body) != item["content_fingerprint"]:
                raise ModelQualityError(
                    "Persisted model-quality input element fingerprint is invalid."
                )
            elements.append(
                ModelQualityInputElement(
                    internal_model_element_id=item["internal_model_element_id"],
                    approved_input_id=item["approved_input_id"],
                    model_subject_key=item["model_subject_key"],
                    original_name=item["original_name"],
                    original_description=item["original_description"],
                    element_type=item["element_type"],
                    model_area=item["model_area"],
                    framework_assignment=item["framework_assignment"],
                    source_element_fingerprint=item["source_element_fingerprint"],
                    classification_fingerprint=item["classification_fingerprint"],
                    quality_rule_ids=tuple(item["quality_rule_ids"]),
                    quality_rule_texts=tuple(item["quality_rule_texts"]),
                    content_fingerprint=item["content_fingerprint"],
                )
            )
        body = {
            "schema_version": payload["schema_version"],
            "project_id": payload["project_id"],
            "source_internal_engineering_model_id": (
                payload["source_internal_engineering_model_id"]
            ),
            "source_internal_engineering_model_fingerprint": (
                payload["source_internal_engineering_model_fingerprint"]
            ),
            "quality_profile_id": payload["quality_profile_id"],
            "quality_profile_version": payload["quality_profile_version"],
            "quality_profile_fingerprint": payload["quality_profile_fingerprint"],
            "elements": [
                {
                    "internal_model_element_id": item.internal_model_element_id,
                    "approved_input_id": item.approved_input_id,
                    "model_subject_key": item.model_subject_key,
                    "original_name": item.original_name,
                    "original_description": item.original_description,
                    "element_type": item.element_type,
                    "model_area": item.model_area,
                    "framework_assignment": item.framework_assignment,
                    "source_element_fingerprint": item.source_element_fingerprint,
                    "classification_fingerprint": item.classification_fingerprint,
                    "quality_rule_ids": list(item.quality_rule_ids),
                    "quality_rule_texts": list(item.quality_rule_texts),
                    "content_fingerprint": item.content_fingerprint,
                }
                for item in elements
            ],
        }
        if _fingerprint(body) != payload["request_fingerprint"]:
            raise ModelQualityError(
                "Persisted model-quality request fingerprint is invalid."
            )
        return ModelQualityRefinementRequest(
            schema_version=payload["schema_version"],
            project_id=payload["project_id"],
            source_internal_engineering_model_id=(
                payload["source_internal_engineering_model_id"]
            ),
            source_internal_engineering_model_fingerprint=(
                payload["source_internal_engineering_model_fingerprint"]
            ),
            quality_profile_id=payload["quality_profile_id"],
            quality_profile_version=payload["quality_profile_version"],
            quality_profile_fingerprint=payload["quality_profile_fingerprint"],
            elements=tuple(elements),
            request_fingerprint=payload["request_fingerprint"],
        )
    except Exception as exc:
        if isinstance(exc, ModelQualityError):
            raise
        raise ModelQualityError(
            "Persisted model-quality request violates exact schema."
        ) from exc


def bundle_from_json(text: str, *, request):
    try:
        payload = json.loads(text)
        proposals = []
        for item in payload["proposals"]:
            body = {
                "internal_model_element_id": item["internal_model_element_id"],
                "input_element_fingerprint": item["input_element_fingerprint"],
                "classification_fingerprint": item["classification_fingerprint"],
                "refined_name": item["refined_name"],
                "refined_description": item["refined_description"],
                "quality_findings": list(item["quality_findings"]),
                "applied_rule_ids": list(item["applied_rule_ids"]),
                "meaning_preserved": item["meaning_preserved"],
                "unsupported_information_added": (
                    item["unsupported_information_added"]
                ),
                "requires_human_attention": item["requires_human_attention"],
                "rationale": item["rationale"],
            }
            if _fingerprint(body) != item["content_fingerprint"]:
                raise ModelQualityError(
                    "Persisted model-quality proposal fingerprint is invalid."
                )
            proposals.append(
                ModelQualityRefinementProposal(
                    internal_model_element_id=item["internal_model_element_id"],
                    input_element_fingerprint=item["input_element_fingerprint"],
                    classification_fingerprint=item["classification_fingerprint"],
                    refined_name=item["refined_name"],
                    refined_description=item["refined_description"],
                    quality_findings=tuple(item["quality_findings"]),
                    applied_rule_ids=tuple(item["applied_rule_ids"]),
                    meaning_preserved=item["meaning_preserved"],
                    unsupported_information_added=(
                        item["unsupported_information_added"]
                    ),
                    requires_human_attention=item["requires_human_attention"],
                    rationale=item["rationale"],
                    content_fingerprint=item["content_fingerprint"],
                )
            )
        rebuilt = create_refinement_bundle(
            request=request,
            review_id=payload["review_id"],
            provider=payload["provider"],
            model=payload["model"],
            proposals=tuple(proposals),
            supporting_response_fingerprints=tuple(
                payload["supporting_response_fingerprints"]
            ),
            generated_at=payload["generated_at"],
        )
    except Exception as exc:
        if isinstance(exc, ModelQualityError):
            raise
        raise ModelQualityError(
            "Persisted model-quality bundle violates exact schema."
        ) from exc
    if (
        rebuilt.schema_version != payload["schema_version"]
        or rebuilt.content_fingerprint != payload["content_fingerprint"]
    ):
        raise ModelQualityError(
            "Persisted model-quality bundle fingerprint is invalid."
        )
    return rebuilt


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
