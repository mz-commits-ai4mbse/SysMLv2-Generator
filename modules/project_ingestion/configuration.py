"""Validated configuration for project-bound Team Agentic Ingestion."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
)

from .errors import ProjectIngestionConfigurationError


PIPELINE_CONFIGURATION_VERSION = "1.0.0"
LEGACY_PIPELINE_CONFIGURATION_VERSION = "1.0.0"
CORRECTED_PIPELINE_CONFIGURATION_VERSION = "2.0.0"
DEFAULT_RECIPE_ID = "REC_INGESTION_001"
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_SEMANTIC_REFERENCE_VERSIONS = (
    ("BFO_2020", "2020"),
    ("IOF_CORE_202602", "202602"),
    ("TURING_CORE_VOCABULARY", "1.0.0"),
)

_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]{0,119}$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)


@dataclass(frozen=True, slots=True)
class ProjectIngestionConfiguration:
    """Material, secret-free execution settings for one Processing Run."""

    recipe_id: str = DEFAULT_RECIPE_ID
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    runs_per_member: int = 1
    max_members_per_team: int | None = 1
    dry_run: bool = True
    pipeline_configuration_version: str = (
        PIPELINE_CONFIGURATION_VERSION
    )
    semantic_reference_versions: tuple[
        tuple[str, str],
        ...
    ] = DEFAULT_SEMANTIC_REFERENCE_VERSIONS


def validate_ingestion_configuration(
    configuration: Any,
) -> ProjectIngestionConfiguration:
    """Validate and return one immutable ingestion configuration."""

    if not isinstance(
        configuration,
        ProjectIngestionConfiguration,
    ):
        raise ProjectIngestionConfigurationError(
            "configuration must be a "
            "ProjectIngestionConfiguration instance."
        )

    for field_name in (
        "recipe_id",
        "provider",
        "model",
    ):
        value = getattr(configuration, field_name)
        if (
            not isinstance(value, str)
            or _IDENTIFIER_PATTERN.fullmatch(value) is None
        ):
            raise ProjectIngestionConfigurationError(
                f"{field_name} must be a stable identifier."
            )

    if (
        not isinstance(
            configuration.pipeline_configuration_version,
            str,
        )
        or _SEMANTIC_VERSION_PATTERN.fullmatch(
            configuration.pipeline_configuration_version
        )
        is None
    ):
        raise ProjectIngestionConfigurationError(
            "pipeline_configuration_version must be a semantic "
            "version such as 1.0.0."
        )

    if (
        isinstance(configuration.runs_per_member, bool)
        or not isinstance(configuration.runs_per_member, int)
        or not 1 <= configuration.runs_per_member <= 5
    ):
        raise ProjectIngestionConfigurationError(
            "runs_per_member must be an integer from 1 to 5."
        )

    maximum = configuration.max_members_per_team
    if maximum is not None and (
        isinstance(maximum, bool)
        or not isinstance(maximum, int)
        or not 1 <= maximum <= 100
    ):
        raise ProjectIngestionConfigurationError(
            "max_members_per_team must be None or an integer "
            "from 1 to 100."
        )

    if not isinstance(configuration.dry_run, bool):
        raise ProjectIngestionConfigurationError(
            "dry_run must be a boolean."
        )

    if not configuration.semantic_reference_versions:
        raise ProjectIngestionConfigurationError(
            "semantic_reference_versions must not be empty."
        )

    seen: set[str] = set()
    for item in configuration.semantic_reference_versions:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
        ):
            raise ProjectIngestionConfigurationError(
                "Each semantic reference must contain an ID "
                "and version."
            )

        reference_id, reference_version = item
        if (
            not isinstance(reference_id, str)
            or _IDENTIFIER_PATTERN.fullmatch(
                reference_id
            ) is None
        ):
            raise ProjectIngestionConfigurationError(
                "Semantic reference IDs must be stable identifiers."
            )
        if (
            not isinstance(reference_version, str)
            or not reference_version
            or reference_version != reference_version.strip()
        ):
            raise ProjectIngestionConfigurationError(
                "Semantic reference versions must be non-empty "
                "trimmed strings."
            )
        if reference_id in seen:
            raise ProjectIngestionConfigurationError(
                "Semantic reference IDs must be unique."
            )
        seen.add(reference_id)

    return configuration


def calculate_ingestion_configuration_fingerprint(
    configuration: ProjectIngestionConfiguration,
) -> str:
    """Fingerprint all material settings without including secrets."""

    validated = validate_ingestion_configuration(configuration)
    payload = {
        "dry_run": validated.dry_run,
        "max_members_per_team": (
            validated.max_members_per_team
        ),
        "model": validated.model,
        "pipeline_configuration_version": (
            validated.pipeline_configuration_version
        ),
        "provider": validated.provider,
        "recipe_id": validated.recipe_id,
        "runs_per_member": validated.runs_per_member,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def workflow_profile_for_source_role(
    source_role: str,
) -> str:
    """Map an accepted P3 Source role to its P5 workflow profile."""

    if source_role == ENGINEERING_SOURCE_ROLE:
        return "engineering_source_processing"
    if source_role == CONTEXT_ONLY_SOURCE_ROLE:
        return "context_only_processing"

    raise ProjectIngestionConfigurationError(
        "Unsupported Source role for project-bound ingestion."
    )
