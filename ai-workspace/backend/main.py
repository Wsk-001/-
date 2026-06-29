"""
AI Workspace - Chat Backend (FastAPI)
MVP: Streaming Chat with Session Memory
"""

import os
import json
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Workspace Chat API")

# CORS - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 配置 ───────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))

# ─── Session 存储（内存） ────────────────────────────────

sessions: dict[str, list[dict]] = {}

# ─── OpenAI 客户端（延迟初始化，无 key 时仍可启动） ──────

client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """获取 OpenAI 客户端，首次调用时初始化"""
    global client
    if client is None:
        if not OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY not configured. Please set it in .env file.",
            )
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
    return client


# ─── 数据模型 ───────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str


# ─── API 接口 ───────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/chat")
async def chat(req: ChatRequest):
    """流式聊天接口：逐 token 返回 assistant 回复"""

    # 获取或创建 session
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id]

    # 添加用户消息到历史
    history.append({"role": "user", "content": req.message})

    # 保留最近 MAX_HISTORY 条消息（控制上下文长度）
    if len(history) > MAX_HISTORY:
        history[:] = history[-MAX_HISTORY:]

    # 构建发送给 LLM 的消息列表
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant. Respond in the same language as the user's message.",
        },
        *history,
    ]

    async def stream_generator():
        """生成流式响应"""
        try:
            response = await get_client().chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=2048,
            )

            assistant_content = ""

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    assistant_content += token
                    # SSE 格式输出
                    data = json.dumps({"token": token}, ensure_ascii=False)
                    yield f"data: {data}\n\n"

            # 流结束，保存 assistant 回复到 session
            history.append({"role": "assistant", "content": assistant_content})

            # 发送结束标记
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """清除指定 session 的历史记录"""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "cleared"}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定 session 的历史记录"""
    return {"session_id": session_id, "messages": sessions.get(session_id, [])}


# ─── 启动入口 ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
