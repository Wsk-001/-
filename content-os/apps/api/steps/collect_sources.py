from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
import re

from core.pipeline_engine import StepContext, StepResult
from core.step_registry import StepRegistry
from steps.base import StepExecutor


# ---------------------------------------------------------------------------
# Core collection logic (copied from the original collect_sources.py CLI).
# These functions are kept synchronous because they use urllib; the step
# executor wraps the synchronous ``collect`` call in ``asyncio.to_thread``.
# ---------------------------------------------------------------------------


class TextExtractor(HTMLParser):
    """Extract title and visible text from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        self.chunks.append(text)


def fetch_url(url: str, timeout: int, max_chars: int) -> dict[str, Any]:
    """Fetch a URL and extract title + visible text."""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get_content_type()
        body = response.read().decode("utf-8", errors="ignore")
    if content_type == "text/plain":
        text = " ".join(body.split())
        title = ""
    else:
        parser = TextExtractor()
        parser.feed(re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", body))
        title = parser.title
        text = " ".join(parser.chunks)
    return {"title": title, "content": text[:max_chars], "content_type": content_type}


def read_file(path: str | Path, max_chars: int) -> dict[str, Any]:
    """Read a local file and return its content."""
    text = Path(path).read_text(encoding="utf-8")
    return {"title": Path(path).name, "content": text[:max_chars], "content_type": "text/plain"}


def collect(spec: dict[str, Any], timeout: int, max_chars: int) -> dict[str, Any]:
    """Collect sources from a spec dict.

    The ``spec`` must contain a ``sources`` list where each entry has a
    ``type`` of ``file``, ``text``, or ``url``.
    """
    items: list[dict[str, Any]] = []
    for entry in spec.get("sources") or []:
        entry_type = entry.get("type")
        label = (
            entry.get("label")
            or entry.get("title")
            or entry.get("path")
            or entry.get("url")
            or entry_type
        )
        try:
            if entry_type == "file":
                payload = read_file(entry["path"], max_chars)
                payload.update({"type": "file", "label": label, "path": entry["path"]})
            elif entry_type == "text":
                text = str(entry.get("text") or "")
                payload = {
                    "type": "text",
                    "label": label,
                    "title": entry.get("title") or label,
                    "content": text[:max_chars],
                    "content_type": "text/plain",
                }
            elif entry_type == "url":
                payload = fetch_url(entry["url"], timeout, max_chars)
                payload.update({"type": "url", "label": label, "url": entry["url"]})
            else:
                payload = {
                    "type": entry_type or "unknown",
                    "label": label,
                    "error": f"Unsupported source type: {entry_type}",
                }
        except Exception as exc:  # noqa: BLE001
            payload = {
                "type": entry_type or "unknown",
                "label": label,
                "error": str(exc),
            }

        content = payload.get("content", "")
        payload["excerpt"] = content[: min(240, len(content))]
        payload["ok"] = "error" not in payload
        items.append(payload)

    ok_count = sum(1 for item in items if item.get("ok"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "ok_count": ok_count,
        "items": items,
    }


# ---------------------------------------------------------------------------
# Step executor
# ---------------------------------------------------------------------------


@StepRegistry.register("collect_sources")
class CollectSourcesStep(StepExecutor):
    """Collect data sources (files, URLs, text) into a normalized source bundle."""

    step_type = "collect_sources"
    name = "Collect Sources"
    description = "Collect local files, URLs, or raw text into a normalized source bundle."
    required_inputs: list[str] = []
    produced_outputs = ["source_bundle"]

    async def execute(self, ctx: StepContext) -> StepResult:
        config = ctx.config
        sources = config.get("sources") or []
        if not sources:
            raise ValueError(
                "No data sources specified. Provide a 'sources' list in step config."
            )

        timeout = int(config.get("timeout", 15))
        max_chars = int(config.get("max_chars", 4000))

        spec = {"sources": sources}

        # collect() uses synchronous urllib; run in a thread to avoid blocking.
        source_bundle = await asyncio.to_thread(collect, spec, timeout, max_chars)

        logs = [
            f"Collected {source_bundle['count']} sources "
            f"({source_bundle['ok_count']} ok)"
        ]
        for item in source_bundle["items"]:
            if not item.get("ok"):
                logs.append(f"  FAILED: {item.get('label')} - {item.get('error')}")

        return StepResult(
            outputs={"source_bundle": source_bundle},
            artifacts={"source_bundle": source_bundle},
            metrics={
                "count": source_bundle["count"],
                "ok_count": source_bundle["ok_count"],
            },
            logs=logs,
        )
