"""BLK-002 MVP-B2B2 Project-Fit workflow switch tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import modules.model_candidates.derivation_workflow as module
from modules.model_candidates.derivation_workflow import (
    ModelDerivationWorkflowService,
)
from modules.model_candidates.errors import (
    ModelCandidateGenerationBlockedError,
)


class ApprovedInputs:
    def __init__(self, values):
        self.values = values

    def list_active_approved_inputs(self, project_id):
        return self.values


class Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(
            framework_template=object(),
        )


class Candidates:
    def load_candidate_set(self, project_id, candidate_set_id):
        raise AssertionError(
            "No predecessor should be loaded in this focused test."
        )


class FitRepository:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def list_project_fit(self, project_id):
        self.calls.append(project_id)
        return self.values


class BombFitRepository:
    def list_project_fit(self, project_id):
        raise AssertionError(
            "Legacy Project Authority path must not read Project Fit."
        )


def inputs():
    return (
        SimpleNamespace(
            approved_input_id="AIN-000001",
            source_id="SRC-000001",
        ),
        SimpleNamespace(
            approved_input_id="AIN-000002",
            source_id="SRC-000002",
        ),
    )


@pytest.fixture
def lightweight_derivation(monkeypatch):
    profile = object()
    rules = object()

    monkeypatch.setattr(
        module,
        "load_model_structure_profile",
        lambda: profile,
    )
    monkeypatch.setattr(
        module,
        "load_model_derivation_rules_reference",
        lambda: rules,
    )
    monkeypatch.setattr(
        module,
        "model_structure_profile_reference",
        lambda value: object(),
    )
    monkeypatch.setattr(
        module,
        "ProfileDrivenModelCandidateDeriver",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        module,
        "ApprovedEngineeringInformationDeriver",
        lambda **kwargs: object(),
    )

    return profile, rules


def service(*, fit_repository):
    value = object.__new__(ModelDerivationWorkflowService)
    value._workspace = Workspace()
    value._approved_inputs = ApprovedInputs(inputs())
    value._candidates = Candidates()
    value._project_fit_repository = fit_repository
    value._approved_engineering_information_sets_for_inputs = (
        lambda project_id, approved_inputs: (
            SimpleNamespace(content_fingerprint="a" * 64),
            SimpleNamespace(content_fingerprint="b" * 64),
        )
    )
    return value


def test_multi_source_defaults_to_project_fit_handoff(
    monkeypatch,
    lightweight_derivation,
):
    fits = (object(), object())
    repository = FitRepository(fits)
    workflow = service(fit_repository=repository)

    fit_handoff = object()
    captured = {}

    def create_fit(**kwargs):
        captured.update(kwargs)
        return fit_handoff

    monkeypatch.setattr(
        module,
        "create_project_fit_phase_h_handoff",
        create_fit,
    )
    monkeypatch.setattr(
        module,
        "select_project_fit_active_inputs",
        lambda values, handoff: values,
    )

    request, _deriver, predecessor = workflow._assessment_request(
        "308131",
        predecessor_candidate_set_id=None,
    )

    assert predecessor is None
    assert repository.calls == ["308131"]
    assert captured["project_fit_assessments"] == fits
    assert captured["approved_input_manifests"] == inputs()
    assert len(
        captured["approved_engineering_information_sets"]
    ) == 2

    assert request.project_fit_handoff is fit_handoff
    assert request.project_authority_handoff is None
    assert request.approved_engineering_information is None


def test_explicit_legacy_authority_path_remains_available(
    monkeypatch,
    lightweight_derivation,
):
    workflow = service(
        fit_repository=BombFitRepository(),
    )

    authority = object()
    impact = object()
    legacy_handoff = object()

    monkeypatch.setattr(
        module,
        "create_project_authority_phase_h_handoff",
        lambda **kwargs: legacy_handoff,
    )
    monkeypatch.setattr(
        module,
        "select_project_authority_active_inputs",
        lambda values, handoff: values,
    )

    request, _deriver, _predecessor = workflow._assessment_request(
        "308131",
        predecessor_candidate_set_id=None,
        project_engineering_authority=authority,
        model_impact_reconciliation=impact,
    )

    assert request.project_authority_handoff is legacy_handoff
    assert request.project_fit_handoff is None
    assert request.approved_engineering_information is None


def test_partial_legacy_authority_fails_closed(
    lightweight_derivation,
):
    workflow = service(
        fit_repository=BombFitRepository(),
    )

    with pytest.raises(
        ModelCandidateGenerationBlockedError,
        match="requires both Project Engineering Authority",
    ):
        workflow._assessment_request(
            "308131",
            predecessor_candidate_set_id=None,
            project_engineering_authority=object(),
            model_impact_reconciliation=None,
        )


def test_missing_or_non_admitted_project_fit_fails_closed(
    monkeypatch,
    lightweight_derivation,
):
    workflow = service(
        fit_repository=FitRepository((object(),)),
    )

    def fail(**kwargs):
        raise RuntimeError("no exact admitted fit")

    monkeypatch.setattr(
        module,
        "create_project_fit_phase_h_handoff",
        fail,
    )

    with pytest.raises(
        ModelCandidateGenerationBlockedError,
        match="exact admitted Project Fit evidence",
    ):
        workflow._assessment_request(
            "308131",
            predecessor_candidate_set_id=None,
        )
