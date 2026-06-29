@echo off
chcp 65001 >nul 2>&1
title AI Workspace

:: AI Workspace 一键启动脚本 (Windows)
:: 同时启动后端 FastAPI 和前端 Next.js

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend
set FRONTEND_DIR=%ROOT_DIR%frontend

echo [AI Workspace] 启动中...

:: 检查 .env
if not exist "%BACKEND_DIR%\.env" (
    echo [WARN] 未找到 backend\.env，从模板创建...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo [WARN] 请编辑 backend\.env 填入 OPENAI_API_KEY 后重新启动
)

:: 安装后端依赖
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [AI Workspace] 安装后端依赖...
    cd /d "%BACKEND_DIR%"
    pip install -r requirements.txt -q
)

:: 安装前端依赖
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [AI Workspace] 安装前端依赖...
    cd /d "%FRONTEND_DIR%"
    call npm install
)

:: 启动后端
echo [AI Workspace] 启动后端 (FastAPI -^> http://localhost:8000)...
cd /d "%BACKEND_DIR%"
start "AI Workspace - Backend" cmd /c "python main.py"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
echo [AI Workspace] 启动前端 (Next.js -^> http://localhost:3000)...
cd /d "%FRONTEND_DIR%"
start "AI Workspace - Frontend" cmd /c "npx next dev -p 3000"

echo =====================================
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo   关闭弹出的窗口即可停止服务
echo =====================================

:: 打开浏览器
timeout /t 5 /nobreak >nul
start http://localhost:3000
