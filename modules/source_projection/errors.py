"""Exceptions raised by deterministic Source Projection processing."""


class SourceProjectionError(Exception):
    """Base exception for Source Projection failures."""


class SourceProjectionManifestError(SourceProjectionError):
    """Raised when persisted Source Projection metadata is invalid."""


class SourceProjectionNotFoundError(SourceProjectionError):
    """Raised when a requested Source Projection does not exist."""


class SourceProjectionIdExhaustedError(SourceProjectionError):
    """Raised when no project-local Source Projection ID remains."""


class SegmentIdExhaustedError(SourceProjectionError):
    """Raised when no projection-local Segment ID remains."""


class SourceAdapterError(SourceProjectionError):
    """Base exception for deterministic source-adapter failures."""


class UnsupportedSourceFormatError(SourceAdapterError):
    """Raised when no accepted deterministic adapter supports a source."""


class UnsupportedTextEncodingError(SourceAdapterError):
    """Raised when textual source bytes are not valid UTF-8."""


class DuplicateJsonKeyError(SourceAdapterError):
    """Raised when a JSON object contains a duplicate member name."""


class SourceProjectionIntegrityError(SourceProjectionError):
    """Raised when persisted projection content fails integrity checks."""


class UnsafeSourceProjectionPathError(SourceProjectionError):
    """Raised when a projection path violates the storage boundary."""