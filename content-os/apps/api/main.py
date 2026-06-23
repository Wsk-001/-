from __future__ import annotations

import os
import json
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import init_db
from api import auth, tasks, pipelines, articles, prompts, sources, llm_configs, templates, ws

app = FastAPI(
    title="Content OS API",
    description="Content OS 后端 API 服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(pipelines.router)
app.include_router(articles.router)
app.include_router(prompts.router)
app.include_router(sources.router)
app.include_router(llm_configs.router)
app.include_router(templates.router)
app.include_router(ws.router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "content-os-api"}


@app.websocket("/api/ws/tasks/{task_id}")
async def websocket_task_events(websocket: WebSocket, task_id: str):
    await websocket.accept()
    import redis.asyncio as aioredis
    from core.config import settings

    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    channel = f"task:{task_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis_client.close()
