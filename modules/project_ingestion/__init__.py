"""Public API for project-bound ingestion integration."""

from .configuration import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    DEFAULT_RECIPE_ID,
    DEFAULT_SEMANTIC_REFERENCE_VERSIONS,
    PIPELINE_CONFIGURATION_VERSION,
    ProjectIngestionConfiguration,
    calculate_ingestion_configuration_fingerprint,
    validate_ingestion_configuration,
    workflow_profile_for_source_role,
)
from .errors import (
    ProjectIngestionConfigurationError,
    ProjectIngestionError,
    ProjectIngestionExecutionError,
    ProjectIngestionInputError,
    ProjectIngestionPathError,
    ProjectIngestionTemporaryFileError,
)
from .service import ProjectBoundIngestionService
from .types import (
    ProjectBoundIngestionWorkResult,
    ProjectBoundSourceInventory,
    ProjectBoundSourceIssue,
    ProjectBoundSourceSummary,
)

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "DEFAULT_RECIPE_ID",
    "DEFAULT_SEMANTIC_REFERENCE_VERSIONS",
    "PIPELINE_CONFIGURATION_VERSION",
    "ProjectBoundIngestionService",
    "ProjectBoundIngestionWorkResult",
    "ProjectBoundSourceInventory",
    "ProjectBoundSourceIssue",
    "ProjectBoundSourceSummary",
    "ProjectIngestionConfiguration",
    "ProjectIngestionConfigurationError",
    "ProjectIngestionError",
    "ProjectIngestionExecutionError",
    "ProjectIngestionInputError",
    "ProjectIngestionPathError",
    "ProjectIngestionTemporaryFileError",
    "calculate_ingestion_configuration_fingerprint",
    "validate_ingestion_configuration",
    "workflow_profile_for_source_role",
]
