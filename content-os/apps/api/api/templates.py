from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/templates", tags=["templates"])

TEMPLATES = [
    {
        "key": "daily-intelligence",
        "name": "每日情报",
        "description": "每日自动收集情报源、生成文章、渲染 HTML 并发布到微信公众号",
        "steps": [
            {"step_key": "collect_sources", "step_type": "collect_sources", "name": "收集情报源"},
            {"step_key": "generate_article", "step_type": "generate_article", "name": "生成文章"},
            {"step_key": "plan_images", "step_type": "plan_images", "name": "规划图片"},
            {"step_key": "render_html", "step_type": "render_html", "name": "渲染 HTML"},
            {"step_key": "validate_content", "step_type": "validate_content", "name": "校验内容"},
            {"step_key": "generate_images", "step_type": "generate_images", "name": "生成图片"},
            {"step_key": "upload_images", "step_type": "upload_images", "name": "上传图片"},
            {"step_key": "create_draft", "step_type": "create_draft", "name": "创建草稿"},
            {"step_key": "publish", "step_type": "publish", "name": "发布"},
        ],
    },
    {
        "key": "quick-article",
        "name": "快速文章",
        "description": "快速生成一篇文章，跳过图片生成和微信发布步骤",
        "steps": [
            {"step_key": "collect_sources", "step_type": "collect_sources", "name": "收集情报源"},
            {"step_key": "generate_article", "step_type": "generate_article", "name": "生成文章"},
            {"step_key": "render_html", "step_type": "render_html", "name": "渲染 HTML"},
            {"step_key": "validate_content", "step_type": "validate_content", "name": "校验内容"},
        ],
    },
]


@router.get("")
async def list_templates():
    return TEMPLATES
