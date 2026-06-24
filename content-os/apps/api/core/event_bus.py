from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Dict, Optional

try:
    import redis.asyncio as _redis

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


class EventBus:
    """Simple event bus using Redis pub/sub.

    Events are published to channels named ``task:{task_id}`` so that
    subscribers can listen to all events for a specific task.

    Falls back to a no-op implementation when Redis is not installed.
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        if _REDIS_AVAILABLE:
            self._redis: _redis.Redis = _redis.from_url(redis_url)
            self._pubsub = self._redis.pubsub()
        else:
            self._redis = None  # type: ignore[assignment]
            self._pubsub = None

    async def emit(self, event: str, task_id: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish event to Redis channel ``task:{task_id}``."""
        if not _REDIS_AVAILABLE or self._redis is None:
            return
        payload = {
            "event": event,
            "task_id": task_id,
            "data": data or {},
        }
        await self._redis.publish(f"task:{task_id}", json.dumps(payload, ensure_ascii=False))

    async def subscribe(self, task_id: str) -> None:
        """Subscribe to task events."""
        if not _REDIS_AVAILABLE or self._pubsub is None:
            return
        await self._pubsub.subscribe(f"task:{task_id}")

    async def unsubscribe(self, task_id: str) -> None:
        """Unsubscribe from task events."""
        if not _REDIS_AVAILABLE or self._pubsub is None:
            return
        await self._pubsub.unsubscribe(f"task:{task_id}")

    async def listen(self, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator yielding events for a task.

        Usage::

            async for event in bus.listen(task_id):
                print(event["event"], event["data"])
        """
        if not _REDIS_AVAILABLE or self._pubsub is None:
            return
        await self.subscribe(task_id)
        try:
            async for message in self._pubsub.listen():
                if message is None:
                    continue
                msg_type = message.get("type")
                if msg_type != "message":
                    continue
                raw = message.get("data")
                if raw is None:
                    continue
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                if isinstance(raw, str):
                    try:
                        yield json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                elif isinstance(raw, dict):
                    yield raw
        finally:
            await self.unsubscribe(task_id)

    async def close(self) -> None:
        """Close the Redis connection and pubsub."""
        if not _REDIS_AVAILABLE:
            return
        if self._pubsub is not None:
            try:
                await self._pubsub.close()
            except Exception:
                pass
        if self._redis is not None:
            await self._redis.close()
