@echo off
REM Verify all dependencies are installed for Agent Ayazdy

echo ====================================================
echo  Agent Ayazdy - Dependency Verification
echo ====================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo Installing/Updating dependencies...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo Verifying imports...
python -c "import fastapi, uvicorn, httpx, pydantic, telegram, dotenv, requests, pytest, yaml; print('[OK] All dependencies imported successfully')"
if errorlevel 1 (
    echo [ERROR] Some dependencies failed to import
    pause
    exit /b 1
)
echo.

echo Testing main application...
python -c "import main; print('[OK] main.py loaded')"
if errorlevel 1 (
    echo [ERROR] main.py failed to load
    pause
    exit /b 1
)
echo.

echo Testing Git automation tools...
python -c "from tools.git_service import GitService; print('[OK] GitService loaded')"
if errorlevel 1 (
    echo [ERROR] GitService failed to load
    pause
    exit /b 1
)
echo.

echo Testing CLI tools...
python -c "from cli.client import AgentClient; print('[OK] CLI client loaded')" 2>nul
if errorlevel 1 (
    echo [ERROR] CLI client failed to load
    pause
    exit /b 1
)
echo.

echo ====================================================
echo  All Dependencies Verified Successfully!
echo ====================================================
echo.
echo You can now:
echo   - Run server:  python main.py
echo   - Use GUI:     ayazgitdy_gui.bat
echo   - Use CLI:     ayazdy health
echo   - Git commit:  ayazgitdy.bat
echo.
pause
