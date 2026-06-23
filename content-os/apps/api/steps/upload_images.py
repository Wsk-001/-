from __future__ import annotations

from typing import Any

from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("upload_images")
class UploadImagesStep(StepExecutor):
    """Placeholder for image upload to WeChat CDN.

    In production this step would upload generated images to the WeChat
    MP platform and replace local paths with CDN URLs. For MVP it simply
    logs the images that would be uploaded.
    """

    step_type = "upload_images"
    name = "Upload Images"
    description = "Upload generated images to WeChat CDN (placeholder for wechat_mp integration)."
    required_inputs = ["article_with_images"]
    produced_outputs = ["images_uploaded"]

    async def execute(self, ctx: StepContext) -> StepResult:
        article = ctx.artifacts.get("article_with_images")
        if article is None:
            raise ValueError("article_with_images artifact is required")

        plans: list[dict[str, Any]] = []
        if isinstance(article, dict):
            plans = (article.get("_plans") or {}).get("images", [])

        logs = [
            f"Image upload placeholder: {len(plans)} image(s) would be uploaded.",
            "Image upload requires wechat_mp integration.",
        ]

        return StepResult(
            outputs={
                "images_uploaded": 0,
                "note": "Image upload requires wechat_mp integration",
                "plans_count": len(plans),
            },
            artifacts={},
            metrics={"plans_count": len(plans)},
            logs=logs,
        )
