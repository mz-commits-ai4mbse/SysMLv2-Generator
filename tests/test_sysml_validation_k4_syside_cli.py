from __future__ import annotations

from pathlib import Path
import subprocess
from types import SimpleNamespace

from modules.sysml_validation import (
    EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID,
    EXPECTED_EXTERNAL_VALIDATOR_ID,
    SYSIDE_CHECK_COMMAND_CONFIGURATION,
    SysideCliValidator,
    calculate_json_fingerprint,
)


def _artifact(*, content: str = "package GeneratedModel {\n}\n"):
    unit = SimpleNamespace(
        unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content=content,
    )
    trace = SimpleNamespace(
        generated_unit_id="GSU-000001",
        generated_symbol_id="IME_000001",
        generated_location=SimpleNamespace(start_line=1, end_line=2),
    )
    return SimpleNamespace(units=(unit,), traceability_entries=(trace,))


def _runner_for_check(check_result, *, inspect_check=None, version="0.9.0 (abc123)"):
    def runner(command, **kwargs):
        if tuple(command)[1:] == ("--version",):
            return subprocess.CompletedProcess(command, 0, version + "\n", "")
        if inspect_check is not None:
            inspect_check(tuple(command), kwargs)
        if callable(check_result):
            return check_result(tuple(command), kwargs)
        return check_result

    return runner


def _validator(check_result, *, inspect_check=None, version="0.9.0 (abc123)"):
    return SysideCliValidator(
        executable_finder=lambda _name: "/machine/syside",
        command_runner=_runner_for_check(
            check_result,
            inspect_check=inspect_check,
            version=version,
        ),
    )


def test_k4_configuration_fingerprint_is_deterministic_and_machine_path_free():
    first = SysideCliValidator(executable_finder=lambda _name: "/one/syside")
    second = SysideCliValidator(executable_finder=lambda _name: "/other/syside")
    expected = calculate_json_fingerprint(SYSIDE_CHECK_COMMAND_CONFIGURATION)
    assert first.configuration_fingerprint == expected
    assert second.configuration_fingerprint == expected
    assert SYSIDE_CHECK_COMMAND_CONFIGURATION["warnings_as_errors"] is False
    assert SYSIDE_CHECK_COMMAND_CONFIGURATION["workspace_mode"] == (
        "isolated_exact_units_utf8"
    )


def test_k4_unavailable_validator_is_explicit_and_never_a_pass():
    run = SysideCliValidator(executable_finder=lambda _name: None).validate(_artifact())
    assert run.evidence.execution_status == "unavailable"
    assert run.evidence.exit_code is None
    assert run.evidence.validator_identity.tool_version is None
    assert run.findings[0].category == "validator_infrastructure"
    assert run.findings[0].severity == "error"
    assert run.findings[0].blocking is True
    assert run.findings[0].code == "K4_SYSIDE_UNAVAILABLE"


def test_k4_materializes_exact_bytes_and_runs_only_controlled_check_contract():
    observed_root = None
    expected = "package GeneratedModel {\n    doc /* ä */\n}\n"

    def inspect(command, kwargs):
        nonlocal observed_root
        root = Path(kwargs["cwd"])
        observed_root = root
        assert (root / "generated_model.sysml").read_bytes() == expected.encode("utf-8")
        assert command[0] == "/machine/syside"
        assert command[1:] == (
            "check",
            "--diagnose",
            "project",
            "--colour",
            "no",
            "--crash-reports",
            "ignore",
            "-j",
            "1",
            "generated_model.sysml",
        )

    run = _validator(
        subprocess.CompletedProcess(("syside",), 0, "", ""),
        inspect_check=inspect,
    ).validate(_artifact(content=expected))
    assert run.evidence.execution_status == "completed"
    assert run.evidence.normalized_diagnostic_count == 0
    assert run.findings == ()
    assert observed_root is not None and not observed_root.exists()


def test_k4_normalizes_absolute_error_path_and_links_trace_symbol():
    def result(_command, kwargs):
        path = Path(kwargs["cwd"]) / "generated_model.sysml"
        stdout = (
            f"{path}:1:9: error (type-error): Example semantic error\n"
            "   1 | package GeneratedModel {\n"
            "     |         ^\n"
        )
        return subprocess.CompletedProcess(("syside",), 1, stdout, "")

    run = _validator(result).validate(_artifact())
    assert run.evidence.execution_status == "completed"
    assert run.evidence.exit_code == 1
    assert run.evidence.normalized_diagnostic_count == 1
    finding = run.findings[0]
    assert finding.code == "SYSIDE_TYPE_ERROR"
    assert finding.category == "external_semantics"
    assert finding.severity == "error"
    assert finding.blocking is True
    assert finding.generated_unit_id == "GSU-000001"
    assert finding.generated_symbol_id == "IME_000001"
    assert finding.generated_location.start_line == 1
    assert finding.generated_location.start_column == 9
    assert finding.validator_rule_id == "type-error"


def test_k4_warning_is_visible_but_nonblocking():
    check = subprocess.CompletedProcess(
        ("syside",),
        0,
        "generated_model.sysml:2:3: warning (example-warning): Example warning\n",
        "",
    )
    run = _validator(check).validate(_artifact())
    assert run.evidence.execution_status == "completed"
    assert run.evidence.normalized_diagnostic_count == 1
    finding = run.findings[0]
    assert finding.category == "external_warning"
    assert finding.severity == "warning"
    assert finding.blocking is False


def test_k4_syntax_rule_is_classified_separately_from_semantic_error():
    check = subprocess.CompletedProcess(
        ("syside",),
        1,
        "generated_model.sysml:1:1: error (syntax-error): Unexpected token\n",
        "",
    )
    run = _validator(check).validate(_artifact())
    assert run.evidence.execution_status == "completed"
    assert run.findings[0].category == "external_syntax"
    assert run.findings[0].code == "SYSIDE_SYNTAX_ERROR"


def test_k4_nonzero_without_model_error_is_external_execution_failure():
    check = subprocess.CompletedProcess(("syside",), 2, "license failure\n", "")
    run = _validator(check).validate(_artifact())
    assert run.evidence.execution_status == "failed"
    assert run.evidence.exit_code == 2
    assert run.evidence.normalized_diagnostic_count == 0
    assert run.findings[0].category == "validator_infrastructure"
    assert run.findings[0].severity == "error"
    assert run.findings[0].blocking is True


def test_k4_unmapped_diagnostic_path_fails_normalization_without_leaking_path():
    check = subprocess.CompletedProcess(
        ("syside",),
        1,
        "/private/machine/other.sysml:4:2: error (type-error): Broken\n",
        "",
    )
    run = _validator(check).validate(_artifact())
    assert run.evidence.execution_status == "failed"
    assert run.evidence.normalized_diagnostic_count == 0
    assert len(run.findings) == 1
    assert run.findings[0].code == "K4_SYSIDE_OUTPUT_UNTRUSTED"
    assert "/private/machine" not in run.findings[0].message


def test_k4_ansi_is_removed_from_version_and_diagnostic_output():
    check = subprocess.CompletedProcess(
        ("syside",),
        1,
        "\x1b[31mgenerated_model.sysml:1:1: error (type-error): Red error\x1b[0m\n",
        "",
    )
    run = _validator(check, version="\x1b[32m0.9.0 (abc123)\x1b[0m").validate(
        _artifact()
    )
    assert run.evidence.validator_identity.tool_version == "0.9.0 (abc123)"
    assert run.findings[0].message == "Red error"
    assert "\x1b" not in run.findings[0].message


def test_k4_validator_version_is_part_of_external_identity():
    clean = subprocess.CompletedProcess(("syside",), 0, "", "")
    first = _validator(clean, version="0.9.0 (aaa)").validate(_artifact())
    second = _validator(clean, version="0.9.1 (bbb)").validate(_artifact())
    assert first.evidence.validator_identity.tool_version == "0.9.0 (aaa)"
    assert second.evidence.validator_identity.tool_version == "0.9.1 (bbb)"
    assert first.evidence.validator_identity != second.evidence.validator_identity
    assert first.evidence.validator_identity.validator_id == EXPECTED_EXTERNAL_VALIDATOR_ID
    assert first.evidence.validator_identity.command_contract_id == (
        EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID
    )


def test_k4_version_resolution_failure_is_infrastructure_failure():
    def runner(command, **_kwargs):
        assert tuple(command)[1:] == ("--version",)
        return subprocess.CompletedProcess(command, 1, "", "version error")

    run = SysideCliValidator(
        executable_finder=lambda _name: "/machine/syside",
        command_runner=runner,
    ).validate(_artifact())
    assert run.evidence.execution_status == "failed"
    assert run.evidence.validator_identity.tool_version is None
    assert run.findings[0].code == "K4_SYSIDE_IDENTITY_FAILED"
