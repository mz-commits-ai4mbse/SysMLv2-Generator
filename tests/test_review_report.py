from modules.ingestion.review_report import (
    build_candidate_comparison_section,
    collect_ambiguities_and_risks,
    collect_missing_information,
    collect_review_questions,
    markdown_row,
    repository_relative_path,
    review_required_group_count,
)


def agent_payload(agent_id: str, output: dict) -> dict:
    return {
        "agent_id": agent_id,
        "persona_id": f"PERSONA_{agent_id}",
        "output": output,
    }


def test_consolidates_derivation_and_completeness_gaps() -> None:
    derivation_payload = agent_payload(
        "DERIVATION_AGENT",
        {
            "missing_information_for_model_building": [
                {
                    "missing_info_id": "MISS_001",
                    "missing_information": (
                        "Explicit validation criteria, test cases, "
                        "and acceptance thresholds"
                    ),
                    "limits_or_blocks": ["validation_model"],
                    "needed_for": ["verification_model"],
                    "review_question": (
                        "What observable criteria should be used "
                        "to verify control exclusivity?"
                    ),
                }
            ]
        },
    )
    completeness_payload = agent_payload(
        "COMPLETENESS_AGENT",
        {
            "gaps": [
                {
                    "gap_id": "GAP_001",
                    "missing_information": (
                        "Explicit validation criteria, acceptance thresholds, "
                        "test cases, and verification activities for the "
                        "stated requirements."
                    ),
                    "why_it_matters": (
                        "Verification content would otherwise be speculative."
                    ),
                    "suggested_human_action": (
                        "Confirm measurable acceptance criteria."
                    ),
                }
            ]
        },
    )

    result = collect_missing_information(
        derivation_payloads=[derivation_payload],
        completeness_payloads=[completeness_payload],
    )

    assert len(result) == 1
    assert result[0]["report_gap_id"] == "GAP-001"
    assert result[0]["source_ids"] == ["MISS_001", "GAP_001"]
    assert result[0]["reported_by"] == [
        "DERIVATION_AGENT",
        "COMPLETENESS_AGENT",
    ]
    assert len(result[0]["review_questions"]) == 1
    assert len(result[0]["suggested_actions"]) == 1


def test_does_not_repeat_questions_already_covered_by_gap_actions() -> None:
    gaps = [
        {
            "missing_information": (
                "Formal use case boundaries, preconditions, alternate flows, "
                "and postconditions"
            ),
            "alternative_descriptions": [],
            "review_questions": [
                "What are the formal use case definitions for starting "
                "and joining a session?"
            ],
            "suggested_actions": [],
        }
    ]
    completeness_payload = agent_payload(
        "COMPLETENESS_AGENT",
        {
            "review_questions": [
                {
                    "question_id": "RQ_001",
                    "question": (
                        "What are the preconditions, alternate flows, and "
                        "postconditions for starting and joining a session?"
                    ),
                    "related_artifact_or_candidate": "use-case candidates",
                    "reason": "Use case structure is incomplete.",
                },
                {
                    "question_id": "RQ_002",
                    "question": (
                        "Are the client and software application "
                        "distinct components?"
                    ),
                    "related_artifact_or_candidate": "application candidates",
                    "reason": "Architecture interpretation depends on this.",
                },
            ]
        },
    )

    result = collect_review_questions(
        derivation_payloads=[],
        completeness_payloads=[completeness_payload],
        missing_information=gaps,
    )

    assert [item["question"] for item in result] == [
        "Are the client and software application distinct components?"
    ]


def test_keeps_ambiguities_and_risks_separate_from_gaps() -> None:
    completeness_payload = agent_payload(
        "COMPLETENESS_AGENT",
        {
            "ambiguities_and_risks": [
                {
                    "risk_id": "RISK_001",
                    "topic": "Software application vs client application",
                    "description": "The source does not state whether they are separate.",
                    "potential_impact": "Could cause an incorrect decomposition.",
                    "suggested_review_action": "Confirm their responsibilities.",
                }
            ]
        },
    )

    result = collect_ambiguities_and_risks(
        completeness_payloads=[completeness_payload]
    )

    assert len(result) == 1
    assert result[0]["report_risk_id"] == "RISK-001"
    assert result[0]["source_ids"] == ["RISK_001"]
    assert result[0]["source_stages"] == ["completeness_review"]


def test_links_review_questions_to_related_risks() -> None:
    derivation_payload = agent_payload(
        "DERIVATION_AGENT",
        {
            "possible_but_unsupported_interpretations": [
                {
                    "topic": "The applications may be separate components",
                    "reason_not_accepted": "The source does not define this.",
                    "review_question": (
                        "Are the software application and client application "
                        "distinct components?"
                    ),
                }
            ]
        },
    )
    risks = [
        {
            "report_risk_id": "RISK-001",
            "topic": "Software application vs client application",
            "description": (
                "The source does not state whether the applications are "
                "separate components."
            ),
            "review_actions": ["Confirm whether they are distinct."],
        }
    ]

    result = collect_review_questions(
        derivation_payloads=[derivation_payload],
        completeness_payloads=[],
        missing_information=[],
        risks=risks,
    )

    assert result[0]["related_risk_ids"] == ["RISK-001"]


def test_uses_relative_paths_and_consensus_fallback(tmp_path) -> None:
    project_root = tmp_path / "project"
    artifact_path = project_root / "data" / "report.md"

    assert repository_relative_path(
        artifact_path,
        project_root,
    ) == "data/report.md"

    report = {
        "summary": {"total_groups": 2},
        "groups": [
            {"review_required": True},
            {"review_required": False},
        ],
    }

    assert review_required_group_count(report) == 1

def test_markdown_row_preserves_zero_values() -> None:
    assert markdown_row(["TEAM_EXAMPLE", 19, 0]) == (
        "| TEAM_EXAMPLE | 19 | 0 |"
    )

def test_single_agent_run_is_not_described_as_consensus() -> None:
    candidates = {
        "system::example": {
            "candidate_ids": ["ELEM_001"],
            "element_type": "system",
            "candidate_name": "Example System",
            "agent_results": {
                "AGENT_1": {
                    "confidence": "high",
                    "generation_readiness": "ready",
                    "description": "Example description",
                }
            },
        }
    }

    report_text = "\n".join(
        build_candidate_comparison_section(
            candidates=candidates,
            agent_ids=["AGENT_1"],
        )
    )

    assert "Single-agent observation" in report_text
    assert "All agents identified candidate" not in report_text
    assert "ELEM_001" in report_text
