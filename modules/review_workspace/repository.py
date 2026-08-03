"""Project-isolated persistence for Human Review Workspaces."""

from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import re

from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)

from .document_manifest import (
    REVIEW_DOCUMENT_MANIFEST_FILENAME,
    review_document_from_json,
    review_document_to_json,
    validate_review_document,
)
from .errors import (
    DuplicateReviewRevisionError,
    DuplicateScopedReviewActionError,
    InvalidReviewVersionTransitionError,
    ReviewDocumentNotFoundError,
    ReviewDocumentVersionNotFoundError,
    ReviewIntegrityError,
    ReviewPersistenceError,
    ReviewRecoveryRequiredError,
    ReviewReferenceError,
    ReviewRevisionNotFoundError,
    StaleReviewRevisionError,
    UnsafeReviewWorkspacePathError,
    ReviewValidationError,
    ReviewWorkspaceError,
)
from .identifiers import (
    is_valid_review_document_id,
    is_valid_review_document_version_id,
    is_valid_review_revision_id,
    is_valid_scoped_review_action_id,
    next_review_document_id,
    next_review_document_version_id,
    next_review_revision_id,
    next_scoped_review_action_id,
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
)
from .paths import (
    FINALIZED_DIRECTORY_NAME,
    REVISIONS_DIRECTORY_NAME,
    SCOPED_ACTIONS_DIRECTORY_NAME,
    VERSIONS_DIRECTORY_NAME,
    project_path,
    review_document_path,
    review_document_version_path,
    review_revision_path,
    review_revisions_path,
    review_versions_path,
    reviews_path,
    scoped_review_action_path,
    scoped_review_actions_path,
)
from .scoped_action_manifest import (
    scoped_review_action_filename,
    scoped_review_action_from_json,
    scoped_review_action_to_json,
    validate_scoped_review_action,
)
from .revision_manifest import (
    review_revision_filename,
    review_revision_from_json,
    review_revision_to_json,
    validate_review_revision,
)
from .types import (
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewRevision,
    ReviewWorkspaceIssue,
    ReviewWorkspaceScanResult,
    ScopedReviewAction,
)
from .version_manifest import (
    REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME,
    calculate_review_document_version_fingerprint,
    review_document_version_from_json,
    review_document_version_to_json,
    validate_review_document_version,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")

_TEMP_DOCUMENT_PATTERN = re.compile(
    r"^\.create-(RVD-[0-9]{6})\.tmp$"
)
_TEMP_VERSION_PATTERN = re.compile(
    r"^\.create-(RVV-[0-9]{6})\.tmp$"
)
_TEMP_REVISION_PATTERN = re.compile(
    r"^\.(RVR-[0-9]{6})\.json\.tmp$"
)
_TEMP_SCOPED_ACTION_PATTERN = re.compile(
    r"^\.(SRA-[0-9]{6})\.json\.tmp$"
)

_DOCUMENT_DIRECTORY_ENTRIES = frozenset(
    {
        REVIEW_DOCUMENT_MANIFEST_FILENAME,
        VERSIONS_DIRECTORY_NAME,
    }
)

_REQUIRED_VERSION_DIRECTORY_ENTRIES = frozenset(
    {
        REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME,
        REVISIONS_DIRECTORY_NAME,
        SCOPED_ACTIONS_DIRECTORY_NAME,
    }
)

_OPTIONAL_VERSION_DIRECTORY_ENTRIES = frozenset(
    {
        FINALIZED_DIRECTORY_NAME,
    }
)


class ReviewWorkspaceRepository:
    """Persist and reopen project-local Human Review Workspaces."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
    ) -> None:
        self.root = Path(root)
        self._workspace = ProjectWorkspace(root=self.root)

    def scan_project(
        self,
        project_id: str,
    ) -> ReviewWorkspaceScanResult:
        """Discover valid review records and blocking issues."""

        self._load_project(project_id)

        documents: list[ReviewDocument] = []
        versions: list[ReviewDocumentVersion] = []
        revisions: list[ReviewRevision] = []
        scoped_actions: list[ScopedReviewAction] = []
        issues: list[ReviewWorkspaceIssue] = []

        self._scan_review_documents(
            project_id,
            documents,
            versions,
            revisions,
            scoped_actions,
            issues,
        )

        documents.sort(
            key=lambda item: item.review_document_id
        )
        versions.sort(
            key=lambda item: (
                item.review_document_id,
                item.version_number,
                item.review_document_version_id,
            )
        )
        revisions.sort(
            key=lambda item: (
                item.review_document_id,
                item.review_document_version_id,
                item.revision_sequence,
                item.review_revision_id,
            )
        )
        scoped_actions.sort(
            key=lambda item: (
                item.review_document_id,
                item.review_document_version_id,
                item.scoped_review_action_id,
            )
        )
        issues.sort(
            key=lambda issue: (
                str(issue.path or ""),
                issue.code,
                issue.review_document_id or "",
                issue.review_document_version_id or "",
                issue.review_revision_id or "",
                issue.review_item_id or "",
                issue.scoped_review_action_id or "",
                issue.message,
            )
        )

        return ReviewWorkspaceScanResult(
            documents=tuple(documents),
            versions=tuple(versions),
            revisions=tuple(revisions),
            scoped_actions=tuple(scoped_actions),
            issues=tuple(issues),
        )

    def next_document_id(
        self,
        project_id: str,
    ) -> str:
        """Return the next project-local Review Document ID."""

        self._load_project(project_id)

        root = reviews_path(
            self.root,
            project_id,
        )
        self._assert_optional_directory_safe(
            root,
            label="Review Workspace root",
        )

        return next_review_document_id(
            self._occupied_document_ids(root)
        )

    def next_version_id(
        self,
        project_id: str,
        review_document_id: str,
    ) -> str:
        """Return the next ID for one Review Document version."""

        self.load_document(
            project_id,
            review_document_id,
        )

        root = review_versions_path(
            self.root,
            project_id,
            review_document_id,
        )
        self._assert_directory_safe(
            root,
            label="Review Document Version root",
        )

        return next_review_document_version_id(
            self._occupied_version_ids(root)
        )

    def next_revision_id(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> str:
        """Return the next ID for one immutable revision."""

        self.load_version(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        root = review_revisions_path(
            self.root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        self._assert_directory_safe(
            root,
            label="Review Revision root",
        )

        return next_review_revision_id(
            self._occupied_revision_ids(root)
        )

    def next_scoped_action_id(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> str:
        """Return the next Scoped Review Action ID."""

        self.load_version(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        root = scoped_review_actions_path(
            self.root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        self._assert_directory_safe(
            root,
            label="Scoped Review Action root",
        )

        return next_scoped_review_action_id(
            self._occupied_scoped_action_ids(root)
        )

    def create_document_workspace(
        self,
        document: ReviewDocument,
        initial_version: ReviewDocumentVersion,
        initial_revision: ReviewRevision,
    ) -> tuple[
        ReviewDocument,
        ReviewDocumentVersion,
        ReviewRevision,
    ]:
        """Atomically create one Review Document workspace."""

        validate_review_document(document)
        validate_review_document_version(initial_version)
        validate_review_revision(initial_revision)

        self._validate_initial_bundle(
            document,
            initial_version,
            initial_revision,
        )
        self._load_project(document.project_id)

        project_directory = project_path(
            self.root,
            document.project_id,
        )
        reviews_directory = reviews_path(
            self.root,
            document.project_id,
        )

        self._ensure_directory(
            reviews_directory,
            parent=project_directory,
            label="Review Workspace root",
        )

        final_directory = review_document_path(
            self.root,
            document.project_id,
            document.review_document_id,
        )
        temporary_directory = reviews_directory / (
            f".create-{document.review_document_id}.tmp"
        )

        if (
            final_directory.exists()
            or final_directory.is_symlink()
        ):
            raise ReviewPersistenceError(
                "Review Document workspace already exists: "
                f"{final_directory}."
            )

        if (
            temporary_directory.exists()
            or temporary_directory.is_symlink()
        ):
            raise ReviewRecoveryRequiredError(
                "Interrupted Review Document creation requires "
                f"explicit recovery: {temporary_directory}."
            )

        version_directory = (
            temporary_directory
            / VERSIONS_DIRECTORY_NAME
            / initial_version.review_document_version_id
        )
        revisions_directory = (
            version_directory
            / REVISIONS_DIRECTORY_NAME
        )
        scoped_actions_directory = (
            version_directory
            / SCOPED_ACTIONS_DIRECTORY_NAME
        )

        try:
            temporary_directory.mkdir()

            versions_directory = (
                temporary_directory
                / VERSIONS_DIRECTORY_NAME
            )
            versions_directory.mkdir()
            version_directory.mkdir()
            revisions_directory.mkdir()
            scoped_actions_directory.mkdir()
        except OSError as exc:
            raise ReviewPersistenceError(
                "Unable to create temporary Review Document "
                f"workspace {temporary_directory}: {exc}"
            ) from exc

        document_manifest_path = (
            temporary_directory
            / REVIEW_DOCUMENT_MANIFEST_FILENAME
        )
        version_manifest_path = (
            version_directory
            / REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME
        )
        revision_file_path = (
            revisions_directory
            / review_revision_filename(
                initial_revision.review_revision_id
            )
        )

        self._write_new_text(
            document_manifest_path,
            review_document_to_json(document),
            label="Review Document Manifest",
        )
        self._write_new_text(
            version_manifest_path,
            review_document_version_to_json(
                initial_version
            ),
            label="Review Document Version Manifest",
        )
        self._write_new_text(
            revision_file_path,
            review_revision_to_json(initial_revision),
            label="initial Review Revision",
        )

        persisted_document = (
            self._load_document_from_directory(
                document.project_id,
                document.review_document_id,
                temporary_directory,
            )
        )
        persisted_version = (
            self._load_version_from_directory(
                document.project_id,
                document.review_document_id,
                initial_version.review_document_version_id,
                version_directory,
            )
        )
        persisted_revision = self._load_revision_file(
            revision_file_path,
            expected_project_id=document.project_id,
            expected_document_id=document.review_document_id,
            expected_version_id=(
                initial_version.review_document_version_id
            ),
            expected_revision_id=(
                initial_revision.review_revision_id
            ),
        )

        if persisted_document != document:
            raise ReviewIntegrityError(
                "Persisted Review Document differs from the "
                "validated input."
            )

        if persisted_version != initial_version:
            raise ReviewIntegrityError(
                "Persisted Review Document Version differs from "
                "the validated input."
            )

        if persisted_revision != initial_revision:
            raise ReviewIntegrityError(
                "Persisted initial Review Revision differs from "
                "the validated input."
            )

        if (
            final_directory.exists()
            or final_directory.is_symlink()
        ):
            raise ReviewPersistenceError(
                "Review Document path appeared during creation: "
                f"{final_directory}."
            )

        try:
            temporary_directory.rename(final_directory)
        except OSError as exc:
            raise ReviewPersistenceError(
                "Unable to finalize Review Document workspace "
                f"{final_directory}: {exc}"
            ) from exc

        return (
            self.load_document(
                document.project_id,
                document.review_document_id,
            ),
            self.load_version(
                document.project_id,
                document.review_document_id,
                initial_version.review_document_version_id,
            ),
            self.load_revision(
                document.project_id,
                document.review_document_id,
                initial_version.review_document_version_id,
                initial_revision.review_revision_id,
            ),
        )

    def load_document(
        self,
        project_id: str,
        review_document_id: str,
    ) -> ReviewDocument:
        """Load one complete Review Document root."""

        self._load_project(project_id)

        validated_document_id = validate_review_document_id(
            review_document_id
        )
        reviews_directory = reviews_path(
            self.root,
            project_id,
        )

        self._assert_optional_directory_safe(
            reviews_directory,
            label="Review Workspace root",
        )

        if not reviews_directory.exists():
            raise ReviewDocumentNotFoundError(
                "Review Document was not found: "
                f"{project_id}/{validated_document_id}."
            )

        directory = review_document_path(
            self.root,
            project_id,
            validated_document_id,
        )

        if directory.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                "Symbolic-link Review Document directories are "
                f"rejected: {directory}."
            )

        if not directory.exists() or not directory.is_dir():
            raise ReviewDocumentNotFoundError(
                "Review Document was not found: "
                f"{project_id}/{validated_document_id}."
            )

        return self._load_document_from_directory(
            project_id,
            validated_document_id,
            directory,
        )

    def load_version(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ReviewDocumentVersion:
        """Load one Review Document Version."""

        self.load_document(
            project_id,
            review_document_id,
        )

        validated_version_id = (
            validate_review_document_version_id(
                review_document_version_id
            )
        )
        directory = review_document_version_path(
            self.root,
            project_id,
            review_document_id,
            validated_version_id,
        )

        if directory.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                "Symbolic-link Review Document Version "
                f"directories are rejected: {directory}."
            )

        if not directory.exists() or not directory.is_dir():
            raise ReviewDocumentVersionNotFoundError(
                "Review Document Version was not found: "
                f"{project_id}/{review_document_id}/"
                f"{validated_version_id}."
            )

        return self._load_version_from_directory(
            project_id,
            review_document_id,
            validated_version_id,
            directory,
        )

    def load_revision(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_revision_id: str,
    ) -> ReviewRevision:
        """Load one immutable Review Revision."""

        self.load_version(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        validated_revision_id = validate_review_revision_id(
            review_revision_id
        )
        path = review_revision_path(
            self.root,
            project_id,
            review_document_id,
            review_document_version_id,
            validated_revision_id,
        )

        if path.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                "Symbolic-link Review Revision files are "
                f"rejected: {path}."
            )

        if not path.exists() or not path.is_file():
            raise ReviewRevisionNotFoundError(
                "Review Revision was not found: "
                f"{project_id}/{review_document_id}/"
                f"{review_document_version_id}/"
                f"{validated_revision_id}."
            )

        return self._load_revision_file(
            path,
            expected_project_id=project_id,
            expected_document_id=review_document_id,
            expected_version_id=(
                review_document_version_id
            ),
            expected_revision_id=validated_revision_id,
        )

    def persist_scoped_action(
        self,
        action: ScopedReviewAction,
    ) -> ScopedReviewAction:
        """Persist one immutable Scoped Review Action."""

        validate_scoped_review_action(action)

        try:
            version = self.load_version(
                action.project_id,
                action.review_document_id,
                action.review_document_version_id,
            )
        except (
            ReviewDocumentNotFoundError,
            ReviewDocumentVersionNotFoundError,
        ) as exc:
            raise ReviewReferenceError(
                "Scoped Review Action references an "
                "unavailable Review Document Version."
            ) from exc

        if version.version_state != "draft":
            raise InvalidReviewVersionTransitionError(
                "Scoped Review Actions may be added only "
                "to a draft Review Document Version."
            )

        head_revision = self.load_revision(
            action.project_id,
            action.review_document_id,
            action.review_document_version_id,
            version.head_revision_id,
        )

        self._validate_action_materialization(
            action,
            head_revision,
        )

        target = scoped_review_action_path(
            self.root,
            action.project_id,
            action.review_document_id,
            action.review_document_version_id,
            action.scoped_review_action_id,
        )

        if target.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                "Symbolic-link Scoped Review Action files "
                f"are rejected: {target}."
            )

        if target.exists():
            existing = self._load_scoped_action_file(
                target,
                expected_project_id=action.project_id,
                expected_document_id=(
                    action.review_document_id
                ),
                expected_version_id=(
                    action.review_document_version_id
                ),
                expected_action_id=(
                    action.scoped_review_action_id
                ),
            )

            if existing == action:
                raise DuplicateScopedReviewActionError(
                    "Scoped Review Action already exists "
                    "unchanged: "
                    f"{action.scoped_review_action_id}."
                )

            raise ReviewIntegrityError(
                "Scoped Review Action identifier is "
                "occupied by different content: "
                f"{action.scoped_review_action_id}."
            )

        temporary = target.parent / (
            f".{target.name}.tmp"
        )

        if (
            temporary.exists()
            or temporary.is_symlink()
        ):
            raise ReviewRecoveryRequiredError(
                "Interrupted Scoped Review Action "
                "persistence requires explicit recovery: "
                f"{temporary}."
            )

        self._write_new_text(
            temporary,
            scoped_review_action_to_json(action),
            label="temporary Scoped Review Action",
        )

        persisted = self._load_scoped_action_file(
            temporary,
            expected_project_id=action.project_id,
            expected_document_id=(
                action.review_document_id
            ),
            expected_version_id=(
                action.review_document_version_id
            ),
            expected_action_id=(
                action.scoped_review_action_id
            ),
        )

        if persisted != action:
            raise ReviewIntegrityError(
                "Persisted Scoped Review Action differs "
                "from the validated action."
            )

        if target.exists() or target.is_symlink():
            raise ReviewPersistenceError(
                "Scoped Review Action path appeared "
                f"during persistence: {target}."
            )

        try:
            temporary.rename(target)
        except OSError as exc:
            raise ReviewPersistenceError(
                "Unable to finalize Scoped Review Action "
                f"{target}: {exc}"
            ) from exc

        return self.load_scoped_action(
            action.project_id,
            action.review_document_id,
            action.review_document_version_id,
            action.scoped_review_action_id,
        )

    def load_scoped_action(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        scoped_review_action_id: str,
    ) -> ScopedReviewAction:
        """Load one immutable Scoped Review Action."""

        self.load_version(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        target = scoped_review_action_path(
            self.root,
            project_id,
            review_document_id,
            review_document_version_id,
            scoped_review_action_id,
        )

        if target.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                "Symbolic-link Scoped Review Action files "
                f"are rejected: {target}."
            )

        if not target.exists() or not target.is_file():
            raise ReviewReferenceError(
                "Scoped Review Action was not found: "
                f"{project_id}/{review_document_id}/"
                f"{review_document_version_id}/"
                f"{scoped_review_action_id}."
            )

        return self._load_scoped_action_file(
            target,
            expected_project_id=project_id,
            expected_document_id=review_document_id,
            expected_version_id=(
                review_document_version_id
            ),
            expected_action_id=(
                scoped_review_action_id
            ),
        )

    def append_revision(
        self,
        revision: ReviewRevision,
    ) -> tuple[
        ReviewDocumentVersion,
        ReviewRevision,
    ]:
        """Append a revision and advance the draft head."""

        validate_review_revision(revision)

        version_directory = review_document_version_path(
            self.root,
            revision.project_id,
            revision.review_document_id,
            revision.review_document_version_id,
        )
        version_manifest = (
            version_directory
            / REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME
        )
        temporary_version_manifest = (
            version_directory
            / (
                "."
                f"{REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME}"
                ".tmp"
            )
        )

        if (
            temporary_version_manifest.exists()
            or temporary_version_manifest.is_symlink()
        ):
            raise ReviewRecoveryRequiredError(
                "Interrupted Review Version update requires "
                "explicit recovery: "
                f"{temporary_version_manifest}."
            )

        try:
            version = self.load_version(
                revision.project_id,
                revision.review_document_id,
                revision.review_document_version_id,
            )
        except (
            ReviewDocumentNotFoundError,
            ReviewDocumentVersionNotFoundError,
        ) as exc:
            raise ReviewReferenceError(
                "Review Revision references an unavailable "
                "Review Document Version."
            ) from exc

        if version.version_state != "draft":
            raise InvalidReviewVersionTransitionError(
                "A Review Revision may be appended only "
                "to a draft Review Document Version."
            )

        target = review_revision_path(
            self.root,
            revision.project_id,
            revision.review_document_id,
            revision.review_document_version_id,
            revision.review_revision_id,
        )
        temporary_revision = target.parent / (
            f".{target.name}.tmp"
        )

        if target.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                "Symbolic-link Review Revision files are "
                f"rejected: {target}."
            )

        if target.exists():
            existing = self._load_revision_file(
                target,
                expected_project_id=revision.project_id,
                expected_document_id=(
                    revision.review_document_id
                ),
                expected_version_id=(
                    revision.review_document_version_id
                ),
                expected_revision_id=(
                    revision.review_revision_id
                ),
            )

            if existing != revision:
                raise ReviewIntegrityError(
                    "Review Revision identifier is occupied "
                    "by different content: "
                    f"{revision.review_revision_id}."
                )

            if (
                version.head_revision_id
                == revision.review_revision_id
            ):
                raise DuplicateReviewRevisionError(
                    "Review Revision already exists "
                    "unchanged: "
                    f"{revision.review_revision_id}."
                )

            raise ReviewRecoveryRequiredError(
                "Review Revision exists but the version "
                "head does not reference it; explicit "
                "recovery is required: "
                f"{revision.review_revision_id}."
            )

        if (
            temporary_revision.exists()
            or temporary_revision.is_symlink()
        ):
            raise ReviewRecoveryRequiredError(
                "Interrupted Review Revision append "
                "requires explicit recovery: "
                f"{temporary_revision}."
            )

        current_head = self.load_revision(
            revision.project_id,
            revision.review_document_id,
            revision.review_document_version_id,
            version.head_revision_id,
        )

        if (
            revision.predecessor_revision_id
            != current_head.review_revision_id
        ):
            raise StaleReviewRevisionError(
                "Review Revision predecessor does not "
                "match the current draft head."
            )

        if (
            revision.revision_sequence
            != current_head.revision_sequence + 1
        ):
            raise StaleReviewRevisionError(
                "Review Revision sequence does not follow "
                "the current draft head."
            )

        for action_id in (
            revision.scoped_review_action_ids
        ):
            self.load_scoped_action(
                revision.project_id,
                revision.review_document_id,
                revision.review_document_version_id,
                action_id,
            )

        updated_version = (
            self._updated_version_with_head(
                version,
                revision.review_revision_id,
            )
        )

        self._write_new_text(
            temporary_revision,
            review_revision_to_json(revision),
            label="temporary Review Revision",
        )
        self._write_new_text(
            temporary_version_manifest,
            review_document_version_to_json(
                updated_version
            ),
            label=(
                "temporary Review Document Version "
                "Manifest"
            ),
        )

        persisted_revision = (
            self._load_revision_file(
                temporary_revision,
                expected_project_id=(
                    revision.project_id
                ),
                expected_document_id=(
                    revision.review_document_id
                ),
                expected_version_id=(
                    revision.review_document_version_id
                ),
                expected_revision_id=(
                    revision.review_revision_id
                ),
            )
        )
        persisted_version = (
            self._load_version_manifest_file(
                temporary_version_manifest,
                expected_project_id=(
                    revision.project_id
                ),
                expected_document_id=(
                    revision.review_document_id
                ),
                expected_version_id=(
                    revision.review_document_version_id
                ),
            )
        )

        if persisted_revision != revision:
            raise ReviewIntegrityError(
                "Persisted Review Revision differs "
                "from the validated revision."
            )

        if persisted_version != updated_version:
            raise ReviewIntegrityError(
                "Persisted updated Review Version "
                "differs from the validated version."
            )

        if target.exists() or target.is_symlink():
            raise ReviewPersistenceError(
                "Review Revision path appeared during "
                f"append: {target}."
            )

        try:
            temporary_revision.rename(target)
        except OSError as exc:
            raise ReviewPersistenceError(
                "Unable to finalize Review Revision "
                f"{target}: {exc}"
            ) from exc

        try:
            os.replace(
                temporary_version_manifest,
                version_manifest,
            )
        except OSError as exc:
            raise ReviewRecoveryRequiredError(
                "Review Revision was persisted but "
                "advancing the version head failed; "
                "explicit recovery is required: "
                f"{target}."
            ) from exc

        persisted_version = self.load_version(
            revision.project_id,
            revision.review_document_id,
            revision.review_document_version_id,
        )
        persisted_revision = self.load_revision(
            revision.project_id,
            revision.review_document_id,
            revision.review_document_version_id,
            revision.review_revision_id,
        )

        if persisted_version != updated_version:
            raise ReviewIntegrityError(
                "Reloaded Review Version differs from "
                "the appended version state."
            )

        if persisted_revision != revision:
            raise ReviewIntegrityError(
                "Reloaded Review Revision differs from "
                "the appended revision."
            )

        return persisted_version, persisted_revision

    def _updated_version_with_head(
        self,
        version: ReviewDocumentVersion,
        review_revision_id: str,
    ) -> ReviewDocumentVersion:
        provisional = replace(
            version,
            head_revision_id=review_revision_id,
            content_fingerprint="0" * 64,
        )
        updated = replace(
            provisional,
            content_fingerprint=(
                calculate_review_document_version_fingerprint(
                    provisional
                )
            ),
        )

        validate_review_document_version(updated)

        return updated

    def _validate_action_materialization(
        self,
        action: ScopedReviewAction,
        head_revision: ReviewRevision,
    ) -> None:
        indexed_items = {
            item.review_item_id: item
            for item in head_revision.review_items
        }

        for reference in action.materialized_items:
            item = indexed_items.get(
                reference.review_item_id
            )

            if item is None:
                raise ReviewReferenceError(
                    "Scoped Review Action materializes "
                    "an unavailable Review Item: "
                    f"{reference.review_item_id}."
                )

            if (
                item.item_content_fingerprint
                != reference.item_content_fingerprint
            ):
                raise ReviewIntegrityError(
                    "Scoped Review Action materialization "
                    "fingerprint does not match the "
                    "current Review Item: "
                    f"{reference.review_item_id}."
                )

    def _load_scoped_action_file(
        self,
        path: Path,
        *,
        expected_project_id: str,
        expected_document_id: str,
        expected_version_id: str,
        expected_action_id: str,
    ) -> ScopedReviewAction:
        self._assert_file_safe(
            path,
            label="Scoped Review Action",
        )

        action = scoped_review_action_from_json(
            self._read_text(
                path,
                label="Scoped Review Action",
            )
        )
        expected_filename = (
            scoped_review_action_filename(
                expected_action_id
            )
        )

        if path.name not in {
            expected_filename,
            f".{expected_filename}.tmp",
        }:
            raise ReviewIntegrityError(
                "Scoped Review Action filename does "
                "not match its identifier."
            )

        if action.project_id != expected_project_id:
            raise ReviewIntegrityError(
                "Scoped Review Action project_id does "
                "not match its Project directory."
            )

        if (
            action.review_document_id
            != expected_document_id
        ):
            raise ReviewIntegrityError(
                "Scoped Review Action does not belong "
                "to its Review Document directory."
            )

        if (
            action.review_document_version_id
            != expected_version_id
        ):
            raise ReviewIntegrityError(
                "Scoped Review Action does not belong "
                "to its Review Document Version "
                "directory."
            )

        if (
            action.scoped_review_action_id
            != expected_action_id
        ):
            raise ReviewIntegrityError(
                "Scoped Review Action ID does not "
                "match its filename."
            )

        return action

    def _load_version_manifest_file(
        self,
        path: Path,
        *,
        expected_project_id: str,
        expected_document_id: str,
        expected_version_id: str,
    ) -> ReviewDocumentVersion:
        self._assert_file_safe(
            path,
            label=(
                "Review Document Version Manifest"
            ),
        )

        version = review_document_version_from_json(
            self._read_text(
                path,
                label=(
                    "Review Document Version Manifest"
                ),
            )
        )
        expected_filename = (
            REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME
        )

        if path.name not in {
            expected_filename,
            f".{expected_filename}.tmp",
        }:
            raise ReviewIntegrityError(
                "Review Document Version Manifest "
                "filename is invalid."
            )

        if version.project_id != expected_project_id:
            raise ReviewIntegrityError(
                "Review Document Version project_id "
                "does not match its Project directory."
            )

        if (
            version.review_document_id
            != expected_document_id
        ):
            raise ReviewIntegrityError(
                "Review Document Version does not "
                "belong to its Review Document "
                "directory."
            )

        if (
            version.review_document_version_id
            != expected_version_id
        ):
            raise ReviewIntegrityError(
                "Review Document Version ID does not "
                "match its version directory."
            )

        return version

    def _scan_review_documents(
        self,
        project_id: str,
        documents: list[ReviewDocument],
        versions: list[ReviewDocumentVersion],
        revisions: list[ReviewRevision],
        scoped_actions: list[ScopedReviewAction],
        issues: list[ReviewWorkspaceIssue],
    ) -> None:
        root = reviews_path(
            self.root,
            project_id,
        )

        if root.is_symlink():
            issues.append(
                self._issue(
                    project_id,
                    code="unsafe_reviews_root",
                    message=(
                        "Symbolic-link Review Workspace roots "
                        "are rejected."
                    ),
                    path=root,
                )
            )
            return

        if not root.exists():
            return

        if not root.is_dir():
            issues.append(
                self._issue(
                    project_id,
                    code="unsafe_reviews_root",
                    message=(
                        "Review Workspace root is not a "
                        "directory."
                    ),
                    path=root,
                )
            )
            return

        entries = self._scan_directory_entries(
            project_id,
            root,
            issues,
            code="reviews_root_read_error",
            label="Review Workspace root",
        )

        if entries is None:
            return

        for entry in entries:
            temporary_match = (
                _TEMP_DOCUMENT_PATTERN.fullmatch(
                    entry.name
                )
            )

            if temporary_match is not None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "interrupted_review_document_creation"
                        ),
                        message=(
                            "Interrupted Review Document "
                            "creation requires explicit "
                            "recovery."
                        ),
                        path=entry,
                        review_document_id=(
                            temporary_match.group(1)
                        ),
                    )
                )
                continue

            candidate_document_id = (
                entry.name
                if is_valid_review_document_id(
                    entry.name
                )
                else None
            )

            if entry.is_symlink():
                issues.append(
                    self._issue(
                        project_id,
                        code="unsafe_review_document_path",
                        message=(
                            "Symbolic-link Review Document "
                            "entries are rejected."
                        ),
                        path=entry,
                        review_document_id=(
                            candidate_document_id
                        ),
                    )
                )
                continue

            if entry.name.startswith("."):
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "unexpected_hidden_review_entry"
                        ),
                        message=(
                            "Unexpected hidden entry in the "
                            "Review Workspace root."
                        ),
                        path=entry,
                    )
                )
                continue

            if not entry.is_dir():
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_review_entry",
                        message=(
                            "Review Workspace entries must "
                            "be Review Document directories."
                        ),
                        path=entry,
                        review_document_id=(
                            candidate_document_id
                        ),
                    )
                )
                continue

            if candidate_document_id is None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "invalid_review_document_directory"
                        ),
                        message=(
                            "Review Document directory name "
                            "must match "
                            "^RVD-[0-9]{6}$."
                        ),
                        path=entry,
                    )
                )
                continue

            try:
                document = self.load_document(
                    project_id,
                    candidate_document_id,
                )
            except ReviewWorkspaceError as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            self._issue_code_for_exception(
                                exc,
                                default=(
                                    "invalid_review_document"
                                ),
                            )
                        ),
                        message=str(exc),
                        path=entry,
                        review_document_id=(
                            candidate_document_id
                        ),
                    )
                )
                continue

            documents.append(document)

            self._scan_review_versions(
                project_id,
                candidate_document_id,
                versions,
                revisions,
                scoped_actions,
                issues,
            )

    def _scan_review_versions(
        self,
        project_id: str,
        review_document_id: str,
        versions: list[ReviewDocumentVersion],
        revisions: list[ReviewRevision],
        scoped_actions: list[ScopedReviewAction],
        issues: list[ReviewWorkspaceIssue],
    ) -> None:
        root = review_versions_path(
            self.root,
            project_id,
            review_document_id,
        )
        entries = self._scan_directory_entries(
            project_id,
            root,
            issues,
            code="versions_root_read_error",
            label="Review Document Version root",
            review_document_id=review_document_id,
        )

        if entries is None:
            return

        for entry in entries:
            temporary_match = (
                _TEMP_VERSION_PATTERN.fullmatch(
                    entry.name
                )
            )

            if temporary_match is not None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "interrupted_review_version_creation"
                        ),
                        message=(
                            "Interrupted Review Document "
                            "Version creation requires "
                            "explicit recovery."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            temporary_match.group(1)
                        ),
                    )
                )
                continue

            candidate_version_id = (
                entry.name
                if is_valid_review_document_version_id(
                    entry.name
                )
                else None
            )

            if entry.is_symlink():
                issues.append(
                    self._issue(
                        project_id,
                        code="unsafe_review_version_path",
                        message=(
                            "Symbolic-link Review Document "
                            "Version entries are rejected."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            candidate_version_id
                        ),
                    )
                )
                continue

            if entry.name.startswith("."):
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "unexpected_hidden_version_entry"
                        ),
                        message=(
                            "Unexpected hidden entry in the "
                            "Review Document Version root."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                    )
                )
                continue

            if not entry.is_dir():
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_version_entry",
                        message=(
                            "Review Document Version entries "
                            "must be directories."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            candidate_version_id
                        ),
                    )
                )
                continue

            if candidate_version_id is None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "invalid_review_version_directory"
                        ),
                        message=(
                            "Review Document Version "
                            "directory name must match "
                            "^RVV-[0-9]{6}$."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                    )
                )
                continue

            temporary_manifest = entry / (
                "."
                f"{REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME}"
                ".tmp"
            )

            if (
                temporary_manifest.exists()
                or temporary_manifest.is_symlink()
            ):
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "interrupted_review_version_update"
                        ),
                        message=(
                            "Interrupted Review Document "
                            "Version update requires explicit "
                            "recovery."
                        ),
                        path=temporary_manifest,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            candidate_version_id
                        ),
                    )
                )
                continue

            try:
                version = self.load_version(
                    project_id,
                    review_document_id,
                    candidate_version_id,
                )
            except ReviewWorkspaceError as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            self._issue_code_for_exception(
                                exc,
                                default=(
                                    "invalid_review_version"
                                ),
                            )
                        ),
                        message=str(exc),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            candidate_version_id
                        ),
                    )
                )
                continue

            versions.append(version)

            scanned_revisions = (
                self._scan_review_revisions(
                    project_id,
                    review_document_id,
                    candidate_version_id,
                    revisions,
                    issues,
                )
            )
            scanned_actions = (
                self._scan_scoped_actions(
                    project_id,
                    review_document_id,
                    candidate_version_id,
                    scoped_actions,
                    issues,
                )
            )

            self._validate_scanned_version(
                version,
                scanned_revisions,
                scanned_actions,
                issues,
            )

    def _scan_review_revisions(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        revisions: list[ReviewRevision],
        issues: list[ReviewWorkspaceIssue],
    ) -> tuple[ReviewRevision, ...]:
        root = review_revisions_path(
            self.root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        entries = self._scan_directory_entries(
            project_id,
            root,
            issues,
            code="revisions_root_read_error",
            label="Review Revision root",
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
        )

        if entries is None:
            return ()

        scanned: list[ReviewRevision] = []

        for entry in entries:
            temporary_match = (
                _TEMP_REVISION_PATTERN.fullmatch(
                    entry.name
                )
            )

            if temporary_match is not None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "interrupted_review_revision_append"
                        ),
                        message=(
                            "Interrupted Review Revision "
                            "append requires explicit recovery."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        review_revision_id=(
                            temporary_match.group(1)
                        ),
                    )
                )
                continue

            candidate_revision_id = None

            if entry.name.endswith(".json"):
                possible_id = entry.name.removesuffix(
                    ".json"
                )

                if is_valid_review_revision_id(
                    possible_id
                ):
                    candidate_revision_id = possible_id

            if entry.is_symlink():
                issues.append(
                    self._issue(
                        project_id,
                        code="unsafe_review_revision_path",
                        message=(
                            "Symbolic-link Review Revision "
                            "entries are rejected."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        review_revision_id=(
                            candidate_revision_id
                        ),
                    )
                )
                continue

            if entry.name.startswith("."):
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "unexpected_hidden_revision_entry"
                        ),
                        message=(
                            "Unexpected hidden entry in the "
                            "Review Revision root."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                    )
                )
                continue

            if not entry.is_file():
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_revision_entry",
                        message=(
                            "Review Revision entries must "
                            "be JSON files."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        review_revision_id=(
                            candidate_revision_id
                        ),
                    )
                )
                continue

            if candidate_revision_id is None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "invalid_review_revision_filename"
                        ),
                        message=(
                            "Review Revision filename must "
                            "match "
                            "^RVR-[0-9]{6}\\.json$."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                    )
                )
                continue

            try:
                revision = self.load_revision(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                    candidate_revision_id,
                )
            except ReviewWorkspaceError as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            self._issue_code_for_exception(
                                exc,
                                default=(
                                    "invalid_review_revision"
                                ),
                            )
                        ),
                        message=str(exc),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        review_revision_id=(
                            candidate_revision_id
                        ),
                    )
                )
                continue

            scanned.append(revision)
            revisions.append(revision)

        return tuple(scanned)

    def _scan_scoped_actions(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        scoped_actions: list[ScopedReviewAction],
        issues: list[ReviewWorkspaceIssue],
    ) -> tuple[ScopedReviewAction, ...]:
        root = scoped_review_actions_path(
            self.root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        entries = self._scan_directory_entries(
            project_id,
            root,
            issues,
            code="scoped_actions_root_read_error",
            label="Scoped Review Action root",
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
        )

        if entries is None:
            return ()

        scanned: list[ScopedReviewAction] = []

        for entry in entries:
            temporary_match = (
                _TEMP_SCOPED_ACTION_PATTERN.fullmatch(
                    entry.name
                )
            )

            if temporary_match is not None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "interrupted_scoped_action_persistence"
                        ),
                        message=(
                            "Interrupted Scoped Review Action "
                            "persistence requires explicit "
                            "recovery."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        scoped_review_action_id=(
                            temporary_match.group(1)
                        ),
                    )
                )
                continue

            candidate_action_id = None

            if entry.name.endswith(".json"):
                possible_id = entry.name.removesuffix(
                    ".json"
                )

                if is_valid_scoped_review_action_id(
                    possible_id
                ):
                    candidate_action_id = possible_id

            if entry.is_symlink():
                issues.append(
                    self._issue(
                        project_id,
                        code="unsafe_scoped_action_path",
                        message=(
                            "Symbolic-link Scoped Review Action "
                            "entries are rejected."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        scoped_review_action_id=(
                            candidate_action_id
                        ),
                    )
                )
                continue

            if entry.name.startswith("."):
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "unexpected_hidden_scoped_action_entry"
                        ),
                        message=(
                            "Unexpected hidden entry in the "
                            "Scoped Review Action root."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                    )
                )
                continue

            if not entry.is_file():
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "unexpected_scoped_action_entry"
                        ),
                        message=(
                            "Scoped Review Action entries "
                            "must be JSON files."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        scoped_review_action_id=(
                            candidate_action_id
                        ),
                    )
                )
                continue

            if candidate_action_id is None:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            "invalid_scoped_action_filename"
                        ),
                        message=(
                            "Scoped Review Action filename "
                            "must match "
                            "^SRA-[0-9]{6}\\.json$."
                        ),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                    )
                )
                continue

            try:
                action = self.load_scoped_action(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                    candidate_action_id,
                )
            except ReviewWorkspaceError as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code=(
                            self._issue_code_for_exception(
                                exc,
                                default=(
                                    "invalid_scoped_action"
                                ),
                            )
                        ),
                        message=str(exc),
                        path=entry,
                        review_document_id=(
                            review_document_id
                        ),
                        review_document_version_id=(
                            review_document_version_id
                        ),
                        scoped_review_action_id=(
                            candidate_action_id
                        ),
                    )
                )
                continue

            scanned.append(action)
            scoped_actions.append(action)

        return tuple(scanned)

    def _validate_scanned_version(
        self,
        version: ReviewDocumentVersion,
        revisions: tuple[ReviewRevision, ...],
        actions: tuple[ScopedReviewAction, ...],
        issues: list[ReviewWorkspaceIssue],
    ) -> None:
        revision_index = {
            revision.review_revision_id: revision
            for revision in revisions
        }
        action_index = {
            action.scoped_review_action_id: action
            for action in actions
        }
        version_directory = review_document_version_path(
            self.root,
            version.project_id,
            version.review_document_id,
            version.review_document_version_id,
        )

        head = revision_index.get(
            version.head_revision_id
        )

        if head is None:
            issues.append(
                self._issue(
                    version.project_id,
                    code="missing_head_revision",
                    message=(
                        "Review Document Version head_revision_id "
                        "does not identify a valid persisted "
                        "Review Revision."
                    ),
                    path=review_revision_path(
                        self.root,
                        version.project_id,
                        version.review_document_id,
                        version.review_document_version_id,
                        version.head_revision_id,
                    ),
                    review_document_id=(
                        version.review_document_id
                    ),
                    review_document_version_id=(
                        version.review_document_version_id
                    ),
                    review_revision_id=(
                        version.head_revision_id
                    ),
                )
            )
        elif revisions:
            maximum_sequence = max(
                revision.revision_sequence
                for revision in revisions
            )

            if (
                head.revision_sequence
                != maximum_sequence
            ):
                issues.append(
                    self._issue(
                        version.project_id,
                        code="stale_version_head",
                        message=(
                            "Review Document Version head is "
                            "not the latest valid persisted "
                            "Review Revision."
                        ),
                        path=version_directory,
                        review_document_id=(
                            version.review_document_id
                        ),
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                        review_revision_id=(
                            version.head_revision_id
                        ),
                    )
                )

        revisions_by_sequence: dict[
            int,
            list[ReviewRevision],
        ] = {}

        for revision in revisions:
            revisions_by_sequence.setdefault(
                revision.revision_sequence,
                [],
            ).append(revision)

        for sequence, matching in (
            revisions_by_sequence.items()
        ):
            if len(matching) <= 1:
                continue

            issues.append(
                self._issue(
                    version.project_id,
                    code="duplicate_revision_sequence",
                    message=(
                        "Multiple Review Revisions use "
                        f"revision_sequence {sequence}."
                    ),
                    path=version_directory,
                    review_document_id=(
                        version.review_document_id
                    ),
                    review_document_version_id=(
                        version.review_document_version_id
                    ),
                )
            )

        for revision in revisions:
            if revision.revision_sequence == 1:
                continue

            predecessor = revision_index.get(
                revision.predecessor_revision_id
                or ""
            )

            if predecessor is None:
                issues.append(
                    self._issue(
                        version.project_id,
                        code="missing_predecessor_revision",
                        message=(
                            "Review Revision predecessor does "
                            "not identify a valid persisted "
                            "Review Revision."
                        ),
                        path=review_revision_path(
                            self.root,
                            version.project_id,
                            version.review_document_id,
                            version.review_document_version_id,
                            revision.review_revision_id,
                        ),
                        review_document_id=(
                            version.review_document_id
                        ),
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                        review_revision_id=(
                            revision.review_revision_id
                        ),
                    )
                )
                continue

            if (
                predecessor.revision_sequence
                != revision.revision_sequence - 1
            ):
                issues.append(
                    self._issue(
                        version.project_id,
                        code="invalid_revision_chain",
                        message=(
                            "Review Revision predecessor does "
                            "not have the immediately preceding "
                            "revision_sequence."
                        ),
                        path=review_revision_path(
                            self.root,
                            version.project_id,
                            version.review_document_id,
                            version.review_document_version_id,
                            revision.review_revision_id,
                        ),
                        review_document_id=(
                            version.review_document_id
                        ),
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                        review_revision_id=(
                            revision.review_revision_id
                        ),
                    )
                )

        action_references: dict[
            str,
            list[ReviewRevision],
        ] = {
            action_id: []
            for action_id in action_index
        }

        for revision in revisions:
            for action_id in (
                revision.scoped_review_action_ids
            ):
                action = action_index.get(action_id)

                if action is None:
                    issues.append(
                        self._issue(
                            version.project_id,
                            code=(
                                "missing_scoped_action_reference"
                            ),
                            message=(
                                "Review Revision references an "
                                "unavailable Scoped Review "
                                "Action."
                            ),
                            path=review_revision_path(
                                self.root,
                                version.project_id,
                                version.review_document_id,
                                version.review_document_version_id,
                                revision.review_revision_id,
                            ),
                            review_document_id=(
                                version.review_document_id
                            ),
                            review_document_version_id=(
                                version.review_document_version_id
                            ),
                            review_revision_id=(
                                revision.review_revision_id
                            ),
                            scoped_review_action_id=(
                                action_id
                            ),
                        )
                    )
                    continue

                action_references[action_id].append(
                    revision
                )

                predecessor = revision_index.get(
                    revision.predecessor_revision_id
                    or ""
                )

                if predecessor is None:
                    issues.append(
                        self._issue(
                            version.project_id,
                            code=(
                                "invalid_scoped_action_"
                                "reference_context"
                            ),
                            message=(
                                "Scoped Review Action reference "
                                "has no valid predecessor "
                                "revision for materialization "
                                "validation."
                            ),
                            path=review_revision_path(
                                self.root,
                                version.project_id,
                                version.review_document_id,
                                version.review_document_version_id,
                                revision.review_revision_id,
                            ),
                            review_document_id=(
                                version.review_document_id
                            ),
                            review_document_version_id=(
                                version.review_document_version_id
                            ),
                            review_revision_id=(
                                revision.review_revision_id
                            ),
                            scoped_review_action_id=(
                                action_id
                            ),
                        )
                    )
                    continue

                try:
                    self._validate_action_materialization(
                        action,
                        predecessor,
                    )
                except ReviewWorkspaceError as exc:
                    issues.append(
                        self._issue(
                            version.project_id,
                            code=(
                                "scoped_action_"
                                "materialization_mismatch"
                            ),
                            message=str(exc),
                            path=scoped_review_action_path(
                                self.root,
                                version.project_id,
                                version.review_document_id,
                                version.review_document_version_id,
                                action_id,
                            ),
                            review_document_id=(
                                version.review_document_id
                            ),
                            review_document_version_id=(
                                version.review_document_version_id
                            ),
                            review_revision_id=(
                                revision.review_revision_id
                            ),
                            scoped_review_action_id=(
                                action_id
                            ),
                        )
                    )

        for action_id, referencing_revisions in (
            action_references.items()
        ):
            action_path = scoped_review_action_path(
                self.root,
                version.project_id,
                version.review_document_id,
                version.review_document_version_id,
                action_id,
            )

            if not referencing_revisions:
                issues.append(
                    self._issue(
                        version.project_id,
                        code="unreferenced_scoped_action",
                        message=(
                            "Persisted Scoped Review Action "
                            "is not referenced by any valid "
                            "Review Revision."
                        ),
                        path=action_path,
                        review_document_id=(
                            version.review_document_id
                        ),
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                        scoped_review_action_id=(
                            action_id
                        ),
                    )
                )
                continue

            if len(referencing_revisions) > 1:
                issues.append(
                    self._issue(
                        version.project_id,
                        code=(
                            "scoped_action_referenced_"
                            "multiple_times"
                        ),
                        message=(
                            "Scoped Review Action is referenced "
                            "by more than one Review Revision."
                        ),
                        path=action_path,
                        review_document_id=(
                            version.review_document_id
                        ),
                        review_document_version_id=(
                            version.review_document_version_id
                        ),
                        scoped_review_action_id=(
                            action_id
                        ),
                    )
                )

    def _scan_directory_entries(
        self,
        project_id: str,
        root: Path,
        issues: list[ReviewWorkspaceIssue],
        *,
        code: str,
        label: str,
        review_document_id: str | None = None,
        review_document_version_id: str | None = None,
    ) -> tuple[Path, ...] | None:
        try:
            return tuple(
                sorted(
                    root.iterdir(),
                    key=lambda entry: entry.name,
                )
            )
        except OSError as exc:
            issues.append(
                self._issue(
                    project_id,
                    code=code,
                    message=(
                        f"Unable to inspect {label}: {exc}"
                    ),
                    path=root,
                    review_document_id=(
                        review_document_id
                    ),
                    review_document_version_id=(
                        review_document_version_id
                    ),
                )
            )
            return None

    @staticmethod
    def _issue(
        project_id: str,
        *,
        code: str,
        message: str,
        path: Path,
        review_document_id: str | None = None,
        review_document_version_id: str | None = None,
        review_revision_id: str | None = None,
        review_item_id: str | None = None,
        scoped_review_action_id: str | None = None,
    ) -> ReviewWorkspaceIssue:
        return ReviewWorkspaceIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
            review_revision_id=review_revision_id,
            review_item_id=review_item_id,
            scoped_review_action_id=(
                scoped_review_action_id
            ),
        )

    @staticmethod
    def _issue_code_for_exception(
        exc: Exception,
        *,
        default: str,
    ) -> str:
        if isinstance(
            exc,
            UnsafeReviewWorkspacePathError,
        ):
            return "unsafe_review_workspace_path"

        if isinstance(
            exc,
            ReviewRecoveryRequiredError,
        ):
            return "review_recovery_required"

        if isinstance(exc, ReviewReferenceError):
            return "invalid_review_reference"

        if isinstance(exc, ReviewIntegrityError):
            return "review_integrity_error"

        if isinstance(exc, ReviewValidationError):
            return "review_validation_error"

        if isinstance(exc, ReviewPersistenceError):
            return "review_persistence_error"

        return default

    def _occupied_document_ids(
        self,
        root: Path,
    ) -> tuple[str, ...]:
        occupied: set[str] = set()

        for entry in self._directory_entries(
            root,
            label="Review Workspace root",
        ):
            if is_valid_review_document_id(entry.name):
                occupied.add(entry.name)
                continue

            match = _TEMP_DOCUMENT_PATTERN.fullmatch(
                entry.name
            )

            if match is not None:
                occupied.add(match.group(1))

        return tuple(sorted(occupied))

    def _occupied_version_ids(
        self,
        root: Path,
    ) -> tuple[str, ...]:
        occupied: set[str] = set()

        for entry in self._directory_entries(
            root,
            label="Review Document Version root",
        ):
            if is_valid_review_document_version_id(
                entry.name
            ):
                occupied.add(entry.name)
                continue

            match = _TEMP_VERSION_PATTERN.fullmatch(
                entry.name
            )

            if match is not None:
                occupied.add(match.group(1))

        return tuple(sorted(occupied))

    def _occupied_revision_ids(
        self,
        root: Path,
    ) -> tuple[str, ...]:
        occupied: set[str] = set()

        for entry in self._directory_entries(
            root,
            label="Review Revision root",
        ):
            if entry.name.endswith(".json"):
                candidate = entry.name.removesuffix(
                    ".json"
                )

                if is_valid_review_revision_id(
                    candidate
                ):
                    occupied.add(candidate)
                    continue

            match = _TEMP_REVISION_PATTERN.fullmatch(
                entry.name
            )

            if match is not None:
                occupied.add(match.group(1))

        return tuple(sorted(occupied))

    def _occupied_scoped_action_ids(
        self,
        root: Path,
    ) -> tuple[str, ...]:
        occupied: set[str] = set()

        for entry in self._directory_entries(
            root,
            label="Scoped Review Action root",
        ):
            if entry.name.endswith(".json"):
                candidate = entry.name.removesuffix(
                    ".json"
                )

                if is_valid_scoped_review_action_id(
                    candidate
                ):
                    occupied.add(candidate)
                    continue

            match = (
                _TEMP_SCOPED_ACTION_PATTERN.fullmatch(
                    entry.name
                )
            )

            if match is not None:
                occupied.add(match.group(1))

        return tuple(sorted(occupied))

    def _directory_entries(
        self,
        root: Path,
        *,
        label: str,
    ) -> tuple[Path, ...]:
        if not root.exists():
            return ()

        try:
            return tuple(root.iterdir())
        except OSError as exc:
            raise ReviewPersistenceError(
                f"Unable to inspect {label} {root}: {exc}"
            ) from exc

    def _validate_initial_bundle(
        self,
        document: ReviewDocument,
        version: ReviewDocumentVersion,
        revision: ReviewRevision,
    ) -> None:
        expected_project_id = document.project_id
        expected_document_id = document.review_document_id
        expected_version_id = (
            version.review_document_version_id
        )

        if version.project_id != expected_project_id:
            raise ReviewReferenceError(
                "Initial Review Document Version project_id "
                "does not match the Review Document."
            )

        if (
            version.review_document_id
            != expected_document_id
        ):
            raise ReviewReferenceError(
                "Initial Review Document Version does not "
                "belong to the Review Document."
            )

        if revision.project_id != expected_project_id:
            raise ReviewReferenceError(
                "Initial Review Revision project_id does not "
                "match the Review Document."
            )

        if (
            revision.review_document_id
            != expected_document_id
        ):
            raise ReviewReferenceError(
                "Initial Review Revision does not belong to "
                "the Review Document."
            )

        if (
            revision.review_document_version_id
            != expected_version_id
        ):
            raise ReviewReferenceError(
                "Initial Review Revision does not belong to "
                "the initial Review Document Version."
            )

        if version.version_state != "draft":
            raise ReviewIntegrityError(
                "An initial Review Document Version must be "
                "in draft state."
            )

        if version.version_number != 1:
            raise ReviewIntegrityError(
                "An initial Review Document Version must have "
                "version_number 1."
            )

        if version.predecessor_version_id is not None:
            raise ReviewIntegrityError(
                "An initial Review Document Version must not "
                "have a predecessor."
            )

        if version.reopen_reason is not None:
            raise ReviewIntegrityError(
                "An initial Review Document Version must not "
                "have a reopen reason."
            )

        if revision.revision_sequence != 1:
            raise ReviewIntegrityError(
                "An initial Review Revision must have "
                "revision_sequence 1."
            )

        if revision.predecessor_revision_id is not None:
            raise ReviewIntegrityError(
                "An initial Review Revision must not have "
                "a predecessor."
            )

        if (
            version.head_revision_id
            != revision.review_revision_id
        ):
            raise ReviewIntegrityError(
                "Initial version head_revision_id must identify "
                "the initial Review Revision."
            )

        if revision.scoped_review_action_ids:
            raise ReviewIntegrityError(
                "An initial Review Revision must not reference "
                "Scoped Review Actions."
            )

    def _load_document_from_directory(
        self,
        project_id: str,
        review_document_id: str,
        directory: Path,
    ) -> ReviewDocument:
        self._assert_directory_safe(
            directory,
            label="Review Document directory",
        )
        self._assert_exact_directory_entries(
            directory,
            required=_DOCUMENT_DIRECTORY_ENTRIES,
            optional=frozenset(),
            label="Review Document directory",
        )

        manifest_path = (
            directory
            / REVIEW_DOCUMENT_MANIFEST_FILENAME
        )
        versions_directory = (
            directory
            / VERSIONS_DIRECTORY_NAME
        )

        self._assert_file_safe(
            manifest_path,
            label="Review Document Manifest",
        )
        self._assert_directory_safe(
            versions_directory,
            label="Review Document Version root",
        )

        document = review_document_from_json(
            self._read_text(
                manifest_path,
                label="Review Document Manifest",
            )
        )

        if document.project_id != project_id:
            raise ReviewIntegrityError(
                "Review Document project_id does not match "
                "its Project directory."
            )

        if (
            document.review_document_id
            != review_document_id
        ):
            raise ReviewIntegrityError(
                "Review Document ID does not match its "
                "workspace directory."
            )

        return document

    def _load_version_from_directory(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        directory: Path,
    ) -> ReviewDocumentVersion:
        self._assert_directory_safe(
            directory,
            label="Review Document Version directory",
        )
        self._assert_exact_directory_entries(
            directory,
            required=_REQUIRED_VERSION_DIRECTORY_ENTRIES,
            optional=_OPTIONAL_VERSION_DIRECTORY_ENTRIES,
            label="Review Document Version directory",
        )

        manifest_path = (
            directory
            / REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME
        )
        revisions_directory = (
            directory
            / REVISIONS_DIRECTORY_NAME
        )
        scoped_actions_directory = (
            directory
            / SCOPED_ACTIONS_DIRECTORY_NAME
        )
        finalized_directory = (
            directory
            / FINALIZED_DIRECTORY_NAME
        )

        self._assert_file_safe(
            manifest_path,
            label="Review Document Version Manifest",
        )
        self._assert_directory_safe(
            revisions_directory,
            label="Review Revision root",
        )
        self._assert_directory_safe(
            scoped_actions_directory,
            label="Scoped Review Action root",
        )

        if finalized_directory.exists():
            self._assert_directory_safe(
                finalized_directory,
                label="finalized Review artifact root",
            )

        version = review_document_version_from_json(
            self._read_text(
                manifest_path,
                label="Review Document Version Manifest",
            )
        )

        if version.project_id != project_id:
            raise ReviewIntegrityError(
                "Review Document Version project_id does not "
                "match its Project directory."
            )

        if (
            version.review_document_id
            != review_document_id
        ):
            raise ReviewIntegrityError(
                "Review Document Version does not belong to "
                "its Review Document directory."
            )

        if (
            version.review_document_version_id
            != review_document_version_id
        ):
            raise ReviewIntegrityError(
                "Review Document Version ID does not match "
                "its version directory."
            )

        return version

    def _load_revision_file(
        self,
        path: Path,
        *,
        expected_project_id: str,
        expected_document_id: str,
        expected_version_id: str,
        expected_revision_id: str,
    ) -> ReviewRevision:
        self._assert_file_safe(
            path,
            label="Review Revision",
        )

        revision = review_revision_from_json(
            self._read_text(
                path,
                label="Review Revision",
            )
        )

        expected_filename = review_revision_filename(
            expected_revision_id
        )

        if path.name not in {
            expected_filename,
            f".{expected_filename}.tmp",
        }:
            raise ReviewIntegrityError(
                "Review Revision filename does not match "
                "its identifier."
            )

        if revision.project_id != expected_project_id:
            raise ReviewIntegrityError(
                "Review Revision project_id does not match "
                "its Project directory."
            )

        if (
            revision.review_document_id
            != expected_document_id
        ):
            raise ReviewIntegrityError(
                "Review Revision does not belong to its "
                "Review Document directory."
            )

        if (
            revision.review_document_version_id
            != expected_version_id
        ):
            raise ReviewIntegrityError(
                "Review Revision does not belong to its "
                "Review Document Version directory."
            )

        if revision.review_revision_id != expected_revision_id:
            raise ReviewIntegrityError(
                "Review Revision ID does not match its filename."
            )

        return revision

    def _load_project(self, project_id: str) -> None:
        try:
            self._workspace.load_project(project_id)
        except ProjectWorkspaceError as exc:
            raise ReviewReferenceError(
                "Review Workspace references an unavailable "
                f"Project: {project_id!r}."
            ) from exc

    def _ensure_directory(
        self,
        path: Path,
        *,
        parent: Path,
        label: str,
    ) -> None:
        self._assert_lexically_within(path, parent)

        if path.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if path.exists():
            if not path.is_dir():
                raise UnsafeReviewWorkspacePathError(
                    f"{label} is not a directory: {path}."
                )
            return

        if parent.is_symlink() or not parent.is_dir():
            raise UnsafeReviewWorkspacePathError(
                f"Parent directory is unsafe for {label}: "
                f"{parent}."
            )

        try:
            path.mkdir()
        except OSError as exc:
            raise ReviewPersistenceError(
                f"Unable to create {label} {path}: {exc}"
            ) from exc

    def _assert_optional_directory_safe(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if path.exists() and not path.is_dir():
            raise UnsafeReviewWorkspacePathError(
                f"{label} is not a directory: {path}."
            )

    def _assert_directory_safe(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if not path.exists() or not path.is_dir():
            raise ReviewIntegrityError(
                f"Required {label} is missing or not a "
                f"directory: {path}."
            )

    def _assert_file_safe(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeReviewWorkspacePathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if not path.exists() or not path.is_file():
            raise ReviewIntegrityError(
                f"Required {label} is missing or not a file: "
                f"{path}."
            )

    def _assert_exact_directory_entries(
        self,
        directory: Path,
        *,
        required: frozenset[str],
        optional: frozenset[str],
        label: str,
    ) -> None:
        try:
            entries = tuple(directory.iterdir())
        except OSError as exc:
            raise ReviewPersistenceError(
                f"Unable to inspect {label} {directory}: {exc}"
            ) from exc

        for entry in entries:
            if entry.is_symlink():
                raise UnsafeReviewWorkspacePathError(
                    f"Symbolic-link entries are rejected in "
                    f"{label}: {entry}."
                )

        actual = frozenset(
            entry.name
            for entry in entries
        )
        missing = required - actual
        unknown = actual - required - optional

        if missing or unknown:
            raise ReviewIntegrityError(
                f"{label} has invalid entries; "
                f"missing={sorted(missing)}, "
                f"unknown={sorted(unknown)}."
            )

    @staticmethod
    def _assert_lexically_within(
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.relative_to(parent)
        except ValueError as exc:
            raise UnsafeReviewWorkspacePathError(
                "Review Workspace path escapes its authority "
                f"root: {path}."
            ) from exc

    @staticmethod
    def _write_new_text(
        path: Path,
        text: str,
        *,
        label: str,
    ) -> None:
        try:
            with path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise ReviewPersistenceError(
                f"{label} path already exists: {path}."
            ) from exc
        except OSError as exc:
            raise ReviewPersistenceError(
                f"Unable to persist {label} {path}: {exc}"
            ) from exc

    @staticmethod
    def _read_text(
        path: Path,
        *,
        label: str,
    ) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ReviewPersistenceError(
                f"Unable to read {label} {path}: {exc}"
            ) from exc
