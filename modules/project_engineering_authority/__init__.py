"""ADR-032 S4 project-level Engineering Authority reconciliation."""

from .contract import (
    PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION,
    build_project_engineering_authority_state,
    create_project_authority_decision,
    prepare_project_authority_bindings,
    project_engineering_authority_to_dict,
    project_engineering_authority_to_json,
    validate_project_authority_decision,
    validate_project_engineering_authority_state,
)
from .errors import (
    ProjectEngineeringAuthorityError,
    ProjectEngineeringAuthorityIntegrityError,
    ProjectEngineeringAuthorityValidationError,
)
from .types import (
    PROJECT_AUTHORITY_DECISION_OUTCOMES,
    PROJECT_AUTHORITY_STATES,
    ProjectAuthorityDecision,
    ProjectAuthorityEntry,
    ProjectAuthoritySubjectBinding,
    ProjectEngineeringAuthorityState,
)

__all__ = [
    "PROJECT_AUTHORITY_DECISION_OUTCOMES",
    "PROJECT_AUTHORITY_STATES",
    "PROJECT_ENGINEERING_AUTHORITY_SCHEMA_VERSION",
    "ProjectAuthorityDecision",
    "ProjectAuthorityEntry",
    "ProjectAuthoritySubjectBinding",
    "ProjectEngineeringAuthorityError",
    "ProjectEngineeringAuthorityIntegrityError",
    "ProjectEngineeringAuthorityState",
    "ProjectEngineeringAuthorityValidationError",
    "build_project_engineering_authority_state",
    "create_project_authority_decision",
    "prepare_project_authority_bindings",
    "project_engineering_authority_to_dict",
    "project_engineering_authority_to_json",
    "validate_project_authority_decision",
    "validate_project_engineering_authority_state",
]
