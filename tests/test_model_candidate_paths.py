"""Tests for canonical Phase-H Candidate repository paths."""

from pathlib import Path

import pytest

from modules.model_candidates import (
    ModelCandidateValidationError,
    model_candidate_elements_path,
    model_candidate_relationships_path,
    model_candidate_set_manifest_path,
    model_candidate_set_path,
    model_candidate_sets_path,
    model_candidates_path,
    model_element_candidate_path,
    model_relationship_candidate_path,
)


ROOT = Path("data/projects")


def test_candidate_paths_are_nested_under_explicit_project_and_set():
    assert model_candidates_path(ROOT, "000042") == Path(
        "data/projects/000042/model_candidates"
    )
    assert model_candidate_sets_path(ROOT, "000042") == Path(
        "data/projects/000042/model_candidates/sets"
    )
    assert model_candidate_set_path(
        ROOT,
        "000042",
        "MCS-000001",
    ) == Path(
        "data/projects/000042/model_candidates/sets/MCS-000001"
    )
    assert model_candidate_set_manifest_path(
        ROOT,
        "000042",
        "MCS-000001",
    ).name == "manifest.json"
    assert model_candidate_elements_path(
        ROOT,
        "000042",
        "MCS-000001",
    ).name == "elements"
    assert model_candidate_relationships_path(
        ROOT,
        "000042",
        "MCS-000001",
    ).name == "relationships"
    assert model_element_candidate_path(
        ROOT,
        "000042",
        "MCS-000001",
        "MCE-000001",
    ).name == "MCE-000001.json"
    assert model_relationship_candidate_path(
        ROOT,
        "000042",
        "MCS-000001",
        "MCR-000001",
    ).name == "MCR-000001.json"


@pytest.mark.parametrize(
    "call",
    [
        lambda: model_candidates_path(ROOT, "../bad"),
        lambda: model_candidate_set_path(
            ROOT,
            "000042",
            "MCS-000000",
        ),
        lambda: model_element_candidate_path(
            ROOT,
            "000042",
            "MCS-000001",
            "MCE-000000",
        ),
        lambda: model_relationship_candidate_path(
            ROOT,
            "000042",
            "MCS-000001",
            "MCR-000000",
        ),
    ],
)
def test_candidate_paths_reject_invalid_identifiers(call):
    with pytest.raises(ModelCandidateValidationError):
        call()
