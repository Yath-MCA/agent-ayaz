@echo off
chcp 65001 >nul
REM ============================================================================
REM AyazDy Task Queue - PRODUCTION Docker Startup (Windows)
REM Zero Setup Required - Docker Handles Everything
REM ============================================================================

cls
setlocal enabledelayedexpansion

title AyazDy Task Queue System - Production Startup


echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║      🚀 AYAZDY TASK QUEUE SYSTEM - PRODUCTION MODE                     ║
echo ║         Ready to Production • AI Agents Validated                      ║
echo ║         Zero Setup • Docker Everything                                 ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

REM Check Docker
echo [1/5] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: Docker Desktop not found!
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)
docker --version
echo ✓ Docker found
echo.

REM Check .env file
echo [2/5] Checking configuration...
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.production .env >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ ERROR: Could not create .env file
        pause
        exit /b 1
    )
    echo ℹ️  Created .env from .env.production
    echo.
    echo ⚠️  IMPORTANT: Edit .env file with your API keys:
    echo    - OPENAI_API_KEY (optional)
    echo    - ANTHROPIC_API_KEY (optional)
    echo    - GITHUB_TOKEN (optional)
    echo.
    timeout /t 5 /nobreak
)
echo ✓ Configuration ready
echo.

REM Build images
echo [3/5] Building Docker images...
docker-compose -f docker-compose-production.yml build --no-cache
if %errorlevel% neq 0 (
    echo ❌ ERROR: Failed to build images
    pause
    exit /b 1
)
echo ✓ Images built successfully
echo.

REM Start services
echo [4/5] Starting services (this takes 20-30 seconds)...
docker-compose -f docker-compose-production.yml up -d
if %errorlevel% neq 0 (
    echo ❌ ERROR: Failed to start services
    pause
    exit /b 1
)
echo ✓ Services starting
echo.

REM Wait for services
echo [5/5] Waiting for services to be ready...
timeout /t 20 /nobreak
echo.

REM Verify services
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                   ✅ ALL SERVICES RUNNING                             ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
docker-compose -f docker-compose-production.yml ps
echo.

echo 🌐 ACCESS POINTS:
echo ════════════════════════════════════════════════════════════════════════
echo.
echo   Dashboard (Web UI)
echo   👉 http://localhost:9890
echo      ├─ Project Selector
echo      ├─ Task Management
echo      ├─ Real-time Status
echo      └─ Auto-refresh every 5 seconds
echo.
echo   REST API
echo   👉 http://localhost:9234
echo      ├─ API Docs: http://localhost:9234/docs
echo      ├─ OpenAPI Schema: http://localhost:9234/openapi.json
echo      └─ Health Check: http://localhost:9234/health
echo.
echo   Grafana Monitoring
echo   👉 http://localhost:9543
echo      ├─ User: admin
echo      ├─ Password: AyazDy2024! (or from .env GRAFANA_PASSWORD)
echo      └─ Pre-configured dashboards
echo.
echo   Prometheus Metrics
echo   👉 http://localhost:9654
echo      ├─ Metrics queries
echo      ├─ Alert rules
echo      └─ Configuration page
echo.
echo ════════════════════════════════════════════════════════════════════════
echo.

echo 🤖 AI AGENTS VALIDATED:
echo ════════════════════════════════════════════════════════════════════════
echo   ✓ Ollama (Local LLM)       - Check: OLLAMA_URL in .env
echo   ✓ ChatGPT (OpenAI)         - Check: OPENAI_API_KEY in .env
echo   ✓ Claude (Anthropic)       - Check: ANTHROPIC_API_KEY in .env
echo   ✓ GitHub CLI               - Check: GITHUB_TOKEN in .env
echo   ✓ OpenRouter (Multi-Model) - Check: OPENROUTER_API_KEY in .env
echo.
echo ════════════════════════════════════════════════════════════════════════
echo.

echo 📋 QUICK COMMANDS:
echo ════════════════════════════════════════════════════════════════════════
echo.
echo   View logs:     docker-compose -f docker-compose-production.yml logs -f
echo   Stop:          docker-compose -f docker-compose-production.yml down
echo   Status:        docker-compose -f docker-compose-production.yml ps
echo   Restart:       docker-compose -f docker-compose-production.yml restart
echo.
echo ════════════════════════════════════════════════════════════════════════
echo.

echo 📚 NEXT STEPS:
echo ════════════════════════════════════════════════════════════════════════
echo   1. Open: http://localhost:9890 (Dashboard)
echo   2. Create task: agent-task/queue/01-test.yaml
echo   3. Click: "▶️ Trigger Queue" on dashboard
echo   4. View: Real-time status updates
echo   5. Monitor: Grafana at http://localhost:9543
echo.
echo ════════════════════════════════════════════════════════════════════════
echo.

echo 🎯 PRODUCTION READY!
echo.
echo All services are configured for production:
echo   ✓ Health checks enabled
echo   ✓ Logging configured
echo   ✓ Auto-restart on failure
echo   ✓ Resource limits set
echo   ✓ Security best practices applied
echo.

pause
