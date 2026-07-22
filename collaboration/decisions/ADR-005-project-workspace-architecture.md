# ADR-005

Project Workspace Architecture

Status

Accepted

Date

2026-07-21

Context

Phase P introduces a persistent Project Workspace around the completed Phase F
ingestion pipeline.

P1 established the versioned framework template
`TURING_RFLP_FRAMEWORK` version `1.0.0`.

P2 requires a deterministic architecture for:

- project identity
- project metadata
- workspace discovery
- persistence and reopening
- project isolation
- future source, information-unit, run and coverage storage
- validation and recovery behavior

The Project Workspace contains software-operational project metadata. It shall
not redefine engineering knowledge from the authoritative CATIA SysML v2 model.

External repositories, including the Apollo 11 repository, remain
non-normative references and do not define this architecture.

Decision

## Project Identity

Every project receives an immutable technical identifier named `project_id`.

The `project_id`:

- is stored as a JSON string
- consists of exactly six decimal digits
- matches `^[0-9]{6}$`
- permits leading zeros
- is unique within the configured workspace
- remains unchanged for the lifetime of the project
- is used as the project directory name

Valid examples include:

- `000042`
- `318604`
- `999999`

The identifier is generated with:

```python
f"{secrets.randbelow(1_000_000):06d}"
```

Before an identifier is accepted, the workspace checks whether the corresponding
project directory already exists. A collision causes generation to be repeated.

Failure to produce an available identifier raises
`ProjectIdGenerationError`.

The six-digit identifier is a technical identifier only. It is not a password,
authentication credential or security secret.

## Project Display Name

Every project has a human-readable `display_name`.

The display name:

- is required
- contains between 1 and 120 characters after trimming
- is mutable
- must be unique across the complete configured workspace

Display-name uniqueness is checked during:

- project creation
- project rename
- workspace validation

Uniqueness comparison uses one deterministic normalization function:

1. trim leading and trailing whitespace
2. collapse consecutive whitespace
3. apply Unicode normalization
4. apply case-insensitive `casefold()` comparison

The original validated display text is stored in the manifest. The normalized
comparison value is derived and is not persisted.

Two projects must therefore not use names that differ only through casing,
equivalent Unicode representation or whitespace formatting.

The immutable `project_id` remains the authoritative identity even when the
display name changes.

## Workspace Root

The product workspace root is:

`data/projects`

The root is injectable so that tests and future integrations can use an isolated
location.

A persisted project is located at:

`data/projects/<project_id>/`

The P2 project directory initially contains exactly one required file:

`data/projects/<project_id>/project_manifest.json`

P2 does not pre-create empty directories.

Later phases create their own storage only when required:

- P3 owns `sources/`
- P4 owns `information_units/`
- P5 owns `runs/`
- P6 owns `coverage/`

This avoids placeholder directories whose contracts have not yet been
implemented.

## Project Manifest Contract

The manifest schema version is:

`1.0.0`

The manifest contains exactly these top-level fields:

```json
{
  "schema_version": "1.0.0",
  "project_id": "318604",
  "display_name": "Example Project",
  "description": "",
  "framework_template": {
    "template_id": "TURING_RFLP_FRAMEWORK",
    "template_version": "1.0.0"
  },
  "created_at": "2026-07-21T12:00:00Z",
  "updated_at": "2026-07-21T12:00:00Z"
}
```

The required rules are:

- `schema_version` is exactly `1.0.0`
- `project_id` matches the six-digit identifier contract
- `project_id` matches the containing directory name
- `display_name` follows the display-name contract
- `description` is required
- `description` may be empty
- `description` contains at most 2000 characters
- `framework_template.template_id` is
  `TURING_RFLP_FRAMEWORK`
- `framework_template.template_version` is `1.0.0`
- `created_at` is a UTC ISO-8601 timestamp ending in `Z`
- `updated_at` is a UTC ISO-8601 timestamp ending in `Z`
- `created_at` remains unchanged after project creation
- `updated_at` is refreshed when mutable metadata changes
- unknown fields are rejected

The framework reference is pinned. A project is never silently migrated to a
new framework-template version.

A future framework upgrade requires an explicit migration decision and
implementation.

The manifest does not contain:

- source lists
- ingestion runs
- reports
- information units
- coverage results
- approval decisions
- generated-model data
- derived counters
- duplicated filesystem paths

Those concerns belong to their responsible Phase P or later components.

## Project Discovery

The workspace has no central `projects.json` index.

Projects are discovered by scanning:

`data/projects/*/project_manifest.json`

The directory structure and each validated manifest are the source of truth for
project discovery.

Avoiding a central index prevents the index and individual manifests from
diverging.

A scan returns a `WorkspaceScanResult` containing:

- `valid_projects`
- `workspace_issues`

A malformed project must not make valid projects unavailable.

The scanner reports issues for conditions including:

- visible directories whose names are not valid six-digit project identifiers
- missing manifests
- invalid JSON
- missing required fields
- unknown fields
- unsupported schema versions
- invalid framework references
- mismatch between `project_id` and directory name
- duplicate normalized display names
- unsafe paths
- symbolic-link project directories

When two manifests use the same normalized display name, both projects are
reported as conflicting. They remain identifiable through their immutable
project IDs so that one can be renamed explicitly.

Hidden filesystem metadata such as `.DS_Store` is ignored.

Temporary creation directories matching `.create-<project_id>.tmp` are ignored
during discovery but are never deleted automatically.

The workspace does not silently skip validation errors and does not
automatically repair or delete malformed data.

## Safe Persistence

Project creation uses a temporary sibling directory:

`data/projects/.create-<project_id>.tmp/`

Creation follows this sequence:

1. generate an available project ID
2. validate the requested metadata
3. create the temporary sibling directory
4. write the manifest into the temporary directory
5. read and validate the written manifest
6. atomically rename the temporary directory to the final project directory

Manifest updates use:

`project_manifest.json.tmp`

An update follows this sequence:

1. load and validate the existing manifest
2. apply the permitted metadata change
3. preserve `project_id`, `created_at` and the pinned framework reference
4. write the updated manifest to the temporary file
5. validate the temporary manifest
6. atomically replace the existing manifest with `os.replace`

Interrupted or invalid writes must not replace the last valid manifest.

Temporary data is retained for explicit diagnosis and is not automatically
deleted.

## Project Isolation and Path Safety

All project operations are resolved below the configured workspace root.

The implementation rejects:

- absolute external project paths
- path traversal
- paths escaping the configured workspace root
- symbolic-link project directories
- project IDs that do not match the six-digit identifier contract

The implementation does not follow symbolic links while discovering or loading
projects.

Sources, runs, information units and artifacts introduced in later steps must
reference the immutable `project_id` and remain within that project’s directory.

Cross-project data mixing is prohibited.

## Module Boundaries

P2 introduces:

```text
modules/project_workspace/
├── __init__.py
├── errors.py
├── identifiers.py
├── manifest.py
├── types.py
└── workspace.py
```

### `errors.py`

Defines the Project Workspace exception hierarchy:

- `ProjectWorkspaceError`
- `ProjectManifestError`
- `ProjectNotFoundError`
- `DuplicateProjectNameError`
- `ProjectIdGenerationError`
- `UnsafeProjectPathError`

### `identifiers.py`

Owns:

- six-digit project-ID generation
- project-ID validation
- deterministic display-name normalization

### `types.py`

Defines immutable data types:

- `FrameworkTemplateReference`
- `ProjectManifest`
- `WorkspaceIssue`
- `WorkspaceScanResult`

### `manifest.py`

Owns:

- manifest parsing
- manifest serialization
- manifest validation
- schema-version validation
- timestamp validation
- framework-reference validation
- rejection of unknown fields

It does not access project directories or scan the workspace.

### `workspace.py`

Owns:

- workspace scanning
- project creation
- project loading
- project metadata updates
- project-ID collision checks
- display-name uniqueness checks
- path and symbolic-link safety
- atomic filesystem operations
- workspace issue collection

The public `ProjectWorkspace` interface is:

```python
create_project(display_name, description="")
load_project(project_id)
update_project(
    project_id,
    *,
    display_name=None,
    description=None,
)
scan_projects()
```

The workspace root, ID generator and clock are injectable for deterministic
tests.

## Dependency Direction

The dependency direction is:

```text
workspace
    -> manifest
    -> identifiers
    -> types
    -> errors
    -> framework template validation
```

`modules/framework` does not depend on `modules/project_workspace`.

No reverse dependency from the framework-template module to the Project
Workspace is permitted.

## P2 Scope Boundary

P2 includes:

- project identity
- project metadata
- manifest validation
- safe persistence
- project discovery
- project reopening
- project isolation foundations

P2 does not include:

- project deletion or archiving
- source registration
- source upload
- information-unit persistence
- ingestion-run organization
- coverage calculation
- approval decisions
- model-candidate creation
- SysML v2 generation
- Project Dashboard integration

Those capabilities remain assigned to later roadmap steps.

Consequences

Positive consequences:

- Projects have compact, immutable and easily comparable identifiers.
- Display names remain human-readable without becoming technical identities.
- Duplicate or confusing display names are prevented.
- Project metadata can be validated independently of the UI.
- Projects can be reopened without maintaining a second index.
- Atomic writes reduce the risk of corrupted manifests.
- Invalid projects do not prevent access to valid projects.
- Future Phase P components receive a stable isolation boundary.
- Framework-template versions remain explicit and reproducible.

Trade-offs:

- The identifier space is limited to one million values.
- Identifier generation requires collision detection.
- Workspace scanning performs filesystem validation instead of reading a
  central index.
- Strict schema validation rejects manifests with unexpected fields.
- Incomplete temporary data requires explicit operator review.
- Framework-template upgrades require explicit migration.

Alternatives Considered

UUID project identifiers were rejected because they are unnecessarily difficult
to compare manually for the expected workspace size.

Mutable display names as project identities were rejected because renaming would
break references and equal or similar names would create ambiguity.

A central project index was rejected because it would duplicate manifest state
and introduce synchronization risk.

Pre-creating all future Phase P directories was rejected because their storage
contracts belong to later implementation steps.

Permissive manifest parsing and silent issue skipping were rejected because they
would hide inconsistent project state.

Automatic repair or deletion of malformed and temporary data was rejected
because recovery must remain explicit and auditable.

Affected Components

- `modules/project_workspace/`
- `tests/test_project_manifest.py`
- `tests/test_project_workspace.py`
- `data/projects/`
- later P3–P7 components that reference `project_id`

Supersedes

None

Related Roadmap Phase

P2 — Project Manifest and Workspace Structure

Related Implementation

Not yet implemented.

Implementation shall begin only after this accepted ADR has been committed and
pushed by the project owner.