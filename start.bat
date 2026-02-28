@echo off
title AI Agent — Ollama + Telegram + REST API

echo.
echo  =========================================
echo    AI Agent - Windows Launcher
echo  =========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

if not exist ".env" (
    echo [ERROR] .env not found in project root.
    echo [ERROR] Copy .env.example to .env and configure required values.
    pause
    exit /b 1
)

:: Resolve runtime host/port from .env
set "APP_HOST=0.0.0.0"
set "APP_PORT=8000"
set "OLLAMA_BIN="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="HOST" set "APP_HOST=%%B"
    if /I "%%A"=="PORT" set "APP_PORT=%%B"
    if /I "%%A"=="OLLAMA_BIN" set "OLLAMA_BIN=%%~B"
)

if "%APP_HOST%"=="" set "APP_HOST=0.0.0.0"
if "%APP_PORT%"=="" set "APP_PORT=8000"

set "DISPLAY_HOST=%APP_HOST%"
if /I "%DISPLAY_HOST%"=="0.0.0.0" set "DISPLAY_HOST=localhost"

:: Install requirements
echo [INFO] Checking requirements...
pip install -r requirements.txt -q

:: Check if Ollama is running, start if not
echo [INFO] Checking Ollama...
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    if not defined OLLAMA_BIN (
        for /f "delims=" %%I in ('where ollama.exe 2^>nul') do (
            if not defined OLLAMA_BIN set "OLLAMA_BIN=%%~fI"
        )
    )

    if not defined OLLAMA_BIN if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_BIN=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    if not defined OLLAMA_BIN if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_BIN=%ProgramFiles%\Ollama\ollama.exe"
    if not defined OLLAMA_BIN if exist "%ProgramFiles(x86)%\Ollama\ollama.exe" set "OLLAMA_BIN=%ProgramFiles(x86)%\Ollama\ollama.exe"
    if not defined OLLAMA_BIN if exist "D:\Program Files\Ollama\ollama.exe" set "OLLAMA_BIN=D:\Program Files\Ollama\ollama.exe"
    if not defined OLLAMA_BIN if exist "D:\OLLMA\ollama.exe" set "OLLAMA_BIN=D:\OLLMA\ollama.exe"

    if not defined OLLAMA_BIN (
        echo [ERROR] Ollama executable not found.
        echo [ERROR] Add Ollama to PATH or set OLLAMA_BIN in .env, for example:
        echo [ERROR] OLLAMA_BIN=D:\Program Files\Ollama\ollama.exe
        pause
        exit /b 1
    )

    echo [INFO] Starting Ollama server using: "%OLLAMA_BIN%"
    start "" /B "%OLLAMA_BIN%" serve
    timeout /t 4 /nobreak >nul
)

echo.
echo [INFO] Starting AI Agent...
echo [INFO] REST API  -> http://%DISPLAY_HOST%:%APP_PORT%
echo [INFO] API Docs  -> http://%DISPLAY_HOST%:%APP_PORT%/docs
echo [INFO] Status    -> http://%DISPLAY_HOST%:%APP_PORT%/status
echo [INFO] Health    -> http://%DISPLAY_HOST%:%APP_PORT%/health
echo [INFO] Realtime  -> ws://%DISPLAY_HOST%:%APP_PORT%/ws/chat
echo.

python main.py

pause
