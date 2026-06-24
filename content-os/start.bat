@echo off
title Content OS Launcher
setlocal enabledelayedexpansion

echo ============================================
echo    Content OS - AI Content Production System
echo ============================================
echo.

set BASEDIR=%~dp0

:: ============================================================
::  STEP 1: Find or install Python
:: ============================================================
echo [1/6] Checking Python ...
set PYTHON_CMD=

:: Try existing installations
for %%c in (python python3 py) do (
    if "!PYTHON_CMD!"=="" (
        %%c --version >nul 2>&1
        if not errorlevel 1 set PYTHON_CMD=%%c
    )
)

:: Try common paths
for %%p in (
    "C:\Python310\python.exe"
    "C:\Python311\python.exe"
    "C:\Python312\python.exe"
    "C:\Python313\python.exe"
    "C:\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
) do (
    if "!PYTHON_CMD!"=="" (
        if exist %%p set PYTHON_CMD=%%p
    )
)

:: Auto-install Python if not found
if "!PYTHON_CMD!"=="" (
    echo.
    echo    Python not found. Auto-installing Python 3.12 ...
    echo.

    set PY_INSTALLER=%TEMP%\python-3.12.9-amd64.exe
    set PY_URL=https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe

    echo    Downloading Python 3.12.9 ...

    :: Try PowerShell first (faster)
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe','%TEMP%\python-3.12.9-amd64.exe')" >nul 2>&1

    :: If PowerShell failed, try bitsadmin
    if not exist "%TEMP%\python-3.12.9-amd64.exe" (
        echo    PowerShell download failed, trying bitsadmin ...
        bitsadmin /transfer pydownload /download /priority foreground "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe" "%TEMP%\python-3.12.9-amd64.exe" >nul 2>&1
    )

    :: If bitsadmin also failed, try certutil
    if not exist "%TEMP%\python-3.12.9-amd64.exe" (
        echo    bitsadmin failed, trying certutil ...
        certutil -urlcache -split -f "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe" "%TEMP%\python-3.12.9-amd64.exe" >nul 2>&1
    )

    if exist "%TEMP%\python-3.12.9-amd64.exe" (
        echo.
        echo    Installing Python 3.12.9 (silent install, adding to PATH) ...
        echo    Please wait, this may take 1-2 minutes ...
        echo.
        "%TEMP%\python-3.12.9-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1
        if errorlevel 1 (
            echo.
            echo    [ERROR] Python installation failed.
            echo    Please install manually from https://www.python.org/downloads/
            echo    IMPORTANT: Check "Add Python to PATH" during install!
            echo.
            pause
            exit /b 1
        )
        echo    Python installed successfully!
        del "%TEMP%\python-3.12.9-amd64.exe" >nul 2>&1

        :: Refresh PATH for current session
        set PYTHON_CMD=
        for %%c in (python python3 py) do (
            if "!PYTHON_CMD!"=="" (
                %%c --version >nul 2>&1
                if not errorlevel 1 set PYTHON_CMD=%%c
            )
        )
    ) else (
        echo.
        echo    [ERROR] Could not download Python automatically.
        echo.
        echo    Please install Python 3.10+ manually:
        echo      1. Go to https://www.python.org/downloads/
        echo      2. Download Python 3.12
        echo      3. Run installer, CHECK "Add Python to PATH"
        echo      4. Run this script again
        echo.
        pause
        exit /b 1
    )
)

if "!PYTHON_CMD!"=="" (
    echo [ERROR] Python still not found after install. Please restart this script.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('!PYTHON_CMD! --version 2^>^&1') do echo        Python: %%v  [!PYTHON_CMD!]

:: ============================================================
::  STEP 2: Find or install Node.js
:: ============================================================
echo [2/6] Checking Node.js ...
set NODE_CMD=

node --version >nul 2>&1
if not errorlevel 1 set NODE_CMD=node

if "!NODE_CMD!"=="" (
    if exist "C:\Program Files\nodejs\node.exe" set NODE_CMD=C:\Program Files\nodejs\node.exe
)
if "!NODE_CMD!"=="" (
    if exist "C:\Program Files (x86)\nodejs\node.exe" set NODE_CMD=C:\Program Files (x86)\nodejs\node.exe
)

:: Auto-install Node.js if not found
if "!NODE_CMD!"=="" (
    echo.
    echo    Node.js not found. Auto-installing Node.js 20 LTS ...
    echo.

    set NODE_MSI=%TEMP%\node-v20.18.2-x64.msi
    set NODE_URL=https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi

    echo    Downloading Node.js 20.18.2 LTS ...

    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi','%TEMP%\node-v20.18.2-x64.msi')" >nul 2>&1

    if not exist "%TEMP%\node-v20.18.2-x64.msi" (
        bitsadmin /transfer nodedownload /download /priority foreground "https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi" "%TEMP%\node-v20.18.2-x64.msi" >nul 2>&1
    )

    if not exist "%TEMP%\node-v20.18.2-x64.msi" (
        certutil -urlcache -split -f "https://nodejs.org/dist/v20.18.2/node-v20.18.2-x64.msi" "%TEMP%\node-v20.18.2-x64.msi" >nul 2>&1
    )

    if exist "%TEMP%\node-v20.18.2-x64.msi" (
        echo.
        echo    Installing Node.js 20.18.2 LTS (silent install) ...
        echo    Please wait, this may take 1-2 minutes ...
        echo.
        msiexec /i "%TEMP%\node-v20.18.2-x64.msi" /qn /norestart
        echo    Node.js installed successfully!
        del "%TEMP%\node-v20.18.2-x64.msi" >nul 2>&1

        set NODE_CMD=
        node --version >nul 2>&1
        if not errorlevel 1 set NODE_CMD=node
        if "!NODE_CMD!"=="" (
            if exist "C:\Program Files\nodejs\node.exe" set NODE_CMD=C:\Program Files\nodejs\node.exe
        )
    ) else (
        echo.
        echo    [ERROR] Could not download Node.js automatically.
        echo.
        echo    Please install Node.js 18+ manually:
        echo      1. Go to https://nodejs.org/
        echo      2. Download the LTS version
        echo      3. Run installer
        echo      4. Run this script again
        echo.
        pause
        exit /b 1
    )
)

if "!NODE_CMD!"=="" (
    echo [ERROR] Node.js still not found after install. Please restart this script.
    pause
    exit /b 1
)

for /f "tokens=1 delims= " %%v in ('!NODE_CMD! --version 2^>^&1') do echo        Node.js: %%v

:: ============================================================
::  STEP 3: Set environment
:: ============================================================
echo [3/6] Setting environment ...
set PYTHONPATH=%BASEDIR%apps\api
set DATABASE_URL=sqlite+aiosqlite:///./dev.db
echo        Work dir: %BASEDIR%

:: ============================================================
::  STEP 4: Install backend dependencies
:: ============================================================
echo [4/6] Installing backend dependencies ...
if not exist "%BASEDIR%apps\api\venv\Scripts\activate.bat" (
    echo        First run - creating virtual environment ...
    cd /d "%BASEDIR%apps\api"
    "!PYTHON_CMD!" -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call "%BASEDIR%apps\api\venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo        Installing Python packages (first run may take a few minutes)...
pip install -r "%BASEDIR%apps\api\requirements.txt" --quiet 2>nul
if errorlevel 1 (
    echo        [WARN] Some packages failed, trying to continue...
)

:: ============================================================
::  STEP 5: Install frontend dependencies
:: ============================================================
echo [5/6] Installing frontend dependencies ...
if not exist "%BASEDIR%apps\web\node_modules" (
    echo        First run - installing npm packages (may take a few minutes)...
    cd /d "%BASEDIR%apps\web"
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
) else (
    echo        Frontend dependencies already installed.
)

:: ============================================================
::  STEP 6: Initialize database
:: ============================================================
echo [6/6] Initializing database ...
cd /d "%BASEDIR%apps\api"
if not exist "dev.db" (
    echo        Creating database and seeding data ...
    python seed.py
    if errorlevel 1 (
        echo        [WARN] Seed data import failed, trying to continue...
    )
) else (
    echo        Database already exists, skipping.
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
echo    Closing this window will NOT stop services.
echo    To stop, close the two ContentOS windows.
echo ============================================
echo.

echo Opening browser ...
start "" "http://localhost:3000"

pause
