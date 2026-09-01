"""Atomic immutable repository for ADR-032 I2A reconciliation cycles."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import errno
import json
from pathlib import Path
import re
import uuid

from modules.model_impact_reconciliation import (
    model_impact_reconciliation_to_json,
    validate_model_impact_reconciliation_artifact,
)
from modules.project_engineering_authority import (
    project_engineering_authority_to_json,
    validate_project_engineering_authority_state,
)
from modules.project_fit import (
    derive_project_fit_gate_state,
    project_fit_assessment_to_json,
    validate_project_fit_assessment,
)
from modules.project_semantic_reconciliation import (
    project_semantic_reconciliation_to_json,
    validate_project_semantic_reconciliation_artifact,
)

from .case_persistence import (
    PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION,
    case_assessment_from_json,
    case_cycle_manifest_from_json,
    reconciliation_summary_from_json,
    semantic_index_from_json,
)
from .errors import (
    ProjectReconciliationPersistenceIntegrityError,
    ProjectReconciliationPersistenceValidationError,
)
from .serialization import (
    binding_snapshot_from_json,
    binding_snapshot_to_json,
    create_binding_snapshot,
    create_cycle_manifest,
    cycle_manifest_from_json,
    cycle_manifest_to_json,
    model_impact_reconciliation_from_json,
    project_authority_decision_from_json,
    project_authority_decision_to_json,
    project_engineering_authority_state_from_json,
    project_fit_assessment_from_json,
    project_semantic_reconciliation_from_json,
)
from .types import ProjectAuthorityBindingSnapshot


_CYCLE = re.compile(r"^PRC-([0-9]{6})$")
_DECISION = re.compile(r"^PEAD-([0-9]{6})$")
_CONCERN = re.compile(r"^PEAC-([0-9]{6})$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def _default_clock():
    return datetime.now(timezone.utc)


class ProjectReconciliationRepository:
    """Persist exact S2-S5 evidence without rewriting source-local authority."""

    def __init__(
        self,
        root=Path("data/projects"),
        *,
        clock=_default_clock,
    ):
        self.root = Path(root)
        self._clock = clock

    def publish_project_fit(self, assessment):
        validate_project_fit_assessment(assessment)
        path = (
            self._project_root(assessment.project_id)
            / "project_fit"
            / f"{assessment.assessment_fingerprint}.json"
        )
        self._publish_exact(
            path,
            project_fit_assessment_to_json(assessment),
            loader=lambda: self.load_project_fit(
                assessment.project_id,
                assessment.assessment_fingerprint,
            ),
            expected=assessment,
            label="Project Fit assessment",
        )
        return self.load_project_fit(
            assessment.project_id,
            assessment.assessment_fingerprint,
        )

    def load_project_fit(
        self,
        project_id: str,
        assessment_fingerprint: str,
    ):
        self._validate_sha(assessment_fingerprint, "assessment_fingerprint")
        path = (
            self._project_root(project_id)
            / "project_fit"
            / f"{assessment_fingerprint}.json"
        )
        self._require_file(path, "Project Fit assessment")
        value = project_fit_assessment_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.assessment_fingerprint != assessment_fingerprint
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted Project Fit binding is invalid."
            )
        return value

    def list_project_fit(self, project_id: str):
        directory = self._project_root(project_id) / "project_fit"
        if not directory.exists():
            return ()
        self._require_directory(directory, "Project Fit directory")
        values = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if (
                not path.is_file()
                or path.is_symlink()
                or not path.name.endswith(".json")
            ):
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Unexpected Project Fit repository entry."
                )
            fingerprint = path.name[:-5]
            self._validate_sha(fingerprint, "Project Fit filename")
            values.append(self.load_project_fit(project_id, fingerprint))
        return tuple(values)

    def start_cycle(
        self,
        reconciliation,
        project_fit_assessments: tuple,
    ):
        validate_project_semantic_reconciliation_artifact(reconciliation)
        fits = self._validate_cycle_fit_bindings(
            reconciliation,
            project_fit_assessments,
        )

        existing = self.find_cycle_by_reconciliation(
            reconciliation.project_id,
            reconciliation.content_fingerprint,
        )
        if existing is not None:
            return existing

        for fit in fits:
            self.publish_project_fit(fit)

        cycle_id = self.next_cycle_id(reconciliation.project_id)
        manifest = create_cycle_manifest(
            project_id=reconciliation.project_id,
            reconciliation_cycle_id=cycle_id,
            source_ids=reconciliation.source_ids,
            project_fit_fingerprints=tuple(
                sorted(
                    fit.assessment_fingerprint
                    for fit in fits
                )
            ),
            semantic_reconciliation_fingerprint=(
                reconciliation.content_fingerprint
            ),
            created_at=self._timestamp(),
        )

        directory = self._cycle_dir(
            reconciliation.project_id,
            cycle_id,
        )
        if directory.exists() or directory.is_symlink():
            raise ProjectReconciliationPersistenceIntegrityError(
                "Project Reconciliation cycle path is occupied."
            )
        self._ensure_directory(directory.parent)
        temp = directory.parent / (
            f".{cycle_id}.tmp-{uuid.uuid4().hex}"
        )
        if temp.exists() or temp.is_symlink():
            raise ProjectReconciliationPersistenceIntegrityError(
                "Temporary Project Reconciliation cycle path is occupied."
            )
        temp.mkdir()
        try:
            (temp / "manifest.json").write_text(
                cycle_manifest_to_json(manifest),
                encoding="utf-8",
            )
            (temp / "semantic_reconciliation.json").write_text(
                project_semantic_reconciliation_to_json(reconciliation),
                encoding="utf-8",
            )
            temp.replace(directory)
        finally:
            if temp.exists():
                for child in temp.iterdir():
                    child.unlink()
                temp.rmdir()

        loaded = self.load_cycle(
            reconciliation.project_id,
            cycle_id,
        )
        loaded_reconciliation = self.load_semantic_reconciliation(
            reconciliation.project_id,
            cycle_id,
        )
        if (
            loaded != manifest
            or loaded_reconciliation != reconciliation
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted Project Reconciliation cycle differs from source."
            )
        return loaded

    def next_cycle_id(self, project_id: str):
        cycles = self.list_cycles(project_id)
        occupied = [
            int(item.reconciliation_cycle_id.split("-")[1])
            for item in cycles
        ]
        value = 1 if not occupied else max(occupied) + 1
        if value > 999999:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Reconciliation cycle ID space exhausted."
            )
        return f"PRC-{value:06d}"

    def list_cycles(self, project_id: str):
        directory = self._project_root(project_id) / "cycles"
        if not directory.exists():
            return ()
        self._require_directory(
            directory,
            "Project Reconciliation cycles directory",
        )
        values = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            match = _CYCLE.fullmatch(path.name)
            if (
                match is None
                or not path.is_dir()
                or path.is_symlink()
            ):
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Unexpected Project Reconciliation cycle entry."
                )
            values.append(self.load_cycle(project_id, path.name))
        return tuple(values)

    def latest_cycle(self, project_id: str):
        values = self.list_cycles(project_id)
        return None if not values else values[-1]

    def find_cycle_by_reconciliation(
        self,
        project_id: str,
        reconciliation_fingerprint: str,
    ):
        self._validate_sha(
            reconciliation_fingerprint,
            "reconciliation_fingerprint",
        )
        matches = [
            item
            for item in self.list_cycles(project_id)
            if getattr(
                item,
                "semantic_reconciliation_fingerprint",
                None,
            )
            == reconciliation_fingerprint
        ]
        if len(matches) > 1:
            raise ProjectReconciliationPersistenceIntegrityError(
                "More than one cycle binds the same S3 artifact."
            )
        return None if not matches else matches[0]

    def load_cycle(self, project_id: str, cycle_id: str):
        self._validate_cycle_id(cycle_id)
        path = self._cycle_dir(project_id, cycle_id) / "manifest.json"
        self._require_file(path, "Project Reconciliation cycle manifest")
        text = path.read_text(encoding="utf-8")
        try:
            raw_manifest = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Reconciliation cycle manifest must be valid JSON."
            ) from exc
        if (
            isinstance(raw_manifest, dict)
            and raw_manifest.get("schema_version")
            == PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION
        ):
            value = case_cycle_manifest_from_json(text)
        else:
            value = cycle_manifest_from_json(text)
        if (
            value.project_id != project_id
            or value.reconciliation_cycle_id != cycle_id
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Project Reconciliation cycle binding is invalid."
            )
        return value

    def load_semantic_reconciliation(
        self,
        project_id: str,
        cycle_id: str,
    ):
        manifest = self.load_cycle(project_id, cycle_id)
        if (
            getattr(manifest, "schema_version", None)
            == PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Concern-centric Project Reconciliation cycle has no "
                "legacy semantic_reconciliation artifact."
            )
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "semantic_reconciliation.json"
        )
        self._require_file(path, "Project Semantic Reconciliation")
        value = project_semantic_reconciliation_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.content_fingerprint
            != manifest.semantic_reconciliation_fingerprint
            or value.source_ids != manifest.source_ids
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted S3 artifact does not bind the cycle manifest."
            )

        expected_fit_fingerprints = tuple(
            sorted(
                {
                    subject.project_fit_fingerprint
                    for subject in value.subjects
                }
            )
        )
        if (
            expected_fit_fingerprints
            != manifest.project_fit_fingerprints
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Cycle Project Fit fingerprints differ from exact S3 provenance."
            )

        fits = {
            fingerprint: self.load_project_fit(
                project_id,
                fingerprint,
            )
            for fingerprint in manifest.project_fit_fingerprints
        }
        for subject in value.subjects:
            fit = fits[subject.project_fit_fingerprint]
            if (
                fit.source_id != subject.source_id
                or fit.source_projection_id
                != subject.source_projection_id
            ):
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Persisted S2/S3 source provenance is inconsistent."
                )
        return value

    def load_semantic_index(
        self,
        project_id: str,
        cycle_id: str,
    ):
        manifest = self.load_cycle(project_id, cycle_id)
        if (
            getattr(manifest, "schema_version", None)
            != PROJECT_RECONCILIATION_CASE_CYCLE_SCHEMA_VERSION
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Legacy Project Reconciliation cycle has no "
                "concern-centric semantic index."
            )
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "semantic_index.json"
        )
        self._require_file(path, "Project Semantic Index")
        value = semantic_index_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.input_fingerprint
            != manifest.semantic_input_fingerprint
            or value.content_fingerprint
            != manifest.semantic_index_fingerprint
            or value.source_ids != manifest.source_ids
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted semantic index does not bind the V2 cycle."
            )
        return value

    def load_case_assessments(
        self,
        project_id: str,
        cycle_id: str,
    ):
        manifest = self.load_cycle(project_id, cycle_id)
        semantic_index = self.load_semantic_index(
            project_id,
            cycle_id,
        )
        directory = (
            self._cycle_dir(project_id, cycle_id)
            / "case_assessments"
        )
        if (
            not directory.exists()
            or not directory.is_dir()
            or directory.is_symlink()
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Case assessment directory is unavailable."
            )

        paths = tuple(
            sorted(directory.iterdir(), key=lambda item: item.name)
        )
        expected_names = tuple(
            f"{case.case_id}.json"
            for case in semantic_index.cases
        )
        if (
            tuple(path.name for path in paths) != expected_names
            or any(
                not path.is_file() or path.is_symlink()
                for path in paths
            )
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Case assessment repository population is invalid."
            )

        values = tuple(
            case_assessment_from_json(
                path.read_text(encoding="utf-8")
            )
            for path in paths
        )
        if tuple(
            value.content_fingerprint for value in values
        ) != manifest.case_assessment_fingerprints:
            raise ProjectReconciliationPersistenceIntegrityError(
                "Case assessment fingerprints differ from V2 manifest."
            )

        for case, assessment in zip(
            semantic_index.cases,
            values,
        ):
            if (
                assessment.case_id != case.case_id
                or assessment.case_fingerprint
                != case.case_fingerprint
                or assessment.member_subject_refs
                != case.member_subject_refs
                or assessment.source_ids != case.source_ids
            ):
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Persisted Case assessment does not bind its "
                    "exact indexed Case."
                )
        return values

    def load_reconciliation_summary(
        self,
        project_id: str,
        cycle_id: str,
    ):
        manifest = self.load_cycle(project_id, cycle_id)
        semantic_index = self.load_semantic_index(
            project_id,
            cycle_id,
        )
        assessments = self.load_case_assessments(
            project_id,
            cycle_id,
        )
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "reconciliation_summary.json"
        )
        self._require_file(path, "Project Reconciliation Summary")
        value = reconciliation_summary_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.semantic_index_fingerprint
            != semantic_index.content_fingerprint
            or value.content_fingerprint
            != manifest.reconciliation_summary_fingerprint
            or value.case_count != len(assessments)
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted reconciliation summary does not bind "
                "the exact V2 cycle."
            )
        return value

    def publish_authority_bindings(
        self,
        project_id: str,
        cycle_id: str,
        bindings: tuple,
    ) -> ProjectAuthorityBindingSnapshot:
        reconciliation = self.load_semantic_reconciliation(
            project_id,
            cycle_id,
        )
        value = create_binding_snapshot(
            reconciliation,
            bindings,
        )
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "bindings.json"
        )
        self._publish_exact(
            path,
            binding_snapshot_to_json(value, reconciliation),
            loader=lambda: self.load_authority_bindings(
                project_id,
                cycle_id,
            ),
            expected=value,
            label="Project Authority binding snapshot",
        )
        return self.load_authority_bindings(project_id, cycle_id)

    def load_authority_bindings(
        self,
        project_id: str,
        cycle_id: str,
    ) -> ProjectAuthorityBindingSnapshot:
        reconciliation = self.load_semantic_reconciliation(
            project_id,
            cycle_id,
        )
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "bindings.json"
        )
        self._require_file(path, "Project Authority binding snapshot")
        value = binding_snapshot_from_json(
            path.read_text(encoding="utf-8"),
            reconciliation,
        )
        return value

    def load_authority_bindings_if_available(
        self,
        project_id: str,
        cycle_id: str,
    ):
        self.load_cycle(project_id, cycle_id)
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "bindings.json"
        )
        self._reject_symlink(path, "Project Authority binding snapshot")
        if not path.exists():
            return None
        return self.load_authority_bindings(project_id, cycle_id)

    def load_authority_state_if_available(
        self,
        project_id: str,
        cycle_id: str,
    ):
        self.load_cycle(project_id, cycle_id)
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "state.json"
        )
        self._reject_symlink(path, "Project Engineering Authority State")
        if not path.exists():
            return None
        return self.load_authority_state(project_id, cycle_id)

    def load_model_impact_if_available(
        self,
        project_id: str,
        cycle_id: str,
    ):
        self.load_cycle(project_id, cycle_id)
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "model_impact.json"
        )
        self._reject_symlink(path, "Model Impact Reconciliation")
        if not path.exists():
            return None
        return self.load_model_impact(project_id, cycle_id)

    def next_authority_decision_id(
        self,
        project_id: str,
        cycle_id: str,
    ):
        values = self.list_authority_decisions(project_id, cycle_id)
        occupied = [
            int(item.decision_id.split("-")[1])
            for item in values
        ]
        sequence = 1 if not occupied else max(occupied) + 1
        if sequence > 999999:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Authority Decision ID space exhausted."
            )
        return f"PEAD-{sequence:06d}"

    def next_authority_concern_id(
        self,
        project_id: str,
        cycle_id: str,
    ):
        occupied = []
        for item in self.list_authority_decisions(
            project_id,
            cycle_id,
        ):
            if item.authority_concern_id is None:
                continue
            match = _CONCERN.fullmatch(item.authority_concern_id)
            if match is None:
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Persisted Project Authority concern ID is invalid."
                )
            occupied.append(int(match.group(1)))
        sequence = 1 if not occupied else max(occupied) + 1
        if sequence > 999999:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Authority Concern ID space exhausted."
            )
        return f"PEAC-{sequence:06d}"

    def record_authority_decision(
        self,
        project_id: str,
        cycle_id: str,
        decision,
    ):
        reconciliation = self.load_semantic_reconciliation(
            project_id,
            cycle_id,
        )
        binding_snapshot = self.load_authority_bindings(
            project_id,
            cycle_id,
        )
        text = project_authority_decision_to_json(
            decision,
            reconciliation,
            binding_snapshot.bindings,
        )
        existing = self.list_authority_decisions(
            project_id,
            cycle_id,
        )
        pair = (
            decision.left_subject_ref,
            decision.right_subject_ref,
        )
        for item in existing:
            if item.decision_id == decision.decision_id:
                if item != decision:
                    raise ProjectReconciliationPersistenceIntegrityError(
                        "Existing Project Authority Decision ID differs."
                    )
                return item
            if (
                item.left_subject_ref,
                item.right_subject_ref,
            ) == pair:
                raise ProjectReconciliationPersistenceIntegrityError(
                    "One S3 relation may receive only one immutable Human "
                    "Project Authority Decision per cycle."
                )

        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "decisions"
            / f"{decision.decision_id}.json"
        )
        self._atomic_publish(
            path,
            text,
            label="Project Authority Decision",
        )
        return self.load_authority_decision(
            project_id,
            cycle_id,
            decision.decision_id,
        )

    def load_authority_decision(
        self,
        project_id: str,
        cycle_id: str,
        decision_id: str,
    ):
        if _DECISION.fullmatch(decision_id) is None:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Authority Decision ID is invalid."
            )
        reconciliation = self.load_semantic_reconciliation(
            project_id,
            cycle_id,
        )
        bindings = self.load_authority_bindings(
            project_id,
            cycle_id,
        ).bindings
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "decisions"
            / f"{decision_id}.json"
        )
        self._require_file(path, "Project Authority Decision")
        value = project_authority_decision_from_json(
            path.read_text(encoding="utf-8"),
            reconciliation,
            bindings,
        )
        if value.decision_id != decision_id:
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted Project Authority Decision ID differs from path."
            )
        return value

    def list_authority_decisions(
        self,
        project_id: str,
        cycle_id: str,
    ):
        directory = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "decisions"
        )
        if not directory.exists():
            return ()
        self._require_directory(
            directory,
            "Project Authority decisions directory",
        )
        values = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if (
                path.is_symlink()
                or not path.is_file()
                or not path.name.endswith(".json")
            ):
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Unexpected Project Authority Decision entry."
                )
            decision_id = path.name[:-5]
            if _DECISION.fullmatch(decision_id) is None:
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Unexpected Project Authority Decision filename."
                )
            values.append(
                self.load_authority_decision(
                    project_id,
                    cycle_id,
                    decision_id,
                )
            )
        return tuple(values)

    def publish_authority_state(
        self,
        project_id: str,
        cycle_id: str,
        state,
    ):
        validate_project_engineering_authority_state(state)
        reconciliation = self.load_semantic_reconciliation(
            project_id,
            cycle_id,
        )
        binding_snapshot = self.load_authority_bindings(
            project_id,
            cycle_id,
        )
        decisions = self.list_authority_decisions(
            project_id,
            cycle_id,
        )
        if (
            state.project_id != project_id
            or state.reconciliation_fingerprint
            != reconciliation.content_fingerprint
            or state.bindings != binding_snapshot.bindings
            or state.decisions != decisions
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "S4 state does not bind exact persisted cycle authority."
            )

        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "state.json"
        )
        self._publish_exact(
            path,
            project_engineering_authority_to_json(state),
            loader=lambda: self.load_authority_state(
                project_id,
                cycle_id,
            ),
            expected=state,
            label="Project Engineering Authority State",
        )
        return self.load_authority_state(project_id, cycle_id)

    def load_authority_state(
        self,
        project_id: str,
        cycle_id: str,
    ):
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "authority"
            / "state.json"
        )
        self._require_file(path, "Project Engineering Authority State")
        value = project_engineering_authority_state_from_json(
            path.read_text(encoding="utf-8")
        )
        reconciliation = self.load_semantic_reconciliation(
            project_id,
            cycle_id,
        )
        if (
            value.project_id != project_id
            or value.reconciliation_fingerprint
            != reconciliation.content_fingerprint
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted S4 state does not bind exact cycle."
            )
        binding_snapshot = self.load_authority_bindings(
            project_id,
            cycle_id,
        )
        decisions = self.list_authority_decisions(
            project_id,
            cycle_id,
        )
        if (
            value.bindings != binding_snapshot.bindings
            or value.decisions != decisions
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted S4 state differs from frozen bindings or "
                "Human decision history."
            )
        return value

    def publish_model_impact(
        self,
        project_id: str,
        cycle_id: str,
        artifact,
    ):
        validate_model_impact_reconciliation_artifact(artifact)
        state = self.load_authority_state(project_id, cycle_id)
        if (
            artifact.project_id != project_id
            or artifact.project_authority_fingerprint
            != state.content_fingerprint
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "S5 artifact does not bind exact persisted S4 authority."
            )

        path = (
            self._cycle_dir(project_id, cycle_id)
            / "model_impact.json"
        )
        self._publish_exact(
            path,
            model_impact_reconciliation_to_json(artifact),
            loader=lambda: self.load_model_impact(
                project_id,
                cycle_id,
            ),
            expected=artifact,
            label="Model Impact Reconciliation",
        )
        return self.load_model_impact(project_id, cycle_id)

    def load_model_impact(
        self,
        project_id: str,
        cycle_id: str,
    ):
        path = (
            self._cycle_dir(project_id, cycle_id)
            / "model_impact.json"
        )
        self._require_file(path, "Model Impact Reconciliation")
        value = model_impact_reconciliation_from_json(
            path.read_text(encoding="utf-8")
        )
        state = self.load_authority_state(project_id, cycle_id)
        if (
            value.project_id != project_id
            or value.project_authority_fingerprint
            != state.content_fingerprint
        ):
            raise ProjectReconciliationPersistenceIntegrityError(
                "Persisted S5 artifact does not bind exact S4 state."
            )
        return value

    def _validate_cycle_fit_bindings(
        self,
        reconciliation,
        assessments,
    ):
        if not isinstance(assessments, tuple) or not assessments:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Reconciliation cycle requires Project Fit tuple."
            )
        by_fingerprint = {}
        for assessment in assessments:
            validate_project_fit_assessment(assessment)
            if assessment.project_id != reconciliation.project_id:
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Project Fit assessment crosses cycle Project boundary."
                )
            if derive_project_fit_gate_state(assessment) != "admitted":
                raise ProjectReconciliationPersistenceIntegrityError(
                    "S3 cycle may bind only admitted engineering Sources."
                )
            if assessment.assessment_fingerprint in by_fingerprint:
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Duplicate Project Fit fingerprint in cycle input."
                )
            by_fingerprint[assessment.assessment_fingerprint] = assessment

        expected_fingerprints = {
            subject.project_fit_fingerprint
            for subject in reconciliation.subjects
        }
        if set(by_fingerprint) != expected_fingerprints:
            raise ProjectReconciliationPersistenceIntegrityError(
                "Cycle Project Fit set does not match exact S3 provenance."
            )

        for subject in reconciliation.subjects:
            fit = by_fingerprint[subject.project_fit_fingerprint]
            if (
                fit.source_id != subject.source_id
                or fit.source_projection_id
                != subject.source_projection_id
            ):
                raise ProjectReconciliationPersistenceIntegrityError(
                    "S3 Subject Project Fit provenance is inconsistent."
                )

        return tuple(
            sorted(
                assessments,
                key=lambda item: item.assessment_fingerprint,
            )
        )

    def _project_root(self, project_id: str):
        if not isinstance(project_id, str) or not project_id.strip():
            raise ProjectReconciliationPersistenceValidationError(
                "project_id is required."
            )
        if any(ch in project_id for ch in ("/", "\\", "\x00")):
            raise ProjectReconciliationPersistenceValidationError(
                "project_id contains unsafe path characters."
            )
        return self.root / project_id / "project_reconciliation"

    def _cycle_dir(self, project_id: str, cycle_id: str):
        self._validate_cycle_id(cycle_id)
        return self._project_root(project_id) / "cycles" / cycle_id

    @staticmethod
    def _validate_cycle_id(value):
        if _CYCLE.fullmatch(value) is None:
            raise ProjectReconciliationPersistenceValidationError(
                "Project Reconciliation cycle ID is invalid."
            )

    @staticmethod
    def _validate_sha(value, label):
        if not isinstance(value, str) or _SHA.fullmatch(value) is None:
            raise ProjectReconciliationPersistenceValidationError(
                f"{label} must be a SHA-256 fingerprint."
            )

    def _publish_exact(
        self,
        path: Path,
        text: str,
        *,
        loader,
        expected,
        label: str,
    ):
        if path.exists():
            self._reject_symlink(path, label)
            loaded = loader()
            if loaded != expected:
                raise ProjectReconciliationPersistenceIntegrityError(
                    f"Existing {label} differs from requested content."
                )
            return loaded
        self._atomic_publish(path, text, label=label)
        loaded = loader()
        if loaded != expected:
            raise ProjectReconciliationPersistenceIntegrityError(
                f"Persisted {label} differs from requested content."
            )
        return loaded

    def _atomic_publish(self, path: Path, text: str, *, label: str):
        self._ensure_directory(path.parent)
        self._reject_symlink(path.parent, f"{label} directory")
        if path.exists() or path.is_symlink():
            raise ProjectReconciliationPersistenceIntegrityError(
                f"{label} path is occupied."
            )
        temp = path.parent / f".{path.name}.tmp-{uuid.uuid4().hex}"
        try:
            temp.write_text(text, encoding="utf-8")
            temp.replace(path)
        finally:
            if temp.exists():
                temp.unlink()

    def _ensure_directory(self, path: Path):
        current = path
        missing = []
        while not current.exists():
            missing.append(current)
            if current == current.parent:
                break
            current = current.parent
        if current.exists() and current.is_symlink():
            raise ProjectReconciliationPersistenceIntegrityError(
                "Repository path traverses a symlink."
            )
        for item in reversed(missing):
            try:
                item.mkdir()
            except FileExistsError:
                pass
            if item.is_symlink() or not item.is_dir():
                raise ProjectReconciliationPersistenceIntegrityError(
                    "Repository directory creation is unsafe."
                )

    @staticmethod
    def _reject_symlink(path: Path, label: str):
        if path.is_symlink():
            raise ProjectReconciliationPersistenceIntegrityError(
                f"{label} path must not be a symlink."
            )

    def _require_file(self, path: Path, label: str):
        self._reject_symlink(path, label)
        if not path.is_file():
            raise ProjectReconciliationPersistenceValidationError(
                f"{label} not found."
            )

    def _require_directory(self, path: Path, label: str):
        self._reject_symlink(path, label)
        if not path.is_dir():
            raise ProjectReconciliationPersistenceIntegrityError(
                f"{label} is not a directory."
            )

    def _timestamp(self):
        value = self._clock()
        if value.tzinfo is None:
            raise ProjectReconciliationPersistenceValidationError(
                "Repository clock must return timezone-aware datetime."
            )
        return value.astimezone(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )
