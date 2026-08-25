from types import SimpleNamespace

from app.model_final_review_ui import _syside_quality_summary


def _result(*, status, exit_code, diagnostics, version="syside 0.10.3"):
    evidence = SimpleNamespace(
        validator_identity=SimpleNamespace(
            tool_name="SYSIDE Modeler CLI",
            tool_version=version,
        ),
        execution_status=status,
        exit_code=exit_code,
        normalized_diagnostic_count=diagnostics,
    )
    return SimpleNamespace(external_validator_evidence=(evidence,))


def test_syside_quality_metric_reports_real_pass():
    summary = _syside_quality_summary(
        _result(status="completed", exit_code=0, diagnostics=0)
    )
    assert summary["available"] is True
    assert summary["passed"] is True
    assert summary["version"] == "syside 0.10.3"


def test_syside_quality_metric_does_not_false_pass():
    summary = _syside_quality_summary(
        _result(status="completed", exit_code=1, diagnostics=2)
    )
    assert summary["available"] is True
    assert summary["passed"] is False


def test_syside_quality_metric_reports_missing_external_evidence():
    summary = _syside_quality_summary(
        SimpleNamespace(external_validator_evidence=())
    )
    assert summary["available"] is False
    assert summary["passed"] is False
