@echo off
:: Docker Build & Run Script for Dev Team Testing

title AyazGitDy - Docker Build

echo.
echo ========================================
echo  AyazGitDy - Docker Build
echo ========================================
echo.

:: Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found!
    echo.
    echo Install Docker Desktop:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo [OK] Docker installed
echo.

:: Menu
echo Choose an option:
echo.
echo   1. Build Docker image
echo   2. Run with Docker Compose
echo   3. Build and Run
echo   4. Stop and remove containers
echo   5. View logs
echo   6. Exit
echo.

choice /C 123456 /N /M "Select option (1-6): "
set OPTION=%errorlevel%

echo.

if %OPTION%==1 goto BUILD
if %OPTION%==2 goto COMPOSE
if %OPTION%==3 goto BUILD_RUN
if %OPTION%==4 goto STOP
if %OPTION%==5 goto LOGS
if %OPTION%==6 goto END

:BUILD
echo Building Docker image...
docker build -t ayazdy-agent:latest .
echo.
echo [OK] Image built: ayazdy-agent:latest
pause
exit /b 0

:COMPOSE
echo Starting with Docker Compose...
if not exist .env (
    echo [WARN] .env not found, creating from example...
    copy .env.example .env
    echo [INFO] Please edit .env with your settings
    pause
)
docker-compose up -d
echo.
echo [OK] Container started!
echo.
echo Access the application:
echo   API: http://localhost:8000
echo   Health: http://localhost:8000/health
echo   Dashboard: http://localhost:8000/dashboard
echo.
echo To view logs: docker-compose logs -f
pause
exit /b 0

:BUILD_RUN
echo Building and starting...
if not exist .env (
    copy .env.example .env
    echo [INFO] Created .env - please configure before first use
)
docker-compose up --build -d
echo.
echo [OK] Application running!
echo   View at: http://localhost:8000
echo.
pause
exit /b 0

:STOP
echo Stopping containers...
docker-compose down
echo.
echo [OK] Containers stopped and removed
pause
exit /b 0

:LOGS
echo Showing logs (Ctrl+C to exit)...
docker-compose logs -f
exit /b 0

:END
exit /b 0
