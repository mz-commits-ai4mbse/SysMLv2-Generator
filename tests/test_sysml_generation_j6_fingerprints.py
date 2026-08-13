from __future__ import annotations

from dataclasses import replace

from modules.sysml_generation.artifact_builder import (
    calculate_generation_input_fingerprint,
)
from modules.sysml_generation.generator_rules import load_generator_rules_reference
from modules.sysml_generation.types import (
    SysMLArtifactStructureReference,
    SysMLGenerationContext,
    SysMLGenerationProfileReference,
    TargetNotationReference,
)


def _context():
    return SysMLGenerationContext(
        target_notation_reference=TargetNotationReference(
            context_id="CTX_SYSML_V2_TARGET_NOTATION",
            version="0.2.0",
            content_fingerprint="a" * 64,
        ),
        generation_profile_reference=SysMLGenerationProfileReference(
            profile_id="TURING_SYSML_V2_GENERATION",
            profile_version="1.0.0",
            profile_fingerprint="b" * 64,
        ),
        artifact_structure_reference=SysMLArtifactStructureReference(
            profile_id="TURING_SYSML_V2_ARTIFACT_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint="c" * 64,
        ),
        generator_rules_reference=load_generator_rules_reference(),
    )


def test_generation_input_fingerprint_changes_with_source_iem_fingerprint() -> None:
    context = _context()
    first = calculate_generation_input_fingerprint(
        source_iem_content_fingerprint="1" * 64,
        generation_context=context,
    )
    second = calculate_generation_input_fingerprint(
        source_iem_content_fingerprint="2" * 64,
        generation_context=context,
    )
    assert first != second


def test_generation_input_fingerprint_changes_with_generation_profile() -> None:
    context = _context()
    changed = replace(
        context,
        generation_profile_reference=replace(
            context.generation_profile_reference,
            profile_fingerprint="d" * 64,
        ),
    )
    first = calculate_generation_input_fingerprint(
        source_iem_content_fingerprint="1" * 64,
        generation_context=context,
    )
    second = calculate_generation_input_fingerprint(
        source_iem_content_fingerprint="1" * 64,
        generation_context=changed,
    )
    assert first != second
