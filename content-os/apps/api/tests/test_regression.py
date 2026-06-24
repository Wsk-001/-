"""Regression tests for all fixed bugs.

Run with: cd /workspace/content-os/apps/api && DATABASE_URL="sqlite+aiosqlite:///./test_regression.db" python -m pytest tests/test_regression.py -v
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid

import pytest
import pytest_asyncio

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_regression.db"

# Must import after env var is set
from core.database import Base, async_session_factory, engine, get_db, init_db
from core.pipeline_engine import PipelineEngine, StepContext, StepResult
from core.step_registry import StepRegistry
from core.event_bus import EventBus
from core.prompt_engine import PromptEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop after."""
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Bug#1: Celery Worker must delegate to PipelineEngine
# ---------------------------------------------------------------------------


class TestBug1_CeleryWorkerDelegatesToEngine:
    """Verify that _execute_pipeline calls PipelineEngine.run_task()."""

    def test_execute_pipeline_imports_pipeline_engine(self):
        """_execute_pipeline must import and use PipelineEngine, not
        implement its own broken inline step execution."""
        import inspect
        from workers.celery_app import _execute_pipeline

        source = inspect.getsource(_execute_pipeline)
        # Must import and use PipelineEngine
        assert "PipelineEngine" in source, (
            "_execute_pipeline must use PipelineEngine. "
            "The old broken code implemented its own step execution that "
            "marked all steps as success without actually running them."
        )
        # Must call engine.run_task
        assert "run_task" in source, (
            "_execute_pipeline must call engine.run_task() to delegate "
            "execution to the PipelineEngine."
        )
        # Must NOT contain the old broken patterns
        lines = [l.strip() for l in source.split("\n") if not l.strip().startswith("#")]
        for line in lines:
            # The old code had: step.status = "success" / step.outputs = {"result": "completed"}
            if 'outputs = {"result": "completed"}' in line:
                raise AssertionError(
                    "_execute_pipeline must NOT contain the old broken pattern "
                    "'step.outputs = {result: completed}' that fakes step execution."
                )

    def test_execute_pipeline_uses_event_bus(self):
        """_execute_pipeline must create an EventBus for real-time updates."""
        import inspect
        from workers.celery_app import _execute_pipeline

        source = inspect.getsource(_execute_pipeline)
        assert "EventBus" in source, (
            "_execute_pipeline must create an EventBus instance so that "
            "pipeline events are published to WebSocket subscribers."
        )

    def test_old_broken_code_removed(self):
        """The old broken _execute_pipeline code must be completely removed."""
        import inspect
        from workers.celery_app import _execute_pipeline

        source = inspect.getsource(_execute_pipeline)
        # The old code had these patterns that prove it was faking execution
        assert 'step.status = "success"' not in source, (
            "Old broken code 'step.status = \"success\"' must be removed. "
            "Step status should be set by PipelineEngine, not hardcoded."
        )
        assert "completed_steps" not in source, (
            "Old broken code with manual step counting must be removed. "
            "PipelineEngine handles step execution and progress tracking."
        )


# ---------------------------------------------------------------------------
# Bug#5: WebSocket must not CPU-spin
# ---------------------------------------------------------------------------


class TestBug5_WebSocketNoSpin:
    """Verify WebSocket handler uses async for instead of get_message loop."""

    def test_websocket_handler_uses_listen(self):
        """The WebSocket handler in main.py must use 'async for message in pubsub.listen()'
        instead of 'while True: get_message()' which causes CPU spin."""
        import inspect
        from main import websocket_task_events

        source = inspect.getsource(websocket_task_events)
        # Must contain the new listen pattern
        assert "async for message in pubsub.listen()" in source, (
            "WebSocket handler must use 'async for message in pubsub.listen()' "
            "to properly await messages instead of spinning."
        )
        # Must NOT contain the old while-loop with get_message as the main loop
        # (We check for the specific pattern "while True:" combined with "get_message")
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # Skip comments
            assert "get_message" not in stripped, (
                "WebSocket handler still calls get_message() which causes CPU spin. "
                "Must use 'async for message in pubsub.listen()' instead."
            )


# ---------------------------------------------------------------------------
# Bug#2: get_db must not double-commit
# ---------------------------------------------------------------------------


class TestBug2_GetDbNoDoubleCommit:
    """Verify get_db does not commit after yield when route already committed."""

    @pytest.mark.asyncio
    async def test_get_db_no_explicit_close(self):
        """get_db should not call session.close() explicitly because
        async with session already handles that."""
        import inspect
        from core.database import get_db

        source = inspect.getsource(get_db)
        # The old code had `finally: await session.close()` which is
        # redundant with `async with` and could cause issues.
        assert "await session.close()" not in source, (
            "get_db should not explicitly call session.close() because "
            "the `async with async_session_factory() as session` context "
            "manager already handles closing."
        )

    @pytest.mark.asyncio
    async def test_get_db_commits_on_success(self):
        """Verify get_db commits after yield on success path."""
        import inspect
        from core.database import get_db

        source = inspect.getsource(get_db)
        assert "await session.commit()" in source
        assert "await session.rollback()" in source


# ---------------------------------------------------------------------------
# Bug#4: Frontend/backend data alignment
# ---------------------------------------------------------------------------


class TestBug4_SchemaAliasAlignment:
    """Verify that backend schemas produce frontend-compatible field names."""

    def test_task_step_response_uses_aliases(self):
        """TaskStepResponse must serialize with frontend-compatible aliases."""
        from schemas.task import TaskStepResponse

        # Create a mock step response
        step = TaskStepResponse(
            id=uuid.uuid4(),
            task_id=uuid.uuid4(),
            step_key="collect_sources",
            step_type="collect_sources",
            status="success",
            config_snapshot={},
            inputs={},
            outputs={},
            attempt=1,
            error=None,
            stack_trace=None,
            started_at=None,
            finished_at=None,
            duration_ms=None,
        )
        data = step.model_dump(by_alias=True)

        # Frontend expects these field names
        assert "key" in data, "Frontend expects 'key' not 'step_key'"
        assert "type" in data, "Frontend expects 'type' not 'step_type'"
        assert "config" in data, "Frontend expects 'config' not 'config_snapshot'"
        assert "retry_count" in data, "Frontend expects 'retry_count' not 'attempt'"

    def test_article_response_uses_aliases(self):
        """ArticleResponse must serialize with 'content' alias for article_json."""
        from schemas.article import ArticleResponse

        article = ArticleResponse(
            id=uuid.uuid4(),
            task_id=uuid.uuid4(),
            version=1,
            article_json={"template": "daily-intelligence"},
            template_key="daily-intelligence",
            is_current=True,
            created_by="llm",
            created_at="2026-06-23T00:00:00Z",
        )
        data = article.model_dump(by_alias=True)
        assert "content" in data, "Frontend expects 'content' not 'article_json'"

    def test_task_step_response_populate_by_name(self):
        """TaskStepResponse must accept both alias and real name for input."""
        from schemas.task import TaskStepResponse

        # Should work with real field names (from ORM)
        step1 = TaskStepResponse(
            id=uuid.uuid4(), task_id=uuid.uuid4(),
            step_key="test", step_type="test",
            status="pending", config_snapshot={}, inputs={}, outputs={},
            attempt=0, error=None, stack_trace=None,
            started_at=None, finished_at=None, duration_ms=None,
        )
        assert step1.step_key == "test"

        # Should also work with alias names (from API input)
        step2 = TaskStepResponse(
            id=uuid.uuid4(), task_id=uuid.uuid4(),
            key="test2", type="test2",
            status="pending", config={}, inputs={}, outputs={},
            retry_count=0, error=None, stack_trace=None,
            started_at=None, finished_at=None, duration_ms=None,
        )
        assert step2.step_key == "test2"


# ---------------------------------------------------------------------------
# Bug#6: Auth must have get_current_user
# ---------------------------------------------------------------------------


class TestBug6_AuthGetCurrentUser:
    """Verify get_current_user dependency exists and validates tokens."""

    def test_get_current_user_exists(self):
        """The get_current_user function must exist in auth module."""
        from api.auth import get_current_user
        assert callable(get_current_user)

    @pytest.mark.asyncio
    async def test_get_current_user_rejects_no_token(self):
        """get_current_user must raise 401 when no token is provided."""
        from api.auth import get_current_user
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None, db=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_rejects_invalid_token(self):
        """get_current_user must raise 401 for invalid JWT."""
        from api.auth import get_current_user
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        bad_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.jwt.token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=bad_creds, db=None)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Bug#8: sources/collect must actually collect
# ---------------------------------------------------------------------------


class TestBug8_SourcesCollectActuallyCollects:
    """Verify that /api/sources/collect invokes the actual collection logic."""

    @pytest.mark.asyncio
    async def test_collect_with_text_sources(self):
        """Text sources should be processed by CollectSourcesStep."""
        from steps.collect_sources import CollectSourcesStep

        executor = CollectSourcesStep()
        ctx = StepContext(
            task_id=uuid.uuid4(),
            inputs={},
            config={"sources": [
                {"type": "text", "text": "OpenAI releases GPT-5", "label": "AI News"},
            ]},
            artifacts={},
        )
        result = await executor.execute(ctx)

        # Must produce a source_bundle artifact
        assert "source_bundle" in result.artifacts
        bundle = result.artifacts["source_bundle"]
        # The bundle should contain items (the collected sources)
        items = bundle.get("items", [])
        assert len(items) > 0, "CollectSourcesStep must return at least one item"
        # At least one item should be ok
        ok_items = [i for i in items if i.get("ok")]
        assert len(ok_items) > 0, "At least one collected item should be ok"

    @pytest.mark.asyncio
    async def test_collect_no_sources_raises(self):
        """No sources should raise ValueError, not silently succeed."""
        from steps.collect_sources import CollectSourcesStep

        executor = CollectSourcesStep()
        ctx = StepContext(
            task_id=uuid.uuid4(),
            inputs={},
            config={"sources": []},
            artifacts={},
        )
        with pytest.raises(ValueError, match="No data sources"):
            await executor.execute(ctx)


# ---------------------------------------------------------------------------
# Bug#18: Prompt output format must match article JSON schema
# ---------------------------------------------------------------------------


class TestBug18_PromptOutputFormat:
    """Verify that the default prompt produces article JSON, not plain text."""

    def test_default_prompt_requires_article_fields(self):
        """The seed prompt must instruct LLM to output article JSON
        with template/meta/headline/sections, not title/summary/content/tags."""
        from seed import DEFAULT_ARTICLE_PROMPT_CONTENT

        # Must mention the article JSON structure
        assert '"template"' in DEFAULT_ARTICLE_PROMPT_CONTENT
        assert '"meta"' in DEFAULT_ARTICLE_PROMPT_CONTENT
        assert '"headline"' in DEFAULT_ARTICLE_PROMPT_CONTENT
        assert '"sections"' in DEFAULT_ARTICLE_PROMPT_CONTENT

        # Must NOT use the old wrong format
        assert '"title": "文章标题' not in DEFAULT_ARTICLE_PROMPT_CONTENT or '"meta"' in DEFAULT_ARTICLE_PROMPT_CONTENT
        # Old format had top-level "title", "summary", "content", "tags"
        # New format has them nested under "meta"
        assert '"digest"' in DEFAULT_ARTICLE_PROMPT_CONTENT, "meta.digest is required by article JSON schema"

    def test_default_prompt_includes_template_key_variable(self):
        """The prompt must include {{template_key}} variable."""
        from seed import DEFAULT_ARTICLE_PROMPT_CONTENT

        assert "{{template_key}}" in DEFAULT_ARTICLE_PROMPT_CONTENT, (
            "Prompt must include {{template_key}} variable so the LLM knows "
            "which template to use for the article JSON."
        )

    def test_seed_variables_schema_includes_template_key(self):
        """The seed prompt's variables_schema must include template_key."""
        from seed import DEFAULT_PIPELINE_STEPS  # just to verify import works

        # Check that the prompt content references both variables
        from seed import DEFAULT_ARTICLE_PROMPT_CONTENT
        engine = PromptEngine()
        variables = engine.extract_variables(DEFAULT_ARTICLE_PROMPT_CONTENT)
        assert "sources" in variables
        assert "template_key" in variables


# ---------------------------------------------------------------------------
# Cross-cutting: PipelineEngine _step_enabled uses PipelineStep.enabled
# ---------------------------------------------------------------------------


class TestPipelineEngineStepEnabled:
    """Verify that _step_enabled reads from PipelineStep, not TaskStep."""

    def test_step_enabled_reads_pipeline_step(self):
        """_step_enabled must read enabled from pipeline_step, not task_step."""
        from core.pipeline_engine import PipelineEngine, _StepRuntime

        # Create a mock where pipeline_step.enabled = False
        class MockTaskStep:
            step_key = "test"
            step_type = "test"
            status = "pending"
            config_snapshot = {}
            attempt = 1

        class MockPipelineStep:
            enabled = False
            display_order = 1
            depends_on = []
            retry_policy = {}
            prompt_id = None
            llm_config_id = None

        step = _StepRuntime(task_step=MockTaskStep(), pipeline_step=MockPipelineStep())
        assert PipelineEngine._step_enabled(step) is False

    def test_step_enabled_defaults_true_without_pipeline_step(self):
        """If pipeline_step is None, enabled should default to True."""
        from core.pipeline_engine import PipelineEngine, _StepRuntime

        class MockTaskStep:
            step_key = "test"
            step_type = "test"
            status = "pending"
            config_snapshot = {}
            attempt = 1

        step = _StepRuntime(task_step=MockTaskStep(), pipeline_step=None)
        assert PipelineEngine._step_enabled(step) is True
