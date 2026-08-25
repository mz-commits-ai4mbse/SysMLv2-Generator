"""Deterministic J4 renderer for supported IEM element projections."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import SysMLGenerationBlockedError
from .projection_types import (
    SysMLElementProjection,
    SysMLProjectionPlan,
)
from .types import SysMLGenerationFinding


@dataclass(frozen=True, slots=True)
class RenderedSysMLElement:
    """One deterministic SysML textual fragment rendered from one IME."""

    internal_model_element_id: str
    generated_symbol: str
    target_construct_id: str
    generation_rule_id: str
    content: str


class SysMLElementRenderer:
    """Render only explicitly supported J2 element mappings.

    The IEM contains individual reviewed engineering elements. Functions and
    components are therefore rendered as SysML usages/features, not reusable
    definition/type declarations. This also permits relationship constructs
    such as allocation to bind to generated Features.
    """

    _KEYWORDS = {
        "TN_003": "part def",
        "TN_004": "part",
        "TN_006": "action",
        "TN_008": "requirement",
        "TN_012": "use case def",
    }

    def render(
        self,
        projection: SysMLElementProjection,
    ) -> RenderedSysMLElement:
        keyword = self._KEYWORDS.get(projection.target_construct_id)
        if keyword is None:
            self._block(
                "UNSUPPORTED_ELEMENT_RENDERER",
                "J4 has no renderer for target construct "
                f"{projection.target_construct_id}.",
                projection,
            )

        documentation = self._render_documentation(projection)
        content = (
            f"{keyword} {projection.generated_symbol} {{\n"
            f"{documentation}"
            f"}}"
        )

        return RenderedSysMLElement(
            internal_model_element_id=projection.internal_model_element_id,
            generated_symbol=projection.generated_symbol,
            target_construct_id=projection.target_construct_id,
            generation_rule_id=projection.generation_rule_id,
            content=content,
        )

    def render_all(
        self,
        plan: SysMLProjectionPlan,
    ) -> tuple[RenderedSysMLElement, ...]:
        return tuple(self.render(item) for item in plan.elements)

    @staticmethod
    def _render_documentation(
        projection: SysMLElementProjection,
    ) -> str:
        lines = [
            f"Engineering name: {projection.engineering_name}",
        ]
        if projection.engineering_description is not None:
            lines.append("Description:")
            lines.extend(projection.engineering_description.split("\n"))

        body = "\n".join(lines)
        return f"    doc /* {body} */\n"

    @staticmethod
    def _block(
        code: str,
        message: str,
        projection: SysMLElementProjection,
    ) -> None:
        finding = SysMLGenerationFinding(
            code=code,
            message=message,
            issue_level="error",
            blocking=True,
            target_type="internal_model_element",
            target_id=projection.internal_model_element_id,
            profile_rule_id=projection.generation_rule_id,
        )
        error = SysMLGenerationBlockedError(message)
        error.findings = (finding,)
        raise error
