"""Public API for the Phase-I Internal Engineering Model layer."""

from .assembly_rules import (
    DEFAULT_INTERNAL_MODEL_ASSEMBLY_RULES_PATH,
    EXPECTED_INTERNAL_MODEL_ASSEMBLY_RULES_ID,
    INTERNAL_MODEL_ASSEMBLY_RULES_SCHEMA_VERSION,
    calculate_internal_model_assembly_rules_fingerprint,
    load_internal_model_assembly_rules,
    load_internal_model_assembly_rules_reference,
    validate_internal_model_assembly_rules,
)
from .structure_materialization import (
    InternalModelStructureMaterializer,
    InternalModelStructureResolver,
    ResolvedInternalModelStructureContext,
)
from .assembly import InternalModelAssemblyService
from .paths import (
    INTERNAL_MODELS_DIRECTORY_NAME,
    INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME,
    INTERNAL_MODEL_MANIFEST_FILENAME,
    INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME,
    INTERNAL_MODEL_STRUCTURE_FILENAME,
    internal_engineering_model_path,
    internal_model_element_filename,
    internal_model_elements_path,
    internal_model_manifest_path,
    internal_model_relationship_filename,
    internal_model_relationships_path,
    internal_model_structure_path,
    internal_models_path,
)
from .persistence_service import InternalModelPersistenceService
from .phase_j_read_service import InternalModelReadService
from .repository import InternalModelRepository
from .repository_errors import (
    InternalEngineeringModelNotFoundError,
    InternalModelRecoveryRequiredError,
    UnsafeInternalModelPathError,
)
from .repository_integrity import (
    validate_internal_engineering_model_snapshot,
)
from .repository_scan import scan_internal_model_repository
from .repository_types import (
    InternalModelRepositoryIssue,
    InternalModelRepositoryScanResult,
)
from .assembly_input import (
    calculate_model_candidate_assembly_input_fingerprint,
    model_candidate_assembly_input_to_fingerprint_payload,
)
from .element_manifest import (
    INTERNAL_MODEL_ELEMENT_SCHEMA_VERSION,
    calculate_internal_model_element_fingerprint,
    create_internal_model_element,
    internal_model_element_from_json,
    internal_model_element_to_dict,
    internal_model_element_to_json,
    parse_internal_model_element,
    validate_internal_model_element,
)
from .errors import (
    InternalEngineeringModelIdAllocationError,
    InternalModelAssemblyBlockedError,
    InternalModelAssemblyError,
    InternalModelElementIdAllocationError,
    InternalModelError,
    InternalModelIntegrityError,
    InternalModelPersistenceError,
    InternalModelReferenceError,
    InternalModelRelationshipIdAllocationError,
    InternalModelValidationError,
)
from .identifiers import (
    INTERNAL_ENGINEERING_MODEL_ID_PATTERN,
    INTERNAL_MODEL_ELEMENT_ID_PATTERN,
    INTERNAL_MODEL_RELATIONSHIP_ID_PATTERN,
    MAX_INTERNAL_MODEL_SEQUENCE,
    MIN_INTERNAL_MODEL_SEQUENCE,
    format_internal_engineering_model_id,
    format_internal_model_element_id,
    format_internal_model_relationship_id,
    internal_engineering_model_id_sequence,
    internal_model_element_id_sequence,
    internal_model_relationship_id_sequence,
    is_valid_internal_engineering_model_id,
    is_valid_internal_model_element_id,
    is_valid_internal_model_relationship_id,
    next_internal_engineering_model_id,
    next_internal_model_element_id,
    next_internal_model_relationship_id,
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
    validate_internal_model_relationship_id,
)
from .model_manifest import (
    INTERNAL_ENGINEERING_MODEL_SCHEMA_VERSION,
    calculate_internal_engineering_model_fingerprint,
    create_internal_engineering_model_manifest,
    internal_engineering_model_manifest_from_json,
    internal_engineering_model_manifest_to_dict,
    internal_engineering_model_manifest_to_json,
    parse_internal_engineering_model_manifest,
    validate_internal_engineering_model_manifest,
)
from .relationship_manifest import (
    INTERNAL_MODEL_RELATIONSHIP_SCHEMA_VERSION,
    calculate_internal_model_relationship_fingerprint,
    create_internal_model_relationship,
    internal_model_relationship_from_json,
    internal_model_relationship_to_dict,
    internal_model_relationship_to_json,
    parse_internal_model_relationship,
    validate_internal_model_relationship,
)
from .structure_manifest import (
    INTERNAL_MODEL_STRUCTURE_SCHEMA_VERSION,
    calculate_internal_model_structure_fingerprint,
    create_internal_model_structure,
    internal_model_structure_from_json,
    internal_model_structure_to_dict,
    internal_model_structure_to_json,
    parse_internal_model_structure,
    validate_internal_model_structure,
)
from .types import (
    InternalEngineeringModelManifest,
    InternalEngineeringModelSnapshot,
    InternalModelAssemblyContext,
    InternalModelAssemblyFinding,
    InternalModelAssemblyProvenance,
    InternalModelAssemblyRulesReference,
    InternalModelAttribute,
    InternalModelElement,
    InternalModelRelationship,
    InternalModelStructure,
    InternalModelStructureNode,
)

__all__ = [name for name in globals() if not name.startswith("_")]
