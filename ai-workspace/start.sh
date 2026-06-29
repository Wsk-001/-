#!/usr/bin/env bash
# AI Workspace 一键启动脚本
# 同时启动后端 FastAPI 和前端 Next.js

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[AI Workspace]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 .env
check_env() {
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        warn "未找到 backend/.env，从模板创建..."
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        warn "请编辑 backend/.env 填入 OPENAI_API_KEY 后重新启动"
    fi
}

# 安装后端依赖
install_backend() {
    if ! python -c "import fastapi" 2>/dev/null; then
        log "安装后端依赖..."
        cd "$BACKEND_DIR" && pip install -r requirements.txt -q
    fi
}

# 安装前端依赖
install_frontend() {
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log "安装前端依赖..."
        cd "$FRONTEND_DIR" && npm install
    fi
}

# 清理子进程
cleanup() {
    log "正在停止所有服务..."
    kill $(jobs -p) 2>/dev/null
    wait 2>/dev/null
    log "已停止"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── 主流程 ─────────────────────────────────────────────

log "AI Workspace 启动中..."
check_env
install_backend
install_frontend

# 启动后端
log "启动后端 (FastAPI → http://localhost:8000)..."
cd "$BACKEND_DIR"
python main.py &
BACKEND_PID=$!

# 启动前端
log "启动前端 (Next.js → http://localhost:3000)..."
cd "$FRONTEND_DIR"
npx next dev -p 3000 &
FRONTEND_PID=$!

log "====================================="
log "  前端: http://localhost:3000"
log "  后端: http://localhost:8000"
log "  API 文档: http://localhost:8000/docs"
log "  按 Ctrl+C 停止所有服务"
log "====================================="

wait
