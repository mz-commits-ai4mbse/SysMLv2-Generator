"""Synthetic consensus test.

This test does not call an LLM.

It creates structured fake agent outputs in memory and checks whether the
consensus analyzer detects agreement, majority disagreement and minority
interpretations correctly.

Usage:
python scripts/test_consensus_synthetic.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.consensus.analyzer import (
    analyze_consensus,
    write_consensus_json,
    write_consensus_markdown,
)


def make_payload(agent_id: str, output: dict) -> dict:
    return {
        "agent_id": agent_id,
        "persona_id": agent_id.replace("AGENT_", "PERSONA_"),
        "output_text": json.dumps(output, indent=2),
        "_artifact_path": f"synthetic/{agent_id}.json",
    }


def main() -> None:
    payloads = [
        make_payload(
            "AGENT_A",
            {
                "model_artifact_assessments": [
                    {
                        "model_artifact_type": "functional_model",
                        "support_level": "supported",
                        "evidence_basis": ["EV_FUNCTION_OR_CAPABILITY"],
                        "reason": "Functions are clearly described.",
                        "missing_information": [],
                        "recommended_action": "Generate preliminary functional model."
                    },
                    {
                        "model_artifact_type": "validation_or_verification_model",
                        "support_level": "not_supported",
                        "evidence_basis": [],
                        "reason": "No validation criteria are available.",
                        "missing_information": ["validation criteria"],
                        "recommended_action": "Do not generate validation model."
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "GAP_001",
                        "missing_information": "validation criteria",
                        "why_it_matters": "Required for validation model generation.",
                        "suggested_human_action": "Provide acceptance or validation criteria."
                    }
                ],
                "recommended_review_decision": "incomplete_but_reviewable"
            },
        ),
        make_payload(
            "AGENT_B",
            {
                "model_artifact_assessments": [
                    {
                        "model_artifact_type": "functional_model",
                        "support_level": "supported",
                        "evidence_basis": ["EV_FUNCTION_OR_CAPABILITY"],
                        "reason": "Capabilities are present.",
                        "missing_information": [],
                        "recommended_action": "Generate preliminary functional model."
                    },
                    {
                        "model_artifact_type": "validation_or_verification_model",
                        "support_level": "not_supported",
                        "evidence_basis": [],
                        "reason": "No test or acceptance criteria are stated.",
                        "missing_information": ["validation criteria"],
                        "recommended_action": "Do not generate validation model."
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "GAP_001",
                        "missing_information": "validation criteria",
                        "why_it_matters": "Required for validation model generation.",
                        "suggested_human_action": "Provide validation criteria."
                    }
                ],
                "recommended_review_decision": "incomplete_but_reviewable"
            },
        ),
        make_payload(
            "AGENT_C",
            {
                "model_artifact_assessments": [
                    {
                        "model_artifact_type": "functional_model",
                        "support_level": "supported",
                        "evidence_basis": ["EV_FUNCTION_OR_CAPABILITY"],
                        "reason": "Functional behavior is sufficiently described.",
                        "missing_information": [],
                        "recommended_action": "Generate preliminary functional model."
                    },
                    {
                        "model_artifact_type": "validation_or_verification_model",
                        "support_level": "partially_supported",
                        "evidence_basis": ["EV_REQUIREMENT_STATEMENT"],
                        "reason": "Some requirements exist, but no validation criteria.",
                        "missing_information": ["explicit validation criteria"],
                        "recommended_action": "Generate only review questions."
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "GAP_002",
                        "missing_information": "explicit validation criteria",
                        "why_it_matters": "Needed for verification planning.",
                        "suggested_human_action": "Clarify verification approach."
                    }
                ],
                "recommended_review_decision": "review_required"
            },
        ),
    ]

    report = analyze_consensus(
        team_id="TEAM_SYNTHETIC_DERIVATION_ASSESSMENT",
        task_name="Synthetic derivation assessment consensus test",
        agent_payloads=payloads,
    )

    json_output_path = (
        PROJECT_ROOT
        / "data"
        / "consensus_reports"
        / "synthetic_consensus_test.json"
    )

    markdown_output_path = (
        PROJECT_ROOT
        / "data"
        / "consensus_reports"
        / "synthetic_consensus_test.md"
    )

    write_consensus_json(report, json_output_path)
    write_consensus_markdown(report, markdown_output_path)

    print("Synthetic consensus test finished.")
    print(f"JSON report: {json_output_path}")
    print(f"Markdown report: {markdown_output_path}")
    print("")
    print("Summary:")

    for key, value in report["summary"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
