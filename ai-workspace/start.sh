#!/usr/bin/env bash
# AI Workspace 一键启动脚本
# 纯 Python 方案，无需 Node.js

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[AI Workspace]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# 检查 Python
if ! command -v python &>/dev/null; then
    warn "Python not found! Please install Python 3.8+"
    exit 1
fi
log "Python $(python --version 2>&1)"

# 检查目录
if [ ! -d "$BACKEND_DIR" ]; then
    warn "backend folder not found: $BACKEND_DIR"
    exit 1
fi

# 检查 .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
    warn "Creating .env from template..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    warn "Please edit backend/.env and set OPENAI_API_KEY!"
fi

# 安装依赖
cd "$BACKEND_DIR"
if ! python -c "import fastapi" 2>/dev/null; then
    log "Installing dependencies..."
    pip install -r requirements.txt
fi

log "Starting AI Workspace..."
log "Open http://localhost:8000 in your browser"
log "Press Ctrl+C to stop"
log "====================================="

python main.py
