from __future__ import annotations

from typing import Any

from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("publish")
class PublishStep(StepExecutor):
    """Placeholder for publishing a WeChat draft.

    In production this step would call the WeChat MP API to publish a
    draft article. For MVP it simply logs that the article would be
    published.
    """

    step_type = "publish"
    name = "Publish"
    description = "Publish a WeChat draft article (placeholder for wechat_mp integration)."
    required_inputs = ["draft_media_id"]
    produced_outputs = ["publish_id"]

    async def execute(self, ctx: StepContext) -> StepResult:
        draft_media_id = ctx.artifacts.get("draft_media_id")
        logs = [
            "Publish placeholder: the article would be published.",
            f"Draft media ID: {draft_media_id}",
            "Publishing requires wechat_mp integration.",
        ]

        return StepResult(
            outputs={
                "publish_id": None,
                "note": "Publishing requires wechat_mp integration",
            },
            artifacts={},
            metrics={},
            logs=logs,
        )
