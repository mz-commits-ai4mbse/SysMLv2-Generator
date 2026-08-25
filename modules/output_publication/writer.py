"""Controlled Final Model Review → Published Output service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from modules.final_model_review.contracts import (
    validate_final_model_review_decision,
)
from modules.final_model_review.release_gate import (
    require_final_model_review_approved_for_publication,
)
from modules.final_model_review.repository import FinalModelReviewRepository
from modules.final_model_review.types import FinalModelReviewDecision
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT
from modules.sysml_validation.phase_l_gate import validate_phase_l_handoff

from .errors import (
    OutputPublicationIntegrityError,
    OutputPublicationValidationError,
)
from .identifiers import next_output_package_id
from .manifest import (
    calculate_publication_input_fingerprint,
    create_published_output_file_reference,
    create_published_output_manifest,
    validate_manifest_against_profile,
)
from .output_profile import (
    DEFAULT_OUTPUT_PUBLICATION_PROFILE_PATH,
    load_output_publication_profile,
    output_publication_profile_reference,
)
from .paths import DEFAULT_OUTPUT_ROOT
from .repository import OutputPublicationRepository
from .types import PublishedOutputFileReference, PublishedOutputPackage


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class OutputWriter:
    """Publish only one exact K-valid, Human-approved Final Model Review revision."""

    def __init__(
        self,
        *,
        output_root: Path | str = DEFAULT_OUTPUT_ROOT,
        project_root: Path | str = DEFAULT_PROJECTS_ROOT,
        profile_path: Path | str = DEFAULT_OUTPUT_PUBLICATION_PROFILE_PATH,
        output_repository: OutputPublicationRepository | None = None,
        final_review_repository: FinalModelReviewRepository | None = None,
        phase_l_gate: Callable[[object, object], None] = validate_phase_l_handoff,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.output_root = Path(output_root)
        self.project_root = Path(project_root)
        self._profile = load_output_publication_profile(profile_path)
        self._profile_reference = output_publication_profile_reference(self._profile)
        self._outputs = output_repository or OutputPublicationRepository(
            output_root=self.output_root
        )
        self._reviews = final_review_repository or FinalModelReviewRepository(
            root=self.project_root,
            clock=clock,
        )
        self._phase_l_gate = phase_l_gate
        self._clock = clock

    def publish(
        self,
        artifact_set,
        validation_result,
        final_review_decision: FinalModelReviewDecision,
    ) -> PublishedOutputPackage:
        """Publish the exact validated and Human-approved artifact idempotently."""

        try:
            validate_final_model_review_decision(final_review_decision)
        except Exception as exc:
            raise OutputPublicationIntegrityError(
                "Final Human release decision is invalid."
            ) from exc
        if final_review_decision.decision != "approved_for_publication":
            raise OutputPublicationValidationError(
                "Output publication requires decision=approved_for_publication."
            )

        try:
            self._phase_l_gate(artifact_set, validation_result)
        except Exception as exc:
            raise OutputPublicationIntegrityError(
                "Phase-K → Phase-L publication gate rejected the supplied artifacts."
            ) from exc

        project_id = final_review_decision.project_id
        target = final_review_decision.target
        if getattr(artifact_set, "project_id", None) != project_id:
            raise OutputPublicationIntegrityError(
                "Generated artifact Project does not match Human release decision."
            )
        if getattr(validation_result, "project_id", None) != project_id:
            raise OutputPublicationIntegrityError(
                "Validation result Project does not match Human release decision."
            )
        if (
            target.generated_artifact_set_fingerprint
            != artifact_set.content_fingerprint
        ):
            raise OutputPublicationIntegrityError(
                "Human release decision does not authorize this exact artifact set."
            )
        if (
            target.validation_result_fingerprint
            != validation_result.content_fingerprint
        ):
            raise OutputPublicationIntegrityError(
                "Human release decision does not authorize this validation result."
            )

        persisted_decision = self._reviews.load_decision(
            project_id,
            target.final_model_review_id,
            final_review_decision.final_model_review_decision_id,
        )
        if persisted_decision != final_review_decision:
            raise OutputPublicationIntegrityError(
                "Supplied Human release decision does not match persisted review evidence."
            )
        revision_bundle = self._reviews.load_revision(
            project_id,
            target.final_model_review_id,
            target.final_model_review_revision_id,
        )
        revision = revision_bundle.revision
        self._validate_revision_binding(
            revision,
            artifact_set,
            validation_result,
            final_review_decision,
        )

        publication_input_fingerprint = calculate_publication_input_fingerprint(
            source_artifact_set_fingerprint=artifact_set.content_fingerprint,
            validation_result_fingerprint=validation_result.content_fingerprint,
            final_review_decision_fingerprint=(
                final_review_decision.decision_fingerprint
            ),
            final_review_revision_fingerprint=revision.content_fingerprint,
            output_profile_reference=self._profile_reference,
        )

        scan = self._outputs.scan_project(project_id)
        if scan.issues:
            first = scan.issues[0]
            raise OutputPublicationIntegrityError(
                "Output publication is blocked by repository issue "
                f"{first.code}: {first.message}"
            )
        existing = tuple(
            package
            for package in scan.packages
            if package.manifest.publication_input_fingerprint
            == publication_input_fingerprint
        )
        if len(existing) > 1:
            raise OutputPublicationIntegrityError(
                "More than one Published Output exists for the same publication input."
            )
        if existing:
            self._validate_existing_manifest(
                existing[0].manifest,
                artifact_set,
                validation_result,
                final_review_decision,
                revision.content_fingerprint,
            )
            return existing[0]

        current_gate = require_final_model_review_approved_for_publication(
            self._reviews,
            project_id,
            target.final_model_review_id,
            target.final_model_review_revision_id,
        )
        if (
            current_gate.approval_decision_id
            != final_review_decision.final_model_review_decision_id
        ):
            raise OutputPublicationIntegrityError(
                "Current Final Model Review release gate does not resolve the supplied "
                "Human approval decision."
            )
        if current_gate.revision_content_fingerprint != revision.content_fingerprint:
            raise OutputPublicationIntegrityError(
                "Current Final Model Review gate does not cover the loaded revision."
            )

        output_package_id = next_output_package_id(
            package.manifest.output_package_id for package in scan.packages
        )
        file_bytes, file_references = self._build_package_files(
            artifact_set,
            validation_result,
        )
        manifest = create_published_output_manifest(
            project_id=project_id,
            output_package_id=output_package_id,
            source_internal_engineering_model_id=(
                artifact_set.source_internal_engineering_model_id
            ),
            source_artifact_set_fingerprint=artifact_set.content_fingerprint,
            validation_result_fingerprint=validation_result.content_fingerprint,
            final_model_review_id=target.final_model_review_id,
            final_model_review_revision_id=(
                target.final_model_review_revision_id
            ),
            final_review_revision_fingerprint=revision.content_fingerprint,
            final_review_decision_id=(
                final_review_decision.final_model_review_decision_id
            ),
            final_review_decision_fingerprint=(
                final_review_decision.decision_fingerprint
            ),
            final_release_gate_fingerprint=current_gate.evaluation_fingerprint,
            output_profile_reference=self._profile_reference,
            publication_input_fingerprint=publication_input_fingerprint,
            files=file_references,
            published_at=self._timestamp(),
        )
        validate_manifest_against_profile(manifest, self._profile)
        return self._outputs.publish_package(manifest, file_bytes)

    def _validate_revision_binding(
        self,
        revision,
        artifact_set,
        validation_result,
        decision,
    ) -> None:
        target = decision.target
        if revision.project_id != decision.project_id:
            raise OutputPublicationIntegrityError(
                "Final Model Review revision Project does not match release decision."
            )
        if revision.final_model_review_id != target.final_model_review_id:
            raise OutputPublicationIntegrityError(
                "Final Model Review ID does not match release decision."
            )
        if (
            revision.final_model_review_revision_id
            != target.final_model_review_revision_id
        ):
            raise OutputPublicationIntegrityError(
                "Final Model Review revision ID does not match release decision."
            )
        if revision.content_fingerprint != target.revision_content_fingerprint:
            raise OutputPublicationIntegrityError(
                "Human approval targets a stale Final Model Review revision."
            )
        if revision.review_subject_fingerprint != target.review_subject_fingerprint:
            raise OutputPublicationIntegrityError(
                "Human approval review-subject fingerprint is stale."
            )
        if (
            revision.generated_artifact_set_fingerprint
            != artifact_set.content_fingerprint
        ):
            raise OutputPublicationIntegrityError(
                "Final Model Review revision does not bind the supplied artifact set."
            )
        if (
            revision.validation_result_fingerprint
            != validation_result.content_fingerprint
        ):
            raise OutputPublicationIntegrityError(
                "Final Model Review revision does not bind the supplied validation result."
            )
        if (
            revision.source_internal_engineering_model_id
            != artifact_set.source_internal_engineering_model_id
        ):
            raise OutputPublicationIntegrityError(
                "Final Model Review source IEM does not match generated artifacts."
            )

    def _validate_existing_manifest(
        self,
        manifest,
        artifact_set,
        validation_result,
        decision,
        revision_fingerprint: str,
    ) -> None:
        expected = {
            "project_id": decision.project_id,
            "source_internal_engineering_model_id": (
                artifact_set.source_internal_engineering_model_id
            ),
            "source_artifact_set_fingerprint": artifact_set.content_fingerprint,
            "validation_result_fingerprint": validation_result.content_fingerprint,
            "final_model_review_id": decision.target.final_model_review_id,
            "final_model_review_revision_id": (
                decision.target.final_model_review_revision_id
            ),
            "final_review_revision_fingerprint": revision_fingerprint,
            "final_review_decision_id": (
                decision.final_model_review_decision_id
            ),
            "final_review_decision_fingerprint": decision.decision_fingerprint,
        }
        for field, value in expected.items():
            if getattr(manifest, field) != value:
                raise OutputPublicationIntegrityError(
                    "Idempotent Published Output does not match the supplied "
                    f"authority chain at {field}."
                )
        if manifest.output_profile_reference != self._profile_reference:
            raise OutputPublicationIntegrityError(
                "Idempotent Published Output uses a different Output Profile."
            )

    def _build_package_files(
        self,
        artifact_set,
        validation_result,
    ) -> tuple[dict[str, bytes], tuple[PublishedOutputFileReference, ...]]:
        files: dict[str, bytes] = {}
        references: list[PublishedOutputFileReference] = []

        for unit in sorted(artifact_set.units, key=lambda item: item.relative_path):
            data = unit.content.encode("utf-8")
            digest = hashlib.sha256(data).hexdigest()
            if digest != unit.content_fingerprint:
                raise OutputPublicationIntegrityError(
                    "Generated SysML unit bytes no longer match Phase-J fingerprint."
                )
            self._add_file(
                files,
                references,
                relative_path=unit.relative_path,
                role="sysml_unit",
                data=data,
                source_generated_unit_id=unit.unit_id,
            )

        generation_summary = {
            "schema_version": "1.0.0",
            "project_id": artifact_set.project_id,
            "source_internal_engineering_model_id": (
                artifact_set.source_internal_engineering_model_id
            ),
            "source_iem_content_fingerprint": (
                artifact_set.source_iem_content_fingerprint
            ),
            "generation_input_fingerprint": (
                artifact_set.generation_input_fingerprint
            ),
            "generation_context": asdict(artifact_set.generation_context),
            "generation_provenance": asdict(artifact_set.generation_provenance),
            "generated_units": [
                {
                    "unit_id": unit.unit_id,
                    "relative_path": unit.relative_path,
                    "content_fingerprint": unit.content_fingerprint,
                    "generated_symbol_ids": list(unit.generated_symbol_ids),
                    "source_internal_model_element_ids": list(
                        unit.source_internal_model_element_ids
                    ),
                    "source_internal_model_relationship_ids": list(
                        unit.source_internal_model_relationship_ids
                    ),
                }
                for unit in artifact_set.units
            ],
            "nonblocking_diagnostics": [
                asdict(item)
                for item in getattr(
                    artifact_set,
                    "nonblocking_diagnostics",
                    (),
                )
            ],
            "artifact_set_content_fingerprint": artifact_set.content_fingerprint,
        }
        self._add_json_file(
            files,
            references,
            "generation_summary.json",
            "generation_summary",
            generation_summary,
        )
        self._add_json_file(
            files,
            references,
            "validation_result.json",
            "validation_result",
            asdict(validation_result),
        )
        self._add_file(
            files,
            references,
            relative_path="validation_report.md",
            role="validation_report",
            data=self._validation_report(
                artifact_set,
                validation_result,
            ).encode("utf-8"),
        )
        traceability = {
            "schema_version": "1.0.0",
            "project_id": artifact_set.project_id,
            "source_internal_engineering_model_id": (
                artifact_set.source_internal_engineering_model_id
            ),
            "source_artifact_set_fingerprint": artifact_set.content_fingerprint,
            "entries": [
                asdict(item) for item in artifact_set.traceability_entries
            ],
        }
        self._add_json_file(
            files,
            references,
            "traceability.json",
            "traceability",
            traceability,
        )
        references.sort(key=lambda item: item.relative_path)
        return files, tuple(references)

    def _add_json_file(
        self,
        files: dict[str, bytes],
        references: list[PublishedOutputFileReference],
        relative_path: str,
        role: str,
        payload: object,
    ) -> None:
        data = (
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        self._add_file(
            files,
            references,
            relative_path=relative_path,
            role=role,
            data=data,
        )

    def _add_file(
        self,
        files: dict[str, bytes],
        references: list[PublishedOutputFileReference],
        *,
        relative_path: str,
        role: str,
        data: bytes,
        source_generated_unit_id: str | None = None,
    ) -> None:
        if relative_path in files:
            raise OutputPublicationIntegrityError(
                f"Published Output file path collision: {relative_path}."
            )
        digest = hashlib.sha256(data).hexdigest()
        files[relative_path] = data
        references.append(
            create_published_output_file_reference(
                relative_path=relative_path,
                role=role,
                content_fingerprint=digest,
                source_generated_unit_id=source_generated_unit_id,
            )
        )

    def _validation_report(self, artifact_set, validation_result) -> str:
        lines = [
            "# SysML v2 Validation Report",
            "",
            f"- Project: `{validation_result.project_id}`",
            f"- Source IEM: `{validation_result.source_internal_engineering_model_id}`",
            f"- Validation status: **{validation_result.validation_status}**",
            f"- Publication gate: **{validation_result.publication_gate}**",
            f"- Artifact set fingerprint: `{artifact_set.content_fingerprint}`",
            f"- Validation result fingerprint: `{validation_result.content_fingerprint}`",
            (
                "- Validation profile: `"
                f"{validation_result.validation_profile_reference.profile_id} "
                f"{validation_result.validation_profile_reference.profile_version}`"
            ),
            f"- Findings: {len(validation_result.findings)}",
            "",
        ]
        if validation_result.external_validator_evidence:
            lines.append("## External validator evidence")
            lines.append("")
            for evidence in validation_result.external_validator_evidence:
                identity = evidence.validator_identity
                version = identity.tool_version or "unknown"
                lines.append(
                    "- `"
                    f"{identity.validator_id}` — {identity.tool_name} {version}; "
                    f"execution={evidence.execution_status}; "
                    f"diagnostics={evidence.normalized_diagnostic_count}"
                )
            lines.append("")
        lines.append("## Findings")
        lines.append("")
        if not validation_result.findings:
            lines.append("No validation findings.")
        else:
            for finding in validation_result.findings:
                location = ""
                if finding.generated_unit_id is not None:
                    location = f" [{finding.generated_unit_id}"
                    if finding.generated_location is not None:
                        location += (
                            f":{finding.generated_location.start_line}"
                            f"-{finding.generated_location.end_line}"
                        )
                    location += "]"
                lines.append(
                    f"- **{finding.severity}** `{finding.code}` "
                    f"({finding.category}){location}: {finding.message}"
                )
        return "\n".join(lines) + "\n"

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise OutputPublicationValidationError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise OutputPublicationValidationError(
                "clock must return a timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
