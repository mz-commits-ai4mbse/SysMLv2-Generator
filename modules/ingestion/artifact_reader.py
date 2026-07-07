"""Read raw input artifacts for the ingestion workflow."""

from pathlib import Path


class ArtifactReadError(RuntimeError):
    """Raised when an artifact cannot be read."""


def read_text_artifact(path: Path) -> str:
    if not path.exists():
        raise ArtifactReadError(f"Input artifact does not exist: {path}")
    if not path.is_file():
        raise ArtifactReadError(f"Input artifact is not a file: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ArtifactReadError(
            f"Input artifact is not readable as UTF-8 text: {path}"
        ) from exc
