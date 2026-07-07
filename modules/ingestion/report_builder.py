"""Build the human-readable ingestion report for the first MVP workflow."""

from __future__ import annotations

from core.run_context import RunContext
from modules.extraction.basic_markdown_extractor import ExtractionResult
from modules.mapping.derivation_assessor import DerivationAssessment


def build_ingestion_report(
    run_context: RunContext,
    input_artifact: dict,
    raw_text: str,
    extraction: ExtractionResult,
    detected_evidence_types: list[str],
    derivation_assessments: list[DerivationAssessment],
) -> str:
    report_id = f"IR_{run_context.task_id}"
    source_path = input_artifact.get("path", "UNKNOWN_SOURCE")
    artifact_id = input_artifact.get("artifact_id", "UNKNOWN_ARTIFACT")

    lines: list[str] = []
    lines.append("# Ingestion Report")
    lines.append("")
    lines.append("## Report Metadata")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Report ID | {report_id} |")
    lines.append(f"| Task ID | {run_context.task_id} |")
    lines.append(f"| Recipe ID | {run_context.recipe_id} |")
    lines.append(f"| Input Artifact ID | {artifact_id} |")
    lines.append(f"| Source Path | {source_path} |")
    lines.append(f"| Generated At | {run_context.generated_at} |")
    lines.append("| Review Status | ready_for_review |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(
        "This ingestion report was generated from a raw, unreviewed input artifact. "
        "It separates directly extracted source information from interpreted candidate information "
        "and prepares the content for human review."
    )
    lines.append("")
    lines.append(
        "The deterministic MVP extractor identified evidence that may support limited downstream model derivation. "
        "No approval, approved input promotion or SysML v2 generation has been performed."
    )
    lines.append("")

    lines.append("## 2. Source Artifacts Reviewed")
    lines.append("")
    lines.append("| Artifact ID | Path | Type | Description | Source State |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| {artifact_id} | {source_path} | {input_artifact.get('artifact_type', 'unknown')} | "
        f"{input_artifact.get('description', '')} | {input_artifact.get('source_state', 'raw_unreviewed')} |"
    )
    lines.append("")

    lines.append("## 3. Extracted Source Information")
    lines.append("")
    lines.append("| Source Info ID | Extracted Information | Source Reference | Notes |")
    lines.append("|---|---|---|---|")
    for item in extraction.source_information:
        lines.append(
            f"| {item.source_info_id} | {escape_table(item.extracted_information)} | "
            f"{escape_table(item.source_reference)} | {escape_table(item.notes)} |"
        )
    lines.append("")

    lines.append("## 4. Interpreted Engineering Information")
    lines.append("")
    lines.append("| Interpreted Info ID | Candidate Meaning | Based On Source Info | Confidence | Notes |")
    lines.append("|---|---|---|---|---|")
    if extraction.candidate_elements:
        for idx, item in enumerate(extraction.candidate_elements, start=1):
            lines.append(
                f"| INT_INFO_{idx:03d} | {escape_table(item.description)} | {item.source_basis} | "
                f"{item.confidence} | Deterministic preliminary interpretation. Human review required. |"
            )
    else:
        lines.append("| INT_INFO_001 | No candidate engineering information detected. | N/A | low | Human review required. |")
    lines.append("")

    lines.append("## 5. Candidate Downstream Elements")
    lines.append("")
    lines.append("| Candidate ID | Candidate Type | Name | Description | Source Basis | Confidence |")
    lines.append("|---|---|---|---|---|---|")
    for item in extraction.candidate_elements:
        lines.append(
            f"| {item.candidate_id} | {item.candidate_type} | {escape_table(item.name)} | "
            f"{escape_table(item.description)} | {item.source_basis} | {item.confidence} |"
        )
    if not extraction.candidate_elements:
        lines.append("| CAND_001 | none | None | No candidate elements detected. | N/A | low |")
    lines.append("")
    lines.append("This section prepares review only. It does not create approved model data.")
    lines.append("")

    lines.append("## 5a. Downstream Model Derivation Assessment")
    lines.append("")
    lines.append("Detected evidence types:")
    lines.append("")
    if detected_evidence_types:
        for evidence_type in detected_evidence_types:
            lines.append(f"- `{evidence_type}`")
    else:
        lines.append("- No evidence types detected")
    lines.append("")
    lines.append("| Model Artifact Type | Support Level | Evidence Basis | Reason | Missing Information | Recommended Action |")
    lines.append("|---|---|---|---|---|---|")
    for assessment in derivation_assessments:
        lines.append(
            f"| {assessment.model_artifact_type} | {assessment.support_level} | "
            f"{escape_table(assessment.evidence_basis)} | {escape_table(assessment.reason)} | "
            f"{escape_table(assessment.missing_information)} | {escape_table(assessment.recommended_action)} |"
        )
    lines.append("")

    lines.append("## 6. Assumptions")
    lines.append("")
    lines.append("| Assumption ID | Assumption | Reason | Impact | Requires Human Confirmation |")
    lines.append("|---|---|---|---|---|")
    for item in extraction.assumptions:
        lines.append(
            f"| {item['assumption_id']} | {escape_table(item['assumption'])} | {escape_table(item['reason'])} | "
            f"{escape_table(item['impact'])} | {item['requires_human_confirmation']} |"
        )
    lines.append("")

    lines.append("## 7. Missing Information")
    lines.append("")
    lines.append("| Gap ID | Missing Information | Why It Matters | Suggested Human Action |")
    lines.append("|---|---|---|---|")
    if extraction.gaps:
        for item in extraction.gaps:
            lines.append(
                f"| {item['gap_id']} | {escape_table(item['missing_information'])} | "
                f"{escape_table(item['why_it_matters'])} | {escape_table(item['suggested_human_action'])} |"
            )
    else:
        lines.append("| GAP_001 | No explicit gaps detected by deterministic extractor. | Human review still required. | Check input completeness manually. |")
    lines.append("")

    lines.append("## 8. Ambiguities and Risks")
    lines.append("")
    lines.append("| Risk ID | Topic | Description | Potential Impact | Suggested Review Action |")
    lines.append("|---|---|---|---|---|")
    for item in extraction.risks:
        lines.append(
            f"| {item['risk_id']} | {escape_table(item['topic'])} | {escape_table(item['description'])} | "
            f"{escape_table(item['potential_impact'])} | {escape_table(item['suggested_review_action'])} |"
        )
    lines.append("")

    lines.append("## 9. Review Questions")
    lines.append("")
    lines.append("| Question ID | Question | Related Artifact or Candidate | Reason |")
    lines.append("|---|---|---|---|")
    for item in extraction.review_questions:
        lines.append(
            f"| {item['question_id']} | {escape_table(item['question'])} | "
            f"{escape_table(item['related_artifact_or_candidate'])} | {escape_table(item['reason'])} |"
        )
    lines.append("")

    lines.append("## 10. Recommended Review Decision")
    lines.append("")
    lines.append("Recommendation: `incomplete_but_reviewable`")
    lines.append("")
    lines.append("This recommendation is not an approval decision. Approval and rejection are human decisions.")
    lines.append("")

    lines.append("## 11. Traceability Notes")
    lines.append("")
    lines.append(f"- Task ID: `{run_context.task_id}`")
    lines.append(f"- Recipe ID: `{run_context.recipe_id}`")
    lines.append(f"- Input Artifact ID: `{artifact_id}`")
    lines.append(f"- Source Path: `{source_path}`")
    lines.append("- Required context files used:")
    for path in run_context.required_context.keys():
        lines.append(f"  - `{path}`")
    lines.append("- Agent personalities loaded:")
    for path in run_context.agent_personalities.keys():
        lines.append(f"  - `{path}`")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Review Gate Rule")
    lines.append("")
    lines.append("This recipe stops before the ingestion review gate.")
    lines.append("")
    lines.append("Only after human approval may content be promoted into `data/approved_input/`.")

    return "\n".join(lines) + "\n"


def escape_table(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()
