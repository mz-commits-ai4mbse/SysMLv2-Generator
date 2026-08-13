"""Deterministic J5 renderer for supported IEM relationship projections."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import SysMLGenerationBlockedError
from .projection_types import (
    SysMLProjectionPlan,
    SysMLRelationshipProjection,
)
from .types import SysMLGenerationFinding


@dataclass(frozen=True, slots=True)
class RenderedSysMLRelationship:
    """One deterministic SysML textual fragment rendered from one IMR."""

    internal_model_relationship_id: str
    generated_trace_symbol: str
    target_construct_id: str
    generation_rule_id: str
    source_generated_symbol: str
    target_generated_symbol: str
    content: str


class SysMLRelationshipRenderer:
    """Render only relationship mappings explicitly authorized by J2.

    Relationship identity remains the immutable IMR identity / trace symbol.
    J5 does not inject the trace symbol as a SysML relationship name because
    naming syntax is not required for the MVP rendering forms. J6 binds the IMR
    to the exact generated location through machine-readable traceability.
    """

    def render(
        self,
        projection: SysMLRelationshipProjection,
    ) -> RenderedSysMLRelationship:
        if projection.target_construct_id == "TN_013":
            content = self._render_dependency(projection)
        elif projection.target_construct_id == "TN_014":
            content = self._render_allocation(projection)
        elif projection.target_construct_id == "TN_015":
            content = self._render_satisfaction(projection)
        else:
            self._block(
                "UNSUPPORTED_RELATIONSHIP_RENDERER",
                "J5 has no renderer for target construct "
                f"{projection.target_construct_id}.",
                projection,
            )

        return RenderedSysMLRelationship(
            internal_model_relationship_id=(
                projection.internal_model_relationship_id
            ),
            generated_trace_symbol=projection.generated_trace_symbol,
            target_construct_id=projection.target_construct_id,
            generation_rule_id=projection.generation_rule_id,
            source_generated_symbol=projection.source_generated_symbol,
            target_generated_symbol=projection.target_generated_symbol,
            content=content,
        )

    def render_all(
        self,
        plan: SysMLProjectionPlan,
    ) -> tuple[RenderedSysMLRelationship, ...]:
        """Render relationships in the canonical J3 IMR order."""

        return tuple(self.render(item) for item in plan.relationships)

    @staticmethod
    def _render_dependency(
        projection: SysMLRelationshipProjection,
    ) -> str:
        if projection.endpoint_rendering != "source_to_target":
            SysMLRelationshipRenderer._block(
                "RELATIONSHIP_ENDPOINT_RENDERING_MISMATCH",
                "Dependency requires source_to_target endpoint rendering.",
                projection,
            )
        return (
            f"dependency from {projection.source_generated_symbol} "
            f"to {projection.target_generated_symbol};"
        )

    @staticmethod
    def _render_allocation(
        projection: SysMLRelationshipProjection,
    ) -> str:
        if projection.endpoint_rendering != "source_to_target":
            SysMLRelationshipRenderer._block(
                "RELATIONSHIP_ENDPOINT_RENDERING_MISMATCH",
                "Allocation requires source_to_target endpoint rendering.",
                projection,
            )
        return (
            f"allocate {projection.source_generated_symbol} "
            f"to {projection.target_generated_symbol};"
        )

    @staticmethod
    def _render_satisfaction(
        projection: SysMLRelationshipProjection,
    ) -> str:
        if projection.endpoint_rendering != "target_by_source":
            SysMLRelationshipRenderer._block(
                "RELATIONSHIP_ENDPOINT_RENDERING_MISMATCH",
                "Satisfaction requires target_by_source endpoint rendering.",
                projection,
            )
        return (
            f"satisfy {projection.target_generated_symbol} "
            f"by {projection.source_generated_symbol};"
        )

    @staticmethod
    def _block(
        code: str,
        message: str,
        projection: SysMLRelationshipProjection,
    ) -> None:
        finding = SysMLGenerationFinding(
            code=code,
            message=message,
            issue_level="error",
            blocking=True,
            target_type="internal_model_relationship",
            target_id=projection.internal_model_relationship_id,
            profile_rule_id=projection.generation_rule_id,
        )
        error = SysMLGenerationBlockedError(message)
        error.findings = (finding,)
        raise error
