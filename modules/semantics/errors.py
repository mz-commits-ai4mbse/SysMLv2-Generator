"""Exceptions raised by semantic-reference operations."""


class SemanticReferenceError(Exception):
    """Base exception for semantic-reference failures."""


class OntologyRegistryError(SemanticReferenceError):
    """Raised when the Ontology Registry violates its contract."""


class OntologySnapshotError(SemanticReferenceError):
    """Base exception for local ontology snapshot failures."""


class OntologySnapshotNotFoundError(OntologySnapshotError):
    """Raised when a registered ontology snapshot does not exist."""


class OntologySnapshotIntegrityError(OntologySnapshotError):
    """Raised when a snapshot violates its size or checksum contract."""


class UnsafeOntologyPathError(OntologySnapshotError):
    """Raised when an ontology path escapes the repository boundary."""


class UnsupportedOntologySerializationError(
    OntologySnapshotError
):
    """Raised when an ontology serialization is not supported."""


class OntologyParseError(OntologySnapshotError):
    """Raised when a verified ontology snapshot cannot be parsed."""


class ReferenceConceptIndexError(SemanticReferenceError):
    """Raised when a Reference Concept Index is invalid."""


class DuplicateReferenceConceptIriError(
    ReferenceConceptIndexError
):
    """Raised when multiple indexed concepts use the same IRI."""


class ReferenceConceptNotFoundError(
    ReferenceConceptIndexError
):
    """Raised when a requested reference concept does not exist."""


class TuringCoreVocabularyError(SemanticReferenceError):
    """Raised when the Turing Core Vocabulary is invalid."""