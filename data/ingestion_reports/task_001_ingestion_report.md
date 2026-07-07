# Ingestion Report

## Report Metadata

| Field | Value |
|---|---|
| Report ID | IR_TASK_001_INGEST_EXAMPLE_MODEL |
| Task ID | TASK_001_INGEST_EXAMPLE_MODEL |
| Recipe ID | REC_INGESTION_001 |
| Input Artifact ID | RAW_EXAMPLE_MODEL_001 |
| Source Path | legacy/raw/example_legacy_model_description.md |
| Generated At | 2026-07-07T13:37:08Z |
| Review Status | ready_for_review |

---

## 1. Executive Summary

This ingestion report was generated from a raw, unreviewed input artifact. It separates directly extracted source information from interpreted candidate information and prepares the content for human review.

The deterministic MVP extractor identified evidence that may support limited downstream model derivation. No approval, approved input promotion or SysML v2 generation has been performed.

## 2. Source Artifacts Reviewed

| Artifact ID | Path | Type | Description | Source State |
|---|---|---|---|---|
| RAW_EXAMPLE_MODEL_001 | legacy/raw/example_legacy_model_description.md | markdown | Simple raw legacy engineering description used as the first MVP ingestion example. | raw_unreviewed |

## 3. Extracted Source Information

| Source Info ID | Extracted Information | Source Reference | Notes |
|---|---|---|---|
| SRC_INFO_001 | Example Legacy Model Description | line 1 | Markdown heading; section=other |
| SRC_INFO_002 | Source Context | line 3 | Markdown heading; section=source_context |
| SRC_INFO_003 | System Name | line 17 | Markdown heading; section=system_name |
| SRC_INFO_004 | Informal System Description | line 23 | Markdown heading; section=informal_system_description |
| SRC_INFO_005 | The system shall prevent two users from controlling the microscope at the same time. | line 37 | Requirement-like statement; section=informal_system_description |
| SRC_INFO_006 | The system shall show who currently has control. | line 39 | Requirement-like statement; section=informal_system_description |
| SRC_INFO_007 | The system shall record basic session information for later traceability. | line 41 | Requirement-like statement; section=informal_system_description |
| SRC_INFO_008 | Mentioned Users | line 45 | Markdown heading; section=mentioned_users |
| SRC_INFO_009 | microscope operator | line 49 | Markdown bullet item; section=mentioned_users |
| SRC_INFO_010 | remote expert | line 50 | Markdown bullet item; section=mentioned_users |
| SRC_INFO_011 | Mentioned System Capabilities | line 54 | Markdown heading; section=mentioned_system_capabilities |
| SRC_INFO_012 | start streaming session | line 58 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_013 | join streaming session | line 59 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_014 | view live microscope image | line 60 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_015 | request remote control | line 61 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_016 | accept or reject remote control request | line 62 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_017 | adjust microscope view remotely | line 63 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_018 | prevent simultaneous control | line 64 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_019 | show current control owner | line 65 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_020 | record basic session information | line 66 | Markdown bullet item; section=mentioned_system_capabilities |
| SRC_INFO_021 | Mentioned System Elements | line 70 | Markdown heading; section=mentioned_system_elements |
| SRC_INFO_022 | microscope workstation | line 74 | Markdown bullet item; section=mentioned_system_elements |
| SRC_INFO_023 | software application | line 75 | Markdown bullet item; section=mentioned_system_elements |
| SRC_INFO_024 | client application | line 76 | Markdown bullet item; section=mentioned_system_elements |
| SRC_INFO_025 | live image stream | line 77 | Markdown bullet item; section=mentioned_system_elements |
| SRC_INFO_026 | control request | line 78 | Markdown bullet item; section=mentioned_system_elements |
| SRC_INFO_027 | session information | line 79 | Markdown bullet item; section=mentioned_system_elements |
| SRC_INFO_028 | Mentioned Constraints | line 83 | Markdown heading; section=mentioned_constraints |
| SRC_INFO_029 | only one user may control the microscope at a time | line 87 | Markdown bullet item; section=mentioned_constraints |
| SRC_INFO_030 | control transfer requires acceptance by the microscope operator | line 88 | Markdown bullet item; section=mentioned_constraints |
| SRC_INFO_031 | the current control owner must be visible | line 89 | Markdown bullet item; section=mentioned_constraints |
| SRC_INFO_032 | Informal Notes | line 93 | Markdown heading; section=other |

## 4. Interpreted Engineering Information

| Interpreted Info ID | Candidate Meaning | Based On Source Info | Confidence | Notes |
|---|---|---|---|---|
| INT_INFO_001 | The system shall prevent two users from controlling the microscope at the same time. | SRC_INFO_005 | high | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_002 | The system shall show who currently has control. | SRC_INFO_006 | high | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_003 | The system shall record basic session information for later traceability. | SRC_INFO_007 | high | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_004 | microscope operator | SRC_INFO_009 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_005 | remote expert | SRC_INFO_010 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_006 | start streaming session | SRC_INFO_012 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_007 | join streaming session | SRC_INFO_013 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_008 | view live microscope image | SRC_INFO_014 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_009 | request remote control | SRC_INFO_015 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_010 | accept or reject remote control request | SRC_INFO_016 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_011 | adjust microscope view remotely | SRC_INFO_017 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_012 | prevent simultaneous control | SRC_INFO_018 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_013 | show current control owner | SRC_INFO_019 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_014 | record basic session information | SRC_INFO_020 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_015 | microscope workstation | SRC_INFO_022 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_016 | software application | SRC_INFO_023 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_017 | client application | SRC_INFO_024 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_018 | live image stream | SRC_INFO_025 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_019 | control request | SRC_INFO_026 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_020 | session information | SRC_INFO_027 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_021 | only one user may control the microscope at a time | SRC_INFO_029 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_022 | control transfer requires acceptance by the microscope operator | SRC_INFO_030 | medium | Deterministic preliminary interpretation. Human review required. |
| INT_INFO_023 | the current control owner must be visible | SRC_INFO_031 | medium | Deterministic preliminary interpretation. Human review required. |

## 5. Candidate Downstream Elements

| Candidate ID | Candidate Type | Name | Description | Source Basis | Confidence |
|---|---|---|---|---|---|
| CAND_001 | requirement_candidate | TheSystemShallPreventTwoUsers | The system shall prevent two users from controlling the microscope at the same time. | SRC_INFO_005 | high |
| CAND_002 | requirement_candidate | TheSystemShallShowWhoCurrently | The system shall show who currently has control. | SRC_INFO_006 | high |
| CAND_003 | requirement_candidate | TheSystemShallRecordBasicSession | The system shall record basic session information for later traceability. | SRC_INFO_007 | high |
| CAND_004 | actor_candidate | MicroscopeOperator | microscope operator | SRC_INFO_009 | medium |
| CAND_005 | actor_candidate | RemoteExpert | remote expert | SRC_INFO_010 | medium |
| CAND_006 | function_candidate | StartStreamingSession | start streaming session | SRC_INFO_012 | medium |
| CAND_007 | function_candidate | JoinStreamingSession | join streaming session | SRC_INFO_013 | medium |
| CAND_008 | function_candidate | ViewLiveMicroscopeImage | view live microscope image | SRC_INFO_014 | medium |
| CAND_009 | function_candidate | RequestRemoteControl | request remote control | SRC_INFO_015 | medium |
| CAND_010 | function_candidate | AcceptOrRejectRemoteControlRequest | accept or reject remote control request | SRC_INFO_016 | medium |
| CAND_011 | function_candidate | AdjustMicroscopeViewRemotely | adjust microscope view remotely | SRC_INFO_017 | medium |
| CAND_012 | function_candidate | PreventSimultaneousControl | prevent simultaneous control | SRC_INFO_018 | medium |
| CAND_013 | function_candidate | ShowCurrentControlOwner | show current control owner | SRC_INFO_019 | medium |
| CAND_014 | function_candidate | RecordBasicSessionInformation | record basic session information | SRC_INFO_020 | medium |
| CAND_015 | physical_component_candidate | MicroscopeWorkstation | microscope workstation | SRC_INFO_022 | medium |
| CAND_016 | physical_component_candidate | SoftwareApplication | software application | SRC_INFO_023 | medium |
| CAND_017 | physical_component_candidate | ClientApplication | client application | SRC_INFO_024 | medium |
| CAND_018 | artifact_candidate | LiveImageStream | live image stream | SRC_INFO_025 | medium |
| CAND_019 | artifact_candidate | ControlRequest | control request | SRC_INFO_026 | medium |
| CAND_020 | artifact_candidate | SessionInformation | session information | SRC_INFO_027 | medium |
| CAND_021 | constraint_candidate | OnlyOneUserMayControlThe | only one user may control the microscope at a time | SRC_INFO_029 | medium |
| CAND_022 | constraint_candidate | ControlTransferRequiresAcceptanceByThe | control transfer requires acceptance by the microscope operator | SRC_INFO_030 | medium |
| CAND_023 | constraint_candidate | TheCurrentControlOwnerMustBe | the current control owner must be visible | SRC_INFO_031 | medium |

This section prepares review only. It does not create approved model data.

## 5a. Downstream Model Derivation Assessment

Detected evidence types:

- `EV_CONSTRAINT`
- `EV_DATA_OR_ARTIFACT`
- `EV_FUNCTION_OR_CAPABILITY`
- `EV_INTERFACE`
- `EV_PHYSICAL_ELEMENT`
- `EV_REQUIREMENT_STATEMENT`
- `EV_STAKEHOLDER_NEED`
- `EV_USER_ROLE`
- `EV_USE_CASE_OR_WORKFLOW`
- `EV_VALIDATION_CRITERION`

| Model Artifact Type | Support Level | Evidence Basis | Reason | Missing Information | Recommended Action |
|---|---|---|---|---|---|
| stakeholder_needs | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| stakeholder_requirements | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| system_requirements | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| functional_model | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| logical_architecture | partially_supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for partial derivation are present, but full support evidence is missing. | Missing evidence types: EV_LOGICAL_ELEMENT | Generate only preliminary candidates with assumptions, gaps and review questions. |
| physical_architecture | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| interface_model | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| data_or_artifact_model | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| constraint_model | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| validation_or_verification_model | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |
| traceability_model | supported | EV_CONSTRAINT, EV_DATA_OR_ARTIFACT, EV_FUNCTION_OR_CAPABILITY, EV_INTERFACE, EV_PHYSICAL_ELEMENT, EV_REQUIREMENT_STATEMENT, EV_STAKEHOLDER_NEED, EV_USER_ROLE, EV_USE_CASE_OR_WORKFLOW, EV_VALIDATION_CRITERION | Minimum evidence types for supported derivation are present. | None identified by deterministic assessment. Human review still required. | Generate candidate model content and mark it as requiring human review. |

## 6. Assumptions

| Assumption ID | Assumption | Reason | Impact | Requires Human Confirmation |
|---|---|---|---|---|
| ASSUMP_001 | The input artifact is intentionally incomplete and is used only for the first ingestion workflow test. | The source context states that the file is intentionally incomplete. | Downstream model derivation must be limited to sufficiently supported artifact types. | yes |

## 7. Missing Information

| Gap ID | Missing Information | Why It Matters | Suggested Human Action |
|---|---|---|---|
| GAP_001 | No explicit gaps detected by deterministic extractor. | Human review still required. | Check input completeness manually. |

## 8. Ambiguities and Risks

| Risk ID | Topic | Description | Potential Impact | Suggested Review Action |
|---|---|---|---|---|
| RISK_001 | Incomplete evidence | The input does not contain enough evidence for a complete SysML v2 model. | Unsupported model artifacts may be incorrectly inferred if derivation rules are ignored. | Use the derivation assessment before selecting candidate generation tasks. |

## 9. Review Questions

| Question ID | Question | Related Artifact or Candidate | Reason |
|---|---|---|---|
| RQ_001 | Which downstream model artifact types should be allowed for the next MVP step? | Downstream model derivation assessment | The system should not generate unsupported model artifacts from incomplete evidence. |

## 10. Recommended Review Decision

Recommendation: `incomplete_but_reviewable`

This recommendation is not an approval decision. Approval and rejection are human decisions.

## 11. Traceability Notes

- Task ID: `TASK_001_INGEST_EXAMPLE_MODEL`
- Recipe ID: `REC_INGESTION_001`
- Input Artifact ID: `RAW_EXAMPLE_MODEL_001`
- Source Path: `legacy/raw/example_legacy_model_description.md`
- Required context files used:
  - `context/global/project_principles.md`
  - `context/sources/source_manifest.json`
  - `context/sysml/sysml_v2_spec_reference.json`
  - `context/sysml/sysml_v2_target_notation.json`
  - `context/mapping/sysml_model_derivation_rules.json`
- Agent personalities loaded:
  - `agents/systems_engineer.md`
  - `agents/completeness_checker.md`

---

## Review Gate Rule

This recipe stops before the ingestion review gate.

Only after human approval may content be promoted into `data/approved_input/`.
