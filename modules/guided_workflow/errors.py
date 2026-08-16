"""Errors for the non-authoritative Guided Engineering Workflow."""

from __future__ import annotations


class GuidedWorkflowError(Exception):
    """Base error for Guided Workflow presentation failures."""


class GuidedWorkflowValidationError(GuidedWorkflowError, ValueError):
    """Raised when presentation input violates the Guided Workflow contract."""


class GuidedWorkflowWriteError(GuidedWorkflowError):
    """Raised when an explicit Guided Workflow write cannot be delegated safely."""
