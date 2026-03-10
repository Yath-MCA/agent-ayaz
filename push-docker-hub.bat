@echo off
REM ============================================================================
REM AyazDy - Docker Hub Push Script
REM Builds and pushes images to Docker Hub
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set DOCKER_REGISTRY=yasardevops
set IMAGE_TAG=latest
set COMPOSE_FILE=docker-compose-production.yml

echo.
echo ============================================================================
echo 🐳 AyazDy - Docker Hub Push
echo ============================================================================
echo.
echo Registry: !DOCKER_REGISTRY!
echo Tag: !IMAGE_TAG!
echo.

REM Step 1: Check Docker
echo [1/5] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    echo Download: https://www.docker.com/products/docker-desktop
    exit /b 1
)
echo ✓ Docker found

REM Step 2: Check login
echo.
echo [2/5] Checking Docker Hub login...
docker login -u !DOCKER_REGISTRY! --password-stdin < nul >nul 2>&1 || (
    echo Logging in to Docker Hub...
    docker login -u !DOCKER_REGISTRY!
)
echo ✓ Docker Hub authenticated

REM Step 3: Build images
echo.
echo [3/5] Building Docker images...
echo Setting environment variables...
set DOCKER_REGISTRY=!DOCKER_REGISTRY!
set IMAGE_TAG=!IMAGE_TAG!

docker-compose -f !COMPOSE_FILE! build ^
    --build-arg DOCKER_REGISTRY=!DOCKER_REGISTRY! ^
    --build-arg IMAGE_TAG=!IMAGE_TAG!

if errorlevel 1 (
    echo ❌ Build failed
    exit /b 1
)
echo ✓ Images built successfully

REM Step 4: Tag images
echo.
echo [4/5] Tagging images...

for %%i in (queue-api dashboard queue-processor) do (
    echo   Tagging ayazdy-%%i...
    docker tag ayazdy-%%i:latest !DOCKER_REGISTRY!/ayazdy-%%i:!IMAGE_TAG!
    if errorlevel 1 (
        echo ❌ Failed to tag ayazdy-%%i
        exit /b 1
    )
)
echo ✓ All images tagged

REM Step 5: Push images
echo.
echo [5/5] Pushing images to Docker Hub...
echo.

set FAILED=0

for %%i in (queue-api dashboard queue-processor) do (
    echo Pushing !DOCKER_REGISTRY!/ayazdy-%%i:!IMAGE_TAG!...
    docker push !DOCKER_REGISTRY!/ayazdy-%%i:!IMAGE_TAG!
    if errorlevel 1 (
        echo ❌ Failed to push ayazdy-%%i
        set FAILED=1
    ) else (
        echo ✓ Pushed ayazdy-%%i
    )
)

echo.
echo ============================================================================

if !FAILED! equ 0 (
    echo ✅ All images pushed successfully!
    echo.
    echo Access on Docker Hub:
    echo   https://hub.docker.com/r/!DOCKER_REGISTRY!/ayazdy-queue-api
    echo   https://hub.docker.com/r/!DOCKER_REGISTRY!/ayazdy-dashboard
    echo   https://hub.docker.com/r/!DOCKER_REGISTRY!/ayazdy-queue-processor
    echo.
) else (
    echo ❌ Some images failed to push. Check errors above.
    exit /b 1
)

echo ============================================================================
echo.
pause
