"""Exact Phase-J policy-chain resolution for Phase-K validation."""

from __future__ import annotations

from modules.model_candidates.errors import ModelCandidateError
from modules.model_candidates.structure_profile import load_model_structure_profile
from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_profile,
    load_artifact_structure_reference,
)
from modules.sysml_generation.errors import SysMLGenerationError
from modules.sysml_generation.generation_profile import (
    load_generation_profile,
    load_generation_profile_reference,
)
from modules.sysml_generation.generator_rules import load_generator_rules_reference
from modules.sysml_generation.target_notation import load_target_notation_reference
from modules.sysml_generation.types import GeneratedSysMLArtifactSet

from .finding_support import blocking_finding, sort_validation_findings
from .types import SysMLValidationFinding


def validate_generation_context(
    artifact_set: GeneratedSysMLArtifactSet,
) -> tuple[SysMLValidationFinding, ...]:
    """Resolve and compare every exact policy identity pinned by Phase J."""

    findings: list[SysMLValidationFinding] = []
    category = "validation_context"
    context = artifact_set.generation_context

    target_ref = _resolve(
        load_target_notation_reference,
        findings,
        code="K2_TARGET_NOTATION_UNRESOLVABLE",
        message="Pinned Target Notation policy could not be resolved.",
    )
    generation_ref = _resolve(
        load_generation_profile_reference,
        findings,
        code="K2_GENERATION_PROFILE_UNRESOLVABLE",
        message="Pinned SysML Generation Profile could not be resolved.",
    )
    structure_ref = _resolve(
        load_artifact_structure_reference,
        findings,
        code="K2_ARTIFACT_STRUCTURE_UNRESOLVABLE",
        message="Pinned Artifact Structure Profile could not be resolved.",
    )
    rules_ref = _resolve(
        load_generator_rules_reference,
        findings,
        code="K2_GENERATOR_RULES_UNRESOLVABLE",
        message="Pinned Generator Rules could not be resolved.",
    )

    for actual, resolved, code, label in (
        (
            context.target_notation_reference,
            target_ref,
            "K2_TARGET_NOTATION_REFERENCE_MISMATCH",
            "Target Notation",
        ),
        (
            context.generation_profile_reference,
            generation_ref,
            "K2_GENERATION_PROFILE_REFERENCE_MISMATCH",
            "Generation Profile",
        ),
        (
            context.artifact_structure_reference,
            structure_ref,
            "K2_ARTIFACT_STRUCTURE_REFERENCE_MISMATCH",
            "Artifact Structure Profile",
        ),
        (
            context.generator_rules_reference,
            rules_ref,
            "K2_GENERATOR_RULES_REFERENCE_MISMATCH",
            "Generator Rules",
        ),
    ):
        if resolved is not None and actual != resolved:
            findings.append(
                blocking_finding(
                    code=code,
                    category=category,
                    message=f"Pinned {label} reference/fingerprint does not match the exact resolved policy.",
                )
            )

    generation_profile = _resolve(
        load_generation_profile,
        findings,
        code="K2_GENERATION_PROFILE_CHAIN_UNRESOLVABLE",
        message="Generation Profile could not be loaded for policy-chain validation.",
    )
    artifact_structure = _resolve(
        load_artifact_structure_profile,
        findings,
        code="K2_ARTIFACT_STRUCTURE_CHAIN_UNRESOLVABLE",
        message="Artifact Structure Profile could not be loaded for policy-chain validation.",
    )
    model_structure = _resolve_model_structure(findings)

    if generation_profile is not None and target_ref is not None:
        if (
            generation_profile["target_notation_context_id"] != target_ref.context_id
            or generation_profile["target_notation_version"] != target_ref.version
        ):
            findings.append(
                blocking_finding(
                    code="K2_GENERATION_TARGET_NOTATION_CHAIN_MISMATCH",
                    category=category,
                    message="Generation Profile Target Notation binding does not match the resolved target policy.",
                )
            )

    if generation_profile is not None and artifact_structure is not None:
        if (
            generation_profile["framework_template_id"]
            != artifact_structure["framework_template_id"]
            or generation_profile["framework_template_version"]
            != artifact_structure["framework_template_version"]
        ):
            findings.append(
                blocking_finding(
                    code="K2_FRAMEWORK_POLICY_CHAIN_MISMATCH",
                    category=category,
                    message="Generation and Artifact Structure profiles do not bind the same Framework Template.",
                )
            )

    if generation_profile is not None and model_structure is not None:
        if (
            generation_profile["model_structure_profile_id"]
            != model_structure.profile_id
            or generation_profile["model_structure_profile_version"]
            != model_structure.profile_version
        ):
            findings.append(
                blocking_finding(
                    code="K2_MODEL_STRUCTURE_PROFILE_MISMATCH",
                    category=category,
                    message="Generation Profile does not bind the resolved Model Structure / Comparability Profile identity.",
                )
            )
        if (
            generation_profile["framework_template_id"]
            != model_structure.framework_template_id
            or generation_profile["framework_template_version"]
            != model_structure.framework_template_version
        ):
            findings.append(
                blocking_finding(
                    code="K2_MODEL_STRUCTURE_FRAMEWORK_MISMATCH",
                    category=category,
                    message="Model Structure / Comparability Profile does not bind the generation Framework Template.",
                )
            )

    return sort_validation_findings(findings)


def _resolve(loader, findings, *, code: str, message: str):
    try:
        return loader()
    except (SysMLGenerationError, OSError, ValueError, TypeError):
        findings.append(
            blocking_finding(
                code=code,
                category="validation_context",
                message=message,
            )
        )
        return None


def _resolve_model_structure(findings):
    try:
        return load_model_structure_profile()
    except (ModelCandidateError, OSError, ValueError, TypeError):
        findings.append(
            blocking_finding(
                code="K2_MODEL_STRUCTURE_PROFILE_UNRESOLVABLE",
                category="validation_context",
                message="Model Structure / Comparability Profile could not be resolved for policy-chain validation.",
            )
        )
        return None
