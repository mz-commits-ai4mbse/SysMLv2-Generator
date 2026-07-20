# Team Agentic Ingestion Run Summary

## Run Metadata

- Task ID: `TASK_001_INGEST_EXAMPLE_MODEL`
- Recipe ID: `REC_INGESTION_001`
- Run ID: `20260709T115931Z`
- Run Directory: `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z`
- Raw Input Path: `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/legacy/raw/example_legacy_model_description.md`
- Report Output Path: `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/ingestion_reports/task_001_team_agentic_ingestion_report_dry_run.md`
- Provider: `openai`
- Model: `dry-run-model`
- Team Execution Mode: `dry_run_all_configured_team_members`
- Created At: `2026-07-09T11:59:31.418925+00:00`

## Agent Results

| Agent ID | Task | Run | Provider | Model | Status | Output Artifact |
|---|---|---:|---|---|---|---|
| AGENT_LEGACY_LITERAL_INTERPRETER | Interpret raw legacy data | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_literal_interpreter/agent_legacy_literal_interpreter_run_01.json` |
| AGENT_LEGACY_SYSTEMS_ENGINEERING_INTERPRETER | Interpret raw legacy data | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_systems_engineering_interpreter/agent_legacy_systems_engineering_interpreter_run_01.json` |
| AGENT_LEGACY_SKEPTICAL_AMBIGUITY_INTERPRETER | Interpret raw legacy data | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/01_legacy_interpretation/team_legacy_interpretation/agent_legacy_skeptical_ambiguity_interpreter/agent_legacy_skeptical_ambiguity_interpreter_run_01.json` |
| AGENT_EVIDENCE_STRICT_CLASSIFIER | Classify engineering evidence | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_strict_classifier/agent_evidence_strict_classifier_run_01.json` |
| AGENT_EVIDENCE_SEMANTIC_CLASSIFIER | Classify engineering evidence | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_semantic_classifier/agent_evidence_semantic_classifier_run_01.json` |
| AGENT_EVIDENCE_AUDIT_CLASSIFIER | Classify engineering evidence | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/02_evidence_classification/team_evidence_classification/agent_evidence_audit_classifier/agent_evidence_audit_classifier_run_01.json` |
| AGENT_DERIVATION_RULES_FOCUSED_ASSESSOR | Assess downstream model derivation support | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_rules_focused_assessor/agent_derivation_rules_focused_assessor_run_01.json` |
| AGENT_DERIVATION_ARCHITECTURE_FOCUSED_ASSESSOR | Assess downstream model derivation support | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_architecture_focused_assessor/agent_derivation_architecture_focused_assessor_run_01.json` |
| AGENT_DERIVATION_CONSERVATIVE_REVIEWER | Assess downstream model derivation support | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/03_derivation_assessment/team_derivation_assessment/agent_derivation_conservative_reviewer/agent_derivation_conservative_reviewer_run_01.json` |
| AGENT_COMPLETENESS_GAP_FINDER | Check completeness, gaps, risks and review readiness | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_gap_finder/agent_completeness_gap_finder_run_01.json` |
| AGENT_COMPLETENESS_RISK_REVIEWER | Check completeness, gaps, risks and review readiness | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_risk_reviewer/agent_completeness_risk_reviewer_run_01.json` |
| AGENT_COMPLETENESS_TRACEABILITY_CHECKER | Check completeness, gaps, risks and review readiness | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/04_completeness_review/team_completeness_review/agent_completeness_traceability_checker/agent_completeness_traceability_checker_run_01.json` |
| AGENT_REPORT_STRUCTURED_COMPOSER | Compose structured ingestion report | 1 | openai | dry-run-model | dry_run | `/Users/moritz/Desktop/MA Git/SysMLv2-Generator/data/team_runs/TASK_001_INGEST_EXAMPLE_MODEL/20260709T115931Z/agent_outputs/05_report_composition/team_report_composition/agent_report_structured_composer/agent_report_structured_composer_run_01.json` |

## Consensus Reports

| Team ID | Task | Total Agents | Review Required | Full Agreement | Majority Agreement | Disagreement |
|---|---|---:|---:|---:|---:|---:|
| TEAM_LEGACY_INTERPRETATION | Interpret raw legacy data | 3 | 3 | 0 | 0 | 3 |
| TEAM_EVIDENCE_CLASSIFICATION | Classify engineering evidence | 3 | 3 | 0 | 0 | 3 |
| TEAM_DERIVATION_ASSESSMENT | Assess downstream model derivation support | 3 | 3 | 0 | 0 | 3 |
| TEAM_COMPLETENESS_REVIEW | Check completeness, gaps, risks and review readiness | 3 | 3 | 0 | 0 | 3 |