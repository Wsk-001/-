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
echo [1/6] Checking Python ...
set PYTHON_CMD=

python --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python

if "%PYTHON_CMD%"=="" (
    python3 --version >nul 2>&1
    if not errorlevel 1 set PYTHON_CMD=python3
)

if "%PYTHON_CMD%"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set PYTHON_CMD=py
)

if "%PYTHON_CMD%"=="" if exist "C:\Python38\python.exe" set PYTHON_CMD=C:\Python38\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python310\python.exe" set PYTHON_CMD=C:\Python310\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python311\python.exe" set PYTHON_CMD=C:\Python311\python.exe
if "%PYTHON_CMD%"=="" if exist "C:\Python312\python.exe" set PYTHON_CMD=C:\Python312\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python38\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python38\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

:: --- Auto install Python if not found ---
if "%PYTHON_CMD%"=="" (
    echo.
    echo    Python not found. Downloading Python 3.8.20 ...
    echo.

    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.8.20/python-3.8.20-amd64.exe','%TEMP%\py38setup.exe')" 2>nul

    if not exist "%TEMP%\py38setup.exe" (
        bitsadmin /transfer pydl /download /priority foreground "https://www.python.org/ftp/python/3.8.20/python-3.8.20-amd64.exe" "%TEMP%\py38setup.exe" >nul 2>&1
    )

    if not exist "%TEMP%\py38setup.exe" (
        certutil -urlcache -split -f "https://www.python.org/ftp/python/3.8.20/python-3.8.20-amd64.exe" "%TEMP%\py38setup.exe" >nul 2>&1
    )

    if exist "%TEMP%\py38setup.exe" (
        echo    Installing Python 3.8.20 ...
        echo    Please wait 1-2 minutes ...
        "%TEMP%\py38setup.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
        del "%TEMP%\py38setup.exe" >nul 2>&1

        python --version >nul 2>&1
        if not errorlevel 1 set PYTHON_CMD=python

        if "%PYTHON_CMD%"=="" if exist "C:\Python38\python.exe" set PYTHON_CMD=C:\Python38\python.exe
        if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python38\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python38\python.exe
    )
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo [ERROR] Python not found and auto-install failed.
    echo Please install Python 3.8+ manually:
    echo   https://www.python.org/ftp/python/3.8.20/python-3.8.20-amd64.exe
    echo Run installer, CHECK "Add Python to PATH", then retry.
    echo.
    pause
    exit
)

echo        Python found: %PYTHON_CMD%

:: ============================================================
::  STEP 2: Find Node.js
:: ============================================================
echo [2/6] Checking Node.js ...
set NODE_CMD=

node --version >nul 2>&1
if not errorlevel 1 set NODE_CMD=node

if "%NODE_CMD%"=="" if exist "C:\Program Files\nodejs\node.exe" set NODE_CMD=C:\Program Files\nodejs\node.exe
if "%NODE_CMD%"=="" if exist "C:\Program Files (x86)\nodejs\node.exe" set NODE_CMD=C:\Program Files (x86)\nodejs\node.exe

:: --- Auto install Node.js if not found ---
if "%NODE_CMD%"=="" (
    echo.
    echo    Node.js not found. Downloading Node.js 20 LTS ...
    echo.

    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi','%TEMP%\node20setup.msi')" 2>nul

    if not exist "%TEMP%\node20setup.msi" (
        bitsadmin /transfer nodedl /download /priority foreground "https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi" "%TEMP%\node20setup.msi" >nul 2>&1
    )

    if not exist "%TEMP%\node20setup.msi" (
        certutil -urlcache -split -f "https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi" "%TEMP%\node20setup.msi" >nul 2>&1
    )

    if exist "%TEMP%\node20setup.msi" (
        echo    Installing Node.js 20 LTS ...
        echo    Please wait 1-2 minutes ...
        msiexec /i "%TEMP%\node20setup.msi" /qn /norestart
        del "%TEMP%\node20setup.msi" >nul 2>&1

        node --version >nul 2>&1
        if not errorlevel 1 set NODE_CMD=node
        if "%NODE_CMD%"=="" if exist "C:\Program Files\nodejs\node.exe" set NODE_CMD=C:\Program Files\nodejs\node.exe
    )
)

if "%NODE_CMD%"=="" (
    echo.
    echo [ERROR] Node.js not found and auto-install failed.
    echo Please install Node.js 18+ manually:
    echo   https://nodejs.org/
    echo.
    pause
    exit
)

echo        Node.js found: %NODE_CMD%

:: ============================================================
::  STEP 3: Set environment
:: ============================================================
echo [3/6] Setting environment ...
set PYTHONPATH=%BASEDIR%apps\api
set DATABASE_URL=sqlite+aiosqlite:///./dev.db

:: ============================================================
::  STEP 4: Install backend dependencies
:: ============================================================
echo [4/6] Installing backend dependencies ...

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

echo        Installing Python packages ...
pip install -r "%BASEDIR%apps\api\requirements.txt" --quiet 2>nul

:: ============================================================
::  STEP 5: Install frontend dependencies
:: ============================================================
echo [5/6] Installing frontend dependencies ...

if not exist "%BASEDIR%apps\web\node_modules" (
    echo        Installing npm packages (first run, may take a few minutes) ...
    cd /d "%BASEDIR%apps\web"
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed.
        pause
        exit
    )
)

:: ============================================================
::  STEP 6: Initialize database
:: ============================================================
echo [6/6] Initializing database ...
cd /d "%BASEDIR%apps\api"

if not exist "dev.db" (
    echo        Creating database and seeding data ...
    python seed.py
)

:: ============================================================
::  Start services
:: ============================================================
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
ping -n 8 127.0.0.1 >nul

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
echo    To stop: close the two ContentOS windows
echo ============================================
echo.

start "" "http://localhost:3000"

pause
