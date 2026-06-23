from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("generate_images")
class GenerateImagesStep(StepExecutor):
    """Placeholder for image generation.

    In production this step would call the nanobanana image generation
    service for each image plan in the article. For MVP it simply logs
    the plans that would be processed.
    """

    step_type = "generate_images"
    name = "Generate Images"
    description = "Generate images from article image plans (placeholder for nanobanana integration)."
    required_inputs = ["article_with_images"]
    produced_outputs = ["images_generated"]

    async def execute(self, ctx: StepContext) -> StepResult:
        article = ctx.artifacts.get("article_with_images")
        if article is None:
            raise ValueError("article_with_images artifact is required")

        plans: list[dict[str, Any]] = []
        if isinstance(article, dict):
            plans = (article.get("_plans") or {}).get("images", [])

        logs = [
            f"Image generation placeholder: {len(plans)} image plan(s) found.",
            "Image generation requires nanobanana integration.",
        ]
        for plan in plans:
            target = plan.get("target", "unknown")
            prompt = str(plan.get("prompt", ""))[:80]
            logs.append(f"  Would generate: target={target}, prompt={prompt}...")

        return StepResult(
            outputs={
                "images_generated": 0,
                "note": "Image generation requires nanobanana integration",
                "plans_count": len(plans),
            },
            artifacts={},
            metrics={"plans_count": len(plans)},
            logs=logs,
        )
