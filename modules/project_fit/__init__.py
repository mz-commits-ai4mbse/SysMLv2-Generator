"""Project-level source-fit assessment under ADR-032."""

from .contract import (
    PROJECT_FIT_ASSESSMENT_SCHEMA_VERSION,
    create_project_fit_assessment,
    derive_project_fit_gate_state,
    parse_project_fit_response,
    prepare_project_fit_context,
    project_fit_assessment_to_dict,
    project_fit_assessment_to_json,
    validate_project_fit_assessment,
)
from .errors import (
    ProjectFitError,
    ProjectFitIntegrityError,
    ProjectFitValidationError,
)
from .prompt import (
    PROJECT_FIT_MAX_INPUT_CHARACTERS,
    PROJECT_FIT_PROMPT_SCHEMA_VERSION,
    build_project_fit_input,
    build_project_fit_instructions,
)
from .service import ProjectFitAssessmentService
from .types import (
    PROJECT_FIT_GATE_STATES,
    PROJECT_FIT_OUTCOMES,
    ProjectFitAssessment,
    ProjectFitContextReference,
)

__all__ = [
    "PROJECT_FIT_ASSESSMENT_SCHEMA_VERSION",
    "PROJECT_FIT_GATE_STATES",
    "PROJECT_FIT_MAX_INPUT_CHARACTERS",
    "PROJECT_FIT_OUTCOMES",
    "PROJECT_FIT_PROMPT_SCHEMA_VERSION",
    "ProjectFitAssessment",
    "ProjectFitAssessmentService",
    "ProjectFitContextReference",
    "ProjectFitError",
    "ProjectFitIntegrityError",
    "ProjectFitValidationError",
    "build_project_fit_input",
    "build_project_fit_instructions",
    "create_project_fit_assessment",
    "derive_project_fit_gate_state",
    "parse_project_fit_response",
    "prepare_project_fit_context",
    "project_fit_assessment_to_dict",
    "project_fit_assessment_to_json",
    "validate_project_fit_assessment",
]
