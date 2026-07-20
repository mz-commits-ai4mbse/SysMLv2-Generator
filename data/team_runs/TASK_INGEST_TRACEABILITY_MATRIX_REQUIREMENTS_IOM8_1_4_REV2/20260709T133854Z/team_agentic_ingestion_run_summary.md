# Team Agentic Ingestion Run Summary

## Run Metadata

- Task ID: `TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2`
- Recipe ID: `REC_INGESTION_001`
- Run ID: `20260709T133854Z`
- Run Directory: `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2/20260709T133854Z`
- Raw Input Path: `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/legacy/raw/user_uploads/Traceability_Matrix_Requirements_iOM8_1_4_Rev2.CSV`
- Report Output Path: `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/ingestion_reports/task_ingest_traceability_matrix_requirements_iom8_1_4_rev2_team_agentic_ingestion_report.md`
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Team Execution Mode: `llm_single_member_per_team`
- Created At: `2026-07-09T13:40:33.221826+00:00`

## Agent Results

| Agent ID | Task | Run | Provider | Model | Status | Output Artifact |
|---|---|---:|---|---|---|---|
| AGENT_LEGACY_LITERAL_INTERPRETER | Interpret raw legacy data | 1 | openai | gpt-5.4-mini | completed | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2/20260709T133854Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json` |
| AGENT_EVIDENCE_STRICT_CLASSIFIER | Classify engineering evidence | 1 | openai | gpt-5.4-mini | completed | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2/20260709T133854Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json` |
| AGENT_DERIVATION_RULES_FOCUSED_ASSESSOR | Assess downstream model derivation support | 1 | openai | gpt-5.4-mini | completed | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2/20260709T133854Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json` |
| AGENT_COMPLETENESS_GAP_FINDER | Check completeness, gaps, risks and review readiness | 1 | openai | gpt-5.4-mini | completed | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2/20260709T133854Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json` |
| AGENT_REPORT_STRUCTURED_COMPOSER | Compose structured ingestion report | 1 | openai | gpt-5.4-mini | completed | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_INGEST_TRACEABILITY_MATRIX_REQUIREMENTS_IOM8_1_4_REV2/20260709T133854Z/agent_outputs/05_report_composition/team_report_composition/agent_report_structured_composer/agent_report_structured_composer_run_01.json` |

## Consensus Reports

| Team ID | Task | Total Agents | Review Required | Full Agreement | Majority Agreement | Disagreement |
|---|---|---:|---:|---:|---:|---:|
| TEAM_LEGACY_INTERPRETATION | Interpret raw legacy data | 1 | 0 | 20 | 0 | 0 |
| TEAM_EVIDENCE_CLASSIFICATION | Classify engineering evidence | 1 | 0 | 44 | 0 | 0 |
| TEAM_DERIVATION_ASSESSMENT | Assess downstream model derivation support | 1 | 0 | 11 | 0 | 0 |
| TEAM_COMPLETENESS_REVIEW | Check completeness, gaps, risks and review readiness | 1 | 0 | 7 | 0 | 0 |