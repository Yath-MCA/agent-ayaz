@echo off
:: AyazGitDy - EXE Build Script
:: Creates standalone executables using PyInstaller

title AyazGitDy - EXE Builder

echo.
echo ========================================
echo  AyazGitDy - EXE Builder
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

:: Check/Install PyInstaller
echo [1/7] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo     Installing PyInstaller...
    pip install pyinstaller
) else (
    echo     Already installed
)
echo.

:: Create build directories
echo [2/7] Creating build directories...
if exist build-exe rmdir /s /q build-exe
mkdir build-exe
mkdir build-exe\data
echo     Done!
echo.

:: Copy data files
echo [3/7] Copying data files...
xcopy /E /I /Y dashboard build-exe\data\dashboard
xcopy /E /I /Y plugins build-exe\data\plugins
copy /Y .env.example build-exe\data\
copy /Y README.md build-exe\data\
copy /Y QUICK_REFERENCE.md build-exe\data\
echo     Done!
echo.

:: Build Main Server EXE
echo [4/7] Building main server executable...
python -m PyInstaller --clean ^
    --onefile ^
    --name AyazDy-Server ^
    --icon=NONE ^
    --add-data "dashboard;dashboard" ^
    --add-data "plugins;plugins" ^
    --add-data ".env.example;." ^
    --hidden-import "uvicorn" ^
    --hidden-import "fastapi" ^
    --hidden-import "httpx" ^
    --hidden-import "pydantic" ^
    --hidden-import "telegram" ^
    --hidden-import "yaml" ^
    --collect-all uvicorn ^
    --collect-all fastapi ^
    main.py

if %errorlevel% neq 0 (
    echo [ERROR] Main server build failed!
    pause
    exit /b 1
)
echo     Done!
echo.

:: Build Git GUI EXE
echo [5/7] Building Git GUI executable...
python -m PyInstaller --clean ^
    --onefile ^
    --noconsole ^
    --name AyazGitDy-GUI ^
    --icon=NONE ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.scrolledtext" ^
    tools\ayazgitdy_gui.py

if %errorlevel% neq 0 (
    echo [ERROR] GUI build failed!
    pause
    exit /b 1
)
echo     Done!
echo.

:: Build Git CLI EXE
echo [6/7] Building Git CLI executable...
python -m PyInstaller --clean ^
    --onefile ^
    --name AyazGitDy-CLI ^
    --icon=NONE ^
    tools\ayazgitdy.py

if %errorlevel% neq 0 (
    echo [ERROR] CLI build failed!
    pause
    exit /b 1
)
echo     Done!
echo.

:: Package executables
echo [7/7] Creating distribution package...
if exist dist-exe rmdir /s /q dist-exe
mkdir dist-exe\AyazGitDy-EXE
mkdir dist-exe\AyazGitDy-EXE\data

:: Copy executables
copy dist\AyazDy-Server.exe dist-exe\AyazGitDy-EXE\
copy dist\AyazGitDy-GUI.exe dist-exe\AyazGitDy-EXE\
copy dist\AyazGitDy-CLI.exe dist-exe\AyazGitDy-EXE\

:: Copy data files
copy .env.example dist-exe\AyazGitDy-EXE\
copy README.md dist-exe\AyazGitDy-EXE\
copy QUICK_REFERENCE.md dist-exe\AyazGitDy-EXE\
xcopy /E /I /Y dashboard dist-exe\AyazGitDy-EXE\data\dashboard
xcopy /E /I /Y plugins dist-exe\AyazGitDy-EXE\data\plugins

:: Create launcher scripts
echo @echo off > dist-exe\AyazGitDy-EXE\Start-Server.bat
echo title AyazDy Server >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo Starting AyazDy Server... >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo. >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo Server will start on: http://localhost:8000 >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo Dashboard: http://localhost:8000/dashboard >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo. >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo Press Ctrl+C to stop the server >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo echo. >> dist-exe\AyazGitDy-EXE\Start-Server.bat
echo AyazDy-Server.exe >> dist-exe\AyazGitDy-EXE\Start-Server.bat

echo @echo off > dist-exe\AyazGitDy-EXE\Git-GUI.bat
echo start AyazGitDy-GUI.exe >> dist-exe\AyazGitDy-EXE\Git-GUI.bat

echo @echo off > dist-exe\AyazGitDy-EXE\Git-CLI.bat
echo AyazGitDy-CLI.exe %%* >> dist-exe\AyazGitDy-EXE\Git-CLI.bat

:: Create README
(
echo # AyazGitDy - Standalone Executables
echo.
echo ## No Python Required!
echo.
echo This package contains standalone executables that run without Python installation.
echo.
echo ## Quick Start
echo.
echo ### 1. Configure Environment
echo.
echo Edit `.env` file with your settings:
echo - Copy `.env.example` to `.env`
echo - Add your API keys and configuration
echo.
echo ### 2. Start Server
echo.
echo Double-click: `Start-Server.bat`
echo.
echo Or run manually: `AyazDy-Server.exe`
echo.
echo Access:
echo - API: http://localhost:8000
echo - Dashboard: http://localhost:8000/dashboard
echo - Health: http://localhost:8000/health
echo.
echo ### 3. Use Git Tools
echo.
echo **GUI Version:**
echo - Double-click: `Git-GUI.bat`
echo - Or run: `AyazGitDy-GUI.exe`
echo.
echo **CLI Version:**
echo - Run: `Git-CLI.bat`
echo - Or: `AyazGitDy-CLI.exe`
echo.
echo ## Files Included
echo.
echo - `AyazDy-Server.exe` - Main server ^(standalone^)
echo - `AyazGitDy-GUI.exe` - Git automation GUI ^(standalone^)
echo - `AyazGitDy-CLI.exe` - Git automation CLI ^(standalone^)
echo - `Start-Server.bat` - Quick launcher
echo - `Git-GUI.bat` - GUI launcher
echo - `Git-CLI.bat` - CLI launcher
echo - `.env.example` - Configuration template
echo - `README.md` - Full documentation
echo - `data/` - Dashboard and plugins
echo.
echo ## Configuration
echo.
echo Create `.env` file in same directory as executables:
echo.
echo ```
echo PROJECT_ROOT=D:/YOUR/PROJECTS
echo API_SECRET_KEY=your-secret-key
echo TELEGRAM_TOKEN=your-bot-token
echo OLLAMA_MODEL=phi3
echo OLLAMA_URL=http://localhost:11434
echo ```
echo.
echo ## Troubleshooting
echo.
echo ### Server won't start
echo - Check `.env` file exists
echo - Check port 8000 is available
echo - Run as administrator if needed
echo.
echo ### "Python not found" error
echo These are standalone executables - Python not needed!
echo If you see this error, download the EXE version, not source.
echo.
echo ### Antivirus blocks executable
echo This is common with PyInstaller-built executables.
echo Add exception in antivirus or build from source yourself.
echo.
echo ### LLM provider not found
echo - Install Ollama: https://ollama.com/download
echo - Or add OPENAI_API_KEY to .env
echo - Or add OPENROUTER_API_KEY to .env
echo.
echo ## File Sizes
echo.
echo - Server EXE: ~50-80 MB
echo - GUI EXE: ~30-50 MB
echo - CLI EXE: ~20-30 MB
echo.
echo Total package: ~100-160 MB
echo.
echo ## Support
echo.
echo Full documentation: README.md
echo API reference: QUICK_REFERENCE.md
echo.
echo ## Technical Details
echo.
echo Built with:
echo - PyInstaller
echo - Python 3.11
echo - FastAPI + Uvicorn
echo - Tkinter GUI
echo.
echo OS: Windows 10/11 x64
) > dist-exe\AyazGitDy-EXE\README-EXE.md

:: Create .zip archive
echo Creating .zip archive...
cd dist-exe
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
powershell -Command "Compress-Archive -Path 'AyazGitDy-EXE' -DestinationPath 'AyazGitDy-EXE-%TIMESTAMP%.zip' -Force"
cd ..

echo     Done!
echo.

:: Cleanup
echo Cleaning up build files...
rmdir /s /q build
rmdir /s /q build-exe
echo     Done!
echo.

echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Executables created in: dist-exe\AyazGitDy-EXE\
echo.
echo Files:
echo   - AyazDy-Server.exe      (Main server)
echo   - AyazGitDy-GUI.exe      (Git GUI)
echo   - AyazGitDy-CLI.exe      (Git CLI)
echo   - Start-Server.bat       (Quick launcher)
echo   - Git-GUI.bat            (GUI launcher)
echo   - Git-CLI.bat            (CLI launcher)
echo   - README-EXE.md          (Usage guide)
echo.
echo Distribution package: dist-exe\AyazGitDy-EXE-%TIMESTAMP%.zip
echo.
echo No Python installation needed to run these executables!
echo.
echo To test:
echo   1. cd dist-exe\AyazGitDy-EXE
echo   2. Create .env from .env.example
echo   3. Run Start-Server.bat
echo.
pause
