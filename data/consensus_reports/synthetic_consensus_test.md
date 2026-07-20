# Consensus and Variance Report

## Report Metadata

- Consensus Report ID: `CONSENSUS_TEAM_SYNTHETIC_DERIVATION_ASSESSMENT_20260709T114623Z`
- Team ID: `TEAM_SYNTHETIC_DERIVATION_ASSESSMENT`
- Task Name: Synthetic derivation assessment consensus test
- Created At: 2026-07-09T11:46:23.465334+00:00
- Total Agents: 3

## Summary

| Metric | Count |
|---|---:|
| total_groups | 5 |
| full_agreement | 1 |
| majority_agreement | 1 |
| majority_with_disagreement | 2 |
| minority_interpretation | 1 |
| conflict | 0 |
| review_required | 3 |

## Consensus Groups

| Agreement Level | Item Type | Representative Value | Supporting Agents | Review Required | Reason |
|---|---|---|---|---|---|
| full_agreement | model_artifact_assessment | functional_model: supported | AGENT_A, AGENT_B, AGENT_C | False | All agents produced the same comparable item. |
| majority_with_disagreement | model_artifact_assessment | validation_or_verification_model: not_supported | AGENT_A, AGENT_B | True | A majority exists, but at least one agent disagrees. |
| majority_agreement | gap | validation criteria | AGENT_A, AGENT_B | False | A majority of agents produced the same comparable item. |
| majority_with_disagreement | recommended_review_decision | incomplete_but_reviewable | AGENT_A, AGENT_B | True | A majority exists, but at least one agent disagrees. |
| minority_interpretation | gap | explicit validation criteria | AGENT_C | True | Only one agent produced this interpretation. |