from __future__ import annotations

import subprocess
from types import SimpleNamespace

from modules.sysml_validation.syside_cli import SysideCliValidator


def test_syside_0103_all_checks_passed_is_trusted_success():
    unit = SimpleNamespace(
        unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content="package GeneratedModel {\n}\n",
    )
    artifact = SimpleNamespace(
        units=(unit,),
        traceability_entries=(),
    )

    def runner(command, **kwargs):
        if tuple(command)[1:] == ("--version",):
            return subprocess.CompletedProcess(
                command,
                0,
                "syside 0.10.3 (b6e216cb)\n",
                "",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            "All checks passed!\n",
            "",
        )

    result = SysideCliValidator(
        executable_finder=lambda _name: "/machine/syside",
        command_runner=runner,
    ).validate(artifact)

    assert result.evidence.execution_status == "completed"
    assert result.evidence.exit_code == 0
    assert result.evidence.normalized_diagnostic_count == 0
    assert result.findings == ()
