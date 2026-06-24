from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from core.prompt_engine import PromptEngine


class LLMError(RuntimeError):
    """Raised when an LLM provider call fails or returns unparseable output."""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion request and return the raw response text.

        Args:
            messages: List of message dicts with ``role`` and ``content`` keys.
            response_format: Optional structured-output specification.
            **kwargs: Additional provider-specific options (temperature, etc.).
        """
        ...


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI-compatible APIs (OpenAI, Azure OpenAI, etc.)."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        timeout: float = 120.0,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url or "https://api.openai.com/v1"
        self._timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": kwargs.pop("model", self._model),
            "messages": messages,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if response_format is not None:
            payload["response_format"] = response_format
        # Forward any remaining kwargs as top-level fields.
        for key, value in kwargs.items():
            if key not in ("model", "messages", "temperature", "max_tokens", "response_format"):
                payload[key] = value

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise LLMError(
                    f"OpenAI API error {resp.status_code}: {resp.text}"
                )
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected OpenAI response structure: {data}") from exc


class ClaudeProvider(LLMProvider):
    """LLM provider for Anthropic Claude models.

    For structured output, Claude uses tool_use with a JSON schema tool
    rather than a ``response_format`` parameter.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 120.0,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Separate system messages from user/assistant messages.
        system_parts: List[str] = []
        api_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "system":
                system_parts.append(str(msg.get("content", "")))
            else:
                api_messages.append(msg)

        payload: Dict[str, Any] = {
            "model": kwargs.pop("model", self._model),
            "messages": api_messages,
            "max_tokens": kwargs.pop("max_tokens", 4096),
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        # If structured output is requested, use tool_use.
        tools: Optional[List[Dict[str, Any]]] = None
        if response_format is not None:
            schema = response_format.get("json_schema", {}).get("schema", response_format)
            tools = [
                {
                    "name": "output_structured",
                    "description": "Output the structured result according to the provided schema.",
                    "input_schema": schema,
                }
            ]
            payload["tools"] = tools
            payload["tool_choice"] = {"type": "tool", "name": "output_structured"}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise LLMError(
                    f"Claude API error {resp.status_code}: {resp.text}"
                )
            data = resp.json()

        # Extract text content or tool_use result.
        content_blocks = data.get("content", [])
        if tools:
            for block in content_blocks:
                if block.get("type") == "tool_use":
                    tool_input = block.get("input")
                    if isinstance(tool_input, dict):
                        return json.dumps(tool_input, ensure_ascii=False)
                    return str(tool_input)
            raise LLMError(f"Claude did not return a tool_use block: {data}")

        # No tools: concatenate text blocks.
        text_parts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        return "".join(text_parts)


class DeepSeekProvider(LLMProvider):
    """LLM provider for DeepSeek (OpenAI-compatible API)."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout: float = 120.0,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": kwargs.pop("model", self._model),
            "messages": messages,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        # DeepSeek supports response_format={"type":"json_object"} for structured output.
        if response_format is not None:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise LLMError(
                    f"DeepSeek API error {resp.status_code}: {resp.text}"
                )
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected DeepSeek response structure: {data}") from exc


class LLMOrchestrator:
    """Multi-model LLM orchestrator.

    Manages provider instantiation and provides high-level helpers for
    generating structured (JSON) output from prompt templates.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, type[LLMProvider]] = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "deepseek": DeepSeekProvider,
        }
        self._prompt_engine = PromptEngine()

    def get_provider(
        self,
        provider_name: str,
        api_key: str,
        **kwargs: Any,
    ) -> LLMProvider:
        """Instantiate and return an LLM provider by name."""
        if provider_name not in self._providers:
            raise LLMError(
                f"Unknown provider '{provider_name}'. "
                f"Available: {', '.join(sorted(self._providers.keys()))}"
            )
        cls = self._providers[provider_name]
        return cls(api_key=api_key, **kwargs)

    def register_provider(self, name: str, provider_cls: type[LLMProvider]) -> None:
        """Register a custom provider class."""
        self._providers[name] = provider_cls

    async def generate_structured(
        self,
        prompt_content: str,
        variables: Dict[str, Any],
        output_schema: Dict[str, Any],
        provider_name: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        Steps:
            1. Render the prompt template with variables using PromptEngine.
            2. Build the appropriate response_format for the provider.
            3. Call the LLM with the JSON Schema constraint.
            4. Parse the response as JSON and validate against the schema's
               required fields.
            5. Return the parsed dict.
        """
        rendered_prompt = self._prompt_engine.render(prompt_content, variables)

        # Separate constructor kwargs from chat kwargs.
        # Constructor: model, base_url, timeout
        # Chat: temperature, max_tokens (and any other provider-specific opts)
        constructor_kwargs: Dict[str, Any] = {}
        if model is not None:
            constructor_kwargs["model"] = model
        if "base_url" in kwargs:
            constructor_kwargs["base_url"] = kwargs["base_url"]
        if "timeout" in kwargs:
            constructor_kwargs["timeout"] = kwargs["timeout"]

        # Everything else goes to chat().
        chat_kwargs: Dict[str, Any] = {
            k: v for k, v in kwargs.items()
            if k not in ("base_url", "timeout")
        }

        provider = self.get_provider(provider_name, api_key, **constructor_kwargs)

        # Build response_format depending on the provider.
        response_format = self._build_response_format(provider_name, output_schema)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a content generation assistant. "
                    "You must respond with valid JSON that conforms to the provided schema. "
                    "Do not include any text outside the JSON object."
                ),
            },
            {"role": "user", "content": rendered_prompt},
        ]

        raw = await provider.chat(
            messages=messages,
            response_format=response_format,
            **chat_kwargs,
        )

        parsed = self._parse_json_response(raw)
        self._validate_against_schema(parsed, output_schema)
        return parsed

    @staticmethod
    def _build_response_format(
        provider_name: str,
        output_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the provider-specific response_format payload."""
        if provider_name == "openai":
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": output_schema,
                    "strict": False,
                },
            }
        if provider_name == "deepseek":
            return {"type": "json_object"}
        # Claude uses tool_use; the response_format is the schema itself.
        return {"json_schema": {"schema": output_schema}}

    @staticmethod
    def _parse_json_response(raw: str) -> Dict[str, Any]:
        """Parse a raw LLM response string into a dict.

        Handles common wrapping patterns like ```json ... ``` blocks.
        """
        text = raw.strip()
        # Strip markdown code fences.
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Failed to parse LLM response as JSON: {exc}\nRaw: {raw[:500]}") from exc

        if not isinstance(parsed, dict):
            raise LLMError(f"LLM response is not a JSON object: {type(parsed)}")
        return parsed

    @staticmethod
    def _validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Lightweight validation: check that all ``required`` fields are present."""
        required = schema.get("required", [])
        missing = [field for field in required if field not in data]
        if missing:
            raise LLMError(
                f"LLM response missing required fields: {', '.join(missing)}"
            )
