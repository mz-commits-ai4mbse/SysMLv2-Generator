from pathlib import Path

from app.model_refinement_review_ui import (
    _authority_id,
    _formulation_candidate_label,
    _humanize,
)


class Candidate:
    relevance_outcome = "materialize_formally"
    target_notation_construct_id = "TN_003"


class Authority:
    authority_set_id = "MQA-000001"


def test_user_facing_helpers_use_engineering_terms():
    assert _humanize("stakeholder.stakeholder_requirements") == (
        "Stakeholder · Stakeholder Requirements"
    )
    assert _formulation_candidate_label(Candidate()) == (
        "Materialize Formally · TN_003"
    )
    assert _authority_id(Authority()) == "MQA-000001"
    assert _authority_id({"authority_set_id": "TFA-000001"}) == "TFA-000001"


def test_model_refinement_ui_does_not_expose_development_code():
    text = Path("app/model_refinement_review_ui.py").read_text(encoding="utf-8")
    # Internal class/module names may retain legacy implementation identifiers,
    # but no quoted user-facing string may expose the development code.
    assert '"SEM-015' not in text
    assert "'SEM-015" not in text
    assert "Model Refinement" in text
    assert "Human Model Quality Review" in text


def test_model_final_review_delegates_to_refinement_ui():
    text = Path("app/model_final_review_ui.py").read_text(encoding="utf-8")
    assert "render_model_refinement_review" in text
    assert '"SEM-015 approved model"' not in text
    assert '"No SEM-015 quality/formulation successor' not in text

def test_refinement_returns_successor_to_downstream_generation_wrapper(monkeypatch):
    from types import SimpleNamespace

    import app.model_refinement_review_ui as module

    formulation = object()
    quality = object()
    successor = object()

    monkeypatch.setattr(
        module,
        "_render_model_formulation",
        lambda *args, **kwargs: formulation,
    )
    monkeypatch.setattr(
        module,
        "_render_model_quality_review",
        lambda *args, **kwargs: quality,
    )
    monkeypatch.setattr(
        module,
        "_render_approved_model",
        lambda *args, **kwargs: successor,
    )

    class FakeStreamlit:
        def markdown(self, *args, **kwargs):
            return None

        def caption(self, *args, **kwargs):
            return None

        def text_input(self, *args, **kwargs):
            return "MZ"

    base_model = SimpleNamespace(
        internal_engineering_model_id="IEM-000001",
        elements=(),
        relationships=(),
    )
    write_service = SimpleNamespace(project_root=".")

    result = module.render_model_refinement_review(
        FakeStreamlit(),
        project_id="000116",
        base_model=base_model,
        write_service=write_service,
        technical=False,
    )

    assert result is successor


def test_final_model_generation_wrapper_stops_when_refinement_has_no_successor():
    import inspect

    from app.model_final_review_ui import _render_authority_backed_sysml

    source = inspect.getsource(_render_authority_backed_sysml)
    guard = "if model is None:\n        return"
    dereference = "model.internal_engineering_model_id"

    assert guard in source
    assert dereference in source
    assert source.index(guard) < source.index(dereference)
