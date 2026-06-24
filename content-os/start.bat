@echo off
title Content OS Launcher

echo ============================================
echo    Content OS - AI Content Production System
echo ============================================
echo.

set BASEDIR=%~dp0

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

if not "%PYTHON_CMD%"=="" goto :python_found
py -3 --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py -3
if not "%PYTHON_CMD%"=="" goto :python_found
py --version >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=py

:python_found
if not "%PYTHON_CMD%"=="" goto :python_ok
echo.
echo [ERROR] Python not found!
echo   Download: https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe
echo   CHECK "Add Python to PATH" during install!
echo.
pause
exit /b 1

:python_ok
echo        Python found: %PYTHON_CMD%
"%PYTHON_CMD%" --version
echo.

echo [2/3] Installing dependencies ...
echo.

set USE_VENV=0
set PIP_CMD=%PYTHON_CMD% -m pip

if exist "%BASEDIR%apps\api\venv\Scripts\activate.bat" goto :use_venv
goto :try_create_venv

:use_venv
echo        Using existing virtual environment ...
call "%BASEDIR%apps\api\venv\Scripts\activate.bat"
set USE_VENV=1
set PIP_CMD=pip
goto :check_pip

:try_create_venv
echo        Trying to create virtual environment ...
cd /d "%BASEDIR%apps\api"
"%PYTHON_CMD%" -m venv venv
if not exist "venv\Scripts\activate.bat" goto :no_venv
echo        Virtual environment created.
call "venv\Scripts\activate.bat"
set USE_VENV=1
set PIP_CMD=pip
goto :check_pip

:no_venv
echo        venv not available, installing directly ...

:check_pip
echo        Checking pip ...
%PIP_CMD% --version >nul 2>&1
if not errorlevel 1 goto :pip_ok
echo        pip not found, installing pip ...
cd /d "%BASEDIR%"
if exist "get-pip-38.py" goto :run_get_pip
echo        Downloading get-pip.py ...
if exist "get-pip.py" del get-pip.py
if exist "%SystemRoot%\System32\curl.exe" (
    curl -sS -o get-pip-38.py https://bootstrap.pypa.io/pip/3.8/get-pip.py
) else (
    "%PYTHON_CMD%" -c "from urllib.request import urlretrieve; urlretrieve('https://bootstrap.pypa.io/pip/3.8/get-pip.py', 'get-pip-38.py')"
)
if not exist "get-pip-38.py" (
    echo        [ERROR] Could not download get-pip.py
    echo        Please install pip manually or reinstall Python with pip.
    echo.
    pause
    exit /b 1
)
:run_get_pip
"%PYTHON_CMD%" get-pip-38.py
if errorlevel 1 (
    echo        [ERROR] Failed to install pip!
    pause
    exit /b 1
)
echo        pip installed successfully.

:pip_ok
echo.
echo        Upgrading pip ...
%PIP_CMD% install --upgrade pip

echo.
echo        Installing packages ...
%PIP_CMD% install -r "%BASEDIR%apps\api\requirements.txt"
if errorlevel 1 (
    echo.
    echo        [ERROR] Failed to install packages!
    echo        Check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo        All packages installed.
echo.

echo        Verifying installation ...
if "%USE_VENV%"=="1" (
    python -c "import fastapi; import uvicorn; import sqlalchemy; import aiosqlite; print('        Imports OK')"
) else (
    "%PYTHON_CMD%" -c "import fastapi; import uvicorn; import sqlalchemy; import aiosqlite; print('        Imports OK')"
)
if errorlevel 1 (
    echo        [ERROR] Critical packages missing!
    pause
    exit /b 1
)

echo.
echo [3/3] Initializing database ...
cd /d "%BASEDIR%apps\api"

if exist "dev.db" goto :db_exists
echo        Creating database ...
if "%USE_VENV%"=="1" (
    python seed.py
) else (
    "%PYTHON_CMD%" seed.py
)
if errorlevel 1 echo        [WARN] Seed had errors, continuing...

:db_exists
echo        Database ready.
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

echo Waiting for server ...
ping -n 8 127.0.0.1 >nul

echo.
echo        Checking server ...
if "%USE_VENV%"=="1" (
    python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/health'); print('        Server running:', r.read().decode())" 2>nul
) else (
    "%PYTHON_CMD%" -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/health'); print('        Server running:', r.read().decode())" 2>nul
)

if errorlevel 1 (
    echo.
    echo        [WARN] Could not reach server.
    echo        Check the ContentOS-API window for errors.
    echo.
) else (
    echo.
    echo ============================================
    echo    Server started!
    echo ============================================
    echo.
    echo    Open browser: http://localhost:8000
    echo    Login: editor@test.com / password123
    echo    To stop: close the ContentOS-API window
    echo.
    start "" "http://localhost:8000"
)

pause
