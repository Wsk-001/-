@echo off
title Content OS Launcher

echo ============================================
echo    Content OS - AI Content Production System
echo ============================================
echo.

set BASEDIR=%~dp0

:: ============================================================
::  STEP 1: Find Python
:: ============================================================
echo [1/4] Checking Python ...
set PYTHON_CMD=

python --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python

if "%PYTHON_CMD%"=="" if exist "C:\Users\Administrator\AppData\Local\Programs\Python\Python38\python.exe" set PYTHON_CMD=C:\Users\Administrator\AppData\Local\Programs\Python\Python38\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python38\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python38\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python38\python.exe" set PYTHON_CMD=C:\Python38\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python310\python.exe" set PYTHON_CMD=C:\Python310\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python311\python.exe" set PYTHON_CMD=C:\Python311\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python312\python.exe" set PYTHON_CMD=C:\Python312\python.exe

:: Check py launcher
if "%PYTHON_CMD%"=="" (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set PYTHON_CMD=py -3
)
if "%PYTHON_CMD%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set PYTHON_CMD=py
)

:: Check our portable python
if "%PYTHON_CMD%"=="" if exist "%BASEDIR%tools\python38\python.exe" set PYTHON_CMD=%BASEDIR%tools\python38\python.exe

if "%PYTHON_CMD%"=="" (
    echo.
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.8+:
    echo   https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
    echo Run installer, CHECK "Add Python to PATH", then retry.
    echo.
    pause
    exit
)

echo        Python found: %PYTHON_CMD%

:: ============================================================
::  STEP 2: Install backend dependencies
:: ============================================================
echo [2/4] Installing backend dependencies ...

if not exist "%BASEDIR%apps\api\venv\Scripts\activate.bat" (
    echo        Creating virtual environment ...
    cd /d "%BASEDIR%apps\api"
    "%PYTHON_CMD%" -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit
    )
)

call "%BASEDIR%apps\api\venv\Scripts\activate.bat"

echo        Installing Python packages (may take a few minutes)...
pip install -r "%BASEDIR%apps\api\requirements.txt" --quiet 2>nul
if errorlevel 1 (
    echo        [WARN] Some packages failed, trying to continue...
)

:: ============================================================
::  STEP 3: Initialize database
:: ============================================================
echo [3/4] Initializing database ...
cd /d "%BASEDIR%apps\api"

if not exist "dev.db" (
    echo        Creating database and seeding data ...
    python seed.py
    if errorlevel 1 (
        echo        [WARN] Seed failed, trying to continue...
    )
) else (
    echo        Database already exists.
)

:: ============================================================
::  STEP 4: Start server
:: ============================================================
echo [4/4] Starting server ...
echo.

start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && call venv\Scripts\activate.bat && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

echo Waiting for server to start ...
ping -n 5 127.0.0.1 >nul

echo.
echo ============================================
echo    Server started!
echo ============================================
echo.
echo    Open your browser and go to:
echo.
echo    http://localhost:8000
echo.
echo    Login: editor@test.com / password123
echo.
echo    To stop: close the ContentOS-API window
echo ============================================
echo.

start "" "http://localhost:8000"

pause
