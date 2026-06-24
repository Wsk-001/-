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
echo [1/3] Checking Python ...
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

if "%PYTHON_CMD%"=="" (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set PYTHON_CMD=py -3
)
if "%PYTHON_CMD%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set PYTHON_CMD=py
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo [ERROR] Python not found!
    echo   Download: https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
    echo   Make sure to CHECK "Add Python to PATH" during install!
    echo.
    pause
    exit /b 1
)

echo        Python found: %PYTHON_CMD%

:: ============================================================
::  STEP 2: Install dependencies
:: ============================================================
echo [2/3] Installing dependencies ...

set USE_VENV=0
set PIP_CMD=%PYTHON_CMD% -m pip

:: Try existing venv first
if exist "%BASEDIR%apps\api\venv\Scripts\activate.bat" (
    echo        Using existing virtual environment ...
    call "%BASEDIR%apps\api\venv\Scripts\activate.bat"
    set USE_VENV=1
    set PIP_CMD=pip
) else (
    :: Try creating venv
    echo        Trying to create virtual environment ...
    cd /d "%BASEDIR%apps\api"
    "%PYTHON_CMD%" -m venv venv 2>nul
    if not errorlevel 1 (
        if exist "venv\Scripts\activate.bat" (
            echo        Virtual environment created.
            call "venv\Scripts\activate.bat"
            set USE_VENV=1
            set PIP_CMD=pip
        )
    )
)

if "%USE_VENV%"=="0" (
    echo        venv not available, installing packages directly ...
    echo        This may take a few minutes ...
)

echo        Upgrading pip ...
%PIP_CMD% install --upgrade pip --quiet 2>nul

echo        Installing packages ...
%PIP_CMD% install -r "%BASEDIR%apps\api\requirements.txt" --quiet 2>nul
if errorlevel 1 (
    echo        [WARN] Some packages failed, retrying without quiet mode ...
    %PIP_CMD% install -r "%BASEDIR%apps\api\requirements.txt"
)

:: ============================================================
::  STEP 3: Initialize database and start
:: ============================================================
echo [3/3] Initializing database ...
cd /d "%BASEDIR%apps\api"

if not exist "dev.db" (
    echo        Creating database and seeding data ...
    if "%USE_VENV%"=="1" (
        python seed.py
    ) else (
        "%PYTHON_CMD%" seed.py
    )
    if errorlevel 1 (
        echo        [WARN] Seed failed, trying to continue...
    )
)

echo.
echo ============================================
echo    Starting server ...
echo ============================================
echo.

if "%USE_VENV%"=="1" (
    start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && call venv\Scripts\activate.bat && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
) else (
    start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000"
)

echo Waiting for server to start ...
ping -n 6 127.0.0.1 >nul

echo.
echo ============================================
echo    Server started!
echo ============================================
echo.
echo    Open browser: http://localhost:8000
echo.
echo    Login: editor@test.com / password123
echo.
echo    To stop: close the ContentOS-API window
echo ============================================
echo.

start "" "http://localhost:8000"

pause
