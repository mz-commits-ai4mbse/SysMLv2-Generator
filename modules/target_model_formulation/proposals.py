"""Bounded BLK-006 Target-Model Formulation proposal builder."""

from __future__ import annotations

import hashlib
import json
import re

from .contract import (
    APOLLO_REFERENCE_SOURCE_ID,
    PRIMARY_SYNTAX_ROLE,
    PRIMARY_SYNTAX_SOURCE_ID,
    PROJECT_MODEL_CONTEXT_ROLE,
    TURING_MODEL_REFERENCE_SOURCE_ID,
    VALIDATED_FIXTURE_ROLE,
    create_formulation_candidate,
    create_formulation_review,
    create_reference_evidence,
    create_review_item,
)
from .errors import TargetModelFormulationError
from .evidence import LocalReferenceAssessment


SUPPORTED_BRIDGE_ELEMENT_TYPES = frozenset({"stakeholder"})
SUPPORTED_BRIDGE_RELATIONSHIP_SEMANTICS = frozenset({"traces_to"})


def build_blk006_formulation_review(
    *,
    snapshot,
    assessment: LocalReferenceAssessment,
    target_model_profile: dict,
    review_id: str,
    created_at: str,
):
    """Build review proposals only for the unresolved BLK-006 population."""

    _validate_snapshot(snapshot)

    profile_id = _required_text(
        target_model_profile.get("profile_id"),
        "profile_id",
    )
    profile_version = _required_text(
        target_model_profile.get("profile_version"),
        "profile_version",
    )
    profile_fingerprint = _json_fingerprint(target_model_profile)

    items = []
    candidate_index = 1

    for element in sorted(
        snapshot.elements,
        key=lambda item: item.internal_model_element_id,
    ):
        if element.element_type not in SUPPORTED_BRIDGE_ELEMENT_TYPES:
            continue

        release_ref = create_reference_evidence(
            source_id=PRIMARY_SYNTAX_SOURCE_ID,
            role=PRIMARY_SYNTAX_ROLE,
            locator=(
                assessment.stakeholder_evidence_locator
                or f"{assessment.sysml_release_root}:stakeholder-scan"
            ),
            evidence_note=assessment.stakeholder_evidence_note,
        )
        apollo_ref = create_reference_evidence(
            source_id=APOLLO_REFERENCE_SOURCE_ID,
            role="non_normative_modeling_pattern_reference",
            locator="external/apollo11-sysml-v2/",
            evidence_note=(
                "Apollo is used only for definition-vs-usage and model-organization "
                "pattern comparison. It is not syntax or engineering authority."
            ),
        )
        project_ref = create_reference_evidence(
            source_id=TURING_MODEL_REFERENCE_SOURCE_ID,
            role=PROJECT_MODEL_CONTEXT_ROLE,
            locator="model/01_Stakeholder/00_Stakeholders/Stakeholders.sysml",
            evidence_note=(
                "The Turing architecture model uses standalone Part Definitions for "
                "reviewed human stakeholder-role types. This is project modeling "
                "context only and does not establish SysML v2 syntax authority."
            ),
        )
        notation_ref = create_reference_evidence(
            source_id="TURING_SYSML_V2_TARGET_NOTATION",
            role="target_model_formulation_guidance",
            locator="context/sysml/sysml_v2_target_notation.json",
            evidence_note=(
                "TN_003 permits Human-reviewed standalone reusable stakeholder-role "
                "types when the dedicated validated fixture is bound."
                if assessment.tn003_allows_stakeholder
                else (
                    "Current Target Notation does not authorize TN_003 for standalone "
                    "stakeholder-role representation."
                )
            ),
        )

        if (
            assessment.tn003_allows_stakeholder
            and assessment.stakeholder_fixture_validated
        ):
            fixture_ref = create_reference_evidence(
                source_id=(
                    assessment.stakeholder_fixture_id
                    or "SFX-C6C3-001"
                ),
                role=VALIDATED_FIXTURE_ROLE,
                locator=(
                    assessment.stakeholder_fixture_locator
                    or (
                        "context/sysml/fixtures/c6c3/"
                        "stakeholder_role_part_definition.sysml"
                    )
                ),
                evidence_note=(
                    "SYSIDE accepted the standalone stakeholder-role Part Definition "
                    "fixture. The only Semantic Feedback was the non-blocking "
                    "'unused-definition' warning expected for an isolated definition."
                ),
            )
            candidate = create_formulation_candidate(
                candidate_id=f"TFC-{candidate_index:06d}",
                relevance_outcome="materialize_formally",
                target_model_pattern_id=(
                    "standalone_reusable_stakeholder_role_part_definition"
                ),
                target_notation_construct_id="TN_003",
                formulation_text=_standalone_role_part_definition(element),
                reference_evidence=(
                    release_ref,
                    fixture_ref,
                    apollo_ref,
                    project_ref,
                    notation_ref,
                ),
                rationale=(
                    "The source element is an accepted standalone stakeholder role. "
                    "The local SysML v2 release represents human/user/operator types "
                    "with Part Definitions, the project model follows the same role-type "
                    "pattern, TN_003 now explicitly permits Human-reviewed reusable "
                    "stakeholder-role types, and SFX-C6C3-001 is SYSIDE-validated. "
                    "No HumanRole supertype or additional relationship semantics are "
                    "introduced by this proposal."
                ),
            )
        else:
            candidate = create_formulation_candidate(
                candidate_id=f"TFC-{candidate_index:06d}",
                relevance_outcome="unresolved_human_review",
                target_model_pattern_id=None,
                target_notation_construct_id=None,
                formulation_text=None,
                reference_evidence=(
                    release_ref,
                    apollo_ref,
                    project_ref,
                    notation_ref,
                ),
                rationale=(
                    "Standalone stakeholder-role Part Definition evidence is not yet "
                    "fully authorized by both Target Notation policy and validated "
                    "fixture evidence. The proposal therefore fails closed to Human "
                    "Review."
                ),
                unresolved_questions=(
                    "May this accepted standalone stakeholder role be represented as "
                    "a reusable SysML v2 Part Definition under TN_003, or does it "
                    "require a contextual Part Usage or different Target-Model pattern?",
                ),
            )
        candidate_index += 1

        items.append(
            create_review_item(
                subject_kind="element",
                authority_subject_id=(
                    element.internal_model_element_id
                ),
                current_engineering_type=element.element_type,
                current_target_representation=element.element_type,
                candidates=(candidate,),
            )
        )

    for relationship in sorted(
        snapshot.relationships,
        key=lambda item: item.internal_model_relationship_id,
    ):
        if (
            relationship.semantic_intent
            not in SUPPORTED_BRIDGE_RELATIONSHIP_SEMANTICS
        ):
            continue

        release_ref = create_reference_evidence(
            source_id=PRIMARY_SYNTAX_SOURCE_ID,
            role=PRIMARY_SYNTAX_ROLE,
            locator=assessment.trace_evidence_locator,
            evidence_note=assessment.trace_evidence_note,
        )
        notation_ref = create_reference_evidence(
            source_id="TURING_SYSML_V2_TARGET_NOTATION",
            role="target_model_formulation_guidance",
            locator="context/sysml/sysml_v2_target_notation.json",
            evidence_note=(
                "Current Target Notation contains documentation-based traceability "
                "guidance but no authorized formal traces_to construct."
            ),
        )

        if assessment.trace_syntax_match_count == 0:
            candidate = create_formulation_candidate(
                candidate_id=f"TFC-{candidate_index:06d}",
                relevance_outcome="intentionally_not_materialized",
                target_model_pattern_id=None,
                target_notation_construct_id=None,
                formulation_text=None,
                reference_evidence=(release_ref, notation_ref),
                rationale=(
                    "The Human-approved target relationship representation remains "
                    "'traces_to', but no locally supported formal SysML v2 trace syntax "
                    "is evidenced. The relationship should remain authoritative and "
                    "traceable without formal notation materialization rather than being "
                    "strengthened or replaced by dependency/satisfy."
                ),
            )
        else:
            candidate = create_formulation_candidate(
                candidate_id=f"TFC-{candidate_index:06d}",
                relevance_outcome="unresolved_human_review",
                target_model_pattern_id=None,
                target_notation_construct_id=None,
                formulation_text=None,
                reference_evidence=(release_ref, notation_ref),
                rationale=(
                    "Trace-related lexical evidence exists locally, but it has not yet "
                    "been qualified into an authorized Target Notation construct."
                ),
                unresolved_questions=(
                    "Does the local trace-related evidence define a semantically faithful "
                    "formal SysML v2 construct for this approved traces_to relationship?",
                ),
            )
        candidate_index += 1

        items.append(
            create_review_item(
                subject_kind="relationship",
                authority_subject_id=(
                    relationship.internal_model_relationship_id
                ),
                current_engineering_type=(
                    relationship.semantic_intent
                ),
                current_target_representation=(
                    relationship.semantic_intent
                ),
                candidates=(candidate,),
            )
        )

    if not items:
        raise TargetModelFormulationError(
            "No bounded BLK-006 Target-Model Formulation subjects were found."
        )

    return create_formulation_review(
        project_id=snapshot.project_id,
        review_id=review_id,
        source_internal_engineering_model_id=(
            snapshot.internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            snapshot.content_fingerprint
        ),
        final_model_review_decision_id=(
            snapshot.final_model_review_decision_id
        ),
        final_model_review_decision_fingerprint=(
            snapshot.final_model_review_decision_fingerprint
        ),
        target_model_profile_id=profile_id,
        target_model_profile_version=profile_version,
        target_model_profile_fingerprint=profile_fingerprint,
        target_notation_fingerprint=(
            assessment.target_notation_fingerprint
        ),
        items=tuple(items),
        created_at=created_at,
    )


_BARE_SYSML_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _standalone_role_part_definition(element) -> str:
    name = getattr(element, "name", None)
    if not isinstance(name, str) or not name.strip():
        name = getattr(element, "display_name", None)
    if not isinstance(name, str) or not name.strip():
        raise TargetModelFormulationError(
            "Formal stakeholder-role formulation requires an element name."
        )

    selected = name.strip()
    if _BARE_SYSML_NAME.fullmatch(selected):
        symbol = selected
    elif "'" not in selected and "\n" not in selected and "\r" not in selected:
        symbol = f"'{selected}'"
    else:
        words = re.findall(r"[A-Za-z0-9]+", selected)
        if not words:
            raise TargetModelFormulationError(
                "Stakeholder-role name cannot be represented safely in SysML v2."
            )
        symbol = "".join(word[:1].upper() + word[1:] for word in words)

    return f"part def {symbol};"


def _validate_snapshot(snapshot) -> None:
    for name in (
        "project_id",
        "internal_engineering_model_id",
        "content_fingerprint",
        "final_model_review_decision_id",
        "final_model_review_decision_fingerprint",
        "elements",
        "relationships",
    ):
        if not hasattr(snapshot, name):
            raise TargetModelFormulationError(
                f"Authority-backed Internal Model is missing {name}."
            )


def _required_text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TargetModelFormulationError(f"{label} is required.")
    return value.strip()


def _json_fingerprint(value: dict) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
