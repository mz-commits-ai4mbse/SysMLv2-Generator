"""Exceptions raised by terminology and ontology mapping."""


class TerminologyMappingError(Exception):
    """Base exception for terminology-mapping failures."""


class TerminologyMappingValidationError(
    TerminologyMappingError
):
    """Raised when mapping data violates its explicit contract."""


class TerminologyMappingIntegrityError(
    TerminologyMappingError
):
    """Raised when mapping content is internally inconsistent."""


class TerminologyMappingConfigurationError(
    TerminologyMappingError
):
    """Raised when mapping inputs are configured inconsistently."""


class TerminologyMappingReferenceError(
    TerminologyMappingError
):
    """Raised when mapping data references an invalid artifact."""


class TerminologyMappingComparisonError(
    TerminologyMappingError
):
    """Raised when mapping proposals cannot be compared safely."""


class TerminologyMappingPersistenceError(
    TerminologyMappingError
):
    """Raised when a validated mapping candidate cannot be persisted."""


class TerminologyMappingCandidateIdAllocationError(
    TerminologyMappingError
):
    """Raised when no safe persistent mapping-candidate ID is available."""


class TerminologyMappingAgentCandidateIdAllocationError(
    TerminologyMappingError
):
    """Raised when no result-local agent-candidate ID is available."""


class DuplicateTerminologyMappingAgentResultError(
    TerminologyMappingIntegrityError
):
    """Raised when the same persona run occurs more than once."""


class DuplicateTerminologyMappingAgentCandidateError(
    TerminologyMappingIntegrityError
):
    """Raised when one agent candidate occurs more than once."""


class DuplicateTerminologyMappingCandidateError(
    TerminologyMappingIntegrityError
):
    """Raised when persisted mapping-candidate content is duplicated."""


class IncomparableTerminologyMappingClusterError(
    TerminologyMappingComparisonError
):
    """Raised when mapping proposals cannot be aligned deterministically."""