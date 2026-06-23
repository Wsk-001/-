from __future__ import annotations

from typing import Any

from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("create_draft")
class CreateDraftStep(StepExecutor):
    """Placeholder for WeChat draft creation.

    In production this step would call the WeChat MP API to create a draft
    article from the rendered HTML. For MVP it simply logs that a draft
    would be created.
    """

    step_type = "create_draft"
    name = "Create Draft"
    description = "Create a WeChat draft from rendered HTML (placeholder for wechat_mp integration)."
    required_inputs = ["html"]
    produced_outputs = ["draft_media_id"]

    async def execute(self, ctx: StepContext) -> StepResult:
        html = ctx.artifacts.get("html")
        if html is None:
            raise ValueError("html artifact is required")

        html_size = len(str(html).encode("utf-8"))
        logs = [
            "Draft creation placeholder: a WeChat draft would be created.",
            f"HTML size: {html_size} bytes",
            "Draft creation requires wechat_mp integration.",
        ]

        return StepResult(
            outputs={
                "draft_media_id": None,
                "note": "Draft creation requires wechat_mp integration",
                "html_size": html_size,
            },
            artifacts={},
            metrics={"html_size": html_size},
            logs=logs,
        )
