from __future__ import annotations

from adapters.article_lib_proxy import attach_missing_image_plans
from core.compat import to_thread
from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("plan_images")
class PlanImagesStep(StepExecutor):
    """Plan cover and content images for an article.

    Wraps ``attach_missing_image_plans`` from the article_lib proxy to
    generate image prompts and local paths for the cover, headline, and
    up to ``max_content_images`` content sections.
    """

    step_type = "plan_images"
    name = "Plan Images"
    description = "Attach image plans (prompts + local paths) to the article JSON."
    required_inputs = ["article_json"]
    produced_outputs = ["article_with_images", "image_plans"]

    async def execute(self, ctx: StepContext) -> StepResult:
        # Prefer article_with_images if a previous step already produced it;
        # otherwise use article_json.
        article = ctx.artifacts.get("article_with_images")
        if article is None:
            article = ctx.artifacts.get("article_json")
        if article is None:
            raise ValueError("article_json artifact is required")

        config = ctx.config
        max_content_images = int(config.get("max_content_images", 3))
        output_dir = config.get("output_dir", "build/images")

        # attach_missing_image_plans mutates the article dict in place and
        # also returns it. Run in a thread since it does filesystem I/O.
        updated_article = await to_thread(
            attach_missing_image_plans,
            article,
            output_dir=output_dir,
            max_content_images=max_content_images,
        )

        image_plans = (updated_article.get("_plans") or {}).get("images", [])

        logs = [
            f"Planned {len(image_plans)} image(s).",
            f"Max content images: {max_content_images}",
        ]
        for plan in image_plans:
            logs.append(f"  {plan.get('target', 'unknown')}: {plan.get('local_path', '')}")

        return StepResult(
            outputs={
                "article_with_images": updated_article,
                "image_plans": image_plans,
            },
            artifacts={
                "article_with_images": updated_article,
                "image_plans": image_plans,
            },
            metrics={
                "image_count": len(image_plans),
                "max_content_images": max_content_images,
            },
            logs=logs,
        )
