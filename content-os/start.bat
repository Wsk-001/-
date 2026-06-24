@echo off
chcp 65001 >nul 2>&1
title Content OS 启动器
color 0A

echo ============================================
echo    Content OS - AI内容生产系统 启动器
echo ============================================
echo.

:: ========== 检查 Python ==========
echo [1/6] 检查 Python ...
where python >nul 2>&1
IF ERRORLEVEL 1 (
    color 0C
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo        Python 版本: %PY_VER%

:: ========== 检查 Node.js ==========
echo [2/6] 检查 Node.js ...
where node >nul 2>&1
IF ERRORLEVEL 1 (
    color 0C
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1 delims= " %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo        Node.js 版本: %NODE_VER%

:: ========== 设置环境变量 ==========
echo [3/6] 设置环境变量 ...
set PYTHONPATH=%~dp0apps\api
set DATABASE_URL=sqlite+aiosqlite:///./dev.db

:: ========== 安装后端依赖 ==========
echo [4/6] 检查后端依赖 ...
IF NOT EXIST "%~dp0apps\api\venv" (
    echo        首次运行，创建虚拟环境 ...
    python -m venv "%~dp0apps\api\venv"
    IF ERRORLEVEL 1 (
        color 0C
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

echo        激活虚拟环境 ...
call "%~dp0apps\api\venv\Scripts\activate.bat"

echo        安装 Python 依赖 ...
pip install -r "%~dp0apps\api\requirements.txt" -q
IF ERRORLEVEL 1 (
    color 0E
    echo [警告] 部分依赖安装失败，尝试继续 ...
)

:: ========== 安装前端依赖 ==========
echo [5/6] 检查前端依赖 ...
IF NOT EXIST "%~dp0apps\web\node_modules" (
    echo        首次运行，安装 npm 依赖（可能需要几分钟）...
    cd /d "%~dp0apps\web"
    call npm install
    IF ERRORLEVEL 1 (
        color 0C
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
    cd /d "%~dp0"
) else (
    echo        前端依赖已安装
)

:: ========== 初始化数据库 ==========
echo [6/6] 初始化数据库 ...
cd /d "%~dp0apps\api"
IF NOT EXIST "dev.db" (
    echo        创建数据库并导入种子数据 ...
    python seed.py
    IF ERRORLEVEL 1 (
        color 0E
        echo [警告] 种子数据导入失败，尝试继续 ...
    )
) else (
    echo        数据库已存在，跳过初始化
)

:: ========== 启动服务 ==========
echo.
echo ============================================
echo    正在启动服务 ...
echo ============================================
echo.

:: 启动后端 API (新窗口)
echo [启动] 后端 API  -> http://localhost:8000
start "Content OS - API Server" cmd /k "cd /d %~dp0apps\api && call venv\Scripts\activate.bat && set PYTHONPATH=%~dp0apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端 Web (新窗口)
echo [启动] 前端 Web  -> http://localhost:3000
start "Content OS - Web UI" cmd /k "cd /d %~dp0apps\web && npm run dev"

:: 等待前端启动
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo    服务已启动！
echo ============================================
echo.
echo    后端 API:  http://localhost:8000
echo    API 文档:  http://localhost:8000/docs
echo    前端界面:  http://localhost:3000
echo.
echo    默认账号:  editor@test.com / password123
echo.
echo    关闭此窗口不会停止服务
echo    请关闭弹出的两个 CMD 窗口来停止服务
echo ============================================
echo.

:: 尝试打开浏览器
echo 正在打开浏览器 ...
start http://localhost:3000

pause
