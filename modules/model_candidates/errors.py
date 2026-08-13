"""Exceptions raised by the Phase-H Model Candidate layer."""


class ModelCandidateError(Exception):
    """Base exception for Model Candidate failures."""


class ModelCandidateValidationError(ModelCandidateError):
    """Raised when Model Candidate data violates its explicit contract."""


class ModelCandidateIntegrityError(ModelCandidateError):
    """Raised when Model Candidate content is internally inconsistent."""


class ModelCandidateReferenceError(ModelCandidateError):
    """Raised when Model Candidate data references an invalid artifact."""


class ModelCandidatePersistenceError(ModelCandidateError):
    """Raised when validated Model Candidate content cannot be persisted."""


class ModelCandidateNotFoundError(ModelCandidateReferenceError):
    """Raised when a requested Model Candidate Set does not exist."""


class ModelElementCandidateNotFoundError(ModelCandidateReferenceError):
    """Raised when a requested Model Element Candidate does not exist."""


class ModelRelationshipCandidateNotFoundError(
    ModelCandidateReferenceError
):
    """Raised when a requested Model Relationship Candidate does not exist."""


class ModelCandidateRecoveryRequiredError(ModelCandidateIntegrityError):
    """Raised when interrupted Candidate persistence requires recovery."""


class UnsafeModelCandidatePathError(ModelCandidateError):
    """Raised when a Candidate path violates project isolation."""


class ModelCandidateSetIdAllocationError(ModelCandidateError):
    """Raised when no safe Model Candidate Set ID is available."""


class ModelElementCandidateIdAllocationError(ModelCandidateError):
    """Raised when no safe Model Element Candidate ID is available."""


class ModelRelationshipCandidateIdAllocationError(ModelCandidateError):
    """Raised when no safe Model Relationship Candidate ID is available."""


class ModelCandidateDerivationError(ModelCandidateError):
    """Raised when Candidate derivation cannot produce a safe plan."""


class ModelCandidateGenerationBlockedError(ModelCandidateIntegrityError):
    """Raised when Phase-H generation cannot proceed safely."""


class ModelCandidateReviewDecisionIdAllocationError(ModelCandidateError):
    """Raised when no safe Model Candidate Review Decision ID is available."""


class ModelCandidateReviewPersistenceError(ModelCandidatePersistenceError):
    """Raised when a Model Candidate Review Decision cannot be persisted."""


class ModelCandidateReviewNotFoundError(ModelCandidateReferenceError):
    """Raised when a requested Model Candidate Review Decision is absent."""


class ModelCandidatePhaseIGateError(ModelCandidateIntegrityError):
    """Raised when Candidate content is not eligible for Phase-I assembly."""
