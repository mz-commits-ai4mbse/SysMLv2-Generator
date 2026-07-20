# Agents

This directory contains the role and persona definitions used by the Turing Generator.

## Concept

The architecture separates:

1. Roles
2. Personas
3. Teams

## Role

A role defines the task-specific responsibility of an agent.

Examples:

- Legacy Data Interpreter
- Evidence Classifier
- Derivation Assessor
- Completeness Checker
- Report Composer

A role answers:

"What task is this agent allowed to perform?"

## Persona

A persona defines the perspective or behavior style used when executing a role.

Examples:

- literal
- semantic
- skeptical
- audit-focused
- rules-focused
- architecture-focused

A persona answers:

"From which perspective should this task be performed?"

## Team

A team defines which personas are assigned to a specific task.

A team allows multiple agents with the same role but different personas to perform the same task.

The outputs can then be compared by a consensus or variance analyzer.

## Architectural Rule

One agent run performs exactly one task.

Multiple persona agents may perform the same task independently.

Consensus is a separate comparison step and not part of the individual agent task.
