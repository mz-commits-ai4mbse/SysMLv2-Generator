"""Exceptions raised by deterministic semantic consensus."""


class SemanticConsensusError(Exception):
    """Base exception for semantic consensus failures."""


class SemanticConsensusValidationError(
    SemanticConsensusError
):
    """Raised when consensus data violates its contract."""


class SemanticConsensusIntegrityError(
    SemanticConsensusError
):
    """Raised when consensus content is internally inconsistent."""


class SemanticConsensusConfigurationError(
    SemanticConsensusError
):
    """Raised when persona-team inputs are configured inconsistently."""


class SemanticConsensusReferenceError(
    SemanticConsensusError
):
    """Raised when a consensus input references invalid data."""


class SemanticConsensusComparisonError(
    SemanticConsensusError
):
    """Raised when candidate values cannot be compared safely."""


class SemanticConsensusPublicationError(
    SemanticConsensusError
):
    """Raised when an Information Unit cannot be prepared or published."""


class SemanticConsensusPublicationNotAuthorizedError(
    SemanticConsensusPublicationError
):
    """Raised when publication lacks explicit human authorization."""


class SemanticConsensusCandidateIdAllocationError(
    SemanticConsensusError
):
    """Raised when no safe consensus-candidate ID can be allocated."""


class DuplicateSemanticAgentResultError(
    SemanticConsensusIntegrityError
):
    """Raised when the same persona run occurs more than once."""


class DuplicateAgentCandidateReferenceError(
    SemanticConsensusIntegrityError
):
    """Raised when one agent candidate is referenced more than once."""


class IncomparableCandidateClusterError(
    SemanticConsensusComparisonError
):
    """Raised when a cluster cannot be aligned deterministically."""