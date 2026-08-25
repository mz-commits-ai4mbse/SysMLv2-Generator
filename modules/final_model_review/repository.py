"""Atomic project-local persistence for Phase-L Final Model Review."""

from __future__ import annotations

from modules.sysml_generation.authority_backed import (
    AuthorityBackedGeneratedSysMLArtifactSet,
)
from modules.sysml_validation.authority_backed import (
    validate_authority_backed_artifact_integrity,
)

from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import uuid

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT
from modules.sysml_validation.artifact_integrity import (
    calculate_received_artifact_set_fingerprint,
    validate_artifact_set_integrity,
)
from modules.sysml_validation.service import validate_validation_result_integrity

from .change_proposal import (
    final_model_review_change_proposal_from_json,
    final_model_review_change_proposal_to_json,
    validate_final_model_review_change_proposal,
)
from .contracts import (
    create_final_model_review_decision_target,
    create_final_model_review_manifest,
    create_final_model_review_revision,
    validate_final_model_review_decision,
    validate_final_model_review_item,
)
from .errors import (
    FinalModelReviewIntegrityError,
    FinalModelReviewNotFoundError,
    FinalModelReviewPersistenceError,
)
from .identifiers import (
    next_final_model_review_id,
    validate_final_model_review_change_proposal_id,
    next_final_model_review_revision_id,
    validate_final_model_review_decision_id,
    validate_final_model_review_id,
    validate_final_model_review_item_id,
    validate_final_model_review_revision_id,
)
from .release_gate import require_final_model_review_ready_for_approval
from .paths import (
    final_model_review_change_proposal_path,
    final_model_review_change_proposals_path,
    final_model_review_decision_path,
    final_model_review_decisions_path,
    final_model_review_item_path,
    final_model_review_manifest_path,
    final_model_review_path,
    final_model_review_revision_items_path,
    final_model_review_revision_path,
    final_model_review_revisions_path,
    final_model_reviews_path,
)
from .serialization import (
    create_revision_storage_manifest,
    final_model_review_decision_from_json,
    final_model_review_decision_to_json,
    final_model_review_item_from_json,
    final_model_review_item_to_json,
    final_model_review_manifest_from_json,
    final_model_review_manifest_to_json,
    final_model_review_revision_from_json,
    final_model_review_revision_to_json,
    revision_storage_manifest_from_json,
    revision_storage_manifest_to_json,
)
from .types import (
    FinalModelGeneratedUnitReference,
    FinalModelReviewChangeProposal,
    FinalModelReviewDecision,
    FinalModelReviewEvidenceReference,
    FinalModelReviewItem,
    FinalModelReviewManifest,
    FinalModelReviewRepositoryIssue,
    FinalModelReviewRepositoryScanResult,
    FinalModelReviewRevisionBundle,
    FinalModelReviewStoredFileReference,
    FinalModelReviewStoredGeneratedUnit,
)

_REVIEW = re.compile(r"^(FMR-[0-9]{6})$")
_REVISION = re.compile(r"^(FRV-[0-9]{6})$")
_ITEM = re.compile(r"^(FRI-[0-9]{6})\.json$")
_DECISION = re.compile(r"^(FRD-[0-9]{6})\.json$")
_CHANGE_PROPOSAL = re.compile(r"^(FCP-[0-9]{6})\.json$")
_TEMP = re.compile(r"^\..+\.tmp-[A-Za-z0-9-]+$")


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _default_artifact_validator(artifact_set) -> None:
    if isinstance(
        artifact_set,
        AuthorityBackedGeneratedSysMLArtifactSet,
    ):
        findings = validate_authority_backed_artifact_integrity(
            artifact_set
        )
        if any(item.blocking for item in findings):
            raise FinalModelReviewIntegrityError(
                "Authority-backed generated SysML artifact fails "
                "standalone integrity validation."
            )
        return

    if any(
        item.blocking
        for item in validate_artifact_set_integrity(artifact_set)
    ):
        raise FinalModelReviewIntegrityError(
            "Generated SysML artifact fails standalone integrity validation."
        )
    if (
        calculate_received_artifact_set_fingerprint(artifact_set)
        != artifact_set.content_fingerprint
    ):
        raise FinalModelReviewIntegrityError(
            "Generated SysML artifact fingerprint mismatch."
        )


def _default_validation_result_validator(validation_result) -> None:
    validate_validation_result_integrity(validation_result)


class FinalModelReviewRepository:
    """Persist immutable review evidence; never publish final project output."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        workspace=None,
        clock: Callable[[], datetime] = _default_clock,
        artifact_validator: Callable[[object], None] = _default_artifact_validator,
        validation_result_validator: Callable[[object], None] = _default_validation_result_validator,
        rename: Callable = os.rename,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(root=self.root, clock=clock) if workspace is None else workspace
        self._artifact_validator = artifact_validator
        self._validation_result_validator = validation_result_validator
        self._rename = rename

    def create_review(self, project_id: str) -> FinalModelReviewManifest:
        self._workspace.load_project(project_id)
        scan = self.scan(project_id)
        review_id = next_final_model_review_id(
            item.final_model_review_id for item in scan.review_manifests
        )
        manifest = create_final_model_review_manifest(
            project_id=project_id,
            final_model_review_id=review_id,
            created_at=self._timestamp(),
        )
        parent = final_model_reviews_path(self.root, project_id)
        self._ensure_dir(parent)
        final = final_model_review_path(self.root, project_id, review_id)
        temp = parent / f".{review_id}.tmp-{uuid.uuid4().hex}"
        if final.exists() or final.is_symlink():
            raise FinalModelReviewPersistenceError("Final Model Review path is occupied.")
        temp.mkdir()
        (temp / "revisions").mkdir()
        (temp / "decisions").mkdir()
        (temp / "change_proposals").mkdir()
        self._write_text(temp / "manifest.json", final_model_review_manifest_to_json(manifest))
        self._rename(temp, final)
        return self.load_review(project_id, review_id)

    def load_review(self, project_id: str, review_id: str) -> FinalModelReviewManifest:
        self._workspace.load_project(project_id)
        review_id = validate_final_model_review_id(review_id)
        path = final_model_review_manifest_path(self.root, project_id, review_id)
        self._require_file(path, "Final Model Review manifest")
        return final_model_review_manifest_from_json(
            self._read_text(path),
            expected_project_id=project_id,
            expected_review_id=review_id,
        )

    def append_revision(
        self,
        project_id: str,
        review_id: str,
        *,
        artifact_set,
        validation_result,
        evidence_references: tuple[FinalModelReviewEvidenceReference, ...] = (),
    ) -> FinalModelReviewRevisionBundle:
        manifest = self.load_review(project_id, review_id)
        self._artifact_validator(artifact_set)
        self._validation_result_validator(validation_result)
        self._subject_binding(project_id, artifact_set, validation_result)
        existing = self.list_revisions(project_id, review_id)
        revision_id = next_final_model_review_revision_id(
            item.revision.final_model_review_revision_id for item in existing
        )
        predecessor = None if not existing else existing[-1].revision.final_model_review_revision_id
        generated = tuple(
            FinalModelGeneratedUnitReference(
                generated_unit_id=unit.unit_id,
                relative_path=unit.relative_path,
                content_fingerprint=unit.content_fingerprint,
            )
            for unit in sorted(artifact_set.units, key=lambda item: item.unit_id)
        )
        revision = create_final_model_review_revision(
            project_id=project_id,
            final_model_review_id=manifest.final_model_review_id,
            final_model_review_revision_id=revision_id,
            predecessor_revision_id=predecessor,
            source_internal_engineering_model_id=artifact_set.source_internal_engineering_model_id,
            generated_artifact_set_fingerprint=artifact_set.content_fingerprint,
            validation_result_fingerprint=validation_result.content_fingerprint,
            validation_status=validation_result.validation_status,
            publication_gate=validation_result.publication_gate,
            generated_units=generated,
            evidence_references=evidence_references,
            created_at=self._timestamp(),
        )
        self._publish_revision(revision, artifact_set, validation_result)
        return self.load_revision(project_id, review_id, revision_id)

    def list_revisions(self, project_id: str, review_id: str) -> tuple[FinalModelReviewRevisionBundle, ...]:
        self.load_review(project_id, review_id)
        directory = final_model_review_revisions_path(self.root, project_id, review_id)
        self._require_dir(directory, "Final Model Review revisions")
        result = []
        for entry in sorted(directory.iterdir(), key=lambda p: p.name):
            match = _REVISION.fullmatch(entry.name)
            if match is None:
                raise FinalModelReviewIntegrityError("Final Model Review revisions contain an unexpected or interrupted entry.")
            result.append(self.load_revision(project_id, review_id, match.group(1)))
        return tuple(result)

    def load_revision(self, project_id: str, review_id: str, revision_id: str) -> FinalModelReviewRevisionBundle:
        self._workspace.load_project(project_id)
        review_id = validate_final_model_review_id(review_id)
        revision_id = validate_final_model_review_revision_id(revision_id)
        directory = final_model_review_revision_path(self.root, project_id, review_id, revision_id)
        self._require_dir(directory, "Final Model Review revision")
        storage = revision_storage_manifest_from_json(
            self._read_text(directory / "storage_manifest.json"),
            expected_project_id=project_id,
            expected_review_id=review_id,
            expected_revision_id=revision_id,
        )
        expected = {item.relative_path: item for item in storage.files}
        actual = self._bundle_files(directory)
        actual.discard("storage_manifest.json")
        if set(expected) != actual:
            raise FinalModelReviewIntegrityError("Revision bundle file set does not match storage manifest.")
        for relative, reference in expected.items():
            path = directory.joinpath(*PurePosixPath(relative).parts)
            self._require_file(path, "Final Model Review revision file")
            if self._sha(path.read_bytes()) != reference.content_fingerprint:
                raise FinalModelReviewIntegrityError(f"Stored file fingerprint mismatch: {relative}.")
        revision = final_model_review_revision_from_json(
            self._read_text(directory / "revision.json"),
            expected_project_id=project_id,
            expected_review_id=review_id,
            expected_revision_id=revision_id,
        )
        if revision.content_fingerprint != storage.revision_content_fingerprint:
            raise FinalModelReviewIntegrityError("Revision fingerprint does not match storage manifest.")
        artifact = self._read_json(directory / "artifact_set.json", "artifact-set snapshot")
        validation = self._read_json(directory / "validation_result.json", "validation-result snapshot")
        self._snapshot_binding(revision, artifact, validation)
        units = []
        for ref in revision.generated_units:
            path = (directory / "generated").joinpath(*PurePosixPath(ref.relative_path).parts)
            content = self._read_text(path)
            digest = self._sha(content.encode("utf-8"))
            if digest != ref.content_fingerprint:
                raise FinalModelReviewIntegrityError("Generated SysML content fingerprint mismatch.")
            units.append(FinalModelReviewStoredGeneratedUnit(ref.generated_unit_id, ref.relative_path, content, digest))
        return FinalModelReviewRevisionBundle(revision, storage, artifact, validation, tuple(units))

    def persist_item(self, item: FinalModelReviewItem) -> FinalModelReviewItem:
        validate_final_model_review_item(item)
        bundle = self.load_revision(
            item.project_id,
            item.final_model_review_id,
            item.final_model_review_revision_id,
        )
        self._validate_item_target(item, bundle)
        directory = final_model_review_revision_items_path(
            self.root, item.project_id, item.final_model_review_id, item.final_model_review_revision_id
        )
        self._ensure_dir(directory)
        path = final_model_review_item_path(
            self.root, item.project_id, item.final_model_review_id,
            item.final_model_review_revision_id, item.final_model_review_item_id
        )
        self._publish_json(path, final_model_review_item_to_json(item), "Final Model Review item")
        return self.load_item(item.project_id, item.final_model_review_id, item.final_model_review_revision_id, item.final_model_review_item_id)

    def load_item(self, project_id: str, review_id: str, revision_id: str, item_id: str) -> FinalModelReviewItem:
        validate_final_model_review_item_id(item_id)
        path = final_model_review_item_path(self.root, project_id, review_id, revision_id, item_id)
        self._require_file(path, "Final Model Review item")
        return final_model_review_item_from_json(
            self._read_text(path), expected_project_id=project_id, expected_review_id=review_id,
            expected_revision_id=revision_id, expected_item_id=item_id
        )

    def list_items(
        self,
        project_id: str,
        review_id: str,
        revision_id: str,
    ) -> tuple[FinalModelReviewItem, ...]:
        """Load every immutable sidecar review item for one exact FRV."""

        self.load_revision(project_id, review_id, revision_id)
        directory = final_model_review_revision_items_path(
            self.root, project_id, review_id, revision_id
        )
        if not directory.exists():
            return ()
        self._require_dir(directory, "Final Model Review items")
        result = []
        for entry in sorted(directory.iterdir(), key=lambda p: p.name):
            match = _ITEM.fullmatch(entry.name)
            if match is None:
                raise FinalModelReviewIntegrityError(
                    "Unexpected Final Model Review item entry."
                )
            result.append(
                self.load_item(
                    project_id, review_id, revision_id, match.group(1)
                )
            )
        return tuple(result)

    def persist_decision(self, decision: FinalModelReviewDecision) -> FinalModelReviewDecision:
        validate_final_model_review_decision(decision)
        review_id = decision.target.final_model_review_id
        revision_id = decision.target.final_model_review_revision_id
        bundle = self.load_revision(decision.project_id, review_id, revision_id)
        expected_target = create_final_model_review_decision_target(bundle.revision)
        if decision.target != expected_target:
            raise FinalModelReviewIntegrityError(
                "Final Model Review decision does not target the exact persisted revision snapshot."
            )
        if decision.decision == "approved_for_publication":
            require_final_model_review_ready_for_approval(
                self,
                decision.project_id,
                review_id,
                revision_id,
            )
        for saved in self.list_decisions(decision.project_id, review_id):
            if saved.decision_fingerprint == decision.decision_fingerprint:
                raise FinalModelReviewIntegrityError(
                    f"Equivalent Final Model Review decision already exists as {saved.final_model_review_decision_id}."
                )
        directory = final_model_review_decisions_path(self.root, decision.project_id, review_id)
        self._ensure_dir(directory)
        path = final_model_review_decision_path(self.root, decision.project_id, review_id, decision.final_model_review_decision_id)
        self._publish_json(path, final_model_review_decision_to_json(decision), "Final Model Review decision")
        return self.load_decision(decision.project_id, review_id, decision.final_model_review_decision_id)

    def load_decision(self, project_id: str, review_id: str, decision_id: str) -> FinalModelReviewDecision:
        validate_final_model_review_decision_id(decision_id)
        path = final_model_review_decision_path(self.root, project_id, review_id, decision_id)
        self._require_file(path, "Final Model Review decision")
        return final_model_review_decision_from_json(
            self._read_text(path), expected_project_id=project_id,
            expected_review_id=review_id, expected_decision_id=decision_id
        )

    def list_decisions(self, project_id: str, review_id: str) -> tuple[FinalModelReviewDecision, ...]:
        self.load_review(project_id, review_id)
        directory = final_model_review_decisions_path(self.root, project_id, review_id)
        self._require_dir(directory, "Final Model Review decisions")
        result=[]
        for entry in sorted(directory.iterdir(), key=lambda p: p.name):
            match=_DECISION.fullmatch(entry.name)
            if match is None:
                raise FinalModelReviewIntegrityError("Unexpected Final Model Review decision entry.")
            result.append(self.load_decision(project_id, review_id, match.group(1)))
        return tuple(result)

    def persist_change_proposal(
        self,
        proposal: FinalModelReviewChangeProposal,
    ) -> FinalModelReviewChangeProposal:
        validate_final_model_review_change_proposal(proposal)
        bundle = self.load_revision(
            proposal.project_id,
            proposal.final_model_review_id,
            proposal.final_model_review_revision_id,
        )
        if proposal.base_revision_content_fingerprint != bundle.revision.content_fingerprint:
            raise FinalModelReviewIntegrityError(
                "Final Model Review change proposal targets a stale revision."
            )
        if proposal.base_review_subject_fingerprint != bundle.revision.review_subject_fingerprint:
            raise FinalModelReviewIntegrityError(
                "Final Model Review change proposal targets a stale review subject."
            )
        for saved in self.list_change_proposals(proposal.project_id):
            if saved.content_fingerprint == proposal.content_fingerprint:
                raise FinalModelReviewIntegrityError(
                    "Equivalent Final Model Review change proposal already exists as "
                    f"{saved.final_model_review_change_proposal_id}."
                )
            if (
                saved.final_model_review_change_proposal_id
                == proposal.final_model_review_change_proposal_id
            ):
                raise FinalModelReviewIntegrityError(
                    "Final Model Review change proposal ID is already occupied."
                )
        directory = final_model_review_change_proposals_path(
            self.root,
            proposal.project_id,
            proposal.final_model_review_id,
        )
        self._ensure_dir(directory)
        path = final_model_review_change_proposal_path(
            self.root,
            proposal.project_id,
            proposal.final_model_review_id,
            proposal.final_model_review_change_proposal_id,
        )
        self._publish_json(
            path,
            final_model_review_change_proposal_to_json(proposal),
            "Final Model Review change proposal",
        )
        return self.load_change_proposal(
            proposal.project_id,
            proposal.final_model_review_id,
            proposal.final_model_review_change_proposal_id,
        )

    def load_change_proposal(
        self,
        project_id: str,
        review_id: str,
        change_proposal_id: str,
    ) -> FinalModelReviewChangeProposal:
        validate_final_model_review_change_proposal_id(change_proposal_id)
        path = final_model_review_change_proposal_path(
            self.root, project_id, review_id, change_proposal_id
        )
        self._require_file(path, "Final Model Review change proposal")
        proposal = final_model_review_change_proposal_from_json(
            self._read_text(path),
            expected_project_id=project_id,
            expected_review_id=review_id,
            expected_change_proposal_id=change_proposal_id,
        )
        bundle = self.load_revision(
            project_id,
            review_id,
            proposal.final_model_review_revision_id,
        )
        if (
            proposal.base_revision_content_fingerprint
            != bundle.revision.content_fingerprint
            or proposal.base_review_subject_fingerprint
            != bundle.revision.review_subject_fingerprint
        ):
            raise FinalModelReviewIntegrityError(
                "Persisted change proposal no longer binds the exact review revision."
            )
        return proposal

    def list_change_proposals(
        self,
        project_id: str,
        review_id: str | None = None,
        revision_id: str | None = None,
    ) -> tuple[FinalModelReviewChangeProposal, ...]:
        self._workspace.load_project(project_id)
        result = []
        if review_id is None:
            root = final_model_reviews_path(self.root, project_id)
            if not root.exists():
                return ()
            review_ids = tuple(
                match.group(1)
                for entry in sorted(root.iterdir(), key=lambda p: p.name)
                if (match := _REVIEW.fullmatch(entry.name)) is not None
            )
        else:
            self.load_review(project_id, review_id)
            review_ids = (review_id,)
        for selected_review_id in review_ids:
            directory = final_model_review_change_proposals_path(
                self.root, project_id, selected_review_id
            )
            if not directory.exists():
                continue
            self._require_dir(directory, "Final Model Review change proposals")
            for entry in sorted(directory.iterdir(), key=lambda p: p.name):
                match = _CHANGE_PROPOSAL.fullmatch(entry.name)
                if match is None:
                    raise FinalModelReviewIntegrityError(
                        "Unexpected Final Model Review change-proposal entry."
                    )
                proposal = self.load_change_proposal(
                    project_id, selected_review_id, match.group(1)
                )
                if (
                    revision_id is not None
                    and proposal.final_model_review_revision_id != revision_id
                ):
                    continue
                result.append(proposal)
        return tuple(
            sorted(
                result,
                key=lambda item: item.final_model_review_change_proposal_id,
            )
        )

    def scan(self, project_id: str) -> FinalModelReviewRepositoryScanResult:
        try:
            self._workspace.load_project(project_id)
            root = final_model_reviews_path(self.root, project_id)
        except Exception as exc:
            return FinalModelReviewRepositoryScanResult(
                issues=(self._issue(project_id, "unsafe_final_model_review_root", str(exc), None),)
            )
        if not root.exists():
            return FinalModelReviewRepositoryScanResult()
        if root.is_symlink() or not root.is_dir():
            return FinalModelReviewRepositoryScanResult(
                issues=(self._issue(project_id, "unsafe_final_model_review_root", "Final Model Review root is not a safe directory.", root),)
            )
        manifests=[]; revisions=[]; items=[]; decisions=[]; change_proposals=[]; issues=[]
        for entry in sorted(root.iterdir(), key=lambda p: p.name):
            if _TEMP.fullmatch(entry.name):
                issues.append(self._issue(project_id, "interrupted_final_model_review_publication", "Interrupted Final Model Review publication exists.", entry))
                continue
            match=_REVIEW.fullmatch(entry.name)
            if match is None:
                issues.append(self._issue(project_id, "unexpected_final_model_review_entry", "Unexpected entry in Final Model Review root.", entry))
                continue
            review_id=match.group(1)
            try:
                manifests.append(self.load_review(project_id, review_id))
                self._scan_review(project_id, review_id, revisions, items, decisions, change_proposals, issues)
            except Exception as exc:
                issues.append(self._issue(project_id, "invalid_final_model_review", str(exc), entry, review_id=review_id))
        return FinalModelReviewRepositoryScanResult(tuple(manifests), tuple(revisions), tuple(items), tuple(decisions), tuple(change_proposals), tuple(issues))

    def _scan_review(self, project_id, review_id, revisions, items, decisions, change_proposals, issues) -> None:
        directory=final_model_review_path(self.root, project_id, review_id)
        expected={"manifest.json","revisions","decisions","change_proposals"}
        for name in sorted({p.name for p in directory.iterdir()} - expected):
            issues.append(self._issue(project_id, "unexpected_final_model_review_entry", "Unexpected entry inside Final Model Review.", directory/name, review_id=review_id))
        revisions_dir=final_model_review_revisions_path(self.root, project_id, review_id)
        if revisions_dir.is_symlink() or not revisions_dir.is_dir():
            raise FinalModelReviewIntegrityError("Final Model Review revisions path is unsafe.")
        for entry in sorted(revisions_dir.iterdir(), key=lambda p:p.name):
            if _TEMP.fullmatch(entry.name):
                issues.append(self._issue(project_id, "interrupted_final_model_review_revision", "Interrupted Final Model Review revision exists.", entry, review_id=review_id))
                continue
            match=_REVISION.fullmatch(entry.name)
            if match is None:
                issues.append(self._issue(project_id, "unexpected_final_model_review_revision_entry", "Unexpected revision-directory entry.", entry, review_id=review_id))
                continue
            revision_id=match.group(1)
            try:
                revisions.append(self.load_revision(project_id, review_id, revision_id))
                items.extend(self._scan_items(project_id, review_id, revision_id, issues))
            except Exception as exc:
                issues.append(self._issue(project_id, "invalid_final_model_review_revision", str(exc), entry, review_id=review_id, revision_id=revision_id))
        decisions_dir=final_model_review_decisions_path(self.root, project_id, review_id)
        if decisions_dir.is_symlink() or not decisions_dir.is_dir():
            raise FinalModelReviewIntegrityError("Final Model Review decisions path is unsafe.")
        for entry in sorted(decisions_dir.iterdir(), key=lambda p:p.name):
            match=_DECISION.fullmatch(entry.name)
            if match is None:
                issues.append(self._issue(project_id, "unexpected_final_model_review_decision_entry", "Unexpected decision-directory entry.", entry, review_id=review_id))
                continue
            try:
                decisions.append(self.load_decision(project_id, review_id, match.group(1)))
            except Exception as exc:
                issues.append(self._issue(project_id, "invalid_final_model_review_decision", str(exc), entry, review_id=review_id, decision_id=match.group(1)))


        change_dir = final_model_review_change_proposals_path(
            self.root, project_id, review_id
        )
        if change_dir.is_symlink() or not change_dir.is_dir():
            raise FinalModelReviewIntegrityError(
                "Final Model Review change-proposals path is unsafe."
            )
        for entry in sorted(change_dir.iterdir(), key=lambda p: p.name):
            match = _CHANGE_PROPOSAL.fullmatch(entry.name)
            if match is None:
                issues.append(
                    self._issue(
                        project_id,
                        "unexpected_final_model_review_change_proposal_entry",
                        "Unexpected change-proposal entry.",
                        entry,
                        review_id=review_id,
                    )
                )
                continue
            try:
                change_proposals.append(
                    self.load_change_proposal(
                        project_id, review_id, match.group(1)
                    )
                )
            except Exception as exc:
                issues.append(
                    self._issue(
                        project_id,
                        "invalid_final_model_review_change_proposal",
                        str(exc),
                        entry,
                        review_id=review_id,
                    )
                )

    def _scan_items(self, project_id, review_id, revision_id, issues):
        directory=final_model_review_revision_items_path(self.root, project_id, review_id, revision_id)
        if not directory.exists():
            return ()
        if directory.is_symlink() or not directory.is_dir():
            issues.append(self._issue(project_id, "unsafe_final_model_review_items_directory", "Final Model Review items path is unsafe.", directory, review_id=review_id, revision_id=revision_id))
            return ()
        result=[]
        for entry in sorted(directory.iterdir(), key=lambda p:p.name):
            match=_ITEM.fullmatch(entry.name)
            if match is None:
                issues.append(self._issue(project_id, "unexpected_final_model_review_item_entry", "Unexpected item-directory entry.", entry, review_id=review_id, revision_id=revision_id))
                continue
            try:
                result.append(self.load_item(project_id, review_id, revision_id, match.group(1)))
            except Exception as exc:
                issues.append(self._issue(project_id, "invalid_final_model_review_item", str(exc), entry, review_id=review_id, revision_id=revision_id, item_id=match.group(1)))
        return tuple(result)

    def _validate_item_target(self, item, bundle) -> None:
        if item.generated_unit_id is None:
            return
        units = {ref.generated_unit_id for ref in bundle.revision.generated_units}
        if item.generated_unit_id not in units:
            raise FinalModelReviewIntegrityError(
                "Final Model Review item targets a generated unit outside its revision."
            )
        if item.generated_symbol_id is None:
            return
        snapshot_units = bundle.artifact_set_snapshot.get("units")
        if not isinstance(snapshot_units, list):
            raise FinalModelReviewIntegrityError(
                "Artifact-set snapshot does not contain generated-unit evidence."
            )
        matches = [
            value for value in snapshot_units
            if isinstance(value, dict)
            and value.get("unit_id") == item.generated_unit_id
        ]
        if len(matches) != 1:
            raise FinalModelReviewIntegrityError(
                "Final Model Review item unit target does not resolve exactly once."
            )
        symbols = matches[0].get("generated_symbol_ids")
        if not isinstance(symbols, list) or item.generated_symbol_id not in symbols:
            raise FinalModelReviewIntegrityError(
                "Final Model Review item symbol target is not present in the persisted artifact snapshot."
            )

    def _publish_revision(self, revision, artifact_set, validation_result) -> None:
        final=final_model_review_revision_path(self.root, revision.project_id, revision.final_model_review_id, revision.final_model_review_revision_id)
        self._ensure_dir(final.parent)
        temp=final.parent / f".{revision.final_model_review_revision_id}.tmp-{uuid.uuid4().hex}"
        if final.exists() or final.is_symlink():
            raise FinalModelReviewPersistenceError("Final Model Review revision path is occupied.")
        temp.mkdir(); (temp/"generated").mkdir(); (temp/"items").mkdir()
        refs=[]
        self._store(temp,"revision.json",final_model_review_revision_to_json(revision).encode(),"revision",refs)
        self._store(temp,"artifact_set.json",self._snapshot_json(artifact_set).encode(),"artifact_set_snapshot",refs)
        self._store(temp,"validation_result.json",self._snapshot_json(validation_result).encode(),"validation_result_snapshot",refs)
        by_id={u.unit_id:u for u in artifact_set.units}
        for unit_ref in revision.generated_units:
            unit=by_id[unit_ref.generated_unit_id]
            self._store(temp,f"generated/{unit_ref.relative_path}",unit.content.encode("utf-8"),"generated_sysml_unit",refs,unit_ref.generated_unit_id)
        refs=tuple(sorted(refs,key=lambda item:item.relative_path))
        storage=create_revision_storage_manifest(
            project_id=revision.project_id,
            final_model_review_id=revision.final_model_review_id,
            final_model_review_revision_id=revision.final_model_review_revision_id,
            revision_content_fingerprint=revision.content_fingerprint,
            files=refs,
        )
        self._write_text(temp/"storage_manifest.json",revision_storage_manifest_to_json(storage))
        # Complete byte-level verification before the atomic directory rename.
        for ref in storage.files:
            path=temp.joinpath(*PurePosixPath(ref.relative_path).parts)
            self._require_file(path,"temporary Final Model Review revision file")
            if self._sha(path.read_bytes()) != ref.content_fingerprint:
                raise FinalModelReviewIntegrityError("Temporary revision file fingerprint mismatch.")
        self._rename(temp,final)

    def _subject_binding(self, project_id, artifact_set, validation_result) -> None:
        if artifact_set.project_id != project_id or validation_result.project_id != project_id:
            raise FinalModelReviewIntegrityError("Review subject Project mismatch.")
        if validation_result.source_internal_engineering_model_id != artifact_set.source_internal_engineering_model_id:
            raise FinalModelReviewIntegrityError("Validation result source IEM does not match artifact set.")
        if validation_result.source_artifact_set_fingerprint != artifact_set.content_fingerprint:
            raise FinalModelReviewIntegrityError("Validation result does not cover the exact artifact set.")

    def _snapshot_binding(self, revision, artifact, validation) -> None:
        checks=(
            (artifact,"project_id",revision.project_id),(artifact,"source_internal_engineering_model_id",revision.source_internal_engineering_model_id),
            (artifact,"content_fingerprint",revision.generated_artifact_set_fingerprint),(validation,"project_id",revision.project_id),
            (validation,"source_internal_engineering_model_id",revision.source_internal_engineering_model_id),
            (validation,"source_artifact_set_fingerprint",revision.generated_artifact_set_fingerprint),
            (validation,"content_fingerprint",revision.validation_result_fingerprint),(validation,"validation_status",revision.validation_status),
            (validation,"publication_gate",revision.publication_gate),
        )
        for payload,key,expected in checks:
            if payload.get(key) != expected:
                raise FinalModelReviewIntegrityError(f"Persisted review snapshot field {key!r} does not match revision.")

    def _publish_json(self,path:Path,text:str,label:str) -> None:
        if path.exists() or path.is_symlink():
            raise FinalModelReviewPersistenceError(f"{label} path is occupied.")
        temp=path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
        self._write_text(temp,text); self._rename(temp,path)

    def _store(self, root, relative, data, role, target, unit_id=None) -> None:
        path=root.joinpath(*PurePosixPath(relative).parts); path.parent.mkdir(parents=True,exist_ok=True); self._write_bytes(path,data)
        target.append(FinalModelReviewStoredFileReference(relative,role,self._sha(data),unit_id))

    def _snapshot_json(self,value) -> str:
        try: payload=asdict(value)
        except TypeError as exc: raise FinalModelReviewPersistenceError("Review snapshot input must be a dataclass instance.") from exc
        return json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n"

    def _bundle_files(self,directory:Path) -> set[str]:
        result=set()
        items_root = directory / "items"
        for path in directory.rglob("*"):
            if path.is_symlink(): raise FinalModelReviewIntegrityError("Revision bundle contains a symbolic link.")
            if items_root in path.parents or path == items_root:
                continue
            if path.is_file(): result.add(path.relative_to(directory).as_posix())
        return result

    def _read_json(self,path,label):
        text=self._read_text(path)
        try: value=json.loads(text,object_pairs_hook=self._unique_pairs)
        except FinalModelReviewIntegrityError: raise
        except json.JSONDecodeError as exc: raise FinalModelReviewIntegrityError(f"{label} is invalid JSON.") from exc
        if not isinstance(value,dict): raise FinalModelReviewIntegrityError(f"{label} must be a JSON object.")
        return value

    @staticmethod
    def _unique_pairs(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise FinalModelReviewIntegrityError(f"Duplicate snapshot JSON key: {key!r}.")
            result[key]=value
        return result

    def _ensure_dir(self,path:Path) -> None:
        self._reject_symlink(path,"Final Model Review directory")
        path.mkdir(parents=True,exist_ok=True)
        self._reject_symlink(path,"Final Model Review directory")
        if not path.is_dir(): raise FinalModelReviewPersistenceError("Final Model Review path is not a directory.")

    def _require_dir(self,path:Path,label:str) -> None:
        self._reject_symlink(path,label)
        if not path.exists() or not path.is_dir(): raise FinalModelReviewNotFoundError(f"{label} not found: {path}.")

    def _require_file(self,path:Path,label:str) -> None:
        self._reject_symlink(path,label)
        if not path.exists() or not path.is_file(): raise FinalModelReviewNotFoundError(f"{label} not found: {path}.")

    @staticmethod
    def _reject_symlink(path:Path,label:str) -> None:
        if path.is_symlink(): raise FinalModelReviewPersistenceError(f"{label} must not be a symbolic link: {path}.")

    @staticmethod
    def _read_text(path:Path) -> str:
        try: return path.read_text(encoding="utf-8")
        except OSError as exc: raise FinalModelReviewPersistenceError(f"Unable to read Final Model Review file: {path}.") from exc

    def _write_text(self,path,text): self._write_bytes(path,text.encode("utf-8"))

    @staticmethod
    def _write_bytes(path:Path,data:bytes) -> None:
        try:
            with path.open("xb") as handle:
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
        except OSError as exc: raise FinalModelReviewPersistenceError(f"Unable to write Final Model Review file: {path}.") from exc

    def _timestamp(self) -> str:
        value=self._clock()
        if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise FinalModelReviewPersistenceError("clock must return timezone-aware datetime.")
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

    @staticmethod
    def _sha(data:bytes) -> str: return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _issue(project_id,code,message,path,*,review_id=None,revision_id=None,item_id=None,decision_id=None):
        return FinalModelReviewRepositoryIssue(project_id,code,message,"blocking",path,review_id,revision_id,item_id,decision_id)
