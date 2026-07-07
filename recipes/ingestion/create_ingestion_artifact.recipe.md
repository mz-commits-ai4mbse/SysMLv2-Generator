---
recipe_id: REC_INGESTION_001
name: Create Ingestion Artifact
version: 0.1.0
task_type: create_ingestion_artifact
workflow_stage: ingestion
review_gate: RG_001_INGESTION_REVIEW
status: draft
---

# Recipe: Create Ingestion Artifact

## Purpose

This recipe defines how the Turing Generator MVP creates a human-readable ingestion artifact from raw legacy engineering data.

The ingestion artifact is a Markdown report that prepares raw input information for human review.

This recipe does not approve data.

This recipe does not generate SysML v2 output.

This recipe does not promote content into approved input.

---

## Workflow Position

This recipe belongs to the first part of the Turing Generator workflow.

Workflow position:

1. Register raw legacy input
2. Extract readable information from raw legacy input
3. Create human-readable ingestion artifact
4. Present ingestion artifact for human review
5. Stop before approved input promotion

The output of this recipe is intended for the ingestion review gate.

---

## Input State

Required input state:

`raw_legacy_data`

The input may come from:

`legacy/raw/`

The input is unreviewed.

The input shall not be used directly for SysML v2 generation.

---

## Output State

Generated output state:

`ready_for_review`

Primary output folder:

`data/ingestion_reports/`

This recipe creates a human-readable Markdown ingestion report.

The output may later be reviewed by a human.

Only after human approval may reviewed content be promoted into:

`data/approved_input/`

---

## Required Context Files

The orchestrator shall load the following context files when executing this recipe:

- `context/global/project_principles.md`
- `context/sources/source_manifest.json`
- `context/sysml/sysml_v2_spec_reference.json`
- `context/sysml/sysml_v2_target_notation.json`
- `context/mapping/sysml_model_derivation_rules.json`

---

## Optional Context Files

The orchestrator may load the following context files if relevant for the task:

- `context/examples/apollo11_structure_reference.md`

Apollo 11 is a non-normative structure reference.

Apollo 11 shall not be treated as legacy input unless the task explicitly defines it as input.

Apollo 11 shall not override the SysML v2 target notation.

---

## Agent Personalities

The following agent personalities may be used with this recipe:

- `agents/systems_engineer.md`
- `agents/completeness_checker.md`

For the first MVP execution, the systems engineer personality may create the ingestion artifact.

The completeness checker personality may later review the ingestion artifact for completeness and traceability.

---

## Required Input Artifacts

The task file shall define at least one raw input artifact.

Expected task field:

`input_artifacts`

Each input artifact should define:

- artifact ID
- path
- artifact type
- short description
- expected relevance
- source state

Example source state:

`raw_unreviewed`

---

## Expected Output Artifacts

This recipe shall produce:

1. A Markdown ingestion report
2. A structured placeholder feedback file
3. A traceability record or traceability placeholder

Expected folders:

- `data/ingestion_reports/`
- `data/feedback/`
- `data/traceability/`

The MVP may initially create placeholder feedback and traceability files.

---

## Processing Rules

The recipe shall follow these rules:

1. Read the task specification.
2. Identify the raw input artifacts defined by the task.
3. Extract human-readable information from the raw input.
4. Preserve the distinction between source information and interpretation.
5. Create a structured Markdown ingestion report.
6. Identify candidate information that may be relevant for later model generation.
7. Identify missing information.
8. Identify assumptions.
9. Identify unclear or ambiguous content.
10. Prepare the report for human review.
11. Do not approve the content.
12. Do not promote content into approved input.
13. Do not generate SysML v2 output.
14. Do not modify protected architecture model files.
15. Use `context/mapping/sysml_model_derivation_rules.json` to assess which downstream SysML v2 model artifact types are supported, partially supported or not supported by the available input evidence.

---

## Source Handling Rules

Raw input artifacts shall be treated as unreviewed.

External reference repositories shall be treated according to `context/sources/source_manifest.json`.

The SysML v2 release repository may be used as a syntax and language reference.

The Apollo 11 repository may be used as a structure and style reference.

Neither repository shall be treated as raw legacy input unless explicitly defined by the task.

---

## Prompt Template

You are executing the Turing Generator recipe `REC_INGESTION_001`.

Your task is to create a human-readable ingestion artifact from raw legacy engineering input.

Use the provided task specification, context files and agent personality instructions.

You must distinguish clearly between:

- source information
- interpreted information
- assumptions
- missing information
- review questions
- candidate information for downstream processing

You must not approve the input.

You must not promote the input into approved input.

You must not generate SysML v2 output.

You must not modify protected architecture model files.

Create a Markdown ingestion report using the required output structure defined in this recipe.

---

## Required Ingestion Report Structure

The ingestion report shall use the following structure.

# Ingestion Report

## Report Metadata

| Field | Value |
|---|---|
| Report ID | TBD |
| Task ID | TBD |
| Recipe ID | REC_INGESTION_001 |
| Input Artifact ID | TBD |
| Source Path | TBD |
| Generated At | TBD |
| Review Status | ready_for_review |

---

## 1. Executive Summary

Provide a concise summary of what the input artifact appears to contain.

State whether the input appears relevant for downstream model generation.

Do not make approval decisions.

---

## 2. Source Artifacts Reviewed

| Artifact ID | Path | Type | Description | Source State |
|---|---|---|---|---|

---

## 3. Extracted Source Information

List information that is directly observable in the raw input.

Use this table:

| Source Info ID | Extracted Information | Source Reference | Notes |
|---|---|---|---|

Rules:

- Do not mix extracted information with assumptions.
- Keep source information traceable.
- Use stable IDs.

---

## 4. Interpreted Engineering Information

List information that appears relevant for later model generation.

Use this table:

| Interpreted Info ID | Candidate Meaning | Based On Source Info | Confidence | Notes |
|---|---|---|---|---|

Confidence values:

- high
- medium
- low

---

## 5. Candidate Downstream Elements

List possible downstream model-relevant elements.

Use this table:

| Candidate ID | Candidate Type | Name | Description | Source Basis | Confidence |
|---|---|---|---|---|---|

Allowed candidate types may include:

- requirement_candidate
- function_candidate
- logical_component_candidate
- physical_component_candidate
- artifact_candidate
- workflow_step_candidate
- interface_candidate
- traceability_candidate

This section prepares review only.

It does not create approved model data.

---

## 5a. Downstream Model Derivation Assessment

Assess which downstream model artifact types are supported by the available input evidence.

Use this table:

| Model Artifact Type | Support Level | Evidence Basis | Reason | Missing Information | Recommended Action |
|---|---|---|---|---|---|

Support level values:

- supported
- partially_supported
- not_supported
- conflicting

Rules:

- Do not recommend generation for unsupported model artifact types.
- For partially supported model artifact types, state assumptions and missing information.
- Unsupported model artifact types shall be reported as gaps, not ignored.
- Candidate generation shall only continue for supported or explicitly reviewable partially supported model artifact types.

---

## 6. Assumptions

List assumptions separately.

Use this table:

| Assumption ID | Assumption | Reason | Impact | Requires Human Confirmation |
|---|---|---|---|---|

---

## 7. Missing Information

List missing information.

Use this table:

| Gap ID | Missing Information | Why It Matters | Suggested Human Action |
|---|---|---|---|

---

## 8. Ambiguities and Risks

List ambiguity, uncertainty or risk.

Use this table:

| Risk ID | Topic | Description | Potential Impact | Suggested Review Action |
|---|---|---|---|---|

---

## 9. Review Questions

List questions for the human reviewer.

Use this table:

| Question ID | Question | Related Artifact or Candidate | Reason |
|---|---|---|---|

---

## 10. Recommended Review Decision

Provide a recommendation for human review.

Allowed recommendation values:

- review_required
- suitable_for_review_with_minor_gaps
- incomplete_but_reviewable
- incomplete_and_blocking

Do not use:

- approved
- rejected

Approval and rejection are human decisions.

---

## 11. Traceability Notes

Summarize how this ingestion report can be traced back to the raw input artifact, task file, recipe and context files.

Include:

- task ID
- recipe ID
- input artifact IDs
- context files used
- agent personality used, if applicable

---

## Review Gate Rule

This recipe stops before the ingestion review gate.

The next workflow step is human review.

Only after human approval may content be promoted into:

`data/approved_input/`

---

## Forbidden Outputs

This recipe shall not create:

- approved input
- approved model data
- generated SysML v2 output
- modified architecture model files

This recipe shall not write to:

`model/architecture/`

This recipe shall not write generated SysML v2 files to:

`data/output/`

---

## Completion Criteria

This recipe is complete when:

1. A Markdown ingestion report exists.
2. The report has status `ready_for_review`.
3. The report clearly separates source information, interpretation, assumptions and gaps.
4. The report contains review questions.
5. The report does not approve or promote content.
6. The report is traceable to the task, recipe and input artifact.