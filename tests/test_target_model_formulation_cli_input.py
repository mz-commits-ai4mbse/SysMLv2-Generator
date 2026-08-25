import builtins
import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts/wp12_target_model_formulation_review.py"
)


def _load():
    spec = importlib.util.spec_from_file_location(
        "wp12_target_model_formulation_review",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_multiline_rationale_consumes_paste_before_next_prompt(monkeypatch):
    module = _load()
    values = iter(
        [
            "Accepted as a stakeholder-role type.",
            "The SYSIDE fixture was validated.",
            "",
            "y",
        ]
    )
    monkeypatch.setattr(
        builtins,
        "input",
        lambda _prompt="": next(values),
    )

    result = module._multiline_rationale("Rationale")

    assert result == (
        "Accepted as a stakeholder-role type. "
        "The SYSIDE fixture was validated."
    )
    assert builtins.input("") == "y"


def test_multiline_rationale_accepts_done_sentinel(monkeypatch):
    module = _load()
    values = iter(["line one", "line two", ".done"])
    monkeypatch.setattr(
        builtins,
        "input",
        lambda _prompt="": next(values),
    )
    assert module._multiline_rationale("Rationale") == "line one line two"


def test_cli_parser_supports_immutable_successor_review():
    module = _load()
    args = module._parser().parse_args(
        [
            "--project",
            "120412",
            "--iem",
            "IEM-000001",
            "--reviewer",
            "MZ",
            "--revise-existing",
        ]
    )
    assert args.revise_existing is True
