"""Phase-K validation for authority-backed SysML v2 artifacts."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path, PurePosixPath
import uuid

from modules.sysml_generation.authority_backed import (
    AUTHORITY_BACKED_SYSML_ARTIFACT_SCHEMA_VERSION,
    AuthorityBackedGeneratedSysMLArtifactSet,
)
from modules.sysml_generation.errors import SysMLGenerationError
from modules.sysml_generation.identifiers import (
    validate_generated_sysml_symbol,
    validate_generated_sysml_unit_id,
)

from .artifact_structure_validator import validate_artifact_structure
from .errors import SysMLValidationContractError
from .finding_support import blocking_finding, sort_validation_findings
from .fingerprints import calculate_json_fingerprint, validate_sha256_fingerprint
from .relationship_validator import validate_relationship_consistency
from .service import (
    SYSML_VALIDATION_RESULT_SCHEMA_VERSION,
    calculate_validation_input_fingerprint,
    calculate_validation_result_fingerprint,
    validate_validation_result_integrity,
)
from .syside_cli import SysideCliValidator
from .target_notation_validator import validate_target_notation_subset
from .types import (
    SysMLExternalValidationEvidence,
    SysMLExternalValidatorIdentity,
    SysMLValidationFinding,
    SysMLValidationLocation,
    SysMLValidationProfileReference,
    SysMLValidationResult,
)
from .validation_context import validate_generation_context
from .validation_profile import load_validation_profile


_INCOMPLETE_CONTEXT_CODES = frozenset(
    {
        "K2_TARGET_NOTATION_UNRESOLVABLE",
        "K2_GENERATION_PROFILE_UNRESOLVABLE",
        "K2_ARTIFACT_STRUCTURE_UNRESOLVABLE",
        "K2_GENERATOR_RULES_UNRESOLVABLE",
        "K2_GENERATION_PROFILE_CHAIN_UNRESOLVABLE",
        "K2_ARTIFACT_STRUCTURE_CHAIN_UNRESOLVABLE",
        "K2_MODEL_STRUCTURE_PROFILE_UNRESOLVABLE",
    }
)


class AuthorityBackedSysMLValidationService:
    """Validate v2 SysML artifacts without Candidate Review assumptions."""

    def __init__(self, *, external_validator=None):
        self._external_validator = (
            SysideCliValidator()
            if external_validator is None
            else external_validator
        )

    def validate(self, artifact_set):
        if not isinstance(
            artifact_set,
            AuthorityBackedGeneratedSysMLArtifactSet,
        ):
            raise SysMLValidationContractError(
                "Authority-backed Phase K requires the v2 SysML artifact contract."
            )

        profile = load_validation_profile()
        profile_reference = SysMLValidationProfileReference(
            profile_id=str(profile["profile_id"]),
            profile_version=str(profile["profile_version"]),
            profile_fingerprint=calculate_json_fingerprint(profile),
        )

        internal_findings = []
        for validator in (
            validate_authority_backed_artifact_integrity,
            validate_generation_context,
            validate_target_notation_subset,
            validate_artifact_structure,
            validate_authority_backed_traceability,
            validate_relationship_consistency,
        ):
            internal_findings.extend(validator(artifact_set))

        external_run = self._external_validator.validate(artifact_set)
        findings = sort_validation_findings(
            (*internal_findings, *external_run.findings)
        )
        external_complete = (
            external_run.evidence.execution_status == "completed"
        )
        if not external_complete and not any(
            item.blocking
            and item.category == "validator_infrastructure"
            for item in findings
        ):
            raise SysMLValidationContractError(
                "Incomplete external validation requires an explicit "
                "validator_infrastructure finding."
            )

        validation_status, publication_gate = _status_and_gate(
            findings=findings,
            external_complete=external_complete,
        )
        publication = profile["publication_policy"]
        if validation_status == "valid":
            validation_status = publication[
                "pass_validation_status"
            ]
            publication_gate = publication[
                "pass_publication_gate"
            ]
        elif validation_status == "incomplete":
            validation_status = publication[
                "incomplete_validation_status"
            ]
            publication_gate = publication[
                "incomplete_publication_gate"
            ]
        else:
            publication_gate = publication[
                "blocking_finding_gate"
            ]

        validation_input_fingerprint = (
            calculate_validation_input_fingerprint(
                source_artifact_set_fingerprint=(
                    artifact_set.content_fingerprint
                ),
                validation_profile_reference=profile_reference,
                external_validator_identity=(
                    external_run.evidence.validator_identity
                ),
            )
        )

        provisional = SysMLValidationResult(
            schema_version=SYSML_VALIDATION_RESULT_SCHEMA_VERSION,
            project_id=artifact_set.project_id,
            source_internal_engineering_model_id=(
                artifact_set.source_internal_engineering_model_id
            ),
            source_artifact_set_fingerprint=(
                artifact_set.content_fingerprint
            ),
            validation_profile_reference=profile_reference,
            validation_input_fingerprint=(
                validation_input_fingerprint
            ),
            external_validator_evidence=(
                external_run.evidence,
            ),
            findings=findings,
            validation_status=validation_status,
            publication_gate=publication_gate,
            content_fingerprint="0" * 64,
        )
        result = replace(
            provisional,
            content_fingerprint=(
                calculate_validation_result_fingerprint(
                    provisional
                )
            ),
        )
        validate_validation_result_integrity(result)
        return result


class AuthorityBackedSysMLValidationRepository:
    def __init__(
        self,
        root=Path("data/projects"),
        *,
        validation_service=None,
    ):
        self.root = Path(root)
        self._service = (
            AuthorityBackedSysMLValidationService()
            if validation_service is None
            else validation_service
        )

    def validate(self, artifact_set):
        existing = self.load_if_available(
            artifact_set.project_id,
            artifact_set.source_internal_engineering_model_id,
        )
        if existing is not None:
            if (
                existing.source_artifact_set_fingerprint
                != artifact_set.content_fingerprint
            ):
                raise SysMLValidationContractError(
                    "Existing authority-backed validation result is stale."
                )
            return existing

        result = self._service.validate(artifact_set)
        directory = (
            self.root
            / artifact_set.project_id
            / "sysml_validation_v2"
            / artifact_set.source_internal_engineering_model_id
        )
        directory.parent.mkdir(parents=True, exist_ok=True)
        if directory.exists() or directory.is_symlink():
            raise SysMLValidationContractError(
                "Authority-backed validation path is occupied."
            )
        temp = directory.parent / (
            f".{artifact_set.source_internal_engineering_model_id}."
            f"tmp-{uuid.uuid4().hex}"
        )
        temp.mkdir()
        (temp / "validation_result.json").write_text(
            authority_validation_result_to_json(result),
            encoding="utf-8",
        )
        temp.replace(directory)
        return self.load(
            artifact_set.project_id,
            artifact_set.source_internal_engineering_model_id,
        )

    def load_if_available(self, project_id, iem_id):
        path = (
            self.root
            / project_id
            / "sysml_validation_v2"
            / iem_id
            / "validation_result.json"
        )
        if not path.exists():
            return None
        return self.load(project_id, iem_id)

    def load(self, project_id, iem_id):
        path = (
            self.root
            / project_id
            / "sysml_validation_v2"
            / iem_id
            / "validation_result.json"
        )
        if path.is_symlink() or not path.is_file():
            raise SysMLValidationContractError(
                "Authority-backed validation result not found."
            )
        result = authority_validation_result_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            result.project_id != project_id
            or result.source_internal_engineering_model_id != iem_id
        ):
            raise SysMLValidationContractError(
                "Authority-backed validation result binding is invalid."
            )
        return result


def validate_authority_backed_artifact_integrity(
    artifact_set,
):
    findings = []
    category = "artifact_integrity"

    if not isinstance(
        artifact_set,
        AuthorityBackedGeneratedSysMLArtifactSet,
    ):
        return (
            blocking_finding(
                code="K2_AUTHORITY_ARTIFACT_TYPE_INVALID",
                category=category,
                message=(
                    "Authority-backed validation requires the v2 "
                    "generated artifact contract."
                ),
            ),
        )

    if (
        artifact_set.schema_version
        != AUTHORITY_BACKED_SYSML_ARTIFACT_SCHEMA_VERSION
    ):
        findings.append(
            blocking_finding(
                code="K2_AUTHORITY_ARTIFACT_SCHEMA_UNSUPPORTED",
                category=category,
                message=(
                    "Authority-backed generated artifact schema is unsupported."
                ),
            )
        )

    for value, label, code in (
        (
            artifact_set.source_iem_content_fingerprint,
            "source IEM content fingerprint",
            "K2_SOURCE_IEM_FINGERPRINT_INVALID",
        ),
        (
            artifact_set.generation_input_fingerprint,
            "generation input fingerprint",
            "K2_GENERATION_INPUT_FINGERPRINT_INVALID",
        ),
        (
            artifact_set.content_fingerprint,
            "artifact-set content fingerprint",
            "K2_ARTIFACT_FINGERPRINT_INVALID",
        ),
    ):
        try:
            validate_sha256_fingerprint(value, label=label)
        except Exception:
            findings.append(
                blocking_finding(
                    code=code,
                    category=category,
                    message=f"{label} is not a valid SHA-256 fingerprint.",
                )
            )

    if not artifact_set.units:
        findings.append(
            blocking_finding(
                code="K2_ARTIFACT_UNITS_EMPTY",
                category=category,
                message="Generated artifact set must contain generated units.",
            )
        )

    unit_ids = set()
    paths = set()
    symbols = set()
    for unit in artifact_set.units:
        try:
            validate_generated_sysml_unit_id(unit.unit_id)
        except SysMLGenerationError:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_ID_INVALID",
                    category=category,
                    message="Generated unit ID is invalid.",
                    generated_unit_id=unit.unit_id,
                )
            )
        if unit.unit_id in unit_ids:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_ID_DUPLICATE",
                    category=category,
                    message="Generated unit IDs must be unique.",
                    generated_unit_id=unit.unit_id,
                )
            )
        unit_ids.add(unit.unit_id)

        if not _safe_relative_sysml_path(unit.relative_path):
            findings.append(
                blocking_finding(
                    code="K2_UNIT_PATH_UNSAFE",
                    category=category,
                    message=(
                        "Generated unit path must be a safe relative .sysml path."
                    ),
                    generated_unit_id=unit.unit_id,
                )
            )
        if unit.relative_path in paths:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_PATH_DUPLICATE",
                    category=category,
                    message="Generated unit paths must be unique.",
                    generated_unit_id=unit.unit_id,
                )
            )
        paths.add(unit.relative_path)

        expected_unit_fp = __import__("hashlib").sha256(
            unit.content.encode("utf-8")
        ).hexdigest()
        if expected_unit_fp != unit.content_fingerprint:
            findings.append(
                blocking_finding(
                    code="K2_UNIT_FINGERPRINT_MISMATCH",
                    category=category,
                    message="Generated unit fingerprint mismatch.",
                    generated_unit_id=unit.unit_id,
                )
            )
        if "\r" in unit.content or not unit.content.endswith("\n"):
            findings.append(
                blocking_finding(
                    code="K2_UNIT_LINE_ENDING_INVALID",
                    category=category,
                    message="Generated unit must use controlled LF endings.",
                    generated_unit_id=unit.unit_id,
                )
            )

        for symbol in unit.generated_symbol_ids:
            try:
                validate_generated_sysml_symbol(symbol)
            except SysMLGenerationError:
                findings.append(
                    blocking_finding(
                        code="K2_GENERATED_SYMBOL_INVALID",
                        category=category,
                        message="Generated symbol is invalid.",
                        generated_unit_id=unit.unit_id,
                        generated_symbol_id=symbol,
                    )
                )
            if symbol in symbols:
                findings.append(
                    blocking_finding(
                        code="K2_GENERATED_SYMBOL_DUPLICATE",
                        category=category,
                        message="Generated symbols must be globally unique.",
                        generated_unit_id=unit.unit_id,
                        generated_symbol_id=symbol,
                    )
                )
            symbols.add(symbol)

    expected_input = calculate_json_fingerprint(
        {
            "source_iem_content_fingerprint": (
                artifact_set.source_iem_content_fingerprint
            ),
            "generation_context": asdict(
                artifact_set.generation_context
            ),
        }
    )
    if expected_input != artifact_set.generation_input_fingerprint:
        findings.append(
            blocking_finding(
                code="K2_GENERATION_INPUT_FINGERPRINT_MISMATCH",
                category=category,
                message=(
                    "Authority-backed generation_input_fingerprint mismatch."
                ),
            )
        )

    payload = asdict(artifact_set)
    transferred_fp = payload.pop("content_fingerprint")
    expected_artifact_fp = calculate_json_fingerprint(payload)
    if expected_artifact_fp != transferred_fp:
        findings.append(
            blocking_finding(
                code="K2_ARTIFACT_FINGERPRINT_MISMATCH",
                category=category,
                message=(
                    "Authority-backed artifact fingerprint does not match "
                    "transferred content."
                ),
            )
        )

    return sort_validation_findings(findings)


def validate_authority_backed_traceability(artifact_set):
    findings = []
    category = "traceability"
    units = {
        item.unit_id: item
        for item in artifact_set.units
    }
    expected_symbols = {
        (unit.unit_id, symbol)
        for unit in artifact_set.units
        for symbol in unit.generated_symbol_ids
    }
    expected_ime = {
        item
        for unit in artifact_set.units
        for item in unit.source_internal_model_element_ids
    }
    expected_imr = {
        item
        for unit in artifact_set.units
        for item in unit.source_internal_model_relationship_ids
    }

    seen_symbols = set()
    seen_ime = set()
    seen_imr = set()

    for entry in artifact_set.traceability_entries:
        key = (
            entry.generated_unit_id,
            entry.generated_symbol_id,
        )
        if key in seen_symbols:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SYMBOL_DUPLICATE",
                    category=category,
                    message="Generated traceability key must be unique.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        seen_symbols.add(key)

        unit = units.get(entry.generated_unit_id)
        if (
            unit is None
            or entry.generated_symbol_id
            not in unit.generated_symbol_ids
        ):
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SYMBOL_UNKNOWN",
                    category=category,
                    message="Traceability references an unknown unit/symbol.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

        if (
            entry.source_internal_engineering_model_id
            != artifact_set.source_internal_engineering_model_id
        ):
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SOURCE_IEM_MISMATCH",
                    category=category,
                    message="Traceability source IEM binding is invalid.",
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )

        has_ime = (
            entry.source_internal_model_element_id is not None
        )
        has_imr = (
            entry.source_internal_model_relationship_id is not None
        )
        if has_ime == has_imr:
            findings.append(
                blocking_finding(
                    code="K2_TRACE_SOURCE_KIND_INVALID",
                    category=category,
                    message=(
                        "Traceability must reference exactly one IME or IMR."
                    ),
                    generated_unit_id=entry.generated_unit_id,
                    generated_symbol_id=entry.generated_symbol_id,
                    generated_location=entry.generated_location,
                )
            )
        elif has_ime:
            source_id = entry.source_internal_model_element_id
            if source_id in seen_ime:
                findings.append(
                    blocking_finding(
                        code="K2_TRACE_IME_DUPLICATE",
                        category=category,
                        message="A source IME must be traced exactly once.",
                    )
                )
            seen_ime.add(source_id)
            _validate_element_authority(
                entry,
                findings,
            )
        else:
            source_id = entry.source_internal_model_relationship_id
            if source_id in seen_imr:
                findings.append(
                    blocking_finding(
                        code="K2_TRACE_IMR_DUPLICATE",
                        category=category,
                        message="A source IMR must be traced exactly once.",
                    )
                )
            seen_imr.add(source_id)
            _validate_relationship_authority(
                entry,
                findings,
            )

        location = entry.generated_location
        if unit is not None:
            line_count = len(unit.content.splitlines())
            if (
                location.start_line < 1
                or location.end_line < location.start_line
                or location.end_line > line_count
            ):
                findings.append(
                    blocking_finding(
                        code="K2_TRACE_LOCATION_OUT_OF_RANGE",
                        category=category,
                        message=(
                            "Traceability location is outside generated content."
                        ),
                        generated_unit_id=entry.generated_unit_id,
                        generated_symbol_id=entry.generated_symbol_id,
                        generated_location=location,
                    )
                )

    if seen_symbols != expected_symbols:
        findings.append(
            blocking_finding(
                code="K2_TRACE_SYMBOL_COVERAGE_MISMATCH",
                category=category,
                message=(
                    "Traceability must cover every generated symbol exactly once."
                ),
            )
        )
    if seen_ime != expected_ime:
        findings.append(
            blocking_finding(
                code="K2_TRACE_IME_COVERAGE_MISMATCH",
                category=category,
                message="Traceability IME coverage mismatch.",
            )
        )
    if seen_imr != expected_imr:
        findings.append(
            blocking_finding(
                code="K2_TRACE_IMR_COVERAGE_MISMATCH",
                category=category,
                message="Traceability IMR coverage mismatch.",
            )
        )

    return sort_validation_findings(findings)


def authority_validation_result_to_json(value):
    return json.dumps(
        asdict(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def authority_validation_result_from_json(text):
    try:
        raw = json.loads(text)
        profile = SysMLValidationProfileReference(
            **raw["validation_profile_reference"]
        )
        evidence = []
        for item in raw["external_validator_evidence"]:
            evidence.append(
                SysMLExternalValidationEvidence(
                    validator_identity=(
                        SysMLExternalValidatorIdentity(
                            **item["validator_identity"]
                        )
                    ),
                    execution_status=item["execution_status"],
                    exit_code=item["exit_code"],
                    normalized_diagnostic_count=(
                        item["normalized_diagnostic_count"]
                    ),
                )
            )
        findings = []
        for item in raw["findings"]:
            location_raw = item["generated_location"]
            location = (
                None
                if location_raw is None
                else SysMLValidationLocation(**location_raw)
            )
            findings.append(
                SysMLValidationFinding(
                    code=item["code"],
                    category=item["category"],
                    severity=item["severity"],
                    blocking=item["blocking"],
                    message=item["message"],
                    generated_unit_id=item["generated_unit_id"],
                    generated_symbol_id=item["generated_symbol_id"],
                    generated_location=location,
                    validator_id=item["validator_id"],
                    validator_rule_id=item["validator_rule_id"],
                )
            )
        result = SysMLValidationResult(
            schema_version=raw["schema_version"],
            project_id=raw["project_id"],
            source_internal_engineering_model_id=raw[
                "source_internal_engineering_model_id"
            ],
            source_artifact_set_fingerprint=raw[
                "source_artifact_set_fingerprint"
            ],
            validation_profile_reference=profile,
            validation_input_fingerprint=raw[
                "validation_input_fingerprint"
            ],
            external_validator_evidence=tuple(evidence),
            findings=tuple(findings),
            validation_status=raw["validation_status"],
            publication_gate=raw["publication_gate"],
            content_fingerprint=raw["content_fingerprint"],
        )
    except Exception as exc:
        raise SysMLValidationContractError(
            "Authority-backed validation result JSON violates the contract."
        ) from exc
    validate_validation_result_integrity(result)
    return result


def _validate_element_authority(entry, findings):
    category = "traceability"
    if not entry.approved_input_id:
        findings.append(
            blocking_finding(
                code="K2_TRACE_APPROVED_INPUT_MISSING",
                category=category,
                message=(
                    "Generated element trace must retain Approved Input identity."
                ),
            )
        )
    if len(entry.authority_references) != 1:
        findings.append(
            blocking_finding(
                code="K2_TRACE_PLACEMENT_AUTHORITY_INVALID",
                category=category,
                message=(
                    "Generated element requires exactly one placement authority."
                ),
            )
        )
        return
    authority = entry.authority_references[0]
    if (
        authority.authority_type != "model_placement_decision"
        or not authority.authority_id.startswith("MPD-")
    ):
        findings.append(
            blocking_finding(
                code="K2_TRACE_PLACEMENT_AUTHORITY_INVALID",
                category=category,
                message=(
                    "Generated element authority must be the Human "
                    "Model Placement decision."
                ),
            )
        )
    _validate_authority_fingerprint(authority, findings)


def _validate_relationship_authority(entry, findings):
    category = "traceability"
    if len(entry.authority_references) != 2:
        findings.append(
            blocking_finding(
                code="K2_TRACE_RELATIONSHIP_AUTHORITY_INVALID",
                category=category,
                message=(
                    "Generated Relationship requires engineering and final "
                    "representation authority."
                ),
            )
        )
        return

    by_type = {
        item.authority_type: item
        for item in entry.authority_references
    }
    engineering = by_type.get(
        "engineering_relationship_decision"
    )
    final = by_type.get(
        "final_model_relationship_resolution"
    )
    if (
        engineering is None
        or not engineering.authority_id.startswith("SRD-")
        or final is None
        or not final.authority_id.startswith("FAD-")
    ):
        findings.append(
            blocking_finding(
                code="K2_TRACE_RELATIONSHIP_AUTHORITY_INVALID",
                category=category,
                message=(
                    "Generated Relationship authority must retain SRD and FAD."
                ),
            )
        )
        return
    _validate_authority_fingerprint(engineering, findings)
    _validate_authority_fingerprint(final, findings)


def _validate_authority_fingerprint(authority, findings):
    try:
        validate_sha256_fingerprint(
            authority.authority_fingerprint,
            label="authority fingerprint",
        )
    except Exception:
        findings.append(
            blocking_finding(
                code="K2_TRACE_AUTHORITY_FINGERPRINT_INVALID",
                category="traceability",
                message="Generated Human authority fingerprint is invalid.",
            )
        )


def _status_and_gate(*, findings, external_complete):
    has_invalid_blocking = any(
        item.blocking
        and item.category != "validator_infrastructure"
        and item.code not in _INCOMPLETE_CONTEXT_CODES
        for item in findings
    )
    has_incomplete_blocking = any(
        item.blocking
        and (
            item.category == "validator_infrastructure"
            or item.code in _INCOMPLETE_CONTEXT_CODES
        )
        for item in findings
    )
    if has_invalid_blocking:
        return "invalid", "blocked"
    if not external_complete or has_incomplete_blocking:
        return "incomplete", "blocked"
    return "valid", "passed"


def _safe_relative_sysml_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and value == path.as_posix()
        and path.suffix == ".sysml"
        and all(
            part not in {"", ".", ".."}
            for part in path.parts
        )
    )
