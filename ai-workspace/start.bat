@echo off
title AI Workspace

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend
set FRONTEND_DIR=%ROOT_DIR%frontend

echo =====================================
echo   AI Workspace Launcher
echo =====================================
echo.

:: Check Python
echo [1/6] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo   Please install Python 3.10+ from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during install.
    goto :fail
)
python --version
echo.

:: Check Node.js
echo [2/6] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo   Please install Node.js 18+ from https://nodejs.org/
    goto :fail
)
node --version
echo.

:: Check directories
echo [3/6] Checking project files...
if not exist "%BACKEND_DIR%" (
    echo [ERROR] backend folder not found: %BACKEND_DIR%
    goto :fail
)
if not exist "%FRONTEND_DIR%" (
    echo [ERROR] frontend folder not found: %FRONTEND_DIR%
    goto :fail
)
echo [OK] Project files found.
echo.

:: Check .env
if not exist "%BACKEND_DIR%\.env" (
    echo [NOTE] Creating .env from template...
    copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    echo [IMPORTANT] Please edit backend\.env and set OPENAI_API_KEY!
    echo.
)

:: Install backend deps
echo [4/6] Checking backend dependencies...
cd /d "%BACKEND_DIR%"
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing backend dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Backend dependency install failed!
        goto :fail
    )
) else (
    echo [OK] Backend dependencies ready.
)
echo.

:: Install frontend deps
echo [5/6] Checking frontend dependencies...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [INSTALL] Installing frontend dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        echo [ERROR] Frontend dependency install failed!
        goto :fail
    )
) else (
    echo [OK] Frontend dependencies ready.
)
echo.

:: Start backend
echo [6/6] Starting services...
echo.
echo [START] Backend FastAPI (http://localhost:8000)
cd /d "%BACKEND_DIR%"
start "AI Workspace - Backend" cmd /k "python main.py"

:: Wait for backend
echo [WAIT] Waiting for backend...
timeout /t 4 /nobreak >nul

:: Start frontend
echo [START] Frontend Next.js (http://localhost:3000)
cd /d "%FRONTEND_DIR%"
start "AI Workspace - Frontend" cmd /k "npx next dev -p 3000"

echo.
echo [WAIT] Waiting for frontend...
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo =====================================
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Close the popup windows to stop.
echo   This window can be closed safely.
echo =====================================
echo.
goto :end

:fail
echo.
echo =====================================
echo   Startup failed! Check errors above.
echo =====================================
echo.
pause
exit /b 1

:end
pause
