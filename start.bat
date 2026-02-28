@echo off
title AI Agent — Ollama + Telegram + REST API

echo.
echo  =========================================
echo    AI Agent — Windows Launcher
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

:: Install requirements
echo [INFO] Checking requirements...
pip install -r requirements.txt -q

:: Check if Ollama is running, start if not
echo [INFO] Checking Ollama...
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Starting Ollama server...
    start /b "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
    timeout /t 4 /nobreak >nul
)

echo.
echo [INFO] Starting AI Agent...
echo [INFO] REST API  -> http://localhost:8000
echo [INFO] API Docs  -> http://localhost:8000/docs
echo.

python main.py

pause
