@echo off
title Content OS Launcher

echo ============================================
echo    Content OS - AI Content Production System
echo ============================================
echo.

set BASEDIR=%~dp0
set PYDIR=%BASEDIR%tools\python38

:: ============================================================
::  STEP 1: Setup Python (embeddable, no installer needed)
:: ============================================================
echo [1/6] Checking Python ...
set PYTHON_CMD=

:: Check existing Python first
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
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python38\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python38\python.exe
if "%PYTHON_CMD%"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe

:: Check our bundled embeddable Python
if "%PYTHON_CMD%"=="" if exist "%PYDIR%\python.exe" set PYTHON_CMD=%PYDIR%\python.exe

:: --- Auto download embeddable Python (no installer, just unzip) ---
if "%PYTHON_CMD%"=="" (
    echo.
    echo    Python not found. Downloading portable Python 3.8.10 ...
    echo    (No installer needed - just extract and run)
    echo.

    set PYZIP=%BASEDIR%tools\python38.zip
    set PYURL=https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip

    if not exist "%BASEDIR%tools" mkdir "%BASEDIR%tools"

    echo    Downloading ...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip','%BASEDIR%tools\python38.zip')" 2>nul

    if not exist "%BASEDIR%tools\python38.zip" (
        bitsadmin /transfer pydl /download /priority foreground "https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip" "%BASEDIR%tools\python38.zip" >nul 2>&1
    )

    if not exist "%BASEDIR%tools\python38.zip" (
        certutil -urlcache -split -f "https://www.python.org/ftp/python/3.8.10/python-3.8.10-embed-amd64.zip" "%BASEDIR%tools\python38.zip" >nul 2>&1
    )

    if exist "%BASEDIR%tools\python38.zip" (
        echo    Extracting ...
        if not exist "%PYDIR%" mkdir "%PYDIR%"

        :: Try PowerShell unzip first
        powershell -Command "Expand-Archive -Path '%BASEDIR%tools\python38.zip' -DestinationPath '%PYDIR%' -Force" 2>nul

        :: If PowerShell failed, try tar (Win10+)
        if not exist "%PYDIR%\python.exe" (
            tar -xf "%BASEDIR%tools\python38.zip" -C "%PYDIR%" 2>nul
        )

        :: If tar failed, try VBScript unzip
        if not exist "%PYDIR%\python.exe" (
            echo    Using VBScript to unzip ...
            echo Set objShell = CreateObject("Shell.Application") > "%TEMP%\unzip.vbs"
            echo Set objZip = objShell.NameSpace("%BASEDIR%tools\python38.zip") >> "%TEMP%\unzip.vbs"
            echo Set objDest = objShell.NameSpace("%PYDIR%") >> "%TEMP%\unzip.vbs"
            echo objDest.CopyHere objZip.Items, 256 >> "%TEMP%\unzip.vbs"
            cscript //nologo "%TEMP%\unzip.vbs" 2>nul
            del "%TEMP%\unzip.vbs" >nul 2>&1
        )

        if exist "%PYDIR%\python.exe" (
            echo    Python 3.8.10 portable ready!
            del "%BASEDIR%tools\python38.zip" >nul 2>&1

            :: Enable pip in embeddable Python
            echo    Setting up pip ...
            if exist "%PYDIR%\python38._pth" (
                echo Lib\site-packages>> "%PYDIR%\python38._pth"
                echo .>> "%PYDIR%\python38._pth"
                echo Lib>> "%PYDIR%\python38._pth"
                echo import site>> "%PYDIR%\python38._pth"
            )
            if not exist "%PYDIR%\Lib" mkdir "%PYDIR%\Lib"
            if not exist "%PYDIR%\Lib\site-packages" mkdir "%PYDIR%\Lib\site-packages"

            :: Download get-pip.py
            powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://bootstrap.pypa.io/get-pip.py','%PYDIR%\get-pip.py')" 2>nul
            if exist "%PYDIR%\get-pip.py" (
                "%PYDIR%\python.exe" "%PYDIR%\get-pip.py" --no-warn-script-location 2>nul
                del "%PYDIR%\get-pip.py" >nul 2>&1
            )

            set PYTHON_CMD=%PYDIR%\python.exe
        ) else (
            echo.
            echo    [ERROR] Failed to extract Python.
            echo    Please install Python 3.8+ manually:
            echo      https://www.python.org/downloads/
            echo.
            pause
            exit
        )
    ) else (
        echo.
        echo    [ERROR] Could not download Python.
        echo    Please install Python 3.8+ manually:
        echo      https://www.python.org/downloads/
        echo.
        pause
        exit
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found.
    pause
    exit
)

echo        Python found: %PYTHON_CMD%

:: ============================================================
::  STEP 2: Setup Node.js
:: ============================================================
echo [2/6] Checking Node.js ...
set NODE_CMD=

node --version >nul 2>&1
if not errorlevel 1 set NODE_CMD=node

if "%NODE_CMD%"=="" if exist "C:\Program Files\nodejs\node.exe" set NODE_CMD=C:\Program Files\nodejs\node.exe
if "%NODE_CMD%"=="" if exist "C:\Program Files (x86)\nodejs\node.exe" set NODE_CMD=C:\Program Files (x86)\nodejs\node.exe

if "%NODE_CMD%"=="" (
    echo.
    echo    Node.js not found. Please install Node.js 18+ manually:
    echo      https://nodejs.org/
    echo    Then run this script again.
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
        echo Trying without venv ...
        set VENV=0
    ) else (
        set VENV=1
    )
) else (
    set VENV=1
)

if "%VENV%"=="1" call "%BASEDIR%apps\api\venv\Scripts\activate.bat"

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
