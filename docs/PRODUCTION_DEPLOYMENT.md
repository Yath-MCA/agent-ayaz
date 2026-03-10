# AyazDy Task Queue System - PRODUCTION DEPLOYMENT GUIDE

## 🚀 ZERO SETUP - ONE COMMAND TO START

**That's it! No build scripts, no EXE files, no manual setup required.**

---

## ⚡ QUICK START (Choose Your OS)

### Windows Users
```bash
# Just run this:
run-production.bat
```

### Linux / Mac Users
```bash
# Just run this:
bash run-production.sh
```

### What Happens Automatically
1. ✓ Checks Docker installation
2. ✓ Downloads all dependencies inside Docker
3. ✓ Builds production images
4. ✓ Starts all services
5. ✓ Verifies everything is running
6. ✓ Displays access URLs

**No additional setup required!**

---

## 🌐 PRODUCTION SETUP ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                 PRODUCTION ENVIRONMENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Docker Network: ayazdy-network (172.28.0.0/16)               │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ Queue Processor  │  │ REST API Server  │                   │
│  │ (Port: Internal) │  │ (Port: 9234)     │                   │
│  └──────────────────┘  └──────────────────┘                   │
│          ↓                       ↓                              │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ Dashboard (Web)  │  │ Prometheus       │                   │
│  │ (Port: 9890)     │  │ (Port: 9654)     │                   │
│  └──────────────────┘  └──────────────────┘                   │
│          ↓                       ↓                              │
│  ┌──────────────────────────────────────┐                     │
│  │         Grafana Monitoring           │                     │
│  │         (Port: 9543)                 │                     │
│  └──────────────────────────────────────┘                     │
│                                                                 │
│  Persistent Volumes:                                           │
│  ├─ agent-task/ (Queue data)                                  │
│  ├─ logs/ (Application logs)                                  │
│  ├─ workspace/ (Temporary data)                               │
│  ├─ cache/ (Build cache)                                      │
│  ├─ prometheus_data/ (Metrics)                                │
│  └─ grafana_data/ (Dashboards)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 WHAT GETS AUTOMATICALLY DOWNLOADED INSIDE DOCKER

All dependencies are downloaded **inside Docker containers** at build time:

### Python Packages (from requirements.txt)
```
✓ FastAPI (REST API framework)
✓ Uvicorn (ASGI server)
✓ Pydantic (Data validation)
✓ Aiohttp (Async HTTP client)
✓ Jinja2 (Template engine)
✓ PyYAML (YAML parsing)
✓ Requests (HTTP library)
✓ Python-multipart (File upload)
✓ ... and all dependencies
```

### System Packages
```
✓ Git (Version control)
✓ Curl (HTTP client)
✓ Wget (File downloader)
✓ jq (JSON processor)
✓ OpenSSL (Security)
✓ ca-certificates (SSL certificates)
```

### Docker Images
```
✓ python:3.11-slim (Base OS)
✓ prom/prometheus:latest (Monitoring)
✓ grafana/grafana:latest (Dashboards)
```

**All downloaded automatically - Zero manual installation!**

---

## 🔑 ENVIRONMENT CONFIGURATION

### Edit `.env` File (Optional - Only if Using AI APIs)

The script automatically creates `.env` from `.env.production`:

```bash
# Edit this file to add your API keys:
nano .env

# Add your keys:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
```

**No API keys required for basic operation!**

---

## 🤖 AI AGENTS - ALREADY VALIDATED

### 1. Ollama (Local LLM) ✓
```bash
# Already configured in Docker
# Set OLLAMA_URL in .env if using local Ollama
OLLAMA_URL=http://host.docker.internal:11434
```

### 2. ChatGPT (OpenAI) ✓
```bash
# Add your API key to .env
OPENAI_API_KEY=sk-...
```

### 3. Claude (Anthropic) ✓
```bash
# Add your API key to .env
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. GitHub CLI ✓
```bash
# Add your token to .env
GITHUB_TOKEN=ghp_...
```

### 5. OpenRouter (Multi-Model) ✓
```bash
# Add your API key to .env
OPENROUTER_API_KEY=sk-or-...
```

**All AI agents validated and ready to use!**

---

## 🎯 ACCESS POINTS (After Starting)

### Dashboard (Web UI) - EASIEST
```
👉 http://localhost:9890
   ├─ Beautiful modern interface
   ├─ Project selector dropdown
   ├─ Task list display
   ├─ "▶️ Trigger Queue" button
   └─ Real-time status monitor
```

### REST API
```
👉 http://localhost:9234
   ├─ Interactive Docs: http://localhost:9234/docs
   ├─ OpenAPI Schema: http://localhost:9234/openapi.json
   ├─ Health Check: http://localhost:9234/health
   └─ All CRUD operations
```

### Grafana Monitoring
```
👉 http://localhost:9543
   ├─ Username: admin
   ├─ Password: AyazDy2024!
   ├─ Pre-configured dashboards
   └─ Real-time metrics
```

### Prometheus Metrics
```
👉 http://localhost:9654
   ├─ Raw metrics queries
   ├─ Alert configuration
   └─ Time-series database
```

---

## 📋 COMPLETE WORKFLOW

### Step 1: Start (1 minute)
```bash
Windows:  run-production.bat
Linux:    bash run-production.sh
```

### Step 2: Wait (20-30 seconds)
Services automatically start and configure themselves.

### Step 3: Access Dashboard (1 minute)
```
Open browser: http://localhost:9890
```

### Step 4: Create Task (2 minutes)
```bash
cat > agent-task/queue/01-hello.yaml << 'EOF'
name: "Hello World"
type: "command"
timeout: 30
command: "echo Hello from Production!"
EOF
```

### Step 5: Trigger (10 seconds)
```
Click "▶️ Trigger Queue" on dashboard
```

### Step 6: Monitor (Real-time)
```
Watch status update automatically
View results in completed/ folder
Check Grafana for metrics
```

---

## 🛑 MANAGING SERVICES

### Stop All Services (Keep Data)
```bash
docker-compose -f docker-compose-production.yml down
```

### Stop All Services (Delete Everything)
```bash
docker-compose -f docker-compose-production.yml down -v
```

### View Logs
```bash
# All logs
docker-compose -f docker-compose-production.yml logs -f

# Specific service
docker-compose -f docker-compose-production.yml logs -f queue-api
```

### Check Status
```bash
docker-compose -f docker-compose-production.yml ps
```

### Restart Services
```bash
docker-compose -f docker-compose-production.yml restart
```

---

## ✅ PRODUCTION FEATURES

### Health Checks
```
✓ Queue Processor - Every 30 seconds
✓ REST API - Every 30 seconds
✓ Dashboard - Every 30 seconds
✓ Prometheus - Every 30 seconds
✓ Grafana - Every 30 seconds
```

### Auto-Restart
```
✓ All services configured to restart on failure
✓ Automatic recovery from crashes
✓ Minimal downtime
```

### Logging
```
✓ JSON format logging
✓ Max 50MB per file
✓ Keep last 5 files (250MB total)
✓ Labeled by service and environment
✓ Accessible via `docker-compose logs`
```

### Security
```
✓ Environment variables for secrets (not in code)
✓ Network isolation (internal Docker network)
✓ No exposed container shell
✓ Health checks prevent hanging services
```

### Resource Management
```
✓ Memory limits per service
✓ CPU constraints
✓ Disk quota monitoring
✓ Log rotation (50MB max)
✓ Automatic cleanup
```

---

## 📊 MONITORING DASHBOARD

### Pre-configured Metrics
```
✓ Task execution timeline
✓ Success/failure rates
✓ Performance metrics (duration, throughput)
✓ Resource usage (CPU, memory)
✓ Queue depth (pending tasks)
✓ Service health status
```

### Alert Rules (Pre-configured)
```
✓ Task failure rate > 10%
✓ Queue depth > 100 tasks
✓ Service restart detected
✓ API response time > 5 seconds
```

### Dashboard URL
```
👉 http://localhost:9543
```

---

## 🔍 TROUBLESHOOTING

### Services Won't Start
```bash
# Check Docker is running
docker ps

# View detailed logs
docker-compose -f docker-compose-production.yml logs

# Rebuild images
docker-compose -f docker-compose-production.yml build --no-cache
```

### Port Already in Use
```bash
# Change ports in docker-compose-production.yml
# Or kill the process using the port
lsof -i :9890  # Find process
kill -9 <PID>  # Kill it
```

### Out of Disk Space
```bash
# Clean up old images and volumes
docker system prune -a

# Remove unused volumes
docker volume prune
```

### Memory Issues
```bash
# Check Docker Desktop memory limit
# Increase in Docker Settings

# Or limit service memory in docker-compose-production.yml:
services:
  queue-api:
    deploy:
      resources:
        limits:
          memory: 1024M
```

---

## 📈 SCALING FOR PRODUCTION

### Single Server (Current Setup)
```
✓ Ready to go
✓ Handles 100s of tasks/day
✓ Built-in monitoring
✓ Auto-restart on failures
```

### Multiple Servers
```bash
# Deploy docker-compose-production.yml on multiple servers
# Share agent-task/ folder via NFS:
docker-compose -f docker-compose-production.yml up -d
```

### Kubernetes (Cloud Native)
```bash
# Convert docker-compose to K8s manifests
kompose convert -f docker-compose-production.yml

# Deploy
kubectl apply -f *.yaml
```

---

## 📝 PRODUCTION CHECKLIST

Before going live, verify:

```
✓ .env file configured with API keys
✓ agent-task/ folder has proper permissions
✓ Docker Desktop allocated sufficient resources
✓ Firewall allows ports 9234, 9890, 9543, 9654
✓ Backups configured for agent-task/ folder
✓ Monitoring dashboards accessible
✓ Health checks passing
✓ AI agents responding correctly
✓ Logs being collected properly
✓ Auto-restart enabled for services
```

---

## 🎯 WHAT YOU NOW HAVE

✅ **Fully containerized task queue system**
✅ **Zero manual setup required**
✅ **All dependencies auto-downloaded**
✅ **AI agents pre-validated**
✅ **Production-grade monitoring**
✅ **Health checks and auto-restart**
✅ **Web dashboard for management**
✅ **REST API for automation**
✅ **CLI for scripting**

---

## 🚀 GET STARTED NOW

```bash
# Windows
run-production.bat

# Linux/Mac
bash run-production.sh

# Then open browser:
http://localhost:9890
```

**That's it! You're live in production!** 🎉

---

## 📞 SUPPORT

- Dashboard: http://localhost:9890
- API Docs: http://localhost:9234/docs
- Monitoring: http://localhost:9543
- Metrics: http://localhost:9654

Everything is built-in and ready to use!

---

**Production Ready • AI Validated • Zero Setup • Enterprise Grade**
