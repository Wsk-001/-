from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import redis.asyncio as redis


class EventBus:
    """Simple event bus using Redis pub/sub.

    Events are published to channels named ``task:{task_id}`` so that
    subscribers can listen to all events for a specific task.
    """

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: redis.Redis = redis.from_url(redis_url)
        self._pubsub = self._redis.pubsub()

    async def emit(self, event: str, task_id: str, data: dict[str, Any] | None = None) -> None:
        """Publish event to Redis channel ``task:{task_id}``."""
        payload = {
            "event": event,
            "task_id": task_id,
            "data": data or {},
        }
        await self._redis.publish(f"task:{task_id}", json.dumps(payload, ensure_ascii=False))

    async def subscribe(self, task_id: str) -> None:
        """Subscribe to task events."""
        await self._pubsub.subscribe(f"task:{task_id}")

    async def unsubscribe(self, task_id: str) -> None:
        """Unsubscribe from task events."""
        await self._pubsub.unsubscribe(f"task:{task_id}")

    async def listen(self, task_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Async generator yielding events for a task.

        Usage::

            async for event in bus.listen(task_id):
                print(event["event"], event["data"])
        """
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
        try:
            await self._pubsub.close()
        except Exception:
            pass
        await self._redis.close()
