from __future__ import annotations

from typing import Any, Dict, List
from core.compat import to_thread
from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


@StepRegistry.register("validate_content")
class ValidateContentStep(StepExecutor):
    """Validate the article JSON and rendered HTML.

    Wraps ``validate_article`` from the article_lib proxy. If validation
    errors are found, the step raises a ``ValueError`` to halt the pipeline.
    Warnings are recorded but do not stop execution.
    """

    step_type = "validate_content"
    name = "Validate Content"
    description = "Validate article JSON structure and rendered HTML for WeChat compliance."
    required_inputs = ["article_json", "html"]
    produced_outputs = ["validation"]

    async def execute(self, ctx: StepContext) -> StepResult:
        # Prefer article_with_images if available; otherwise use article_json.
        article = ctx.artifacts.get("article_with_images")
        if article is None:
            article = ctx.artifacts.get("article_json")
        if article is None:
            raise ValueError("article_json artifact is required")

        html_text = ctx.artifacts.get("html")

        # validate_article is CPU-bound; run in a thread.
        validation = await to_thread(
            validate_article, article, **({"html_text": html_text} if html_text else {})
        )

        result_dict: Dict[str, Any] = {
            "ok": validation.ok,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        }

        logs: List[str] = []
        if validation.errors:
            for err in validation.errors:
                logs.append(f"ERROR: {err}")
        if validation.warnings:
            for warn in validation.warnings:
                logs.append(f"WARNING: {warn}")
        if validation.ok and not validation.warnings:
            logs.append("Validation passed with no errors or warnings.")
        elif validation.ok:
            logs.append(f"Validation passed with {len(validation.warnings)} warning(s).")

        # If there are errors, raise to halt the pipeline.
        if not validation.ok:
            error_detail = "; ".join(validation.errors)
            raise ValueError(f"Content validation failed: {error_detail}")

        return StepResult(
            outputs={"validation": result_dict},
            artifacts={"validation": result_dict},
            metrics={
                "ok": validation.ok,
                "error_count": len(validation.errors),
                "warning_count": len(validation.warnings),
            },
            logs=logs,
        )
