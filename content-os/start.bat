@echo off
title Content OS Launcher

echo ============================================
echo    Content OS - AI Content Production System
echo ============================================
echo.

:: ========== Check Python ==========
echo [1/6] Checking Python ...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo        Python: %%v

:: ========== Check Node.js ==========
echo [2/6] Checking Node.js ...
node --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1 delims= " %%v in ('node --version 2^>^&1') do echo        Node.js: %%v

:: ========== Set environment ==========
echo [3/6] Setting environment ...
set BASEDIR=%~dp0
set PYTHONPATH=%BASEDIR%apps\api
set DATABASE_URL=sqlite+aiosqlite:///./dev.db
echo        Dir: %BASEDIR%

:: ========== Install backend deps ==========
echo [4/6] Installing backend dependencies ...
IF NOT EXIST "%BASEDIR%apps\api\venv\Scripts\activate.bat" (
    echo        First run - creating virtual environment ...
    cd /d "%BASEDIR%apps\api"
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to create virtual environment.
        echo Make sure Python version >= 3.10
        pause
        exit /b 1
    )
)

call "%BASEDIR%apps\api\venv\Scripts\activate.bat"
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo        Installing Python packages (may take a few minutes on first run)...
pip install -r "%BASEDIR%apps\api\requirements.txt" --quiet 2>nul
IF ERRORLEVEL 1 (
    echo        [WARN] Some packages failed to install, trying to continue...
)

:: ========== Install frontend deps ==========
echo [5/6] Installing frontend dependencies ...
IF NOT EXIST "%BASEDIR%apps\web\node_modules" (
    echo        First run - installing npm packages (may take a few minutes)...
    cd /d "%BASEDIR%apps\web"
    call npm install
    IF ERRORLEVEL 1 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
) else (
    echo        Frontend dependencies already installed.
)

:: ========== Init database ==========
echo [6/6] Initializing database ...
cd /d "%BASEDIR%apps\api"
IF NOT EXIST "dev.db" (
    echo        Creating database and seeding data ...
    python seed.py
    IF ERRORLEVEL 1 (
        echo        [WARN] Seed data import failed, trying to continue...
    )
) else (
    echo        Database already exists, skipping.
)

:: ========== Start services ==========
echo.
echo ============================================
echo    Starting services ...
echo ============================================
echo.

echo [START] Backend API  -> http://localhost:8000
start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && call venv\Scripts\activate.bat && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo [START] Frontend Web -> http://localhost:3000
start "ContentOS-Web" cmd /k "cd /d %BASEDIR%apps\web && npm run dev"

echo Waiting for services to start ...
ping -n 6 127.0.0.1 >nul

echo.
echo ============================================
echo    Services started!
echo ============================================
echo.
echo    Backend API:  http://localhost:8000
echo    API Docs:      http://localhost:8000/docs
echo    Frontend:      http://localhost:3000
echo.
echo    Login:         editor@test.com / password123
echo.
echo    Closing this window will NOT stop services.
echo    To stop, close the two ContentOS windows.
echo ============================================
echo.

echo Opening browser ...
start "" "http://localhost:3000"

pause
