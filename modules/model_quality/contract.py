"""SEM-015 contract: classification-dependent semantic quality refinement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .errors import ModelQualityError
from .types import (
    ModelQualityInputElement,
    ModelQualityRefinementBundle,
    ModelQualityRefinementProposal,
    ModelQualityRefinementRequest,
)


MODEL_QUALITY_REQUEST_SCHEMA_VERSION = "1.0.0"
MODEL_QUALITY_BUNDLE_SCHEMA_VERSION = "1.0.0"
_REVIEW_ID = re.compile(r"^MQR-[0-9]{6}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


MODEL_QUALITY_TASK_INSTRUCTIONS = """\
You are refining already accepted engineering information for a SysML v2 target model.

The Human-reviewed target classification and placement are authoritative inputs.
Your task is NOT to reclassify the element. Improve its model-facing name and
description so they are clear, concise and appropriate to the supplied element
type and modeling level.

Hard rules:
1. Preserve the engineering meaning. Do not invent capabilities, actors,
   quantities, thresholds, conditions, interfaces or constraints absent from
   the supplied meaning.
2. Apply ONLY the quality rules supplied for the element.
3. Requirement wording depends on the supplied requirement level. Do not
   silently turn a stakeholder-level statement into a system obligation or vice
   versa.
4. Requirement statements must be binding and well-formed for their supplied
   level. If source information is too vague to make a requirement verifiable,
   improve only what is source-supported and set requires_human_attention=true.
   Never invent a missing number or success criterion.
5. Functions/actions use concise active verb-object wording. Components,
   information items and stakeholder roles use concise noun/role wording.
6. If meaning cannot be preserved, set meaning_preserved=false and
   requires_human_attention=true.
7. If your proposal contains any information not supported by the input, set
   unsupported_information_added=true and requires_human_attention=true.
8. Return JSON only. No Markdown and no code fences.

Return exactly:
{
  "proposals": [
    {
      "internal_model_element_id": "IME-000001",
      "refined_name": "...",
      "refined_description": "... or null",
      "quality_findings": ["..."],
      "applied_rule_ids": ["..."],
      "meaning_preserved": true,
      "unsupported_information_added": false,
      "requires_human_attention": false,
      "rationale": "..."
    }
  ]
}

Return exactly one proposal for every supplied element and no others.
"""


def load_quality_profile(path: Path) -> dict:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ModelQualityError("Model-quality profile could not be loaded.") from exc
    if not isinstance(value, dict):
        raise ModelQualityError("Model-quality profile must be a JSON object.")
    for field in ("profile_id", "profile_version", "element_profiles"):
        if field not in value:
            raise ModelQualityError(
                f"Model-quality profile is missing required field {field}."
            )
    if not isinstance(value["element_profiles"], dict):
        raise ModelQualityError("element_profiles must be an object.")
    return value


def profile_fingerprint(profile: dict) -> str:
    return _fingerprint(profile)


def build_refinement_request(
    *,
    snapshot,
    quality_profile: dict,
) -> ModelQualityRefinementRequest:
    """Bind refinement to exact Human-reviewed classification and placement."""

    profile_id = _text(quality_profile.get("profile_id"), "profile_id")
    profile_version = _text(
        quality_profile.get("profile_version"),
        "profile_version",
    )
    pfp = profile_fingerprint(quality_profile)
    profiles = quality_profile.get("element_profiles")
    if not isinstance(profiles, dict):
        raise ModelQualityError("element_profiles must be an object.")

    elements = []
    for source in sorted(
        snapshot.elements,
        key=lambda item: item.internal_model_element_id,
    ):
        rule_ids, rule_texts = _rules_for(
            source.element_type,
            profiles,
            quality_profile.get("rules"),
        )
        classification = {
            "element_type": source.element_type,
            "model_area": source.model_area,
            "framework_assignment": source.framework_assignment,
        }
        classification_fp = _fingerprint(classification)
        body = {
            "internal_model_element_id": source.internal_model_element_id,
            "approved_input_id": source.approved_input_id,
            "model_subject_key": source.model_subject_key,
            "original_name": source.name,
            "original_description": source.description,
            "element_type": source.element_type,
            "model_area": source.model_area,
            "framework_assignment": source.framework_assignment,
            "source_element_fingerprint": source.content_fingerprint,
            "classification_fingerprint": classification_fp,
            "quality_rule_ids": list(rule_ids),
            "quality_rule_texts": list(rule_texts),
        }
        elements.append(
            ModelQualityInputElement(
                internal_model_element_id=source.internal_model_element_id,
                approved_input_id=source.approved_input_id,
                model_subject_key=source.model_subject_key,
                original_name=_text(source.name, "original_name"),
                original_description=_optional_text(source.description),
                element_type=_text(source.element_type, "element_type"),
                model_area=_text(source.model_area, "model_area"),
                framework_assignment=_text(
                    source.framework_assignment,
                    "framework_assignment",
                ),
                source_element_fingerprint=_sha(
                    source.content_fingerprint,
                    "source_element_fingerprint",
                ),
                classification_fingerprint=classification_fp,
                quality_rule_ids=rule_ids,
                quality_rule_texts=rule_texts,
                content_fingerprint=_fingerprint(body),
            )
        )

    if not elements:
        raise ModelQualityError(
            "Model-quality refinement requires at least one Internal Model element."
        )

    body = {
        "schema_version": MODEL_QUALITY_REQUEST_SCHEMA_VERSION,
        "project_id": snapshot.project_id,
        "source_internal_engineering_model_id": (
            snapshot.internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            snapshot.content_fingerprint
        ),
        "quality_profile_id": profile_id,
        "quality_profile_version": profile_version,
        "quality_profile_fingerprint": pfp,
        "elements": [_input_payload(item) for item in elements],
    }
    return ModelQualityRefinementRequest(
        schema_version=MODEL_QUALITY_REQUEST_SCHEMA_VERSION,
        project_id=_text(snapshot.project_id, "project_id"),
        source_internal_engineering_model_id=_text(
            snapshot.internal_engineering_model_id,
            "source_internal_engineering_model_id",
        ),
        source_internal_engineering_model_fingerprint=_sha(
            snapshot.content_fingerprint,
            "source_internal_engineering_model_fingerprint",
        ),
        quality_profile_id=profile_id,
        quality_profile_version=profile_version,
        quality_profile_fingerprint=pfp,
        elements=tuple(elements),
        request_fingerprint=_fingerprint(body),
    )


def subset_request(
    request: ModelQualityRefinementRequest,
    element_ids: tuple[str, ...],
) -> ModelQualityRefinementRequest:
    selected = tuple(
        item
        for item in request.elements
        if item.internal_model_element_id in set(element_ids)
    )
    if len(selected) != len(element_ids):
        raise ModelQualityError("Refinement batch does not bind exact requested elements.")
    body = {
        "schema_version": request.schema_version,
        "project_id": request.project_id,
        "source_internal_engineering_model_id": (
            request.source_internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            request.source_internal_engineering_model_fingerprint
        ),
        "quality_profile_id": request.quality_profile_id,
        "quality_profile_version": request.quality_profile_version,
        "quality_profile_fingerprint": request.quality_profile_fingerprint,
        "elements": [_input_payload(item) for item in selected],
    }
    return ModelQualityRefinementRequest(
        schema_version=request.schema_version,
        project_id=request.project_id,
        source_internal_engineering_model_id=(
            request.source_internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            request.source_internal_engineering_model_fingerprint
        ),
        quality_profile_id=request.quality_profile_id,
        quality_profile_version=request.quality_profile_version,
        quality_profile_fingerprint=request.quality_profile_fingerprint,
        elements=selected,
        request_fingerprint=_fingerprint(body),
    )


def refinement_request_to_compact_json(
    request: ModelQualityRefinementRequest,
) -> str:
    payload = {
        "project_id": request.project_id,
        "source_iem": {
            "id": request.source_internal_engineering_model_id,
            "fingerprint": request.source_internal_engineering_model_fingerprint,
        },
        "quality_profile": {
            "id": request.quality_profile_id,
            "version": request.quality_profile_version,
            "fingerprint": request.quality_profile_fingerprint,
        },
        "request_fingerprint": request.request_fingerprint,
        "elements": [
            {
                "internal_model_element_id": item.internal_model_element_id,
                "approved_input_id": item.approved_input_id,
                "engineering_meaning": {
                    "name": item.original_name,
                    "description": item.original_description,
                },
                "authoritative_target_context": {
                    "element_type": item.element_type,
                    "model_area": item.model_area,
                    "framework_assignment": item.framework_assignment,
                    "classification_fingerprint": item.classification_fingerprint,
                },
                "quality_rules": [
                    {
                        "rule_id": rule_id,
                        "instruction": rule_text,
                    }
                    for rule_id, rule_text in zip(
                        item.quality_rule_ids,
                        item.quality_rule_texts,
                    )
                ],
            }
            for item in request.elements
        ],
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def parse_refinement_response(
    *,
    request: ModelQualityRefinementRequest,
    output_text: str,
) -> tuple[ModelQualityRefinementProposal, ...]:
    """Validate an LLM response against the exact classification-bound request."""

    try:
        payload = json.loads(_strip_fences(output_text))
    except Exception as exc:
        raise ModelQualityError(
            "Model-quality LLM response is not valid JSON."
        ) from exc

    if set(payload) != {"proposals"} or not isinstance(
        payload["proposals"],
        list,
    ):
        raise ModelQualityError(
            "Model-quality LLM response must contain only proposals."
        )

    expected = {
        item.internal_model_element_id: item
        for item in request.elements
    }
    received = {}
    for raw in payload["proposals"]:
        if not isinstance(raw, dict):
            raise ModelQualityError("Model-quality proposal must be an object.")
        required = {
            "internal_model_element_id",
            "refined_name",
            "refined_description",
            "quality_findings",
            "applied_rule_ids",
            "meaning_preserved",
            "unsupported_information_added",
            "requires_human_attention",
            "rationale",
        }
        if set(raw) != required:
            raise ModelQualityError(
                "Model-quality proposal fields do not match the exact contract."
            )
        element_id = _text(
            raw["internal_model_element_id"],
            "internal_model_element_id",
        )
        if element_id not in expected or element_id in received:
            raise ModelQualityError(
                "Model-quality response does not bind the exact requested element population."
            )
        source = expected[element_id]
        name = _text(raw["refined_name"], "refined_name")
        description = _optional_text(raw["refined_description"])
        findings = _string_tuple(raw["quality_findings"], "quality_findings")
        applied = _string_tuple(raw["applied_rule_ids"], "applied_rule_ids")
        if not set(applied).issubset(set(source.quality_rule_ids)):
            raise ModelQualityError(
                "Model-quality proposal applies a rule outside the pinned profile."
            )
        meaning = _bool(raw["meaning_preserved"], "meaning_preserved")
        unsupported = _bool(
            raw["unsupported_information_added"],
            "unsupported_information_added",
        )
        attention = _bool(
            raw["requires_human_attention"],
            "requires_human_attention",
        )
        if (not meaning or unsupported) and not attention:
            raise ModelQualityError(
                "Meaning loss or unsupported information must require Human attention."
            )
        rationale = _text(raw["rationale"], "rationale")
        body = {
            "internal_model_element_id": element_id,
            "input_element_fingerprint": source.content_fingerprint,
            "classification_fingerprint": source.classification_fingerprint,
            "refined_name": name,
            "refined_description": description,
            "quality_findings": list(findings),
            "applied_rule_ids": list(applied),
            "meaning_preserved": meaning,
            "unsupported_information_added": unsupported,
            "requires_human_attention": attention,
            "rationale": rationale,
        }
        received[element_id] = ModelQualityRefinementProposal(
            internal_model_element_id=element_id,
            input_element_fingerprint=source.content_fingerprint,
            classification_fingerprint=source.classification_fingerprint,
            refined_name=name,
            refined_description=description,
            quality_findings=findings,
            applied_rule_ids=applied,
            meaning_preserved=meaning,
            unsupported_information_added=unsupported,
            requires_human_attention=attention,
            rationale=rationale,
            content_fingerprint=_fingerprint(body),
        )

    if set(received) != set(expected):
        raise ModelQualityError(
            "Model-quality response must contain exactly one proposal per requested element."
        )
    return tuple(
        received[item.internal_model_element_id]
        for item in request.elements
    )


def create_refinement_bundle(
    *,
    request: ModelQualityRefinementRequest,
    review_id: str,
    provider: str,
    model: str,
    proposals: tuple[ModelQualityRefinementProposal, ...],
    supporting_response_fingerprints: tuple[str, ...],
    generated_at: str,
) -> ModelQualityRefinementBundle:
    if _REVIEW_ID.fullmatch(review_id) is None:
        raise ModelQualityError("Model-quality review ID is invalid.")
    by_id = {
        item.internal_model_element_id: item
        for item in proposals
    }
    if len(by_id) != len(proposals) or set(by_id) != {
        item.internal_model_element_id for item in request.elements
    }:
        raise ModelQualityError(
            "Model-quality bundle must cover every request element exactly once."
        )
    ordered = tuple(
        by_id[item.internal_model_element_id]
        for item in request.elements
    )
    for source, proposal in zip(request.elements, ordered):
        if (
            proposal.input_element_fingerprint != source.content_fingerprint
            or proposal.classification_fingerprint
            != source.classification_fingerprint
        ):
            raise ModelQualityError(
                "Model-quality proposal binding differs from the request."
            )
    response_fps = tuple(
        _sha(value, "supporting_response_fingerprint")
        for value in supporting_response_fingerprints
    )
    body = {
        "schema_version": MODEL_QUALITY_BUNDLE_SCHEMA_VERSION,
        "project_id": request.project_id,
        "review_id": review_id,
        "request_fingerprint": request.request_fingerprint,
        "source_internal_engineering_model_id": (
            request.source_internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            request.source_internal_engineering_model_fingerprint
        ),
        "quality_profile_id": request.quality_profile_id,
        "quality_profile_version": request.quality_profile_version,
        "quality_profile_fingerprint": request.quality_profile_fingerprint,
        "provider": _text(provider, "provider"),
        "model": _text(model, "model"),
        "proposals": [_proposal_payload(item) for item in ordered],
        "supporting_response_fingerprints": list(response_fps),
        "generated_at": _text(generated_at, "generated_at"),
    }
    return ModelQualityRefinementBundle(
        schema_version=MODEL_QUALITY_BUNDLE_SCHEMA_VERSION,
        project_id=request.project_id,
        review_id=review_id,
        request_fingerprint=request.request_fingerprint,
        source_internal_engineering_model_id=(
            request.source_internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            request.source_internal_engineering_model_fingerprint
        ),
        quality_profile_id=request.quality_profile_id,
        quality_profile_version=request.quality_profile_version,
        quality_profile_fingerprint=request.quality_profile_fingerprint,
        provider=body["provider"],
        model=body["model"],
        proposals=ordered,
        supporting_response_fingerprints=response_fps,
        generated_at=body["generated_at"],
        content_fingerprint=_fingerprint(body),
    )


def request_to_json(request: ModelQualityRefinementRequest) -> str:
    payload = {
        "schema_version": request.schema_version,
        "project_id": request.project_id,
        "source_internal_engineering_model_id": request.source_internal_engineering_model_id,
        "source_internal_engineering_model_fingerprint": request.source_internal_engineering_model_fingerprint,
        "quality_profile_id": request.quality_profile_id,
        "quality_profile_version": request.quality_profile_version,
        "quality_profile_fingerprint": request.quality_profile_fingerprint,
        "elements": [_input_payload(item) for item in request.elements],
        "request_fingerprint": request.request_fingerprint,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def bundle_to_json(bundle: ModelQualityRefinementBundle) -> str:
    payload = {
        "schema_version": bundle.schema_version,
        "project_id": bundle.project_id,
        "review_id": bundle.review_id,
        "request_fingerprint": bundle.request_fingerprint,
        "source_internal_engineering_model_id": bundle.source_internal_engineering_model_id,
        "source_internal_engineering_model_fingerprint": bundle.source_internal_engineering_model_fingerprint,
        "quality_profile_id": bundle.quality_profile_id,
        "quality_profile_version": bundle.quality_profile_version,
        "quality_profile_fingerprint": bundle.quality_profile_fingerprint,
        "provider": bundle.provider,
        "model": bundle.model,
        "proposals": [_proposal_payload(item) for item in bundle.proposals],
        "supporting_response_fingerprints": list(
            bundle.supporting_response_fingerprints
        ),
        "generated_at": bundle.generated_at,
        "content_fingerprint": bundle.content_fingerprint,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _rules_for(
    element_type: str,
    profiles: dict,
    rule_catalog,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    raw = profiles.get(element_type, profiles.get("*"))
    if not isinstance(raw, dict):
        raise ModelQualityError(
            f"No model-quality profile exists for element type {element_type}."
        )
    if not isinstance(rule_catalog, dict):
        raise ModelQualityError("Model-quality rule catalog must be an object.")
    rule_ids = _string_tuple(
        raw.get("rule_ids"),
        f"rule_ids[{element_type}]",
    )
    texts = []
    for rule_id in rule_ids:
        text = rule_catalog.get(rule_id)
        texts.append(_text(text, f"rules[{rule_id}]"))
    return rule_ids, tuple(texts)


def _input_payload(item: ModelQualityInputElement) -> dict:
    return {
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


def _proposal_payload(item: ModelQualityRefinementProposal) -> dict:
    return {
        "internal_model_element_id": item.internal_model_element_id,
        "input_element_fingerprint": item.input_element_fingerprint,
        "classification_fingerprint": item.classification_fingerprint,
        "refined_name": item.refined_name,
        "refined_description": item.refined_description,
        "quality_findings": list(item.quality_findings),
        "applied_rule_ids": list(item.applied_rule_ids),
        "meaning_preserved": item.meaning_preserved,
        "unsupported_information_added": item.unsupported_information_added,
        "requires_human_attention": item.requires_human_attention,
        "rationale": item.rationale,
        "content_fingerprint": item.content_fingerprint,
    }


def _strip_fences(text: str) -> str:
    value = text.strip()
    if value.startswith("```") and value.endswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return value


def _string_tuple(value, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ModelQualityError(f"{field} must be a list.")
    result = []
    for item in value:
        result.append(_text(item, field))
    if len(result) != len(set(result)):
        raise ModelQualityError(f"{field} must not contain duplicates.")
    return tuple(result)


def _bool(value, field: str) -> bool:
    if not isinstance(value, bool):
        raise ModelQualityError(f"{field} must be boolean.")
    return value


def _text(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelQualityError(f"{field} must be non-empty text.")
    return value.strip()


def _optional_text(value) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ModelQualityError("Optional text field must be text or null.")
    stripped = value.strip()
    return stripped or None


def _sha(value, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ModelQualityError(f"{field} must be a SHA-256 fingerprint.")
    return value


def _fingerprint(payload) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
