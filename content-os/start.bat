@echo off
title Content OS 启动器

echo ============================================
echo    Content OS - AI内容生产系统 启动器
echo ============================================
echo.

:: ========== 检查 Python ==========
echo [1/6] 检查 Python ...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo        Python: %%v

:: ========== 检查 Node.js ==========
echo [2/6] 检查 Node.js ...
node --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1 delims= " %%v in ('node --version 2^>^&1') do echo        Node.js: %%v

:: ========== 设置路径 ==========
echo [3/6] 设置环境变量 ...
set BASEDIR=%~dp0
set PYTHONPATH=%BASEDIR%apps\api
set DATABASE_URL=sqlite+aiosqlite:///./dev.db
echo        目录: %BASEDIR%

:: ========== 安装后端依赖 ==========
echo [4/6] 安装后端依赖 ...
IF NOT EXIST "%BASEDIR%apps\api\venv\Scripts\activate.bat" (
    echo        首次运行，创建虚拟环境 ...
    cd /d "%BASEDIR%apps\api"
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [错误] 创建虚拟环境失败，请确认 Python 版本 >= 3.10
        pause
        exit /b 1
    )
)

call "%BASEDIR%apps\api\venv\Scripts\activate.bat"
IF ERRORLEVEL 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

echo        安装 Python 包（首次可能需要几分钟）...
pip install -r "%BASEDIR%apps\api\requirements.txt" --quiet 2>nul
IF ERRORLEVEL 1 (
    echo        [提示] 部分包安装失败，尝试继续运行...
)

:: ========== 安装前端依赖 ==========
echo [5/6] 安装前端依赖 ...
IF NOT EXIST "%BASEDIR%apps\web\node_modules" (
    echo        首次运行，安装 npm 依赖（可能需要几分钟）...
    cd /d "%BASEDIR%apps\web"
    call npm install
    IF ERRORLEVEL 1 (
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
) else (
    echo        前端依赖已安装
)

:: ========== 初始化数据库 ==========
echo [6/6] 初始化数据库 ...
cd /d "%BASEDIR%apps\api"
IF NOT EXIST "dev.db" (
    echo        创建数据库并导入种子数据 ...
    python seed.py
    IF ERRORLEVEL 1 (
        echo        [提示] 种子数据导入失败，尝试继续...
    )
) else (
    echo        数据库已存在，跳过
)

:: ========== 启动服务 ==========
echo.
echo ============================================
echo    正在启动服务 ...
echo ============================================
echo.

echo [启动] 后端 API  - http://localhost:8000
start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && call venv\Scripts\activate.bat && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [启动] 前端界面  - http://localhost:3000
start "ContentOS-Web" cmd /k "cd /d %BASEDIR%apps\web && npm run dev"

echo 等待服务启动 ...
ping -n 6 127.0.0.1 >nul

echo.
echo ============================================
echo    启动完成！
echo ============================================
echo.
echo    后端 API:  http://localhost:8000
echo    API 文档:  http://localhost:8000/docs
echo    前端界面:  http://localhost:3000
echo.
echo    默认账号:  editor@test.com
echo    默认密码:  password123
echo.
echo    关闭此窗口不会停止服务
echo    要停止请关闭标题为 ContentOS 的两个窗口
echo ============================================
echo.

echo 正在打开浏览器 ...
start "" "http://localhost:3000"

pause
