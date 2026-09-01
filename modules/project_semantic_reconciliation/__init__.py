"""ADR-032 project-level cross-source semantic reconciliation."""

from .contract import (
    PROJECT_SEMANTIC_RECONCILIATION_SCHEMA_VERSION,
    create_project_semantic_reconciliation_artifact,
    parse_project_semantic_reconciliation_response,
    prepare_project_semantic_subjects,
    project_semantic_reconciliation_to_dict,
    project_semantic_reconciliation_to_json,
    validate_project_semantic_reconciliation_artifact,
)
from .errors import (
    ProjectSemanticReconciliationError,
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)
from .prompt import (
    PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS,
    PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION,
    build_project_semantic_reconciliation_input,
    build_project_semantic_reconciliation_instructions,
)
from .service import ProjectSemanticReconciliationService
from .types import (
    PROJECT_SEMANTIC_RELATION_OUTCOMES,
    ProjectSemanticFieldEvidence,
    ProjectSemanticMentionEvidence,
    ProjectSemanticReconciliationArtifact,
    ProjectSemanticRelation,
    ProjectSemanticSourceInput,
    ProjectSemanticStatementEvidence,
    ProjectSemanticSubject,
)

__all__ = [
    "PROJECT_SEMANTIC_RECONCILIATION_MAX_INPUT_CHARACTERS",
    "PROJECT_SEMANTIC_RECONCILIATION_PROMPT_SCHEMA_VERSION",
    "PROJECT_SEMANTIC_RECONCILIATION_SCHEMA_VERSION",
    "PROJECT_SEMANTIC_RELATION_OUTCOMES",
    "ProjectSemanticFieldEvidence",
    "ProjectSemanticMentionEvidence",
    "ProjectSemanticReconciliationArtifact",
    "ProjectSemanticReconciliationError",
    "ProjectSemanticReconciliationIntegrityError",
    "ProjectSemanticReconciliationService",
    "ProjectSemanticReconciliationValidationError",
    "ProjectSemanticRelation",
    "ProjectSemanticSourceInput",
    "ProjectSemanticStatementEvidence",
    "ProjectSemanticSubject",
    "build_project_semantic_reconciliation_input",
    "build_project_semantic_reconciliation_instructions",
    "create_project_semantic_reconciliation_artifact",
    "parse_project_semantic_reconciliation_response",
    "prepare_project_semantic_subjects",
    "project_semantic_reconciliation_to_dict",
    "project_semantic_reconciliation_to_json",
    "validate_project_semantic_reconciliation_artifact",
]
