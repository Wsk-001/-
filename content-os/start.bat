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

:: Check PATH
python --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python

:: Check common install locations (most likely first)
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
    echo [WARN] Python not found automatically.
    echo.
    echo Searching for python.exe on your computer ...
    echo.

    :: Search C drive for python.exe
    dir /s /b "C:\python.exe" 2>nul | findstr /i "python.exe" > "%TEMP%\pyfound.txt"
    dir /s /b "C:\Users\python.exe" 2>nul | findstr /i "python.exe" >> "%TEMP%\pyfound.txt"

    :: Show found results
    if exist "%TEMP%\pyfound.txt" (
        echo Found these python.exe:
        echo.
        type "%TEMP%\pyfound.txt"
        echo.
    ) else (
        echo No python.exe found on C drive.
        echo.
    )
    del "%TEMP%\pyfound.txt" >nul 2>&1

    echo Please enter the full path to python.exe
    echo Example: C:\Python38\python.exe
    echo Or press Enter to exit:
    echo.
    set /p PYTHON_CMD="Path to python.exe: "

    if "%PYTHON_CMD%"=="" (
        echo.
        echo Cancelled.
        pause
        exit
    )

    if not exist "%PYTHON_CMD%" (
        echo.
        echo [ERROR] File not found: %PYTHON_CMD%
        echo Please check the path and try again.
        pause
        exit
    )

    echo        Using: %PYTHON_CMD%
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

if "%NODE_CMD%"=="" (
    echo.
    echo [ERROR] Node.js not found!
    echo   Download from: https://nodejs.org/
    echo   Install, then run this script again.
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
echo        OK

:: ============================================================
::  STEP 4: Install backend dependencies
:: ============================================================
echo [4/6] Installing backend dependencies ...

if not exist "%BASEDIR%apps\api\venv\Scripts\activate.bat" (
    echo        Creating virtual environment ...
    cd /d "%BASEDIR%apps\api"
    "%PYTHON_CMD%" -m venv venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to create virtual environment.
        echo This may be because Python 3.8 embeddable does not support venv.
        echo Trying direct install instead ...
        echo.
        set USE_VENV=0
    ) else (
        set USE_VENV=1
    )
) else (
    set USE_VENV=1
)

if "%USE_VENV%"=="1" (
    call "%BASEDIR%apps\api\venv\Scripts\activate.bat"
    echo        Virtual environment activated.
)

echo        Installing Python packages (may take a few minutes)...
if "%USE_VENV%"=="1" (
    pip install -r "%BASEDIR%apps\api\requirements.txt" 2>nul
) else (
    "%PYTHON_CMD%" -m pip install -r "%BASEDIR%apps\api\requirements.txt" 2>nul
)

if errorlevel 1 (
    echo        [WARN] Some packages failed to install, trying to continue...
)

:: ============================================================
::  STEP 5: Install frontend dependencies
:: ============================================================
echo [5/6] Installing frontend dependencies ...

if not exist "%BASEDIR%apps\web\node_modules" (
    echo        Installing npm packages (first run, may take a few minutes)...
    cd /d "%BASEDIR%apps\web"
    call npm install
    if errorlevel 1 (
        echo.
        echo [ERROR] npm install failed.
        echo.
        pause
        exit
    )
) else (
    echo        Already installed.
)

:: ============================================================
::  STEP 6: Initialize database
:: ============================================================
echo [6/6] Initializing database ...
cd /d "%BASEDIR%apps\api"

if not exist "dev.db" (
    echo        Creating database ...
    "%PYTHON_CMD%" seed.py
    if errorlevel 1 (
        echo        [WARN] Seed failed, trying python command ...
        python seed.py
    )
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
if "%USE_VENV%"=="1" (
    start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && call venv\Scripts\activate.bat && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
) else (
    start "ContentOS-API" cmd /k "cd /d %BASEDIR%apps\api && set PYTHONPATH=%BASEDIR%apps\api && set DATABASE_URL=sqlite+aiosqlite:///./dev.db && %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000"
)

echo [START] Frontend Web -> http://localhost:3000
start "ContentOS-Web" cmd /k "cd /d %BASEDIR%apps\web && npm run dev"

echo.
echo Waiting for services to start (8 seconds) ...
ping -n 9 127.0.0.1 >nul

echo.
echo ============================================
echo    Done!
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
