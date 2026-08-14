"""Public API for deterministic Phase-K SysML v2 validation."""

from .errors import (
    SysMLValidationContractError,
    SysMLValidationError,
    SysMLValidationProfileError,
)
from .fingerprints import (
    SHA256_HEX_PATTERN,
    calculate_json_fingerprint,
    canonical_json_bytes,
    validate_sha256_fingerprint,
)
from .types import (
    EXTERNAL_VALIDATOR_EXECUTION_STATUSES,
    PUBLICATION_GATES,
    VALIDATION_FINDING_CATEGORIES,
    VALIDATION_SEVERITIES,
    VALIDATION_STATUSES,
    SysMLExternalValidationEvidence,
    SysMLExternalValidationRun,
    SysMLExternalValidatorIdentity,
    SysMLValidationFinding,
    SysMLValidationLocation,
    SysMLValidationProfileReference,
    SysMLValidationResult,
)
from .validation_profile import (
    DEFAULT_VALIDATION_PROFILE_PATH,
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
    EXPECTED_EXTERNAL_TOOL_NAME,
    EXPECTED_VALIDATION_PROFILE_ID,
    EXPECTED_VALIDATION_PROFILE_VERSION,
    VALIDATION_PROFILE_SCHEMA_VERSION,
    calculate_validation_profile_fingerprint,
    load_validation_profile,
    load_validation_profile_reference,
    validate_validation_profile,
)

from .artifact_integrity import (
    calculate_received_artifact_set_fingerprint,
    calculate_received_generation_input_fingerprint,
    validate_artifact_set_integrity,
)
from .artifact_structure_validator import validate_artifact_structure
from .finding_support import sort_validation_findings, to_validation_location
from .target_notation_validator import validate_target_notation_subset
from .traceability import validate_traceability
from .validation_context import validate_generation_context

from .relationship_validator import validate_relationship_consistency

__all__ = [name for name in globals() if not name.startswith("_")]

from .external_validator import SysMLExternalValidator
from .syside_cli import (
    SYSIDE_CHECK_COMMAND_CONFIGURATION,
    SYSIDE_EXECUTABLE_NAME,
    SysideCliValidator,
)
from .service import (
    SYSML_VALIDATION_RESULT_SCHEMA_VERSION,
    SysMLValidationService,
    calculate_validation_input_fingerprint,
    calculate_validation_result_fingerprint,
    validate_validation_result_integrity,
)

from .phase_l_gate import validate_phase_l_handoff
