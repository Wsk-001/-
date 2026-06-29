@echo off
title AI Workspace

echo =====================================
echo   AI Workspace Launcher
echo =====================================
echo.

:: Check Python
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo   Install Python 3.8+ from https://www.python.org/downloads/
    echo   Check "Add Python to PATH" during install.
    goto :fail
)
python --version
echo.

:: Check .env
echo [2/3] Checking config...
if not exist "backend\.env" (
    echo [NOTE] Creating .env from template...
    copy "backend\.env.example" "backend\.env" >nul
    echo [IMPORTANT] Edit backend\.env and set OPENAI_API_KEY!
    echo.
)

:: Install deps
echo [3/3] Checking dependencies...
cd backend
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Install failed!
        goto :fail
    )
) else (
    echo [OK] Dependencies ready.
)
echo.

:: Start server
echo =====================================
echo   Starting AI Workspace...
echo   Open http://localhost:8000
echo   Press Ctrl+C to stop
echo =====================================
echo.

python main.py

goto :end

:fail
echo.
echo =====================================
echo   Startup failed!
echo =====================================
echo.
pause
exit /b 1

:end
pause
