"""
AI Workspace - Chat Backend (FastAPI)
MVP: Streaming Chat with Session Memory
"""

import os
import json
import asyncio
from typing import Optional, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import pathlib
import httpx

load_dotenv()

app = FastAPI(title="AI Workspace Chat API")

# Static files directory
STATIC_DIR = pathlib.Path(__file__).parent / "static"

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

sessions: Dict[str, List[Dict]] = {}

# ─── OpenAI 客户端（使用 httpx 直接调用，绕过 SDK WAF 拦截） ──

API_URL = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"


async def call_llm_stream(messages):
    """使用 httpx 直接调用 OpenAI 兼容 API（流式）"""
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY not configured. Please set it in .env file.",
        )

    headers = {
        "Authorization": "Bearer " + OPENAI_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 8192,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", API_URL, headers=headers, json=payload) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                error_text = body.decode("utf-8", errors="replace")
                raise HTTPException(
                    status_code=resp.status_code,
                    detail="LLM API error: " + error_text,
                )
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    if chunk.get("choices"):
                        delta = chunk["choices"][0].get("delta", {})
                        # 输出思维链内容（reasoning_content）
                        reasoning = delta.get("reasoning_content")
                        if reasoning:
                            yield reasoning
                        # 输出正式回复内容
                        content = delta.get("content")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue


# ─── 数据模型 ───────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str


# ─── 前端页面 ──────────────────────────────────────────

@app.get("/")
async def index():
    """Serve the frontend HTML page"""
    return FileResponse(STATIC_DIR / "index.html")


# ─── API 接口 ───────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.get("/debug")
async def debug():
    """调试接口：检查 API 配置和连通性"""
    result = {
        "model": MODEL_NAME,
        "base_url": OPENAI_BASE_URL,
        "api_url": API_URL,
        "api_key_set": bool(OPENAI_API_KEY),
        "api_key_prefix": OPENAI_API_KEY[:8] + "..." if OPENAI_API_KEY and len(OPENAI_API_KEY) > 8 else "(empty)",
    }
    # 尝试连接测试
    if OPENAI_API_KEY:
        try:
            headers = {
                "Authorization": "Bearer " + OPENAI_API_KEY,
            }
            models_url = OPENAI_BASE_URL.rstrip("/") + "/models"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(models_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    model_ids = [m["id"] for m in data.get("data", [])][:5]
                    result["connection"] = "ok"
                    result["available_models_count"] = len(data.get("data", []))
                    result["sample_models"] = model_ids
                else:
                    result["connection"] = "http_error"
                    result["status_code"] = resp.status_code
                    result["error"] = resp.text[:300]
        except Exception as e:
            result["connection"] = "failed"
            result["error"] = str(e)
    else:
        result["connection"] = "no_api_key"

    return result


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
            "content": "你是一个乐于助人的 AI 助手。请用与用户消息相同的语言进行回复。",
        },
        *history,
    ]

    async def stream_generator():
        """生成流式响应"""
        try:
            assistant_content = ""
            async for token in call_llm_stream(messages):
                assistant_content += token
                data = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # 流结束，保存 assistant 回复到 session
            history.append({"role": "assistant", "content": assistant_content})

            # 发送结束标记
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

        except HTTPException as e:
            error_msg = json.dumps({"error": str(e.detail)}, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
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
    import webbrowser
    import threading

    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 40)
    print("  AI Workspace is running!")
    print("  http://localhost:8000")
    print("  Press Ctrl+C to stop")
    print("=" * 40)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
