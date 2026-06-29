@echo off
chcp 65001 >nul 2>&1
title AI Workspace

:: AI Workspace 一键启动脚本 (Windows)
:: 同时启动后端 FastAPI 和前端 Next.js

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend
set FRONTEND_DIR=%ROOT_DIR%frontend

echo =====================================
echo   AI Workspace 启动脚本
echo =====================================
echo.

:: ─── 检查 Python ──────────────────────────────────────
echo [检查] Python ...
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python！请先安装 Python 3.10+
    echo         下载地址: https://www.python.org/downloads/
    echo         安装时务必勾选 "Add Python to PATH"
    goto :fail
)
python --version
echo.

:: ─── 检查 Node.js ─────────────────────────────────────
echo [检查] Node.js ...
where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js！请先安装 Node.js 18+
    echo         下载地址: https://nodejs.org/
    goto :fail
)
node --version
echo.

:: ─── 检查目录 ─────────────────────────────────────────
if not exist "%BACKEND_DIR%" (
    echo [错误] 未找到 backend 目录: %BACKEND_DIR%
    goto :fail
)
if not exist "%FRONTEND_DIR%" (
    echo [错误] 未找到 frontend 目录: %FRONTEND_DIR%
    goto :fail
)

:: ─── 检查 .env ────────────────────────────────────────
if not exist "%BACKEND_DIR%\.env" (
    echo [提示] 未找到 backend\.env，从模板创建...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo [重要] 请编辑 backend\.env 填入 OPENAI_API_KEY 后重新启动！
    echo.
)

:: ─── 安装后端依赖 ─────────────────────────────────────
echo [检查] 后端依赖...
cd /d "%BACKEND_DIR%"
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装后端依赖，请稍候...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 后端依赖安装失败！
        goto :fail
    )
) else (
    echo [完成] 后端依赖已就绪
)
echo.

:: ─── 安装前端依赖 ─────────────────────────────────────
echo [检查] 前端依赖...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [安装] 正在安装前端依赖，请稍候...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败！
        goto :fail
    )
) else (
    echo [完成] 前端依赖已就绪
)
echo.

:: ─── 启动后端 ─────────────────────────────────────────
echo [启动] 后端 FastAPI (http://localhost:8000)...
cd /d "%BACKEND_DIR%"
start "AI Workspace - 后端" cmd /k "python main.py"
echo.

:: ─── 等待后端就绪 ─────────────────────────────────────
echo [等待] 后端启动中，请稍候...
timeout /t 4 /nobreak >nul

:: ─── 启动前端 ─────────────────────────────────────────
echo [启动] 前端 Next.js (http://localhost:3000)...
cd /d "%FRONTEND_DIR%"
start "AI Workspace - 前端" cmd /k "npx next dev -p 3000"
echo.

:: ─── 等待前端就绪后打开浏览器 ─────────────────────────
echo [等待] 前端启动中，5秒后打开浏览器...
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo =====================================
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000
echo   API:  http://localhost:8000/docs
echo.
echo   关闭弹出的窗口即可停止服务
echo   本窗口可以安全关闭
echo =====================================
echo.
goto :end

:fail
echo.
echo =====================================
echo   启动失败！请检查上方错误信息
echo =====================================
echo.
pause
exit /b 1

:end
pause
