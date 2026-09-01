"""Focused BLK-002 MVP-B2A Phase-H core tests."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import modules.model_candidates.generation as generation_module
import modules.model_candidates.project_fit_handoff as fit_module
from modules.model_candidates.errors import (
    ModelCandidateGenerationBlockedError,
)
from modules.model_candidates.generation import (
    ModelCandidateGenerationService,
)
from modules.model_candidates.project_authority_handoff import (
    phase_h_subject_key,
    phase_h_subject_key_for_source,
)


@dataclass(frozen=True)
class Input:
    approved_input_id: str
    source_id: str
    stable_subject_key: str
    content_fingerprint: str


@dataclass(frozen=True)
class Binding:
    source_id: str
    approved_input_ids: tuple[str, ...]
    approved_input_fingerprints: tuple[str, ...]


def request():
    first = Input(
        approved_input_id="AIN-000001",
        source_id="SRC-000001",
        stable_subject_key="remote.client",
        content_fingerprint="1" * 64,
    )
    second = Input(
        approved_input_id="AIN-000002",
        source_id="SRC-000002",
        stable_subject_key="remote.client",
        content_fingerprint="2" * 64,
    )
    handoff = SimpleNamespace(
        source_bindings=(
            Binding(
                source_id="SRC-000001",
                approved_input_ids=("AIN-000001",),
                approved_input_fingerprints=("1" * 64,),
            ),
            Binding(
                source_id="SRC-000002",
                approved_input_ids=("AIN-000002",),
                approved_input_fingerprints=("2" * 64,),
            ),
        ),
    )
    value = SimpleNamespace(
        project_id="308131",
        approved_inputs=(first, second),
        approved_engineering_information=None,
        project_authority_handoff=None,
        project_fit_handoff=handoff,
    )
    return value, first, second


def test_project_fit_subject_identity_is_source_scoped(monkeypatch):
    value, first, second = request()

    monkeypatch.setattr(
        fit_module,
        "validate_project_fit_phase_h_request",
        lambda request: None,
    )

    assert phase_h_subject_key(value, first) == (
        "project_subject:src-000001:remote.client"
    )
    assert phase_h_subject_key(value, second) == (
        "project_subject:src-000002:remote.client"
    )


def test_project_fit_relationship_endpoint_resolution_is_source_scoped(
    monkeypatch,
):
    value, _first, _second = request()

    monkeypatch.setattr(
        fit_module,
        "validate_project_fit_phase_h_request",
        lambda request: None,
    )

    assert phase_h_subject_key_for_source(
        value,
        source_id="SRC-000001",
        stable_subject_key="remote.client",
    ) == "project_subject:src-000001:remote.client"

    assert phase_h_subject_key_for_source(
        value,
        source_id="SRC-000002",
        stable_subject_key="remote.client",
    ) == "project_subject:src-000002:remote.client"


def test_project_fit_subject_resolution_fails_on_stale_input(
    monkeypatch,
):
    value, first, _second = request()

    monkeypatch.setattr(
        fit_module,
        "validate_project_fit_phase_h_request",
        lambda request: None,
    )

    stale = Input(
        approved_input_id=first.approved_input_id,
        source_id=first.source_id,
        stable_subject_key=first.stable_subject_key,
        content_fingerprint="9" * 64,
    )

    with pytest.raises(
        fit_module.ProjectFitPhaseHHandoffError,
        match="binding is stale",
    ):
        phase_h_subject_key(value, stale)


class _ApprovedInputs:
    def __init__(self, values):
        self.values = values

    def list_active_approved_inputs(self, project_id):
        return self.values


class _Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(
            framework_template=object(),
        )


class _StopAfterRequest(Exception):
    pass


def test_generation_accepts_project_fit_handoff_and_forwards_request(
    monkeypatch,
):
    inputs = (
        SimpleNamespace(
            source_id="SRC-000001",
        ),
        SimpleNamespace(
            source_id="SRC-000002",
        ),
    )
    fit_handoff = object()
    captured = {}

    service = object.__new__(ModelCandidateGenerationService)
    service._workspace = _Workspace()
    service._approved_inputs = _ApprovedInputs(inputs)

    monkeypatch.setattr(
        ModelCandidateGenerationService,
        "_validate_active_snapshot",
        lambda self, project_id, values: values,
    )
    monkeypatch.setattr(
        ModelCandidateGenerationService,
        "_load_predecessor",
        lambda self, project_id, predecessor_id, reason: None,
    )

    def stop(self, deriver, request):
        captured["request"] = request
        raise _StopAfterRequest()

    monkeypatch.setattr(
        ModelCandidateGenerationService,
        "_derive",
        stop,
    )
    monkeypatch.setattr(
        generation_module,
        "select_project_fit_active_inputs",
        lambda values, handoff: values,
    )
    monkeypatch.setattr(
        generation_module,
        "validate_project_fit_phase_h_request",
        lambda request: None,
    )
    monkeypatch.setattr(
        generation_module,
        "validate_project_authority_phase_h_request",
        lambda request: None,
    )

    with pytest.raises(_StopAfterRequest):
        service.generate_candidate_set(
            "308131",
            deriver=object(),
            model_structure_profile_reference=object(),
            derivation_rules_reference=object(),
            project_fit_handoff=fit_handoff,
        )

    assert captured["request"].project_fit_handoff is fit_handoff
    assert captured["request"].project_authority_handoff is None


def test_generation_still_blocks_multi_source_without_any_handoff(
    monkeypatch,
):
    inputs = (
        SimpleNamespace(source_id="SRC-000001"),
        SimpleNamespace(source_id="SRC-000002"),
    )

    service = object.__new__(ModelCandidateGenerationService)
    service._workspace = _Workspace()
    service._approved_inputs = _ApprovedInputs(inputs)

    monkeypatch.setattr(
        ModelCandidateGenerationService,
        "_validate_active_snapshot",
        lambda self, project_id, values: values,
    )

    with pytest.raises(
        ModelCandidateGenerationBlockedError,
        match="Project Fit or Project Engineering Authority",
    ):
        service.generate_candidate_set(
            "308131",
            deriver=object(),
            model_structure_profile_reference=object(),
            derivation_rules_reference=object(),
        )


def test_generation_rejects_both_handoffs(monkeypatch):
    inputs = (
        SimpleNamespace(source_id="SRC-000001"),
        SimpleNamespace(source_id="SRC-000002"),
    )

    service = object.__new__(ModelCandidateGenerationService)
    service._workspace = _Workspace()
    service._approved_inputs = _ApprovedInputs(inputs)

    monkeypatch.setattr(
        ModelCandidateGenerationService,
        "_validate_active_snapshot",
        lambda self, project_id, values: values,
    )

    with pytest.raises(
        ModelCandidateGenerationBlockedError,
        match="mutually exclusive",
    ):
        service.generate_candidate_set(
            "308131",
            deriver=object(),
            model_structure_profile_reference=object(),
            derivation_rules_reference=object(),
            project_authority_handoff=object(),
            project_fit_handoff=object(),
        )
