"""Exceptions raised by framework assignment."""


class FrameworkAssignmentError(Exception):
    """Base exception for framework-assignment failures."""


class FrameworkAssignmentValidationError(
    FrameworkAssignmentError
):
    """Raised when assignment data violates its explicit contract."""


class FrameworkAssignmentIntegrityError(
    FrameworkAssignmentError
):
    """Raised when assignment content is internally inconsistent."""


class FrameworkAssignmentConfigurationError(
    FrameworkAssignmentError
):
    """Raised when assignment inputs are configured inconsistently."""


class FrameworkAssignmentReferenceError(
    FrameworkAssignmentError
):
    """Raised when assignment data references an invalid artifact."""


class FrameworkAssignmentComparisonError(
    FrameworkAssignmentError
):
    """Raised when assignment proposals cannot be compared safely."""


class FrameworkAssignmentPersistenceError(
    FrameworkAssignmentError
):
    """Raised when a validated assignment candidate cannot be persisted."""


class FrameworkAssignmentCandidateIdAllocationError(
    FrameworkAssignmentError
):
    """Raised when no safe persistent candidate ID is available."""


class FrameworkAssignmentAgentCandidateIdAllocationError(
    FrameworkAssignmentError
):
    """Raised when no result-local agent-candidate ID is available."""


class DuplicateFrameworkAssignmentAgentResultError(
    FrameworkAssignmentIntegrityError
):
    """Raised when the same persona run occurs more than once."""


class DuplicateFrameworkAssignmentAgentCandidateError(
    FrameworkAssignmentIntegrityError
):
    """Raised when one agent candidate occurs more than once."""


class DuplicateFrameworkAssignmentCandidateError(
    FrameworkAssignmentIntegrityError
):
    """Raised when persisted assignment-candidate content is duplicated."""


class IncomparableFrameworkAssignmentClusterError(
    FrameworkAssignmentComparisonError
):
    """Raised when assignment proposals cannot be aligned safely."""