from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from modules.framework import load_framework_template
from modules.project_coverage.errors import (
    CoverageAssessmentError,
    CoverageIntegrityError,
    CoverageProfileError,
    CoverageReferenceError,
    CoverageValidationError,
    ProjectCoverageError,
)
from modules.project_coverage.profile import (
    DEFAULT_PRELIMINARY_SUPPORT_PROFILE_PATH,
    PRELIMINARY_SUPPORT_PROFILE_SCHEMA_VERSION,
    calculate_preliminary_support_profile_fingerprint,
    load_preliminary_support_profile,
    parse_preliminary_support_profile,
    preliminary_support_profile_from_json,
    preliminary_support_profile_to_dict,
    preliminary_support_profile_to_json,
    support_target_by_id,
    validate_preliminary_support_profile,
    validate_preliminary_support_profile_instance,
)
from modules.project_coverage.types import (
    APPROVED_READINESS_STATUSES,
    COVERAGE_EVIDENCE_STATES,
    COVERAGE_ISSUE_LEVELS,
    FRAMEWORK_LEVEL_COVERAGE_STATES,
    FRAMEWORK_NODE_COVERAGE_STATES,
    POTENTIAL_SUPPORT_STATES,
    PROJECT_COVERAGE_STATES,
    SUPPORT_PROFILE_STATUSES,
    SUPPORT_TARGET_TYPES,
    CoverageIssue,
    FrameworkAssignmentCoverageEvidence,
    FrameworkLevelCoverage,
    FrameworkNodeCoverage,
    PotentialSupportAssessment,
    PreliminarySupportProfile,
    PreliminarySupportTarget,
    ProjectCoverageAssessment,
)


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_PATH = ROOT / "context/frameworks/turing_rflp_framework.json"
PROFILE_PATH = ROOT / "context/frameworks/turing_preliminary_support_profile.json"


def framework():
    return load_framework_template(FRAMEWORK_PATH)


def profile_dict():
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def mutate(mutator):
    data = profile_dict()
    mutator(data)
    return data


def test_error_hierarchy() -> None:
    assert issubclass(CoverageValidationError, ProjectCoverageError)
    assert issubclass(CoverageValidationError, ValueError)
    assert issubclass(CoverageProfileError, CoverageValidationError)
    assert issubclass(CoverageReferenceError, ProjectCoverageError)
    assert issubclass(CoverageIntegrityError, ProjectCoverageError)
    assert issubclass(CoverageAssessmentError, ProjectCoverageError)


def test_state_constants_are_exact() -> None:
    assert FRAMEWORK_NODE_COVERAGE_STATES == {
        "uncovered", "candidate_covered", "reviewed_candidate_covered"
    }
    assert FRAMEWORK_LEVEL_COVERAGE_STATES == {
        "uncovered", "partially_covered", "covered"
    }
    assert PROJECT_COVERAGE_STATES == {
        "uncovered", "partially_covered", "covered", "attention_required"
    }
    assert POTENTIAL_SUPPORT_STATES == {
        "not_supported", "partially_supported", "potentially_supported", "attention_required"
    }
    assert COVERAGE_ISSUE_LEVELS == {"warning", "blocking"}
    assert APPROVED_READINESS_STATUSES == {"not_available"}
    assert SUPPORT_TARGET_TYPES == {"model", "submodel"}
    assert SUPPORT_PROFILE_STATUSES == {"draft", "active", "retired"}
    assert "eligible_confirmed" in COVERAGE_EVIDENCE_STATES


def test_all_public_types_are_frozen() -> None:
    target = PreliminarySupportTarget(
        "SUPPORT_X", "X", "model", 1, ("FW_X",), ()
    )
    with pytest.raises(FrozenInstanceError):
        target.name = "Y"


def test_load_default_profile_from_explicit_paths() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH,
        framework_template_path=FRAMEWORK_PATH,
    )
    assert loaded.profile_id == "TURING_PRELIMINARY_SUPPORT_PROFILE"
    assert loaded.profile_version == "1.0.0"
    assert loaded.framework_template_id == "TURING_RFLP_FRAMEWORK"
    assert loaded.framework_template_version == "1.0.0"
    assert len(loaded.support_targets) == 3
    assert len(loaded.profile_fingerprint) == 64


def test_default_path_contract() -> None:
    assert DEFAULT_PRELIMINARY_SUPPORT_PROFILE_PATH == Path(
        "context/frameworks/turing_preliminary_support_profile.json"
    )
    assert PRELIMINARY_SUPPORT_PROFILE_SCHEMA_VERSION == "1.0.0"


def test_support_chain_is_conservative_and_ordered() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    stakeholder, system, subsystem = loaded.support_targets
    assert stakeholder.support_target_id == "SUPPORT_STAKEHOLDER_MODEL"
    assert stakeholder.required_support_target_ids == ()
    assert system.required_support_target_ids == (
        "SUPPORT_STAKEHOLDER_MODEL",
    )
    assert subsystem.required_support_target_ids == (
        "SUPPORT_SYSTEM_MODEL",
    )
    assert [target.order for target in loaded.support_targets] == [1, 2, 3]


def test_each_initial_target_requires_four_nodes() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    assert [len(item.required_framework_node_ids) for item in loaded.support_targets] == [4, 4, 4]


def test_profile_round_trip_is_stable() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    text = preliminary_support_profile_to_json(loaded)
    assert text.endswith("\n")
    reloaded = preliminary_support_profile_from_json(
        text, framework_template=framework()
    )
    assert reloaded == loaded


def test_profile_fingerprint_is_reproducible() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    assert calculate_preliminary_support_profile_fingerprint(loaded) == loaded.profile_fingerprint


def test_profile_fingerprint_changes_with_content() -> None:
    first = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    data = preliminary_support_profile_to_dict(first)
    data["name"] = "Changed"
    second = parse_preliminary_support_profile(data, framework_template=framework())
    assert second.profile_fingerprint != first.profile_fingerprint


def test_validate_profile_instance_accepts_exact_profile() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    assert validate_preliminary_support_profile_instance(
        loaded, framework_template=framework()
    ) is loaded


def test_validate_profile_instance_rejects_wrong_fingerprint() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    broken = replace(loaded, profile_fingerprint="0" * 64)
    with pytest.raises(CoverageProfileError, match="fingerprint"):
        validate_preliminary_support_profile_instance(
            broken, framework_template=framework()
        )


def test_support_target_lookup() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    target = support_target_by_id(loaded, "SUPPORT_SYSTEM_MODEL")
    assert target.name == "System Model"


def test_unknown_support_target_lookup_rejected() -> None:
    loaded = load_preliminary_support_profile(
        PROFILE_PATH, framework_template=framework()
    )
    with pytest.raises(CoverageProfileError, match="Unknown"):
        support_target_by_id(loaded, "SUPPORT_UNKNOWN")


@pytest.mark.parametrize("bad", [None, [], "x", 1])
def test_profile_must_be_object(bad) -> None:
    with pytest.raises(CoverageProfileError, match="JSON object"):
        validate_preliminary_support_profile(bad, framework_template=framework())


def test_invalid_json_rejected() -> None:
    with pytest.raises(CoverageProfileError, match="Invalid"):
        preliminary_support_profile_from_json("{", framework_template=framework())


def test_non_string_json_payload_rejected() -> None:
    with pytest.raises(CoverageProfileError, match="string"):
        preliminary_support_profile_from_json(None, framework_template=framework())


def test_missing_profile_file_rejected(tmp_path: Path) -> None:
    with pytest.raises(CoverageProfileError, match="Unable to read"):
        load_preliminary_support_profile(
            tmp_path / "missing.json", framework_template=framework()
        )


def test_missing_top_level_field_rejected() -> None:
    data = mutate(lambda item: item.pop("profile_id"))
    with pytest.raises(CoverageProfileError, match="missing required"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_extra_top_level_field_rejected() -> None:
    data = mutate(lambda item: item.update(extra=True))
    with pytest.raises(CoverageProfileError, match="unsupported"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_unsupported_schema_version_rejected() -> None:
    data = mutate(lambda item: item.update(schema_version="2.0.0"))
    with pytest.raises(CoverageProfileError, match="Unsupported"):
        parse_preliminary_support_profile(data, framework_template=framework())


@pytest.mark.parametrize("field", ["schema_version", "profile_version"])
def test_invalid_semantic_version_rejected(field: str) -> None:
    data = mutate(lambda item: item.update({field: "1.0"}))
    with pytest.raises(CoverageProfileError, match="semantic versioning"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_invalid_profile_id_rejected() -> None:
    data = mutate(lambda item: item.update(profile_id="bad-profile"))
    with pytest.raises(CoverageProfileError, match="profile_id"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_blank_profile_name_rejected() -> None:
    data = mutate(lambda item: item.update(name="  "))
    with pytest.raises(CoverageProfileError, match="name"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_invalid_profile_status_rejected() -> None:
    data = mutate(lambda item: item.update(status="unknown"))
    with pytest.raises(CoverageProfileError, match="status"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_template_id_mismatch_rejected() -> None:
    data = mutate(lambda item: item.update(framework_template_id="OTHER"))
    with pytest.raises(CoverageProfileError, match="framework_template_id"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_template_version_mismatch_rejected() -> None:
    data = mutate(lambda item: item.update(framework_template_version="9.9.9"))
    with pytest.raises(CoverageProfileError, match="framework_template_version"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_empty_support_targets_rejected() -> None:
    data = mutate(lambda item: item.update(support_targets=[]))
    with pytest.raises(CoverageProfileError, match="non-empty"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_support_target_must_be_object() -> None:
    data = mutate(lambda item: item["support_targets"].__setitem__(0, "x"))
    with pytest.raises(CoverageProfileError, match="must be an object"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_missing_target_field_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0].pop("name"))
    with pytest.raises(CoverageProfileError, match="missing required"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_extra_target_field_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(extra=True))
    with pytest.raises(CoverageProfileError, match="unsupported"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_invalid_target_id_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(support_target_id="bad"))
    with pytest.raises(CoverageProfileError, match="support_target_id"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_duplicate_target_id_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][1].update(
        support_target_id=item["support_targets"][0]["support_target_id"]
    ))
    with pytest.raises(CoverageProfileError, match="Duplicate support_target_id"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_invalid_target_type_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(support_target_type="package"))
    with pytest.raises(CoverageProfileError, match="support_target_type"):
        parse_preliminary_support_profile(data, framework_template=framework())


@pytest.mark.parametrize("order", [True, 0, -1, "1"])
def test_invalid_order_rejected(order) -> None:
    data = mutate(lambda item: item["support_targets"][0].update(order=order))
    with pytest.raises(CoverageProfileError, match="positive integer"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_duplicate_order_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][1].update(order=1))
    with pytest.raises(CoverageProfileError, match="Duplicate support target order"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_non_contiguous_order_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][2].update(order=4))
    with pytest.raises(CoverageProfileError, match="contiguous"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_targets_are_normalized_by_order() -> None:
    data = profile_dict()
    data["support_targets"] = list(reversed(data["support_targets"]))
    loaded = parse_preliminary_support_profile(data, framework_template=framework())
    assert [item.order for item in loaded.support_targets] == [1, 2, 3]


def test_required_nodes_must_be_list() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(required_framework_node_ids="x"))
    with pytest.raises(CoverageProfileError, match="must be a list"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_required_nodes_must_not_be_empty() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(required_framework_node_ids=[]))
    with pytest.raises(CoverageProfileError, match="must not be empty"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_duplicate_required_node_rejected() -> None:
    def change(item):
        nodes = item["support_targets"][0]["required_framework_node_ids"]
        nodes.append(nodes[0])
    data = mutate(change)
    with pytest.raises(CoverageProfileError, match="duplicate"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_unknown_framework_node_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0]["required_framework_node_ids"].append("FW_UNKNOWN"))
    with pytest.raises(CoverageProfileError, match="unknown or non-mapping"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_level_node_is_not_a_mapping_target() -> None:
    data = mutate(lambda item: item["support_targets"][0]["required_framework_node_ids"].append("FW_LEVEL_STAKEHOLDER"))
    with pytest.raises(CoverageProfileError, match="non-mapping"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_required_support_targets_must_be_list() -> None:
    data = mutate(lambda item: item["support_targets"][1].update(required_support_target_ids="x"))
    with pytest.raises(CoverageProfileError, match="must be a list"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_duplicate_support_dependency_rejected() -> None:
    def change(item):
        deps = item["support_targets"][1]["required_support_target_ids"]
        deps.append(deps[0])
    data = mutate(change)
    with pytest.raises(CoverageProfileError, match="duplicate"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_invalid_support_dependency_id_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][1].update(required_support_target_ids=["bad"]))
    with pytest.raises(CoverageProfileError, match="invalid identifiers"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_unknown_support_dependency_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][1].update(required_support_target_ids=["SUPPORT_UNKNOWN"]))
    with pytest.raises(CoverageProfileError, match="unknown support target"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_self_dependency_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(
        required_support_target_ids=["SUPPORT_STAKEHOLDER_MODEL"]
    ))
    with pytest.raises(CoverageProfileError, match="itself"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_forward_dependency_rejected() -> None:
    data = mutate(lambda item: item["support_targets"][0].update(
        required_support_target_ids=["SUPPORT_SYSTEM_MODEL"]
    ))
    with pytest.raises(CoverageProfileError, match="earlier"):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_cycle_rejected() -> None:
    data = profile_dict()
    # Preserve earlier-order validation by swapping orders so both references are illegal;
    # the contract rejects the graph before it can become a hidden cycle.
    data["support_targets"][0]["required_support_target_ids"] = ["SUPPORT_SYSTEM_MODEL"]
    data["support_targets"][1]["required_support_target_ids"] = ["SUPPORT_STAKEHOLDER_MODEL"]
    with pytest.raises(CoverageProfileError):
        parse_preliminary_support_profile(data, framework_template=framework())


def test_to_dict_rejects_wrong_type() -> None:
    with pytest.raises(CoverageProfileError, match="PreliminarySupportProfile"):
        preliminary_support_profile_to_dict(object())


def test_validate_instance_rejects_wrong_type() -> None:
    with pytest.raises(CoverageProfileError, match="PreliminarySupportProfile"):
        validate_preliminary_support_profile_instance(object(), framework_template=framework())


def test_lookup_rejects_wrong_profile_type() -> None:
    with pytest.raises(CoverageProfileError, match="PreliminarySupportProfile"):
        support_target_by_id(object(), "SUPPORT_X")


def test_lookup_rejects_non_string_id() -> None:
    loaded = load_preliminary_support_profile(PROFILE_PATH, framework_template=framework())
    with pytest.raises(CoverageProfileError, match="string"):
        support_target_by_id(loaded, None)


def test_profile_types_preserve_tuple_contracts() -> None:
    loaded = load_preliminary_support_profile(PROFILE_PATH, framework_template=framework())
    assert isinstance(loaded.support_targets, tuple)
    assert isinstance(loaded.support_targets[0].required_framework_node_ids, tuple)
    assert isinstance(loaded.support_targets[0].required_support_target_ids, tuple)