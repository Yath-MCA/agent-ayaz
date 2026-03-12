@echo off
REM ============================================================
REM  ollama-start.bat — Start Ollama locally and pull model
REM  Usage:
REM    ollama-start.bat                 (uses OLLAMA_MODEL from .env)
REM    ollama-start.bat mistral         (override model)
REM    ollama-start.bat mistral --pull  (force re-pull model)
REM ============================================================

setlocal enabledelayedexpansion

title Ollama Local Server

set "SCRIPT_DIR=%~dp0"
set "MODEL_OVERRIDE=%~1"
set "FORCE_PULL=%~2"

REM ── Read OLLAMA_MODEL and OLLAMA_BIN from .env ──────────────
set "OLLAMA_MODEL=mistral"
set "OLLAMA_BIN="
set "OLLAMA_URL=http://localhost:11434"

if exist "%SCRIPT_DIR%.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%SCRIPT_DIR%.env") do (
        if /I "%%A"=="OLLAMA_MODEL" set "OLLAMA_MODEL=%%B"
        if /I "%%A"=="OLLAMA_BIN"   set "OLLAMA_BIN=%%~B"
        if /I "%%A"=="OLLAMA_URL"   set "OLLAMA_URL=%%B"
    )
)

REM Override model from command line
if not "%MODEL_OVERRIDE%"=="" (
    if not "%MODEL_OVERRIDE%"=="--pull" set "OLLAMA_MODEL=%MODEL_OVERRIDE%"
)

echo.
echo  ============================================
echo   Ollama Local Server
echo  ============================================
echo   Model : %OLLAMA_MODEL%
echo   URL   : %OLLAMA_URL%
echo  ============================================
echo.

REM ── Locate ollama.exe ───────────────────────────────────────
if not defined OLLAMA_BIN (
    for /f "delims=" %%I in ('where ollama.exe 2^>nul') do (
        if not defined OLLAMA_BIN set "OLLAMA_BIN=%%~fI"
    )
)

if not defined OLLAMA_BIN (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
        "%ProgramFiles%\Ollama\ollama.exe"
        "%ProgramFiles(x86)%\Ollama\ollama.exe"
        "D:\Program Files\Ollama\ollama.exe"
        "D:\OLLAMA\ollama.exe"
        "C:\Ollama\ollama.exe"
    ) do (
        if exist %%P (
            if not defined OLLAMA_BIN set "OLLAMA_BIN=%%~P"
        )
    )
)

if not defined OLLAMA_BIN (
    echo [ERROR] Ollama not found.
    echo [ERROR] Download from: https://ollama.com/download/windows
    echo [ERROR] Or set OLLAMA_BIN in .env
    pause
    exit /b 1
)

echo [INFO] Found Ollama: %OLLAMA_BIN%

REM ── Check if Ollama is already running ──────────────────────
curl -s --max-time 3 "%OLLAMA_URL%/api/tags" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Ollama already running at %OLLAMA_URL%
    goto :pull_model
)

REM ── Start Ollama server ─────────────────────────────────────
echo [INFO] Starting Ollama server...
start "Ollama Server" /MIN "%OLLAMA_BIN%" serve

echo [INFO] Waiting for Ollama to be ready...
set "RETRIES=0"
:wait_loop
timeout /t 2 /nobreak >nul
curl -s --max-time 3 "%OLLAMA_URL%/api/tags" >nul 2>&1
if not errorlevel 1 goto :ollama_ready
set /a RETRIES+=1
if %RETRIES% geq 15 (
    echo [ERROR] Ollama failed to start after 30 seconds.
    echo [ERROR] Check Ollama logs or run manually: ollama serve
    pause
    exit /b 1
)
echo [INFO] Still waiting... (%RETRIES%/15)
goto :wait_loop

:ollama_ready
echo [INFO] Ollama is ready!

REM ── Pull model if not present ────────────────────────────────
:pull_model
echo.
echo [INFO] Checking model: %OLLAMA_MODEL%

"%OLLAMA_BIN%" list 2>nul | findstr /I "%OLLAMA_MODEL%" >nul 2>&1
if not errorlevel 1 (
    if /I not "%FORCE_PULL%"=="--pull" (
        echo [INFO] Model "%OLLAMA_MODEL%" already available.
        goto :done
    )
)

echo [INFO] Pulling model: %OLLAMA_MODEL%
echo [INFO] This may take a few minutes depending on model size...
"%OLLAMA_BIN%" pull %OLLAMA_MODEL%

if errorlevel 1 (
    echo [WARN] Pull failed. Model may be partially available or name may differ.
    echo [WARN] Available models:
    "%OLLAMA_BIN%" list
) else (
    echo [INFO] Model "%OLLAMA_MODEL%" is ready.
)

:done
echo.
echo  ============================================
echo   Ollama is running
echo   API    : %OLLAMA_URL%
echo   Model  : %OLLAMA_MODEL%
echo   Test   : curl %OLLAMA_URL%/api/tags
echo  ============================================
echo.

REM ── Quick verify ─────────────────────────────────────────────
echo [INFO] Installed models:
"%OLLAMA_BIN%" list

echo.
echo [INFO] Ollama server is running in the background.
echo [INFO] Close the "Ollama Server" window to stop it.
echo.
endlocal
