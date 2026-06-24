from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.config import settings

router = APIRouter(tags=["websocket"])


@router.websocket("/api/ws/tasks/{task_id}/events")
async def websocket_task_events(websocket: WebSocket, task_id: str):
    await websocket.accept()

    try:
        import redis.asyncio as aioredis
    except ImportError:
        await websocket.send_text(json.dumps({"event": "info", "data": {"message": "Redis not available, real-time updates disabled"}}))
        await websocket.close()
        return

    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    channel = f"task:{task_id}:events"
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message is None:
                continue
            msg_type = message.get("type")
            if msg_type != "message":
                continue
            data = message.get("data")
            if data is None:
                continue
            await websocket.send_text(data if isinstance(data, str) else data.decode("utf-8"))
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()
