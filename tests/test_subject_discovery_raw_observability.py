from __future__ import annotations

from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

import modules.engineering_subjects.discovery as discovery_module
from modules.engineering_subjects.discovery import EngineeringSubjectDiscoveryAgent
from modules.engineering_subjects.errors import EngineeringSubjectValidationError
from modules.project_ingestion.service import (
    _write_subject_discovery_raw_response,
)


class _Client:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.result


def test_raw_response_is_observed_before_validation_failure(monkeypatch):
    result = SimpleNamespace(
        text='{"subjects":"invalid"}',
        provider="openai",
        model="gpt-test",
        response_id="resp-discovery-invalid",
    )
    client = _Client(result)
    observed = []

    monkeypatch.setattr(
        discovery_module,
        "build_discovery_source_spans",
        lambda source_projection, source_evidence: (),
    )
    monkeypatch.setattr(
        discovery_module,
        "build_context_preserving_source_input",
        lambda source_projection, spans: "input",
    )

    def reject(_text):
        raise EngineeringSubjectValidationError("invalid discovery output")

    monkeypatch.setattr(
        discovery_module,
        "parse_subject_discovery_output",
        reject,
    )

    agent = EngineeringSubjectDiscoveryAgent(
        client_factory=lambda provider: client,
    )

    with pytest.raises(
        EngineeringSubjectValidationError,
        match="invalid discovery output",
    ):
        agent.discover(
            source_projection=SimpleNamespace(),
            source_evidence=(),
            provider="openai",
            model="gpt-test",
            raw_response_observer=(
                lambda response_kind, response: observed.append(
                    (response_kind, response)
                )
            ),
        )

    assert observed == [("initial", result)]
    assert len(client.requests) == 1


def test_project_observer_persists_non_authoritative_raw_response(tmp_path):
    output_text = '{"subjects":[]}'
    result = SimpleNamespace(
        text=output_text,
        provider="openai",
        model="gpt-test",
        response_id="resp-discovery-1",
    )

    _write_subject_discovery_raw_response(
        output_root=tmp_path,
        response_kind="initial",
        result=result,
    )

    path = tmp_path / "initial.json"
    assert path.is_file()

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0.0"
    assert payload["diagnostic_only"] is True
    assert payload["engineering_authority"] is False
    assert payload["response_kind"] == "initial"
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-test"
    assert payload["response_id"] == "resp-discovery-1"
    assert payload["output_text"] == output_text
    assert payload["output_sha256"] == sha256(
        output_text.encode("utf-8")
    ).hexdigest()
