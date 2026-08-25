"""Fresh-process import-order regression for Model Placement boundary."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _fresh_import(code: str) -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        "fresh import failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_model_placement_can_be_imported_before_model_candidates():
    _fresh_import(
        "import modules.model_placement; "
        "import modules.model_candidates"
    )


def test_model_candidates_can_be_imported_before_model_placement():
    _fresh_import(
        "import modules.model_candidates; "
        "import modules.model_placement"
    )
