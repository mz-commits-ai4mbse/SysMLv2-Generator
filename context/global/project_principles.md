# Turing Generator Project Principles

## Purpose

This file defines the global working principles for the Turing Generator MVP.

The Turing Generator is a recipe-based, artifact-driven and human-reviewed system for transforming heterogeneous engineering information into valid SysML v2 model artifacts.

The system shall not rely on implicit chat history alone. Relevant context, task definitions, recipes, agent personalities, intermediate artifacts, feedback, decisions and generated model outputs shall be stored as explicit files in the workspace.

---

## Core Principle

Every file has a defined purpose.

No artifact shall be created without a clear role in the workflow.

The system distinguishes between:

- raw legacy data
- human-readable ingestion artifacts
- approved input
- candidate artifacts
- comparison and review reports
- human feedback
- human decisions
- approved model data
- generated SysML v2 output
- traceability records

---

## Workspace Principle

The project is organized as a repository-based engineering workspace.

The workspace contains:

- architecture model files describing the Turing Generator itself
- external reference repositories
- curated context files
- agent personality files
- recipe files
- task files
- raw legacy data
- intermediate artifacts
- human-readable reports
- feedback and decisions
- generated SysML v2 output

The workspace shall support reviewability, repeatability and traceability.

---

## Source Separation Principle

External reference repositories may be stored locally in full.

However, complete external repositories shall not be loaded into prompts by default.

The system shall use curated context files for routine prompting.

External repositories are used as reference sources only.

The source roles are defined in:

`context/sources/source_manifest.json`

---

## Architecture Model Protection

Files in `model/architecture/` describe the architecture of the Turing Generator itself.

These files may be read as project context, but shall not be modified unless explicitly requested.

Generated SysML v2 output shall not be written to `model/architecture/`.

Generated SysML v2 output belongs in:

`data/output/`

---

## Artifact Type Principle

The system uses different file types for different purposes.

### Markdown

Markdown is used for human-readable artifacts.

Typical Markdown artifacts are:

- recipes
- agent personalities
- ingestion reports
- candidate reports
- comparison reports
- review reports
- explanatory summaries

Markdown reports should be easy to read and may contain tables, checklists and diagrams.

### JSON

JSON is used for structured machine-readable data.

Typical JSON artifacts are:

- context files
- task specifications
- pipeline configuration
- feedback records
- decision records
- traceability records
- manifests
- approved input data
- approved model data

### SysML

SysML v2 text files are used for generated model artifacts and architecture model artifacts.

Generated SysML v2 files shall be written to:

`data/output/`

Architecture model files describing the Turing Generator itself shall be stored in:

`model/architecture/`

---

## Recipe-Based Orchestration Principle

The system uses recipe-based orchestration.

A recipe defines:

- task type
- role and execution instructions
- required context files
- required input artifacts
- expected output artifacts
- prompt structure
- review criteria
- validation expectations

Prompts and task procedures shall not be hardcoded into Python modules.

Prompts and procedures shall be stored in versioned recipe artifacts.

The orchestrator executes recipes. It does not invent uncontrolled workflows.

---

## Orchestrator Principle

The orchestrator acts as the central coordinator of the MVP.

The orchestrator is responsible for:

- reading a task specification
- selecting the appropriate recipe
- loading required context artifacts
- loading selected agent personalities
- preparing task-specific prompts
- executing pipeline steps
- storing intermediate artifacts
- enforcing review gates
- recording feedback and decisions
- writing traceability records
- passing only approved artifacts to downstream steps

The orchestrator is the "kitchen chef" of the system.

It coordinates recipes, ingredients, processing steps, review gates and outputs.

---

## Human Review Principle

Human review is mandatory at defined review gates.

The system shall not automatically promote raw extracted data or candidate model data into downstream processing without human approval.

At minimum, the MVP contains two review gates.

### Review Gate 1: Ingestion Review

Raw legacy data is transformed into a human-readable ingestion artifact.

The human reviews this ingestion artifact.

Only approved or modified content may be promoted into:

`data/approved_input/`

### Review Gate 2: Candidate Review

Candidate artifacts are generated from approved input using recipes, context and agent personalities.

Candidate artifacts are compared.

A human-readable comparison report is generated.

The human reviews this report.

Only approved or modified candidate output may be promoted into approved model data.

Generated SysML v2 artifacts may only be created from approved model data.

---

## Artifact Promotion Principle

The system separates artifact states.

Raw data must not be treated as approved input.

Candidate data must not be treated as approved model data.

Generated output must not be created from unapproved candidate data.

The promotion chain is:

1. raw legacy data
2. human-readable ingestion artifact
3. approved input
4. candidate artifacts
5. candidate comparison report
6. approved model data
7. generated SysML v2 output

Each promotion step requires explicit status information and traceability.

---

## Multi-Persona Principle

The system may execute the same task multiple times using different agent personalities.

An agent personality is a versioned artifact that defines:

- role
- perspective
- review focus
- behavior
- output expectations

The MVP may use one LLM backend with multiple agent personalities.

The target architecture may allow multiple LLM backends or specialized agent implementations.

The purpose of multiple agent personalities is not to replace human review.

The purpose is to produce multiple candidate perspectives that can be compared and presented to the human reviewer.

---

## Candidate Comparison Principle

When multiple candidate artifacts exist for the same task, the system shall compare them.

The comparison shall identify:

- agreement
- differences
- uncertainties
- missing information
- conflicting interpretations
- candidate-specific rationales
- relevant source references

Candidate agreement is review information.

Candidate agreement shall not replace human approval.

Candidate differences are review signals.

Candidate differences shall be made visible to the human reviewer.

---

## Traceability Principle

The system shall maintain traceability between:

- raw legacy data
- extracted content
- ingestion artifacts
- human feedback
- human decisions
- approved input
- recipes
- context files
- agent personalities
- candidate artifacts
- comparison reports
- approved model data
- generated SysML v2 artifacts
- validation findings

Traceability records should make it possible to understand what was generated, from which source, by which recipe, with which agent personality, and after which human decision.

---

## SysML v2 Generation Principle

Generated SysML v2 output shall conform to the selected target notation.

The selected MVP target notation is intentionally limited.

Scope shall be reduced by limiting the generated SysML v2 subset, not by accepting invalid syntax.

The SysML v2 release repository is the primary syntax and language reference.

The Apollo 11 SysML v2 repository may be used as a non-normative structure and style reference.

The system shall distinguish between:

- normative syntax guidance
- project-specific target notation
- example model structure

---

## Validation Principle

Generated SysML v2 artifacts shall be prepared for validation in the selected validation environment.

Validation findings shall be treated as reviewable artifacts.

Validation findings shall not silently modify generated model output.

When validation findings are present, they shall be reported to the human reviewer or stored as traceability information.

---

## MVP Scope Principle

The MVP is not a throwaway prototype.

The MVP is a selected, executable subset of the intended target architecture.

The MVP shall demonstrate:

- artifact-based workflow
- recipe-based orchestration
- human-readable ingestion artifact generation
- human review gate for ingestion
- approved input promotion
- persona-based candidate generation
- candidate comparison
- human review gate for candidate output
- approved model data promotion
- SysML v2 artifact generation
- traceability between relevant artifacts

The MVP may limit:

- supported input formats
- SysML v2 target notation subset
- number of recipes
- number of agent personalities
- validation depth
- user interface sophistication

The MVP shall not compromise the core review and traceability principles.

---

## User Interface Principle

The user interface supports the human review workflow.

The UI shall help the user:

- select or start tasks
- upload or select legacy input
- view human-readable reports
- provide feedback
- approve, reject or modify artifacts
- access generated SysML v2 output

The UI is not responsible for task-specific processing logic.

Processing logic belongs in modules coordinated by the orchestrator.

---

## Implementation Principle

Python modules shall remain modular.

Each module should have a clear responsibility.

The orchestrator coordinates modules, but task-specific logic shall remain separated.

Prompts and procedures shall not be embedded directly in processing modules.

The implementation shall follow the physical MVP architecture.

---

## Review Status Values

The system may use the following review and processing status values:

- draft
- ready_for_review
- feedback_requested
- approved
- approved_with_modifications
- rejected
- promoted_to_approved_input
- promoted_to_approved_model_data
- generated
- validation_ready
- validation_failed
- validated

---

## Working Rule for LLM Assistants

When assisting with this project, follow these rules:

1. Respect the defined workspace structure.
2. Do not overwrite architecture model files unless explicitly requested.
3. Do not write generated SysML v2 output outside `data/output/`.
4. Do not treat external example repositories as legacy input unless explicitly instructed.
5. Use curated context files before using large external repositories.
6. Keep artifacts purpose-specific.
7. Preserve human review gates.
8. Do not promote unapproved artifacts.
9. Store feedback and decisions as structured artifacts.
10. Keep implementation modular.