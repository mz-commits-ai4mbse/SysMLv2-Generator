"""Reference metadata for downstream semantic and modeling stages.

R4c.3 Subject interpretation deliberately does not load these references into
the Persona classification prompt. ADR-011 separates Information
Classification from terminology/ontology candidate mapping, and Apollo 11 is a
non-normative structural example for later modeling concerns.
"""

from __future__ import annotations

from pathlib import Path


ADR_011_PATH = Path(
    "collaboration/decisions/"
    "ADR-011-semantic-information-unit-and-ontology-boundary.md"
)
TURING_CORE_PATH = Path(
    "context/semantics/turing_core_vocabulary.json"
)
ONTOLOGY_REGISTRY_PATH = Path(
    "context/semantics/ontology_registry.json"
)
APOLLO_STRUCTURE_REFERENCE_PATH = Path(
    "context/examples/apollo11_structure_reference.md"
)


def existing_downstream_reference_paths() -> tuple[Path, ...]:
    """Return accepted references without loading them into R4c.3 prompts."""

    return (
        ADR_011_PATH,
        TURING_CORE_PATH,
        ONTOLOGY_REGISTRY_PATH,
        APOLLO_STRUCTURE_REFERENCE_PATH,
    )
