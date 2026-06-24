from __future__ import annotations

from adapters.article_lib_proxy import render_article
from core.compat import to_thread
from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("render_html")
class RenderHtmlStep(StepExecutor):
    """Render an article JSON to WeChat-compatible HTML.

    Wraps ``render_article`` from the article_lib proxy. If
    ``article_with_images`` is available (from the plan_images step) it is
    preferred over the raw ``article_json``.
    """

    step_type = "render_html"
    name = "Render HTML"
    description = "Render article JSON to WeChat-compatible HTML using the template engine."
    required_inputs = ["article_json"]
    produced_outputs = ["html", "article_resolved"]

    async def execute(self, ctx: StepContext) -> StepResult:
        # Prefer article_with_images if plan_images ran; otherwise use article_json.
        article = ctx.artifacts.get("article_with_images")
        if article is None:
            article = ctx.artifacts.get("article_json")
        if article is None:
            raise ValueError("article_json artifact is required")

        # render_article is CPU-bound (template parsing); run in a thread.
        html_text = await to_thread(render_article, article)

        html_size = len(html_text.encode("utf-8"))
        template_name = article.get("template", "unknown") if isinstance(article, dict) else "unknown"

        logs = [
            f"Rendered article to HTML using template '{template_name}'.",
            f"HTML size: {html_size} bytes",
        ]

        return StepResult(
            outputs={
                "html": html_text,
                "article_resolved": article,
            },
            artifacts={
                "html": html_text,
                "article_resolved": article,
            },
            metrics={
                "html_size": html_size,
                "template": template_name,
            },
            logs=logs,
        )
