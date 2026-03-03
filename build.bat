@echo off
:: AyazGitDy - Build Script for Distribution
:: Creates a distributable package for dev team testing

title AyazGitDy - Build Distribution Package

echo.
echo ========================================
echo  AyazGitDy - Build Distribution
echo ========================================
echo.

:: Set variables
set BUILD_DIR=dist
set PACKAGE_NAME=AyazGitDy-Portable
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo [1/6] Cleaning previous build...
if exist %BUILD_DIR% (
    rmdir /s /q %BUILD_DIR%
)
mkdir %BUILD_DIR%
mkdir %BUILD_DIR%\%PACKAGE_NAME%
echo     Done!

echo.
echo [2/6] Copying application files...
:: Copy Python files
xcopy /E /I /Y agents %BUILD_DIR%\%PACKAGE_NAME%\agents
xcopy /E /I /Y services %BUILD_DIR%\%PACKAGE_NAME%\services
xcopy /E /I /Y config %BUILD_DIR%\%PACKAGE_NAME%\config
xcopy /E /I /Y security %BUILD_DIR%\%PACKAGE_NAME%\security
xcopy /E /I /Y plugins %BUILD_DIR%\%PACKAGE_NAME%\plugins
xcopy /E /I /Y cli %BUILD_DIR%\%PACKAGE_NAME%\cli
xcopy /E /I /Y dashboard %BUILD_DIR%\%PACKAGE_NAME%\dashboard
xcopy /E /I /Y tools %BUILD_DIR%\%PACKAGE_NAME%\tools

:: Copy main files
copy /Y main.py %BUILD_DIR%\%PACKAGE_NAME%\
copy /Y project_utils.py %BUILD_DIR%\%PACKAGE_NAME%\
copy /Y requirements.txt %BUILD_DIR%\%PACKAGE_NAME%\

:: Copy batch wrappers
copy /Y *.bat %BUILD_DIR%\%PACKAGE_NAME%\

:: Copy documentation
copy /Y README.md %BUILD_DIR%\%PACKAGE_NAME%\
copy /Y CHANGELOG.md %BUILD_DIR%\%PACKAGE_NAME%\
copy /Y CONTRIBUTING.md %BUILD_DIR%\%PACKAGE_NAME%\
copy /Y QUICK_REFERENCE.md %BUILD_DIR%\%PACKAGE_NAME%\
copy /Y .env.example %BUILD_DIR%\%PACKAGE_NAME%\

echo     Done!

echo.
echo [3/6] Creating quick setup script...
(
echo @echo off
echo :: AyazGitDy - Quick Setup for Dev Team
echo title AyazGitDy - Quick Setup
echo.
echo echo ========================================
echo echo  AyazGitDy - Quick Setup
echo echo ========================================
echo echo.
echo.
echo :: Check Python
echo python --version 2^>nul
echo if %%errorlevel%% neq 0 ^(
echo     echo [ERROR] Python not found!
echo     echo Install Python 3.9+: https://www.python.org/downloads/
echo     pause
echo     exit /b 1
echo ^)
echo echo [OK] Python installed
echo.
echo :: Install dependencies
echo echo Installing dependencies...
echo python -m pip install --upgrade pip
echo pip install -r requirements.txt
echo.
echo :: Create .env from example
echo if not exist .env ^(
echo     echo Creating .env file...
echo     copy .env.example .env
echo     echo [INFO] Please edit .env with your settings
echo ^)
echo.
echo :: Create logs directory
echo if not exist logs mkdir logs
echo.
echo echo.
echo echo ========================================
echo echo  Setup Complete!
echo echo ========================================
echo echo.
echo echo Next steps:
echo echo   1. Edit .env with your configuration
echo echo   2. Run: start.bat
echo echo   3. Or run GUI: ayazgitdy_gui.bat
echo echo.
echo pause
) > %BUILD_DIR%\%PACKAGE_NAME%\SETUP.bat
echo     Done!

echo.
echo [4/6] Creating test script...
(
echo @echo off
echo :: AyazGitDy - Test Runner
echo title AyazGitDy - Running Tests
echo.
echo echo ========================================
echo echo  AyazGitDy - Test Suite
echo echo ========================================
echo echo.
echo.
echo :: Test 1: Verify Python
echo echo [1/5] Checking Python...
echo python --version
echo if %%errorlevel%% neq 0 exit /b 1
echo.
echo :: Test 2: Verify dependencies
echo echo [2/5] Checking dependencies...
echo python verify_all.py
echo if %%errorlevel%% neq 0 exit /b 1
echo.
echo :: Test 3: LLM providers
echo echo [3/5] Checking LLM providers...
echo python tools\check_llm.py
echo.
echo :: Test 4: Git service
echo echo [4/5] Testing Git service...
echo python -c "from tools.git_service import GitService; print('Git service OK')"
echo if %%errorlevel%% neq 0 exit /b 1
echo.
echo :: Test 5: Main imports
echo echo [5/5] Testing main imports...
echo python -c "import main; print('Main module OK')"
echo if %%errorlevel%% neq 0 exit /b 1
echo.
echo echo.
echo echo ========================================
echo echo  All Tests Passed!
echo echo ========================================
echo echo.
echo pause
) > %BUILD_DIR%\%PACKAGE_NAME%\TEST.bat
echo     Done!

echo.
echo [5/6] Creating README for dev team...
(
echo # AyazGitDy - Dev Team Quick Start
echo.
echo ## Quick Setup (3 Steps^)
echo.
echo ### 1. Run Setup
echo ```
echo SETUP.bat
echo ```
echo.
echo ### 2. Configure Environment
echo Edit `.env` file:
echo - Add your Telegram token
echo - Add API secret key
echo - Configure LLM provider (Ollama/OpenAI/etc.^)
echo.
echo ### 3. Start Application
echo ```
echo start.bat
echo ```
echo.
echo ## Testing
echo.
echo Run comprehensive tests:
echo ```
echo TEST.bat
echo ```
echo.
echo ## Usage Options
echo.
echo ### 1. Full Agent System
echo ```
echo start.bat
echo ```
echo Visit: http://localhost:8000
echo.
echo ### 2. Git Automation GUI
echo ```
echo ayazgitdy_gui.bat
echo ```
echo.
echo ### 3. Git Automation CLI
echo ```
echo ayazgitdy.bat
echo ```
echo.
echo ### 4. CLI Control
echo ```
echo ayazdy.bat health
echo ayazdy.bat gitcommit
echo ```
echo.
echo ## Troubleshooting
echo.
echo ### No LLM Provider?
echo Run diagnostic:
echo ```
echo check_llm.bat
echo ```
echo.
echo ### Need Tools?
echo - Open GUI: `ayazgitdy_gui.bat`
echo - Click [Setup Tools] button
echo - Terminal shows installation commands
echo.
echo ## Documentation
echo.
echo - `README.md` - Full documentation
echo - `QUICK_REFERENCE.md` - API/CLI cheat sheet
echo - `tools/LLM_PROVIDER_GUIDE.md` - LLM setup guide
echo - `tools/COPILOT_CLI_GIT_GUIDE.md` - GitHub Copilot guide
echo.
echo ## Support
echo.
echo Issues? Check:
echo - `CONTRIBUTING.md` - Development guide
echo - `CHANGELOG.md` - Version history
echo - System status in GUI (shows missing tools^)
) > %BUILD_DIR%\%PACKAGE_NAME%\DEV_QUICKSTART.md
echo     Done!

echo.
echo [6/6] Creating distribution archive...
cd %BUILD_DIR%
powershell -Command "Compress-Archive -Path '%PACKAGE_NAME%' -DestinationPath '%PACKAGE_NAME%-%TIMESTAMP%.zip' -Force"
cd ..
echo     Done!

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Package created: %BUILD_DIR%\%PACKAGE_NAME%-%TIMESTAMP%.zip
echo.
echo Distribution includes:
echo   - Application code
echo   - All dependencies list
echo   - BAT wrappers for easy execution
echo   - SETUP.bat for one-click setup
echo   - TEST.bat for validation
echo   - DEV_QUICKSTART.md guide
echo   - Full documentation
echo.
echo To share with dev team:
echo   1. Send the .zip file
echo   2. They extract and run SETUP.bat
echo   3. They configure .env
echo   4. They run TEST.bat to verify
echo   5. They run start.bat to use
echo.
pause
