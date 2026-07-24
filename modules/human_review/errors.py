"""Exceptions raised by Human Review and token budgeting."""


class HumanReviewError(Exception):
    """Base exception for Human Review failures."""


class HumanReviewValidationError(HumanReviewError):
    """Raised when review data violates its explicit contract."""


class HumanReviewIntegrityError(HumanReviewError):
    """Raised when review content is internally inconsistent."""


class HumanReviewReferenceError(HumanReviewError):
    """Raised when a review references an invalid artifact."""


class HumanReviewPersistenceError(HumanReviewError):
    """Raised when an immutable review decision cannot be persisted."""


class HumanReviewDecisionIdAllocationError(HumanReviewError):
    """Raised when no safe Human Review Decision ID is available."""


class DuplicateHumanReviewDecisionError(
    HumanReviewIntegrityError
):
    """Raised when equivalent review content already exists."""


class TokenBudgetError(HumanReviewError):
    """Base exception for deterministic context budgeting."""


class TokenBudgetValidationError(TokenBudgetError):
    """Raised when token-budget input violates its contract."""


class TokenBudgetExceededError(TokenBudgetError):
    """Raised when required context cannot fit without truncation."""


class TokenEstimationError(TokenBudgetError):
    """Raised when deterministic token estimation is unavailable."""