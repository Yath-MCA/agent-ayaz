# AyazGitDy - Deployment Guide for Dev Team

## Quick Start Options

### Option 1: Standard Installation (Recommended)

**For Windows local development:**

```bash
# 1. Extract the distribution package
unzip AyazGitDy-Portable-*.zip
cd AyazGitDy-Portable

# 2. Run setup (installs dependencies)
SETUP.bat

# 3. Configure environment
notepad .env

# 4. Test installation
TEST.bat

# 5. Start application
start.bat
```

**Access:**
- API: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard
- Health: http://localhost:8000/health

---

### Option 2: Docker (Isolated Testing)

**For containerized testing:**

```bash
# 1. Build and run
docker-build.bat

# 2. Select option 3 (Build and Run)

# 3. Access application
# API: http://localhost:8000
```

**Advantages:**
- No Python installation needed
- Isolated environment
- Easy cleanup
- Consistent across team

---

### Option 3: Development Mode

**For active development:**

```bash
# 1. Clone repository
git clone <repo-url>
cd agent-ayaz

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment
copy .env.example .env

# 4. Run directly
python main.py
```

---

## Distribution Package Contents

### Files Included

```
AyazGitDy-Portable/
├── SETUP.bat              # One-click setup
├── TEST.bat               # Validation tests
├── start.bat              # Start main server
├── ayazdy.bat            # CLI wrapper
├── ayazgitdy.bat         # Git CLI tool
├── ayazgitdy_gui.bat     # Git GUI tool
├── check_llm.bat         # LLM diagnostic
├── docker-build.bat      # Docker helper
├── main.py               # Main application
├── requirements.txt      # Python dependencies
├── .env.example          # Config template
├── DEV_QUICKSTART.md     # This guide
├── README.md             # Full documentation
├── CHANGELOG.md          # Version history
├── QUICK_REFERENCE.md    # API/CLI cheat sheet
├── agents/               # Agent modules
├── services/             # Service modules
├── tools/                # Utility tools
├── dashboard/            # React dashboard
└── ...
```

---

## Setup Steps (Detailed)

### 1. Prerequisites

**Required:**
- Windows 10/11
- Python 3.9 or higher

**Optional (for full features):**
- Git (for version control)
- GitHub CLI (for Copilot integration)
- Ollama (for local LLM)
- Docker Desktop (for containerized testing)

### 2. Run SETUP.bat

This script will:
- ✅ Check Python installation
- ✅ Install Python dependencies
- ✅ Create .env file from template
- ✅ Create logs directory
- ✅ Verify installation

### 3. Configure .env

Edit `.env` with your settings:

```env
# Required
PROJECT_ROOT=D:/YOUR/PROJECTS/PATH
API_SECRET_KEY=your-secret-key-here

# Optional: Telegram
TELEGRAM_TOKEN=your-bot-token
ALLOWED_TELEGRAM_USER_ID=your-user-id

# Optional: LLM Providers
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434

# Or use OpenAI
# OPENAI_API_KEY=sk-your-key

# Or use OpenRouter (free tier available)
# OPENROUTER_API_KEY=sk-or-v1-your-key
```

### 4. Run TEST.bat

Validates:
- ✅ Python version
- ✅ Dependencies installed
- ✅ LLM providers available
- ✅ Module imports working
- ✅ Git service functional

### 5. Start Application

```bash
start.bat
```

Visit: http://localhost:8000

---

## Testing Checklist

### Basic Tests

- [ ] API responds at http://localhost:8000
- [ ] Health endpoint returns OK: `/health`
- [ ] Dashboard loads: `/dashboard`
- [ ] LLM providers detected: `/llm-providers`

### Feature Tests

- [ ] Git GUI opens: `ayazgitdy_gui.bat`
  - Check system status indicators (top bar)
  - Test repository selection
  - Verify commit message generation
  
- [ ] CLI works: `ayazdy.bat health`
  - Test various commands
  - Check API connectivity
  
- [ ] Chat endpoint: POST to `/chat`
  - Verify LLM responses
  - Test error handling

### Advanced Tests

- [ ] Agent pipeline: POST to `/run-task`
- [ ] Task queue: GET `/queue/status`
- [ ] Memory system: GET `/monitor/history`
- [ ] Approval workflow: GET `/monitor/approvals`

---

## Docker Deployment

### Build Image

```bash
docker-build.bat
# Select option 1: Build Docker image
```

### Run with Docker Compose

```bash
docker-build.bat
# Select option 2: Run with Docker Compose
```

### Manual Docker Commands

```bash
# Build
docker build -t ayazdy-agent:latest .

# Run
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name ayazdy \
  ayazdy-agent:latest

# Logs
docker logs -f ayazdy

# Stop
docker stop ayazdy
docker rm ayazdy
```

---

## Troubleshooting

### Python Not Found

**Error:** `Python not found`

**Fix:**
```bash
# Install Python
winget install Python.Python.3.11

# Or download from: https://www.python.org/downloads/
```

### Dependencies Failed

**Error:** `pip install failed`

**Fix:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install again
pip install -r requirements.txt
```

### No LLM Provider

**Error:** `All providers unavailable`

**Fix:**
```bash
# Run diagnostic
check_llm.bat

# Option A: Install Ollama (free, local)
# Download: https://ollama.com/download
ollama pull phi3

# Option B: Use OpenAI (paid)
# Add to .env: OPENAI_API_KEY=sk-...

# Option C: Use OpenRouter (free tier)
# Add to .env: OPENROUTER_API_KEY=sk-or-v1-...
```

### Port Already in Use

**Error:** `Port 8000 already in use`

**Fix:**
```env
# Edit .env
PORT=8001
```

### Docker Issues

**Error:** `Docker not found`

**Fix:**
```bash
# Install Docker Desktop
# Download: https://www.docker.com/products/docker-desktop/
```

---

## Development Workflow

### 1. Daily Setup

```bash
# Pull latest changes
git pull

# Update dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Start server
start.bat
```

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
# ... code ...

# Test
TEST.bat

# Commit (use the GUI!)
ayazgitdy_gui.bat

# Push
git push origin feature/your-feature
```

### 3. Code Review

```bash
# Build distribution for review
build.bat

# Share dist/*.zip with team

# Run tests on their machine
TEST.bat
```

---

## Performance Tips

### Faster Startup

```env
# Use local LLM (Ollama) instead of cloud
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434
```

### Reduce Memory Usage

```env
# Limit log retention
MAX_LOG_SIZE=1000
```

### Better Response Time

```env
# Use faster model
OLLAMA_MODEL=phi3  # Faster than llama3.2
# Or
OPENAI_MODEL=gpt-4o-mini  # Faster than gpt-4
```

---

## Team Collaboration

### Sharing Configurations

Create team `.env.template`:

```env
# Team defaults
PROJECT_ROOT=D:/Projects
OLLAMA_MODEL=phi3
AGENT_MODE=CONTROLLED
AUTONOMOUS_RISK_THRESHOLD=3
```

### Shared Task Queue

Use network share for task queue:

```env
# In .env
TASK_QUEUE_ROOT=\\server\share\agent-task
```

### Centralized Logs

```env
# Shared log directory
LOG_DIR=\\server\logs\agent-ayaz
```

---

## Security Notes

### API Keys

**Never commit `.env` to git!**

Already in `.gitignore`:
```
.env
*.key
```

### Secrets Management

For production:
- Use environment variables
- Use Azure Key Vault
- Use AWS Secrets Manager
- Use HashiCorp Vault

### RBAC

Configure role-based access:

```env
# In .env
RBAC_ROLES=admin-key:admin,dev-key:operator,view-key:viewer
```

---

## Support

### Documentation

- `README.md` - Complete feature docs
- `QUICK_REFERENCE.md` - API/CLI reference
- `tools/LLM_PROVIDER_GUIDE.md` - LLM setup
- `tools/COPILOT_CLI_GIT_GUIDE.md` - Copilot guide
- `tools/GUI_STATUS_BAR.md` - GUI features

### Getting Help

1. Check `TROUBLESHOOTING.md`
2. Run `TEST.bat` to diagnose
3. Check logs in `logs/` directory
4. Contact dev team lead

---

## Summary

✅ **Quick Start:**
1. Extract package
2. Run `SETUP.bat`
3. Edit `.env`
4. Run `TEST.bat`
5. Run `start.bat`

✅ **Docker Start:**
1. Run `docker-build.bat`
2. Select option 3 (Build and Run)
3. Visit http://localhost:8000

✅ **Dev Start:**
1. Clone repo
2. `pip install -r requirements.txt`
3. `copy .env.example .env`
4. `python main.py`

**Need Help?** Run `TEST.bat` and check the output!
