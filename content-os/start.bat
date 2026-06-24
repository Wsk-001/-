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
"%PYTHON_CMD%" --version

:: ============================================================
::  STEP 2: Install dependencies
:: ============================================================
echo.
echo [2/3] Installing dependencies ...
echo.

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
    "%PYTHON_CMD%" -m venv venv
    if not errorlevel 1 (
        if exist "venv\Scripts\activate.bat" (
            echo        Virtual environment created.
            call "venv\Scripts\activate.bat"
            set USE_VENV=1
            set PIP_CMD=pip
        )
    ) else (
        echo        [INFO] venv creation failed, will install directly.
    )
)

if "%USE_VENV%"=="0" (
    echo        Installing packages directly (no venv)...
)

echo.
echo        Upgrading pip ...
%PIP_CMD% install --upgrade pip

echo.
echo        Installing packages (this may take a few minutes) ...
%PIP_CMD% install -r "%BASEDIR%apps\api\requirements.txt"
if errorlevel 1 (
    echo.
    echo        [ERROR] Failed to install some packages!
    echo        Please check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo        All packages installed successfully.

:: ============================================================
::  STEP 3: Verify critical imports
:: ============================================================
echo.
echo        Verifying installation ...
if "%USE_VENV%"=="1" (
    python -c "import fastapi; import uvicorn; import sqlalchemy; import aiosqlite; print('        All critical imports OK')"
) else (
    "%PYTHON_CMD%" -c "import fastapi; import uvicorn; import sqlalchemy; import aiosqlite; print('        All critical imports OK')"
)
if errorlevel 1 (
    echo.
    echo        [ERROR] Critical Python packages are missing!
    echo        Please check the error messages above.
    echo.
    pause
    exit /b 1
)

:: ============================================================
::  STEP 4: Initialize database and start
:: ============================================================
echo.
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
) else (
    echo        Database already exists, skipping seed.
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
ping -n 8 127.0.0.1 >nul

echo.
echo ============================================
echo    Checking server ...
echo ============================================
echo.

:: Try to connect to the server
if "%USE_VENV%"=="1" (
    python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/health'); print('        Server is running! Status:', r.read().decode())" 2>nul
) else (
    "%PYTHON_CMD%" -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/health'); print('        Server is running! Status:', r.read().decode())" 2>nul
)

if errorlevel 1 (
    echo.
    echo        [WARN] Could not connect to server.
    echo        Check the ContentOS-API window for error messages.
    echo        Common issues:
    echo          - Port 8000 already in use
    echo          - Python packages not fully installed
    echo.
) else (
    echo.
    echo ============================================
    echo    Server started successfully!
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
)

pause
