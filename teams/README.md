# Teams

This directory contains team configurations.

A team defines which agent role and persona combinations are used for a given task.

Teams are used when the same task should be executed by multiple persona agents.

The purpose is not to let agents debate freely.
The purpose is to create independent outputs that can be compared by a consensus or variance analyzer.

## Example

Task:
Classify engineering evidence

Team:
Evidence Classification Team

Members:
- strict evidence classifier
- semantic evidence classifier
- skeptical audit classifier

Result:
The system compares the outputs and identifies agreement, disagreement and uncertain classifications.
