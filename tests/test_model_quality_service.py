from datetime import datetime, timezone
from types import SimpleNamespace

from modules.model_quality.contract import (
    create_refinement_bundle,
    parse_refinement_response,
)
from modules.model_quality.repository import ModelQualityRepository
from modules.model_quality.service import ModelQualityLiveService


class _IEMRepo:
    def __init__(self):
        self.snapshot = SimpleNamespace(
            project_id="120412",
            internal_engineering_model_id="IEM-000001",
            content_fingerprint="a" * 64,
            elements=(
                SimpleNamespace(
                    internal_model_element_id="IME-000001",
                    approved_input_id="AEI-000001",
                    model_subject_key="subject",
                    name="remote control",
                    description="The remote expert may control the microscope.",
                    element_type="function",
                    model_area="functional",
                    framework_assignment="FUN",
                    content_fingerprint="1" * 64,
                ),
            ),
        )

    def load(self, project_id, iem_id):
        assert project_id == "120412"
        assert iem_id == "IEM-000001"
        return self.snapshot


class _Executor:
    def __init__(self):
        self.calls = 0

    def execute(self, *, request, review_id, output_dir, progress=None):
        self.calls += 1
        proposals = parse_refinement_response(
            request=request,
            output_text=(
                '{"proposals":[{'
                '"internal_model_element_id":"IME-000001",'
                '"refined_name":"Control microscope remotely",'
                '"refined_description":"The remote expert may control the microscope.",'
                '"quality_findings":["Action wording normalized."],'
                '"applied_rule_ids":["GENERAL_MEANING","GENERAL_CONCISE","FUNCTION_VERBAL"],'
                '"meaning_preserved":true,'
                '"unsupported_information_added":false,'
                '"requires_human_attention":false,'
                '"rationale":"Meaning preserved."'
                '}]}'
            ),
        )
        return create_refinement_bundle(
            request=request,
            review_id=review_id,
            provider="openai",
            model="gpt-test",
            proposals=proposals,
            supporting_response_fingerprints=("b" * 64,),
            generated_at="2026-08-25T16:00:00Z",
        )


def _clock():
    return datetime(2026, 8, 25, 16, 0, tzinfo=timezone.utc)


def _repo_root(tmp_path):
    root = tmp_path / "repo"
    path = root / "context/model_quality"
    path.mkdir(parents=True)
    (path / "model_quality_profile.json").write_text(
        """{
          "profile_id":"TURING_MODEL_QUALITY",
          "profile_version":"1.0.0",
          "rules":{
            "GENERAL_MEANING":"Preserve meaning.",
            "GENERAL_CONCISE":"Use concise wording.",
            "FUNCTION_VERBAL":"Use active verb-object wording."
          },
          "element_profiles":{
            "function":{"rule_ids":["GENERAL_MEANING","GENERAL_CONCISE","FUNCTION_VERBAL"]}
          }
        }""",
        encoding="utf-8",
    )
    return root


def test_service_generates_once_then_resumes_same_review(tmp_path):
    executor = _Executor()
    service = ModelQualityLiveService(
        projects_root=tmp_path / "projects",
        repo_root=_repo_root(tmp_path),
        repository=ModelQualityRepository(tmp_path / "projects"),
        internal_model_repository=_IEMRepo(),
        executor=executor,
        clock=_clock,
    )
    first_request, first_bundle = service.prepare(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )
    second_request, second_bundle = service.prepare(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )
    assert executor.calls == 1
    assert second_request == first_request
    assert second_bundle == first_bundle


def test_service_human_review_finalizes_quality_authority(tmp_path):
    executor = _Executor()
    service = ModelQualityLiveService(
        projects_root=tmp_path / "projects",
        repo_root=_repo_root(tmp_path),
        repository=ModelQualityRepository(tmp_path / "projects"),
        internal_model_repository=_IEMRepo(),
        executor=executor,
        clock=_clock,
    )
    _request, bundle = service.prepare(
        project_id="120412",
        internal_engineering_model_id="IEM-000001",
    )
    service.decide(
        bundle=bundle,
        internal_model_element_id="IME-000001",
        decision="approved",
        reviewer_identity="MZ",
        rationale="Reviewed.",
    )
    authority = service.finalize(bundle)
    assert authority.authority_set_id == "MQA-000001"
    assert authority.effective_decisions[0].approved_name == (
        "Control microscope remotely"
    )
