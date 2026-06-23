from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.article import Article
from schemas.article import ArticleCreate, ArticleResponse, ArticleValidateResponse

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/{article_id}/html")
async def get_article_html(article_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    article_json = article.article_json

    title = article_json.get("title", "Untitled")
    content = article_json.get("content", "")
    summary = article_json.get("summary", "")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.8; color: #333; }}
        h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .summary {{ color: #666; font-style: italic; margin-bottom: 2rem; padding: 1rem; background: #f9f9f9; border-radius: 4px; }}
        .content {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {f'<div class="summary">{summary}</div>' if summary else ''}
    <div class="content">{content}</div>
</body>
</html>"""

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: uuid.UUID,
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    article.article_json = body.article_json
    if body.template_key is not None:
        article.template_key = body.template_key
    article.version += 1

    await db.flush()
    await db.refresh(article)
    return article


@router.post("/{article_id}/validate", response_model=ArticleValidateResponse)
async def validate_article(article_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    errors: list[str] = []
    warnings: list[str] = []

    article_json = article.article_json

    if not article_json.get("title"):
        errors.append("Article title is missing")
    if not article_json.get("content"):
        errors.append("Article content is missing")
    if article_json.get("title") and len(article_json.get("title", "")) > 64:
        warnings.append("Title exceeds 64 characters, may be truncated on some platforms")
    if article_json.get("content") and len(article_json.get("content", "")) < 200:
        warnings.append("Article content is very short (< 200 characters)")

    return ArticleValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
