from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select

from core.llm_orchestrator import LLMError, LLMOrchestrator
from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


# JSON Schema describing the expected article structure.
ARTICLE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "template": {
            "type": "string",
            "description": "Template name, e.g. daily-intelligence, weekly-financial, deep-analysis.",
        },
        "meta": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "digest": {"type": "string"},
                "author": {"type": "string"},
                "date": {"type": "string"},
            },
            "required": ["title", "digest"],
        },
        "headline": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "source": {"type": "string"},
                "image": {"type": "object"},
            },
            "required": ["title", "body"],
        },
        "sections": {
            "type": "array",
            "items": {"type": "object"},
        },
        "conclusion": {"type": "string"},
        "cta": {"type": "string"},
    },
    "required": ["template", "meta", "headline", "sections"],
}


@StepRegistry.register("generate_article")
class GenerateArticleStep(StepExecutor):
    """Generate article JSON from collected sources using an LLM.

    The step config may contain either direct values (``prompt_content``,
    ``provider``, ``api_key``, ``model``) or database IDs (``prompt_id``,
    ``llm_config_id``) that are resolved at runtime.  The engine merges
    ``prompt_id`` and ``llm_config_id`` from the PipelineStep into the config.
    """

    step_type = "generate_article"
    name = "Generate Article"
    description = "Generate structured article JSON from collected sources using an LLM."
    required_inputs = ["source_bundle"]
    produced_outputs = ["article_json"]

    async def execute(self, ctx: StepContext) -> StepResult:
        source_bundle = ctx.artifacts.get("source_bundle")
        if source_bundle is None:
            raise ValueError("source_bundle artifact is required")

        config = ctx.config
        orchestrator = LLMOrchestrator()

        # Resolve prompt content (from DB or direct config).
        prompt_content, output_schema_from_prompt = await self._resolve_prompt_content(config)
        if not prompt_content:
            raise ValueError(
                "No prompt content available. Provide 'prompt_content' in config "
                "or ensure 'prompt_id' resolves to a stored prompt."
            )

        # Resolve LLM config (from DB or direct config).
        llm_config = await self._resolve_llm_config(config)
        provider_name = llm_config["provider"]
        api_key = llm_config["api_key"]
        model = llm_config.get("model")
        base_url = llm_config.get("base_url")
        temperature = llm_config.get("temperature", 0.7)
        max_tokens = llm_config.get("max_tokens", 4096)

        # Build variables for prompt rendering.
        variables: Dict[str, Any] = {
            "sources": source_bundle,
            "source_count": source_bundle.get("count", 0) if isinstance(source_bundle, dict) else 0,
            "template_key": config.get("template_key", ""),
            "context": config.get("context", ""),
        }

        output_schema = config.get("output_schema") or output_schema_from_prompt or ARTICLE_JSON_SCHEMA

        article_json = await orchestrator.generate_structured(
            prompt_content=prompt_content,
            variables=variables,
            output_schema=output_schema,
            provider_name=provider_name,
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Validate the generated JSON has required fields.
        self._validate_article_json(article_json)

        logs = [
            f"Generated article JSON using {provider_name}/{model or 'default'}.",
            f"Template: {article_json.get('template', 'unknown')}",
            f"Sections: {len(article_json.get('sections', []))}",
        ]

        return StepResult(
            outputs={"article_json": article_json},
            artifacts={"article_json": article_json},
            metrics={
                "provider": provider_name,
                "model": model or "",
                "template": article_json.get("template", ""),
                "section_count": len(article_json.get("sections", [])),
            },
            logs=logs,
        )

    async def _resolve_prompt_content(self, config: Dict[str, Any]) -> Tuple[str, Optional[Dict]]:
        """Resolve prompt content and output schema from direct config or DB.

        Returns a tuple of (content, output_schema).  output_schema may be
        ``None`` if not available from the prompt version.
        """
        # Direct content takes priority.
        content = config.get("prompt_content")
        if content:
            return content, None

        # Try DB lookup by prompt_id.
        prompt_id = config.get("prompt_id")
        if prompt_id:
            try:
                from core.database import async_session_factory
                from models.prompt import Prompt, PromptVersion

                async with async_session_factory() as session:
                    result = await session.execute(
                        select(Prompt).where(Prompt.id == prompt_id)
                    )
                    prompt = result.scalar_one_or_none()
                    if prompt is not None and prompt.current_version_id is not None:
                        result = await session.execute(
                            select(PromptVersion).where(
                                PromptVersion.id == prompt.current_version_id
                            )
                        )
                        version = result.scalar_one_or_none()
                        if version is not None:
                            return version.content, version.output_schema or None
            except Exception:
                pass

        return "", None

    async def _resolve_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve LLM config from direct values or DB lookup."""
        # Direct config takes priority.
        if config.get("provider") and config.get("api_key"):
            return {
                "provider": config["provider"],
                "api_key": config["api_key"],
                "model": config.get("model"),
                "base_url": config.get("base_url"),
                "temperature": config.get("temperature", 0.7),
                "max_tokens": config.get("max_tokens", 4096),
            }

        # Try DB lookup by llm_config_id.
        llm_config_id = config.get("llm_config_id")
        if llm_config_id:
            try:
                from core.database import async_session_factory
                from models.llm_config import LLMConfig

                async with async_session_factory() as session:
                    result = await session.execute(
                        select(LLMConfig).where(LLMConfig.id == llm_config_id)
                    )
                    llm_cfg = result.scalar_one_or_none()
                    if llm_cfg is not None:
                        return {
                            "provider": llm_cfg.provider,
                            "api_key": llm_cfg.api_key_encrypted or "",
                            "model": llm_cfg.model,
                            "base_url": llm_cfg.base_url,
                            "temperature": llm_cfg.temperature,
                            "max_tokens": llm_cfg.max_tokens,
                        }
            except Exception:
                pass

        # Fall back to direct values even if incomplete.
        return {
            "provider": config.get("provider", "openai"),
            "api_key": config.get("api_key", ""),
            "model": config.get("model"),
            "base_url": config.get("base_url"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 4096),
        }

    @staticmethod
    def _validate_article_json(article_json: Dict[str, Any]) -> None:
        """Validate that the generated JSON has required top-level fields."""
        required_fields = ["template", "meta", "headline", "sections"]
        missing = [f for f in required_fields if f not in article_json]
        if missing:
            raise LLMError(
                f"Generated article JSON missing required fields: {', '.join(missing)}"
            )

        meta = article_json.get("meta") or {}
        if not isinstance(meta, dict):
            raise LLMError("article_json.meta must be an object")
        if not str(meta.get("title") or "").strip():
            raise LLMError("article_json.meta.title is required")
        if not str(meta.get("digest") or "").strip():
            raise LLMError("article_json.meta.digest is required")

        headline = article_json.get("headline") or {}
        if not isinstance(headline, dict):
            raise LLMError("article_json.headline must be an object")
        if not str(headline.get("title") or "").strip():
            raise LLMError("article_json.headline.title is required")
        if not headline.get("body"):
            raise LLMError("article_json.headline.body is required")

        sections = article_json.get("sections")
        if not isinstance(sections, list) or not sections:
            raise LLMError("article_json.sections must be a non-empty array")
