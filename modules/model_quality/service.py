"""Live SEM-015 service: IEM classification -> LLM refinement -> Human Review 2."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from modules.internal_model.authority_backed import (
    AuthorityBackedInternalModelRepository,
)

from .contract import (
    build_refinement_request,
    load_quality_profile,
)
from .errors import ModelQualityError
from .executor import ModelQualityRefinementExecutor
from .repository import ModelQualityRepository
from .serde import bundle_from_json, request_from_json


class ModelQualityLiveService:
    def __init__(
        self,
        *,
        projects_root=Path("data/projects"),
        repo_root=Path("."),
        repository=None,
        internal_model_repository=None,
        executor=None,
        provider="openai",
        model="gpt-5.5",
        api_key=None,
        clock=None,
    ) -> None:
        self.projects_root = Path(projects_root)
        self.repo_root = Path(repo_root)
        self.repository = (
            repository
            if repository is not None
            else ModelQualityRepository(self.projects_root)
        )
        self.internal_model_repository = (
            internal_model_repository
            if internal_model_repository is not None
            else AuthorityBackedInternalModelRepository(self.projects_root)
        )
        self.executor = executor
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self._clock = clock

    def prepare(
        self,
        *,
        project_id: str,
        internal_engineering_model_id: str,
        progress=None,
    ):
        snapshot = self.internal_model_repository.load(
            project_id,
            internal_engineering_model_id,
        )
        profile = load_quality_profile(
            self.repo_root
            / "context/model_quality/model_quality_profile.json"
        )
        request = build_refinement_request(
            snapshot=snapshot,
            quality_profile=profile,
        )
        existing = self.repository.find_review_for_source(
            project_id,
            internal_engineering_model_id,
            snapshot.content_fingerprint,
            request.request_fingerprint,
        )
        if existing is not None:
            review_id = existing["review_id"]
            raw_request, _raw_bundle = self.repository.raw_review(
                project_id,
                review_id,
            )
            req_path = (
                self.projects_root
                / project_id
                / "model_quality"
                / "reviews"
                / review_id
                / "request.json"
            )
            bundle_path = req_path.with_name("bundle.json")
            loaded_request = request_from_json(
                req_path.read_text(encoding="utf-8")
            )
            loaded_bundle = bundle_from_json(
                bundle_path.read_text(encoding="utf-8"),
                request=loaded_request,
            )
            if loaded_request.request_fingerprint != request.request_fingerprint:
                raise ModelQualityError(
                    "Persisted model-quality request differs from live classification."
                )
            return loaded_request, loaded_bundle

        review_id = self.repository.allocate_review_id(project_id)
        executor = self.executor
        if executor is None:
            executor = ModelQualityRefinementExecutor(
                project_root=self.repo_root,
                provider=self.provider,
                model=self.model,
                api_key=self.api_key,
                clock=self._clock,
            )
        output_dir = (
            self.projects_root
            / project_id
            / "model_quality"
            / "runs"
            / review_id
        )
        bundle = executor.execute(
            request=request,
            review_id=review_id,
            output_dir=output_dir,
            progress=progress,
        )
        self.repository.record_review(
            request=request,
            bundle=bundle,
        )
        return request, bundle

    def effective_decisions(self, bundle):
        return self.repository.effective_decisions(bundle)

    def decide(
        self,
        *,
        bundle,
        internal_model_element_id: str,
        decision: str,
        reviewer_identity: str,
        rationale: str,
        approved_name: str | None = None,
        approved_description: str | None = None,
    ):
        return self.repository.record_decision(
            bundle=bundle,
            internal_model_element_id=internal_model_element_id,
            decision=decision,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            decided_at=self._now(),
            approved_name=approved_name,
            approved_description=approved_description,
        )

    def finalize(self, bundle):
        return self.repository.finalize(
            bundle=bundle,
            created_at=self._now(),
        )

    def _now(self):
        if self._clock is None:
            value = datetime.now(timezone.utc)
        else:
            value = self._clock()
        return value.astimezone(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )
