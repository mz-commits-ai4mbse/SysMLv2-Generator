# ADR-009

Textual Source Processing Boundary

Status

Accepted

Date

2026-07-22

Context

The Turing Generator shall ingest heterogeneous customer documents and derive
traceable engineering information through the agentic ingestion pipeline.

The original Phase F implementation reads UTF-8 text directly from a source
path. Phase P introduces registered project sources and heterogeneous,
source-traceable information units.

Modern LLM APIs can accept document files such as PDF, DOCX, PPTX and
spreadsheets directly. Some providers and models may additionally interpret
page images, diagrams and other visual content.

Supporting arbitrary multimodal engineering sources would require architectural
decisions for:

- optical character recognition
- drawing and diagram interpretation
- symbol recognition
- geometric and spatial relationships
- visual provenance
- multimodal uncertainty
- conflict resolution between textual and visual information
- human validation of visually extracted statements

These concerns exceed the accepted MVP and thesis scope.

Decision

## Supported Information Modality

The only supported source-information modality in the MVP is textual
information.

The original source file does not have to be a plain-text file.

A binary container format may be used when its relevant textual content can be
converted deterministically into a traceable textual representation before the
LLM-based engineering extraction begins.

Examples include:

- a PDF containing a machine-readable text layer
- a future DOCX adapter that extracts paragraphs and tables
- other document containers for which a deterministic textual adapter is
  explicitly implemented and validated

File-container support and information-modality support are separate concerns.

Supporting a file extension does not imply support for every type of content
that the file may contain.

## Immutable Original Source

The registered original source remains immutable.

It is stored with:

- `project_id`
- `source_id`
- original filename
- media type
- byte size
- SHA-256 hash
- explicit source role
- registration timestamp

Normalization never replaces or modifies the registered original source.

## Deterministic Text Normalization

Before an LLM processes a registered source, the source must produce a
normalized textual artifact through a deterministic, versioned source adapter.

The normalized artifact must remain traceable to:

- `project_id`
- `source_id`
- original source SHA-256
- adapter identifier
- adapter version
- source locations used to produce the normalized text

Source-location references depend on the input format.

Examples include:

- text and Markdown: line ranges
- PDF: page references
- JSON: JSON Pointer locations
- CSV: row and column references
- future DOCX support: sections, paragraphs or table cells

The normalized textual artifact is a derived processing artifact. It is not an
authoritative engineering source and does not replace the original file.

## PDF Boundary

The MVP may support PDF files only when they contain a usable
machine-readable text layer.

PDF normalization extracts textual content and retains page boundaries for
traceability.

The MVP does not interpret:

- technical drawings
- diagrams
- photographs
- graphical relationships
- dimensions represented only visually
- symbols represented only visually
- scanned pages without a machine-readable text layer

A PDF must not be sent as unrestricted multimodal input when doing so would
allow the selected model to derive engineering information from visual content
outside the accepted MVP scope.

## Explicit Failure States

A source that cannot produce sufficient traceable textual content must not be
silently treated as an empty or irrelevant source.

Processing must end with an explicit diagnostic state such as:

- `unsupported_non_textual_content`
- `text_extraction_insufficient`
- `unsupported_source_format`
- `source_normalization_failed`

The original source remains registered and available for diagnosis.

No failed source is silently discarded or promoted.

## LLM Processing Boundary

The LLM receives the normalized textual artifact together with explicit
provenance information.

The LLM may semantically interpret, classify and derive candidate engineering
information from that textual input.

The LLM must not silently invent information that is absent from the normalized
source.

The LLM output remains unreviewed and non-authoritative.

## Canonical Extraction Output

The canonical result of LLM extraction is validated structured data.

The canonical structured output shall use a versioned JSON contract for
source-traceable candidate information units.

Markdown is not the canonical extraction format.

A Markdown review report is generated deterministically from the validated
structured extraction data.

The raw LLM output is retained as a technical traceability artifact but is not
used directly as approved engineering information.

## Human-in-the-Loop Boundary

Extracted information units remain unreviewed until a human decision has been
recorded.

The review workflow must allow information units to be:

- accepted
- corrected
- rejected
- marked as requiring clarification

Generating or reading a Markdown report does not approve its contents.

Phase P may persist preliminary and review-oriented information, but it does not
promote information into generation-ready input.

Approved Input Promotion remains assigned to Phase G.

Only explicitly human-approved structured engineering information may become
input to later model-candidate and model-generation stages.

## Provider and Model Independence

The Project Workspace does not assume that every provider, endpoint or model
supports the same file types.

Provider-specific capabilities are evaluated separately from source
registration.

The deterministic normalized textual artifact forms the provider-independent
boundary for MVP ingestion.

Direct provider file input may be introduced later only when it preserves the
accepted modality boundary, provenance requirements and review behavior.

## Excluded MVP Scope

The following capabilities are explicitly excluded from the MVP:

- optical character recognition
- scanned-document interpretation
- technical-drawing interpretation
- diagram interpretation
- image-based engineering evidence
- handwritten-content recognition
- audio ingestion
- video ingestion
- spatial or geometric relation extraction from visual media
- general multimodal engineering information extraction

Consequences

Positive consequences:

- The MVP scope remains technically and academically manageable.
- Existing text-oriented Phase F pipeline concepts remain reusable.
- Different source containers can use a common ingestion boundary.
- LLM inputs remain reproducible and provider-independent.
- Engineering statements can reference deterministic source locations.
- Human review operates on structured and traceable information units.
- Visual information cannot silently become engineering evidence.
- Future multimodal extensions have a clear architectural starting point.

Trade-offs:

- Scanned PDFs cannot be processed without a future OCR capability.
- Relevant information contained only in drawings or diagrams is not extracted.
- Binary document containers require a deterministic text adapter.
- Source normalization introduces an additional persisted artifact and
  validation step.
- Some direct multimodal capabilities of selected LLMs remain intentionally
  unused in the MVP.

Alternatives Considered

Accepting every file type supported by the selected LLM was rejected because
provider support does not establish traceability, reproducibility or a stable
human-review boundary.

Sending PDFs directly as unrestricted multimodal model input was rejected for
the MVP because it could introduce engineering information derived from
drawings, images or spatial relationships without an accepted visual-evidence
contract.

Restricting registration to plain-text file extensions was rejected because
common customer documents may use binary containers while still containing
deterministically extractable textual information.

Using Markdown as the canonical extracted-information store was rejected
because Markdown is intended for human-readable reporting rather than strict
schema validation and downstream processing.

Replacing the original file with extracted text was rejected because it would
destroy source integrity and weaken traceability.

Affected Components

- Project Source Registry introduced in P3
- deterministic source-normalization adapters
- Phase F ingestion integration
- framework-mapped information units introduced in P4
- processing state and artifact organization introduced in P5
- human review and Approved Input Promotion introduced in Phase G
- future provider and model adapters
- future SysML v2 representation of the Turing Generator

Model Impact

When the authoritative SysML v2 model is next updated, it shall represent the
accepted textual-source-processing constraint.

The model update shall distinguish:

- supported textual information
- text-bearing document containers
- excluded non-textual and multimodal information
- deterministic source normalization
- human review before Approved Input Promotion
- multimodal processing as a future extension

Stable model element identifiers and their relationships shall be assigned in
the authoritative model. This ADR does not create or redefine those engineering
model elements.

SSOT Impact

The next scheduled SSOT UPDATE after completion of Phase P shall document:

- the textual-only MVP information-modality constraint
- deterministic text normalization
- the exclusion of OCR, drawings and multimodal extraction
- structured JSON as the canonical unreviewed extraction format
- Markdown as the derived review representation
- the required future SysML v2 model synchronization

Supersedes

None

Related Roadmap Phase

- P3 — Source Registry and Mandatory Project Assignment
- P4 — Framework-mapped Heterogeneous Information Units
- P5 — Processing State and Artifact Organization
- G — Approved Input Promotion

Related Implementation

Not yet implemented.

Implementation that depends on this boundary shall begin only after this
accepted ADR has been committed and pushed by the project owner.