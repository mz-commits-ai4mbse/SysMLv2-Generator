"""Public API for deterministic Phase-J SYSIDE-compatible SysML v2 generation."""

from .errors import (
    SysMLGenerationBlockedError,
    SysMLGenerationError,
    SysMLGenerationIntegrityError,
    SysMLGenerationProfileError,
    SysMLGenerationValidationError,
    SysMLSyntaxEvidenceError,
)
from .fingerprints import (
    SHA256_HEX_PATTERN,
    calculate_json_fingerprint,
    calculate_text_fingerprint,
    canonical_json_bytes,
    validate_sha256_fingerprint,
)
from .identifiers import (
    GENERATED_SYSML_SYMBOL_PATTERN,
    GENERATED_SYSML_UNIT_ID_PATTERN,
    MAX_GENERATED_SYSML_UNIT_SEQUENCE,
    MIN_GENERATED_SYSML_UNIT_SEQUENCE,
    format_generated_sysml_unit_id,
    generated_element_symbol,
    generated_relationship_symbol,
    validate_generated_sysml_symbol,
    validate_generated_sysml_unit_id,
)
from .target_notation import (
    DEFAULT_TARGET_NOTATION_PATH,
    EXPECTED_TARGET_NOTATION_CONTEXT_ID,
    PHASE_J_TARGET_NOTATION_VERSION,
    calculate_target_notation_fingerprint,
    load_target_notation,
    load_target_notation_reference,
    validate_target_notation,
)
from .types import (
    GeneratedSysMLArtifactSet,
    GeneratedSysMLLocation,
    GeneratedSysMLTraceabilityEntry,
    GeneratedSysMLUnit,
    SysMLArtifactStructureReference,
    SysMLGenerationContext,
    SysMLGenerationFinding,
    SysMLGenerationProfileReference,
    SysMLGenerationProvenance,
    SysMLGeneratorRulesReference,
    TargetNotationReference,
)
from .generation_profile import (
    DEFAULT_GENERATION_PROFILE_PATH,
    EXPECTED_GENERATION_PROFILE_ID,
    EXPECTED_GENERATION_PROFILE_VERSION,
    GENERATION_PROFILE_SCHEMA_VERSION,
    calculate_generation_profile_fingerprint,
    find_element_mapping,
    find_relationship_mapping,
    load_generation_profile,
    load_generation_profile_reference,
    validate_generation_profile,
)
from .artifact_structure import (
    ARTIFACT_STRUCTURE_SCHEMA_VERSION,
    DEFAULT_ARTIFACT_STRUCTURE_PATH,
    EXPECTED_ARTIFACT_STRUCTURE_PROFILE_ID,
    EXPECTED_ARTIFACT_STRUCTURE_PROFILE_VERSION,
    calculate_artifact_structure_fingerprint,
    load_artifact_structure_profile,
    load_artifact_structure_reference,
    validate_artifact_structure_profile,
)
from .preflight import (
    SysMLGenerationPreflightResult,
    SysMLGenerationPreflightService,
)
from .text_safety import (
    normalize_engineering_text,
    normalize_optional_engineering_text,
)
from .projection_types import (
    SysMLElementProjection,
    SysMLPackageProjection,
    SysMLProjectionPlan,
    SysMLRelationshipProjection,
)
from .projection import SysMLProjectionPlanService
from .element_renderer import (
    RenderedSysMLElement,
    SysMLElementRenderer,
)
from .relationship_renderer import (
    RenderedSysMLRelationship,
    SysMLRelationshipRenderer,
)

from .generator_rules import (
    DEFAULT_GENERATOR_RULES_PATH,
    EXPECTED_GENERATOR_RULES_ID,
    EXPECTED_GENERATOR_RULES_VERSION,
    GENERATOR_RULES_SCHEMA_VERSION,
    calculate_generator_rules_fingerprint,
    load_generator_rules,
    load_generator_rules_reference,
    validate_generator_rules,
)
from .artifact_builder import (
    GENERATED_SYSML_ARTIFACT_SET_SCHEMA_VERSION,
    GENERATOR_IMPLEMENTATION_REFERENCE,
    SysMLArtifactSetBuilder,
    calculate_generation_input_fingerprint,
    validate_generated_artifact_set_integrity,
)

from .service import SysMLGenerationService

__all__ = [name for name in globals() if not name.startswith("_")]
