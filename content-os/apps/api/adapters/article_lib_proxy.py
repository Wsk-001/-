from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Patch TEMPLATES_DIR so article_lib reads from the content-os templates dir.
# article_lib.py is at: apps/api/adapters/article_lib.py
#   -> parent       = apps/api/adapters/
#   -> parent.parent = apps/api/
#   -> parent.parent.parent = apps/
#   -> parent.parent.parent.parent = content-os/
# Templates live at: content-os/templates/
# ---------------------------------------------------------------------------
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"

import adapters.article_lib as _lib  # noqa: E402

# Monkey-patch the module-level TEMPLATES_DIR so all functions that reference it
# (available_templates, read_template, etc.) use the correct path.
_lib.TEMPLATES_DIR = TEMPLATES_DIR

# Re-export key functions and classes from the original article_lib.
from adapters.article_lib import (  # noqa: E402, F401
    ArticleError,
    ValidationResult,
    available_templates,
    ensure_meta_defaults,
    find_content_images,
    normalize_paragraphs,
    render_article,
    validate_article,
)

# Also re-export helpers that step executors or other modules may need.
from adapters.article_lib import (  # noqa: E402, F401
    count_news_items,
    count_sources,
    is_wechat_image_url,
    load_json,
    dump_json,
    normalize_text,
    parse_iso_date,
    read_template,
    strip_html_comments,
)


# ---------------------------------------------------------------------------
# attach_missing_image_plans
#
# Copied from the original scripts/plan_images.py and adapted to import
# helpers from adapters.article_lib instead of a sibling script module.
# ---------------------------------------------------------------------------


def _safe_fragment(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isascii() and ch.isalnum() else "-" for ch in value)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "image"


def _cover_prompt(article: dict[str, Any], meta: Optional[dict[str, Any]] = None) -> str:
    meta = meta if meta is not None else ensure_meta_defaults(article)
    title = meta.get("title") or "微信公众号封面"
    date_short = meta.get("date_short")
    template = article.get("template")
    if template == "daily-intelligence":
        return (
            f"Futuristic AI daily news cover for {date_short}. Theme: {title}. "
            "Dark blue gradient, neural network nodes, holographic interface, editorial magazine cover, 16:9."
        )
    if template == "weekly-financial":
        return (
            f"Dramatic financial weekly cover for {date_short}. Theme: {title}. "
            "Dark red and black gradient, stock charts, commodities, Bloomberg or Economist style, 16:9."
        )
    return (
        f"Editorial deep analysis cover for {date_short}. Theme: {title}. "
        "Deep navy palette, analytical charts, serious longform magazine style, cinematic light, 16:9."
    )


def _content_prompt(article: dict[str, Any], title: str, detail: str) -> str:
    template = article.get("template")
    if template == "daily-intelligence":
        return (
            f"Futuristic AI news illustration about {title}. {detail}. "
            "Modern research lab, holographic data panels, blue and white palette, professional editorial image, 16:9."
        )
    if template == "weekly-financial":
        return (
            f"Financial news illustration about {title}. {detail}. "
            "Institutional market screens, macroeconomic tension, professional media photography style, 16:9."
        )
    return (
        f"Editorial analysis illustration about {title}. {detail}. "
        "Longform magazine style, layered charts and symbolic objects, restrained dramatic lighting, 16:9."
    )


def _section_detail(section: dict[str, Any], block: dict[str, Any]) -> str:
    text_bits: list[str] = []
    if section.get("cn"):
        text_bits.append(str(section["cn"]))
    if block.get("body"):
        paragraphs = normalize_paragraphs(block.get("body"))
        if paragraphs:
            text_bits.append(paragraphs[0][:120])
    if not text_bits and block.get("days"):
        labels = [str(row.get("label") or "").strip() for row in block["days"][:2]]
        text_bits.append(" / ".join(label for label in labels if label))
    return ". ".join(part for part in text_bits if part)


def _choose_section_subject(section: dict[str, Any]) -> Optional[dict[str, Any]]:
    for block in section.get("blocks") or []:
        if block.get("type", "card") in {"card", "opinion", "week-ahead"}:
            return block
    return None


def attach_missing_image_plans(
    article: dict[str, Any],
    *,
    output_dir: str | Path,
    max_content_images: int = 3,
) -> dict[str, Any]:
    """Attach image plans (prompts + local paths) to an article.

    Adds a cover image plan and up to ``max_content_images`` content image plans
    to sections that don't already have one. The plans are stored under
    ``article["_plans"]["images"]`` and the image dicts are embedded in the
    article structure (headline.image, section.image).
    """
    meta = ensure_meta_defaults(article)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    date_short = str(meta.get("date_short")).replace(".", "-")

    cover = dict(meta.get("cover_image") or {})
    if not cover.get("prompt"):
        cover["prompt"] = _cover_prompt(article, meta)
    if not cover.get("local_path"):
        cover["local_path"] = str(output_path / f"cover-{date_short}.png")
    meta["cover_image"] = cover

    plans: list[dict[str, Any]] = []
    plans.append({"target": "cover", **cover})

    headline = article.get("headline") or {}
    planned_slots = 0
    if max_content_images > 0:
        headline_image = dict(headline.get("image") or {})
        if not headline_image.get("prompt"):
            headline_body = normalize_paragraphs(headline.get("body"))
            headline_image["prompt"] = _content_prompt(
                article,
                str(headline.get("title") or meta.get("title") or "头条"),
                headline_body[0][:120] if headline_body else "",
            )
        if not headline_image.get("caption"):
            headline_image["caption"] = str(headline.get("title") or "头条配图")
        if not headline_image.get("local_path"):
            headline_image["local_path"] = str(output_path / f"headline-{date_short}.png")
        headline["image"] = headline_image
        article["headline"] = headline
        plans.append({"target": "headline", **headline_image})
        planned_slots += 1

    section_index = 0
    while planned_slots < max_content_images and section_index < len(article.get("sections") or []):
        section = article["sections"][section_index]
        section_index += 1
        if section.get("image"):
            continue
        subject = _choose_section_subject(section)
        if not subject:
            continue
        title = str(subject.get("title") or section.get("cn") or "正文配图")
        section["image"] = {
            "prompt": _content_prompt(article, title, _section_detail(section, subject)),
            "caption": title,
            "local_path": str(output_path / f"section-{planned_slots:02d}-{_safe_fragment(title)[:24]}.png"),
        }
        plans.append({"target": f"section[{section_index - 1}]", **section["image"]})
        planned_slots += 1

    article.setdefault("_plans", {})
    article["_plans"]["images"] = plans
    return article
