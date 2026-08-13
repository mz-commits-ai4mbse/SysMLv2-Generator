from __future__ import annotations

from types import SimpleNamespace

from modules.sysml_generation.service import SysMLGenerationService


class _RecordingReadService:
    def __init__(self, snapshot) -> None:
        self.snapshot = snapshot
        self.calls: list[tuple[str, str]] = []

    def load_phase_j_input(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ):
        self.calls.append((project_id, internal_engineering_model_id))
        return self.snapshot


class _RecordingBuilder:
    def __init__(self, result) -> None:
        self.result = result
        self.calls = []

    def build(self, snapshot):
        self.calls.append(snapshot)
        return self.result


def test_generation_service_forwards_exact_explicit_iem_identity() -> None:
    snapshot = SimpleNamespace(marker="snapshot")
    result = SimpleNamespace(marker="artifact-set")

    reader = _RecordingReadService(snapshot)
    builder = _RecordingBuilder(result)

    service = SysMLGenerationService(
        read_service=reader,
        artifact_builder=builder,
    )

    actual = service.generate("000123", "IEM-000456")

    assert actual is result
    assert reader.calls == [("000123", "IEM-000456")]
    assert builder.calls == [snapshot]


def test_generation_service_has_no_implicit_latest_selection_api() -> None:
    service = SysMLGenerationService(
        read_service=_RecordingReadService(SimpleNamespace()),
        artifact_builder=_RecordingBuilder(SimpleNamespace()),
    )

    assert not hasattr(service, "generate_latest")
    assert not hasattr(service, "load_latest")
    assert not hasattr(service, "latest")


def test_generation_service_does_not_own_validation_or_publication() -> None:
    service = SysMLGenerationService(
        read_service=_RecordingReadService(SimpleNamespace()),
        artifact_builder=_RecordingBuilder(SimpleNamespace()),
    )

    assert not hasattr(service, "validate")
    assert not hasattr(service, "publish")
    assert not hasattr(service, "write_output")
