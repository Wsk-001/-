from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory, init_db
from models.user import User
from models.pipeline import Pipeline, PipelineStep
from models.prompt import Prompt, PromptVersion
from models.llm_config import LLMConfig
from api.auth import get_password_hash


DEFAULT_PIPELINE_STEPS = [
    {"step_key": "collect_sources", "step_type": "collect_sources", "name": "收集情报源", "display_order": 1},
    {"step_key": "generate_article", "step_type": "generate_article", "name": "生成文章", "display_order": 2},
    {"step_key": "plan_images", "step_type": "plan_images", "name": "规划图片", "display_order": 3},
    {"step_key": "render_html", "step_type": "render_html", "name": "渲染 HTML", "display_order": 4},
    {"step_key": "validate_content", "step_type": "validate_content", "name": "校验内容", "display_order": 5},
    {"step_key": "generate_images", "step_type": "generate_images", "name": "生成图片", "display_order": 6},
    {"step_key": "upload_images", "step_type": "upload_images", "name": "上传图片", "display_order": 7},
    {"step_key": "create_draft", "step_type": "create_draft", "name": "创建草稿", "display_order": 8},
    {"step_key": "publish", "step_type": "publish", "name": "发布", "display_order": 9},
]

DEFAULT_LLM_CONFIGS = [
    {"name": "GPT-4o", "provider": "openai", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 4096, "is_default": True},
    {"name": "Claude 3.5 Sonnet", "provider": "claude", "model": "claude-3-5-sonnet-20241022", "temperature": 0.7, "max_tokens": 4096, "is_default": False},
    {"name": "DeepSeek Chat", "provider": "deepseek", "model": "deepseek-chat", "temperature": 0.7, "max_tokens": 4096, "is_default": False},
]

DEFAULT_ARTICLE_PROMPT_CONTENT = """你是一位专业的内容编辑。请根据以下情报源，生成一篇微信公众号文章的 JSON 数据。

## 情报源
{{sources}}

## 模板
{{template_key}}

## 输出格式
请严格以 JSON 格式输出，结构如下：
```json
{
  "template": "{{template_key}}",
  "meta": {
    "title": "文章标题（不超过32字）",
    "digest": "文章摘要（不超过128字）",
    "author": "39Claw",
    "date": "2026-06-23"
  },
  "headline": {
    "title": "头条标题",
    "body": ["第一段正文", "第二段正文"],
    "source": "来源"
  },
  "sections": [
    {
      "en": "BRIEFING",
      "cn": "要闻",
      "blocks": [
        {
          "type": "card",
          "number": "01",
          "title": "卡片标题",
          "body": "卡片正文",
          "source": "来源"
        }
      ]
    }
  ],
  "cta": "你最关注哪一点？欢迎留言讨论。"
}
```

## 写作要求
1. 标题简洁有力，不超过32字
2. 每条情报用 card 类型 block
3. 语言专业但易懂，关键数据用红色加粗
4. 总字数控制在800-1500字
5. 只输出 JSON，不要输出其他内容"""


async def seed() -> None:
    await init_db()

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == "editor@test.com"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Seed data already exists, skipping...")
            return

        user = User(
            email="editor@test.com",
            name="Default Editor",
            hashed_password=get_password_hash("password123"),
            role="admin",
        )
        db.add(user)
        await db.flush()

        llm_configs: list[LLMConfig] = []
        for config_data in DEFAULT_LLM_CONFIGS:
            config = LLMConfig(**config_data)
            db.add(config)
            llm_configs.append(config)
        await db.flush()

        prompt = Prompt(
            owner_id=user.id,
            name="文章生成提示词",
            description="用于生成每日情报文章的默认提示词",
            category="article",
        )
        db.add(prompt)
        await db.flush()

        prompt_version = PromptVersion(
            prompt_id=prompt.id,
            content=DEFAULT_ARTICLE_PROMPT_CONTENT,
            variables_schema=[
                {"name": "sources", "type": "string", "description": "情报源内容"},
                {"name": "template_key", "type": "string", "description": "文章模板名称"},
            ],
            output_schema={
                "type": "object",
                "required": ["template", "meta", "headline", "sections"],
                "properties": {
                    "template": {"type": "string"},
                    "meta": {"type": "object"},
                    "headline": {"type": "object"},
                    "sections": {"type": "array"},
                },
            },
            model_hint="gpt-4o",
            changelog="初始版本",
            version=1,
        )
        db.add(prompt_version)
        await db.flush()

        prompt.current_version_id = prompt_version.id
        await db.flush()

        pipeline = Pipeline(
            owner_id=user.id,
            name="每日情报",
            description="每日自动收集情报源、生成文章、渲染 HTML 并发布到微信公众号",
            template_key="daily-intelligence",
            is_default=True,
        )
        db.add(pipeline)
        await db.flush()

        for step_data in DEFAULT_PIPELINE_STEPS:
            step = PipelineStep(
                pipeline_id=pipeline.id,
                step_key=step_data["step_key"],
                step_type=step_data["step_type"],
                name=step_data["name"],
                display_order=step_data["display_order"],
                config={},
                prompt_id=prompt.id if step_data["step_type"] == "generate_article" else None,
                llm_config_id=llm_configs[0].id if step_data["step_type"] == "generate_article" else None,
                depends_on=[],
                enabled=True,
                retry_policy={"max_retries": 3, "delay_seconds": 30},
            )
            db.add(step)

        await db.commit()

        print("Seed data created successfully!")
        print(f"  User: editor@test.com / password123 (role=admin)")
        print(f"  Pipeline: {pipeline.name} ({len(DEFAULT_PIPELINE_STEPS)} steps)")
        print(f"  LLM Configs: {len(llm_configs)}")
        print(f"  Prompt: {prompt.name}")


if __name__ == "__main__":
    asyncio.run(seed())
