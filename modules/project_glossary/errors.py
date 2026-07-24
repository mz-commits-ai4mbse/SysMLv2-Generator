"""Exceptions raised by Project Glossary operations."""


class ProjectGlossaryError(Exception):
    """Base exception for Project Glossary failures."""


class ProjectGlossaryValidationError(ProjectGlossaryError):
    """Raised when a Project Glossary violates its contract."""


class ProjectGlossaryIntegrityError(ProjectGlossaryError):
    """Raised when persisted glossary data fails integrity checks."""


class ProjectGlossaryNotFoundError(ProjectGlossaryError):
    """Raised when a project has no persisted Project Glossary."""


class ProjectGlossaryPersistenceError(ProjectGlossaryError):
    """Raised when a Project Glossary cannot be persisted safely."""


class UnsafeProjectGlossaryPathError(ProjectGlossaryError):
    """Raised when a glossary path escapes its project boundary."""


class ProjectConceptNotFoundError(ProjectGlossaryError):
    """Raised when a requested Project Concept does not exist."""


class ProjectConceptIdAllocationError(ProjectGlossaryError):
    """Raised when no safe Project Concept ID can be allocated."""


class ProjectConceptRevisionError(ProjectGlossaryError):
    """Raised when a Project Concept revision is invalid."""


class DuplicatePreferredLabelError(ProjectGlossaryError):
    """Raised when accepted preferred labels conflict."""


class AmbiguousAlternativeLabelError(ProjectGlossaryError):
    """Raised when an ambiguous label lacks an Ambiguity Group."""


class AmbiguityGroupNotFoundError(ProjectGlossaryError):
    """Raised when a requested Ambiguity Group does not exist."""


class AmbiguityGroupIdAllocationError(ProjectGlossaryError):
    """Raised when no safe Ambiguity Group ID can be allocated."""


class TerminologyDecisionError(ProjectGlossaryError):
    """Raised when a Terminology Decision is invalid."""


class InvalidTerminologyLifecycleTransitionError(
    TerminologyDecisionError
):
    """Raised when a terminology lifecycle transition is invalid."""