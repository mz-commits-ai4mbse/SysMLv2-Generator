import json

from modules.target_model_formulation.evidence import (
    assess_local_references,
)


def test_local_reference_assessment_separates_stakeholder_and_trace_evidence(
    tmp_path,
):
    release = tmp_path / "release"
    release.mkdir()
    sysml = release / "SysML.sysml"
    sysml.write_text(
        """
metadata def StakeholderMembership {
    derived item ownedStakeholderParameter : PartUsage[1..1];
}
""",
        encoding="utf-8",
    )

    notation = tmp_path / "notation.json"
    notation.write_text(
        json.dumps(
            {
                "constructs": [
                    {
                        "construct_id": "TN_003",
                        "name": "Part definition",
                        "usage_rules": [
                            "logical or physical components"
                        ],
                    },
                    {
                        "construct_id": "TN_004",
                        "name": "Part usage",
                        "usage_rules": [
                            "logical or physical IEM components"
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = assess_local_references(
        sysml_release_root=release,
        target_notation_path=notation,
    )

    assert result.stakeholder_part_usage_found is True
    assert result.stakeholder_evidence_locator == "SysML.sysml:3"
    assert result.trace_syntax_match_count == 0
    assert result.tn003_allows_stakeholder is False
    assert result.tn004_allows_stakeholder is False
    assert len(result.sysml_release_fingerprint) == 64
    assert len(result.target_notation_fingerprint) == 64


def test_local_reference_assessment_recognizes_validated_stakeholder_fixture(
    tmp_path,
):
    release = tmp_path / "release"
    release.mkdir()
    (release / "SysML.sysml").write_text(
        """
metadata def StakeholderMembership {
    derived item ownedStakeholderParameter : PartUsage[1..1];
}
""",
        encoding="utf-8",
    )

    notation = tmp_path / "notation.json"
    notation.write_text(
        json.dumps(
            {
                "constructs": [
                    {
                        "construct_id": "TN_003",
                        "name": "Part definition",
                        "usage_rules": [
                            (
                                "Use part definitions for Human-reviewed standalone "
                                "reusable stakeholder-role types."
                            )
                        ],
                        "syntax_evidence": {
                            "fixture_id": "SFX-C6C3-001",
                            "fixture_path": (
                                "context/sysml/fixtures/c6c3/"
                                "stakeholder_role_part_definition.sysml"
                            ),
                            "validation_status": (
                                "passed_with_nonblocking_warning"
                            ),
                        },
                    },
                    {
                        "construct_id": "TN_004",
                        "name": "Part usage",
                        "usage_rules": [
                            "logical or physical IEM components"
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = assess_local_references(
        sysml_release_root=release,
        target_notation_path=notation,
    )

    assert result.tn003_allows_stakeholder is True
    assert result.stakeholder_fixture_validated is True
    assert result.stakeholder_fixture_id == "SFX-C6C3-001"
    assert result.stakeholder_fixture_locator.endswith(
        "stakeholder_role_part_definition.sysml"
    )
    assert (
        result.stakeholder_fixture_status
        == "passed_with_nonblocking_warning"
    )
