"""Application version and local development build identity."""

from __future__ import annotations

from pathlib import Path
import subprocess


TURING_GENERATOR_VERSION = "0.4.0"


def local_build_label(project_root: Path) -> str:
    """Return a compact best-effort Git build label for local development."""

    root = Path(project_root)

    def run(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        value = result.stdout.strip()
        return value or None

    branch = run("branch", "--show-current") or "git-unavailable"
    commit = run("rev-parse", "--short", "HEAD") or "unknown"

    try:
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
        )
    except (OSError, subprocess.SubprocessError):
        dirty = False

    suffix = " · modified" if dirty else ""
    return f"{branch} · {commit}{suffix}"
