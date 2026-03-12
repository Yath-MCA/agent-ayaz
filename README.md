# 🤖 AyazDy - AI DevOps Agent + Task Queue System

**Production-Ready • Zero Setup • Docker Everything • AI Agents Validated**

> FastAPI + Task Queue System + Telegram + Multi-Provider LLM integration for secure DevOps automation.

---

## 🚀 QUICK START - ONE COMMAND TO PRODUCTION

### Choose Your OS:

**Windows:**
```bash
run-production.bat
```

**Linux / Mac:**
```bash
bash run-production.sh
```

✅ **That's it!** Starts everything automatically:
- All dependencies downloaded inside Docker
- Services configured and running
- Web dashboard ready at `http://localhost:9890`
- REST API at `http://localhost:9234`
- Monitoring at `http://localhost:9543`

---

## 📌 What You Get

✅ **AgentAyazDaddy CLI Layer**
- `agent` CLI with Rich terminal UI (colorized output, panels, tables)
- Workflow verification before execution (project, script, Python, API checks)
- APScheduler cron-like scheduling (`config/schedule.json`)
- Structured logs — `logs/agent.log`, `tasks.log`, `errors.log`
- Central project config (`config/projects.json`)
- Task module definitions (`tasks/*.task.json`)
- Direct Ollama queries (`agent ask "..."`)
- Dashboard status posting (`agent dashboard <task> <status>`)

✅ **Task Queue System**
- File-based queue management (queue/ → completed/)
- Multi-project support with project selector
- Task lifecycle management and monitoring
- REST API + CLI + Web Dashboard

✅ **Multi-Provider LLM Integration**
- Local Ollama
- GitHub Copilot CLI
- OpenAI API (optional)
- OpenRouter (optional)
- Auto-failover if primary provider unavailable

✅ **Production Grade**
- Docker containerization (all dependencies included)
- Health checks and auto-restart
- Grafana monitoring dashboard
- Prometheus metrics collection
- JSON logging with rotation
- Enterprise configuration

✅ **Zero Setup**
- All dependencies download inside Docker at build time
- No manual installation required
- Ready to run immediately after `run-production.bat`

---

## 🎯 Two Deployment Options

### Option 1: PRODUCTION (Recommended)
```bash
# Windows
run-production.bat

# Linux/Mac
bash run-production.sh
```
**Features:** Zero setup, all dependencies included, production monitoring, auto-scaling ready

### Option 2: DEVELOPMENT (Manual Setup)
See [Development Setup](#-setup-windows) section below for running locally with Ollama

Production services use 9xxx ports by default (e.g., API `9234`, Dashboard `9890`, Grafana `9543`, Prometheus `9654`).

---

## 🤖 AgentAyazDaddy — Workflow Refactor & CLI Task Runner

A dedicated CLI layer built on top of the ecosystem, providing structured task execution, workflow verification, cron scheduling, and Rich terminal UI.

### Quick start

```bash
# New agent CLI (Rich UI, typer-based)
agent status
agent run <task> --project my-project
agent run <task> --verify              # with pre-flight checks
agent queue
agent queue --run
agent projects --local
agent schedule
agent logs tasks
agent analyze "summarize last failure"
agent ask "how do I optimize a Python loop?"
agent verify <task> --project impact
agent dashboard compare-html running
```

### Key files

| Path | Purpose |
|------|---------|
| `agent.bat` | Windows entry point |
| `cli/agent_cli.py` | Typer+Rich CLI (10 commands) |
| `cli/terminal_ui.py` | Rich panels, tables, banners |
| `agents/workflow_verifier.py` | Pre-run checks (project, script, Python, API) |
| `services/scheduler_service.py` | APScheduler integration |
| `services/structured_logger.py` | `logs/agent.log`, `tasks.log`, `errors.log` |
| `config/projects.json` | Central project config |
| `config/schedule.json` | Cron-like schedule config |
| `tasks/*.task.json` | Structured task module definitions |

### New API endpoint

```
POST /api/agent/task-status   — receive task status updates from agents
GET  /api/agent/task-status   — retrieve recent status history
```

---

## 🖥 Desktop CLI (Inspired by Copilot-Ralph)

Launch the local desktop assistant window from CLI:

```bash
ayazdy desktop
```

This opens the built-in desktop Git assistant (archived to `temp/standalone-tools/ayazgitdy_gui.py`) and keeps API/queue logic in the same project.

---

## 📊 Access Points (After Starting)

| Component | URL | Purpose |
|-----------|-----|---------|
| **Web Dashboard** | http://localhost:9890 | Project selector, task management, real-time status |
| **REST API** | http://localhost:9234 | Programmatic task queue management |
| **API Docs** | http://localhost:9234/docs | Interactive Swagger documentation |
| **Agent Task Status** | http://localhost:9234/api/agent/task-status | AgentAyazDaddy status feed |
| **Grafana** | http://localhost:9543 | Monitoring dashboards (user: admin, pwd: AyazDy2024!) |
| **Prometheus** | http://localhost:9654 | Raw metrics and queries |

---

## 📚 COMPLETE DOCUMENTATION

### Production Deployment
- **[PRODUCTION_DEPLOYMENT.md](./docs/PRODUCTION_DEPLOYMENT.md)** - Complete guide with Zero Setup workflow, architecture, monitoring

### Task Queue System
- **[TASK_QUEUE_SYSTEM.md](./docs/TASK_QUEUE_SYSTEM.md)** - Complete architecture and usage guide
- **[TASK_QUEUE_QUICKSTART.md](./docs/TASK_QUEUE_QUICKSTART.md)** - 5-minute quick start
- **[TASK_QUEUE_EXAMPLES.md](./docs/TASK_QUEUE_EXAMPLES.md)** - Real-world working examples
- **[TASK_QUEUE_SUGGESTIONS.md](./docs/TASK_QUEUE_SUGGESTIONS.md)** - Advanced strategies

### Docker Deployment
- **[DOCKER_SETUP.md](./DOCKER_SETUP.md)** - Docker configuration and custom ports

### Getting Started
- **[GETTING_STARTED.md](./GETTING_STARTED.md)** - First-time setup guide
- **[how_to_run.md](./how_to_run.md)** - Command cheat sheet for Bot, Dashboard, and CLI

---

## 🧠 Architecture

```text
agent-ayaz/
├── main.py                          # FastAPI app + agent pipeline composition
├── agent.bat                        # AgentAyazDaddy CLI entry point (new)
├── config/
│   ├── settings.py                  # Environment/config loading
│   ├── projects.json                # Central project config (new)
│   └── schedule.json                # Cron-like schedule config (new)
├── tasks/                           # Task module definitions (new)
│   ├── build.task.json
│   ├── deploy.task.json
│   └── htmlCompare.task.json
├── security/
│   └── command_filter.py            # Command policy/validation
├── agents/                          # Multi-agent system
│   ├── planner.py                   # LLM → ExecutionPlan JSON
│   ├── validator.py                 # Policy gate
│   ├── executor.py                  # Validated execution
│   ├── risk.py                      # Risk scoring (1-10)
│   ├── approval.py                  # Token-based approval
│   ├── auditor.py                   # Immutable JSONL audit
│   ├── workflow_verifier.py         # Pre-run checks (new)
│   └── nodes.py                     # Distributed registry
├── services/
│   ├── llm_provider.py              # Multi-provider LLM + auto-fallback
│   ├── ollama_service.py            # Ollama HTTP integration
│   ├── telegram_service.py          # Telegram bot (15+ commands)
│   ├── execution_service.py         # Command execution wrapper
│   ├── memory_service.py            # SQLite execution history
│   ├── task_queue_service.py        # File-based task queue lifecycle
│   ├── scheduler_service.py         # APScheduler cron integration (new)
│   └── structured_logger.py         # agent/tasks/errors log (new)
├── cli/
│   ├── agent_cli.py                 # AgentAyazDaddy CLI — typer+rich (new)
│   ├── terminal_ui.py               # Rich UI components (new)
│   ├── cli.py                       # Legacy ayazdy argparse CLI
│   ├── commands.py                  # Command handlers
│   └── client.py                    # HTTP client
├── plugins/
│   ├── __init__.py                  # PluginManager (4 lifecycle hooks)
│   └── logger_plugin.py             # Example plugin
├── logs/                            # Log output
│   ├── agent.log                    # Agent lifecycle (new)
│   ├── tasks.log                    # Task events (new)
│   ├── errors.log                   # Error events (new)
│   ├── audit.log                    # Immutable JSONL audit
│   └── memory.db                    # SQLite execution history
├── agent-task/
│   ├── queue/                       # Tasks to run (sorted alpha)
│   ├── completed/                   # Finished tasks
│   └── later/                       # Deferred tasks
├── project_utils.py                 # Project discovery
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup (Windows)

### 1) Install Ollama

Download: <https://ollama.com/download/windows>

```bash
ollama pull phi3
ollama list
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

Copy `.env.example` to `.env` and set values:

```env
PROJECT_ROOT=D:/PERSONAL/LIVE_PROJECTS
# Optional: multiple allowed roots (Windows separator: ';')
PROJECT_ROOTS=C:/_IMPACT/tomcat/webapps/impact_vite;C:/_IMPACT/tomcat/webapps/impact_web;C:/_IMPACT/tomcat/webapps/impactweb
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434
OLLAMA_BIN=D:/Program Files/Ollama/ollama.exe
TELEGRAM_TOKEN=your_bot_token
API_SECRET_KEY=your_super_secret_key
ALLOWED_TELEGRAM_USER_ID=your_telegram_user_id
HOST=0.0.0.0
PORT=9234
CORS_ORIGINS=http://localhost,http://127.0.0.1
```

If Ollama is installed in a custom folder, set `OLLAMA_BIN` to the full executable path.
Example on Windows: `D:/Program Files/Ollama/ollama.exe`

> Use `.env` only for runtime configuration. Do not commit secrets.

### 4) Run

```bash
python main.py
```

### 5) Run Bot, Dashboard, and CLI

Server/API (required first):

```bash
python main.py
```

Dashboard (open in browser):

```text
http://localhost:9234/dashboard
```

GUI control center (one-click buttons for start/build/run):

```bash
open-control-center.bat
```

This opens a desktop window with click buttons for `start.bat`, `build.bat`, `build-exe.bat`, `run-production.bat`, and common CLI checks.

CLI examples:

```bash
# Health (public endpoint, no API key needed)
python -m cli.cli health

# Protected commands (API key required)
python -m cli.cli --key your_super_secret_key projects
python -m cli.cli --key your_super_secret_key qstatus
python -m cli.cli --key your_super_secret_key qrun
python -m cli.cli --key your_super_secret_key qrun-text --limit 20
python -m cli.cli --key your_super_secret_key select my-project
python -m cli.cli --key your_super_secret_key analyze "summarize current setup" --project my-project
python -m cli.cli --key your_super_secret_key exec "python --version" --project my-project
python -m cli.cli --key your_super_secret_key run build.ps1 --project my-project
```

Optional runtime behavior:

```env
AUTO_OPEN_VSCODE=false
```

When `AUTO_OPEN_VSCODE=false`, selecting a project will not auto-open VS Code and stays CLI-first.

Telegram bot:

```env
TELEGRAM_TOKEN=<your_bot_token>
ALLOWED_TELEGRAM_USER_ID=<your_numeric_telegram_user_id>
```

After setting `.env`, restart `python main.py` and then use Telegram commands:

```text
/help
/projects
/project <name>
/tasks
/task <file_name>
/qstatus
/qrun
```

---

## 🔐 API Endpoints

- `GET /` - basic service status
- `GET /status` - runtime status (model, host/port, Telegram configured/started)
- `GET /health` - dependency health (`ollama_running`, service state)
- `POST /chat` - public chat (no command execution)
- `WS /ws/chat` - real-time token streaming chat (`[DONE]` marks completion)
- `POST /run-task` - protected by `X-Api-Key`, optional command execution
- `POST /run-project` - protected by `X-Api-Key`, command execution in selected project
- `GET /projects` - protected, list projects under configured `PROJECT_ROOT`/`PROJECT_ROOTS`
- `POST /project/select` - protected, choose project by name (or absolute path under configured roots), open in VS Code, and return `run-task/` availability
- `GET /project/current` - protected, get current selected project for the current API key
- `GET /project/tasks?project=<name>` - protected, list files in project `run-task/`
- `POST /project/run-task` - protected, execute one file from project `run-task/` (`dry_run`, `auto_approve`, `delay_seconds` supported)
- `POST /project/run-custom` - protected, execute custom command in selected project path (`dry_run`, `auto_approve`, `delay_seconds` supported)

## 🤖 Telegram Commands

- `/projects` - list project folders under configured `PROJECT_ROOT`/`PROJECT_ROOTS`
- `/project <name|absolute_path>` - select project, open it in VS Code, and show files inside `run-task/` if available
- `/current` - show currently selected project
- `/tasks` - list available files in selected project's `run-task/`
- `/task <file_name>` - run one task file from `run-task/`
- `/custom <command>` - run a custom command in selected project when no task files exist (or by choice)
- `/status`, `/help`, `/id` - runtime status, command help, and Telegram user ID

## 🔧 REST Examples (Windows)

Set your API key once in terminal:

```bat
set API_KEY=your_super_secret_key
```

List projects:

```bat
curl -X GET "http://localhost:9234/projects" -H "X-Api-Key: %API_KEY%"
```

Select a project (opens VS Code and returns run-task availability):

```bat
curl -X POST "http://localhost:9234/project/select" ^
  -H "Content-Type: application/json" ^
  -H "X-Api-Key: %API_KEY%" ^
  -d "{\"project\":\"my-project\"}"
```

List run-task files for a selected project:

```bat
curl -X GET "http://localhost:9234/project/tasks?project=my-project" -H "X-Api-Key: %API_KEY%"
```

Get current selected project for this API key:

```bat
curl -X GET "http://localhost:9234/project/current" -H "X-Api-Key: %API_KEY%"
```

Run a task file from `run-task/`:

```bat
curl -X POST "http://localhost:9234/project/run-task" ^
  -H "Content-Type: application/json" ^
  -H "X-Api-Key: %API_KEY%" ^
  -d "{\"project\":\"my-project\",\"task\":\"build.ps1\",\"dry_run\":false,\"auto_approve\":true,\"delay_seconds\":0}"
```

Run a custom command when no run-task files are available:

```bat
curl -X POST "http://localhost:9234/project/run-custom" ^
  -H "Content-Type: application/json" ^
  -H "X-Api-Key: %API_KEY%" ^
  -d "{\"project\":\"my-project\",\"command\":\"python --version\",\"dry_run\":false,\"auto_approve\":true,\"delay_seconds\":0}"
```

## 🔧 PowerShell Examples (Windows)

Set your API key:

```powershell
$apiKey = "your_super_secret_key"
$headers = @{ "X-Api-Key" = $apiKey }
```

List projects:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:9234/projects" -Headers $headers
```

Select project (opens VS Code + returns run-task availability):

```powershell
$body = @{ project = "my-project" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:9234/project/select" -Headers $headers -ContentType "application/json" -Body $body
```

List run-task files:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:9234/project/tasks?project=my-project" -Headers $headers
```

Get current selected project:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:9234/project/current" -Headers $headers
```

Run a task file from run-task folder:

```powershell
$body = @{ project = "my-project"; task = "build.ps1"; dry_run = $false; auto_approve = $true; delay_seconds = 0 } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:9234/project/run-task" -Headers $headers -ContentType "application/json" -Body $body
```

Run a custom command:

```powershell
$body = @{ project = "my-project"; command = "python --version"; dry_run = $false; auto_approve = $true; delay_seconds = 0 } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:9234/project/run-custom" -Headers $headers -ContentType "application/json" -Body $body
```

## ✅ Quick Smoke Test Order

1. Start service: `python main.py`
2. Check health: `GET /health`
3. List projects: `GET /projects`
4. Select one project: `POST /project/select`
5. If `tasks` is not empty, run `POST /project/run-task`; otherwise run `POST /project/run-custom`

Expected result:

- Project path returns correctly
- VS Code open attempt message is returned
- Task execution or custom command output is returned

## 🧾 Sample JSON Responses

`GET /health`

```json
{
  "status": "ok",
  "ollama_url": "http://localhost:11434",
  "ollama_running": true,
  "telegram_configured": true,
  "telegram_started": true
}
```

`GET /projects`

```json
{
  "projects": ["my-project", "another-project"],
  "count": 2,
  "message": "Use POST /project/select with a project name."
}
```

`POST /project/select`

```json
{
  "project": "my-project",
  "path": "D:/PERSONAL/LIVE_PROJECTS/my-project",
  "open_vscode": "Opened in VS Code.",
  "tasks": [
    {"name": "build.ps1", "description": "Build project", "auto_approve": true, "delay_seconds": 0},
    {"name": "test.ps1", "description": "Run tests", "auto_approve": true, "delay_seconds": 0}
  ],
  "message": "run-task files available. Use POST /project/run-task to execute one."
}
```

`GET /project/current`

```json
{
  "project": "my-project",
  "path": "D:/PERSONAL/LIVE_PROJECTS/my-project",
  "tasks": [
    {"name": "build.ps1", "description": "Build project", "auto_approve": true, "delay_seconds": 0}
  ]
}
```

`GET /project/tasks?project=my-project`

```json
{
  "project": "my-project",
  "path": "D:/PERSONAL/LIVE_PROJECTS/my-project",
  "tasks": [
    {"name": "build.ps1", "description": "Build project", "auto_approve": true, "delay_seconds": 0},
    {"name": "test.ps1", "description": "Run tests", "auto_approve": true, "delay_seconds": 0}
  ],
  "count": 2
}
```

`POST /project/run-task`

```json
{
  "project": "my-project",
  "task": "build.ps1",
  "output": "Build completed successfully",
  "exit_code": 0,
  "started_at": 1740710000.0,
  "duration_ms": 215,
  "auto_approve": true,
  "delay_seconds": 0
}
```

`POST /project/run-custom`

```json
{
  "project": "my-project",
  "command": "python --version",
  "output": "Python 3.12.4",
  "exit_code": 0,
  "started_at": 1740710000.0,
  "duration_ms": 42,
  "auto_approve": true,
  "delay_seconds": 0
}
```

## ❌ Sample Error Responses

`401 Unauthorized` (missing or invalid `X-Api-Key`)

```json
{
  "detail": {
    "code": "UNAUTHORIZED",
    "message": "Unauthorized",
    "hint": "Provide valid X-Api-Key"
  }
}
```

`500 Server API secret is not configured`

```json
{
  "detail": {
    "code": "API_SECRET_MISSING",
    "message": "Server API secret is not configured",
    "hint": "Set API_SECRET_KEY or API_SECRET_KEYS in .env"
  }
}
```

`400 Project not found` (for `/project/select`, `/project/tasks`, `/project/run-task`, `/project/run-custom`)

```json
{
  "detail": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project not found",
    "hint": "Call /projects and choose a valid project name"
  }
}
```

`400 Task file not found in run-task folder` (for `/project/run-task`)

```json
{
  "detail": {
    "code": "TASK_NOT_FOUND",
    "message": "Task file not found in run-task folder",
    "hint": "Call /project/tasks to list valid tasks"
  }
}
```

## ⚙ Runtime Controls

- `COMMAND_TIMEOUT`, `TASK_TIMEOUT` - execution timeout in seconds
- `MAX_OUTPUT_CHARS` - output truncation limit
- `STRICT_COMMAND_MODE` + `ALLOWED_COMMAND_PREFIXES` - enforce strict command prefix policy
- `RATE_LIMIT_PER_MINUTE` - per key/client/endpoint request cap
- `API_SECRET_KEYS` - comma-separated keys for key rotation
- `AUTO_APPROVE` + `DEFAULT_EXECUTION_DELAY_SECONDS` - default auto approval and delay behavior

## 🧪 Reference Client

- Python reference client is available at `cli/client.py`
- Uses structured error handling and retry logic for transport/429 scenarios

## 🧭 Client Handling Guide

| Condition | Meaning | Client action |
| --- | --- | --- |
| `401 Unauthorized` | API key missing or invalid | Prompt for API key, refresh secret in client config, retry request |
| `500 Server API secret is not configured` | Server missing `API_SECRET_KEY` | Fix server `.env`, restart service, retry |
| `400 Project not found` | Project name invalid or not under `PROJECT_ROOT` | Call `GET /projects`, let user reselect, call endpoint again |
| `400 Task file not found in run-task folder` | Task file missing/renamed/not allowed extension | Call `GET /project/tasks`, show valid files, retry with selected task |
| Empty `tasks` in `/project/select` or `/project/tasks` | `run-task/` has no task scripts | Ask user for custom command and call `POST /project/run-custom` |

Retry policy suggestion:

- Retry only for transient transport failures (network timeout, connection reset).
- Do not blind-retry `400/401/500` logical/config errors; require user/config fix first.

### Realtime chat (WebSocket)

Connect to:

`ws://localhost:PORT/ws/chat`

Send plain text prompt messages. Server streams response chunks and sends `[DONE]` when the response is complete.

---

## 🛡 Security Notes

- Protected endpoints require `X-Api-Key`
- Telegram access is restricted by `ALLOWED_TELEGRAM_USER_ID`
- Command execution is filtered by allow/deny policy in `security/command_filter.py`
- Project execution path is constrained to folders under configured `PROJECT_ROOT`/`PROJECT_ROOTS`

---

## 🌍 Optional External Access

```bash
cloudflared tunnel --url http://localhost:9234
```

---

## ✅ Production Checklist

### Security
- [ ] Strong `API_SECRET_KEY` set in `.env`
- [ ] `RBAC_ROLES` configured for multi-user access
- [ ] `ALLOWED_TELEGRAM_USER_ID` restricted to trusted users
- [ ] Firewall rules verified (if exposing externally)

### Configuration
- [ ] Correct `PROJECT_ROOT` path set
- [ ] `AGENT_MODE` set to appropriate level (SAFE/CONTROLLED/AUTONOMOUS)
- [ ] `AUTONOMOUS_RISK_THRESHOLD` tuned for your risk tolerance
- [ ] Ollama running and reachable at `OLLAMA_URL`

### Monitoring
- [ ] Dashboard accessible at `/dashboard/`
- [ ] Audit log writing to `logs/agent_audit.log`
- [ ] Memory database created at `logs/memory.db`
- [ ] Plugins auto-loading from `plugins/` directory

### Testing
- [ ] Run `ayazdy health` — all checks pass
- [ ] Run `ayazdy self-check` — Ollama, DB, approval store, DSL validated
- [ ] Run `agent status` — system status with Rich UI
- [ ] Run `agent verify <task> --project <name>` — workflow pre-run checks pass
- [ ] Test approval workflow: reject high-risk task, approve low-risk
- [ ] Verify queue processing: place test `.yaml` in `agent-task/queue/`, run `agent queue --run`

---

## 🧭 Troubleshooting

**Dashboard can't connect to API**
- Check API URL in Settings (⚙️ icon) — should be `http://127.0.0.1:8000`
- Verify API key matches `API_SECRET_KEY` from `.env`
- Check CORS settings — `CORS_ORIGINS` must include dashboard origin

**Telegram bot not responding**
- Verify `TELEGRAM_TOKEN` is valid
- Check `ALLOWED_TELEGRAM_USER_ID` matches your Telegram user ID (use `/id` command)
- Ensure Telegram service started successfully (check startup logs)

**"Ollama not running" error**
- Start Ollama: `ollama serve` or run Ollama Desktop app
- Verify `OLLAMA_URL` in `.env` (default: `http://localhost:11434`)
- Test manually: `ollama list` should show installed models

**Tasks stuck in "pending" approval**
- Check `/monitor/approvals` for pending tokens
- Approve via CLI: `ayazdy approve <token>`
- Or via dashboard: Approvals tab → ✔ Approve button
- Or via Telegram: `/approve <token>`

**High memory usage from SQLite**
- Periodically archive old entries from `logs/memory.db`
- Or delete the file (will reset history) — auto-recreates on next run

**Plugin not loading**
- Check plugin file doesn't start with `_` (those are skipped)
- Verify `register(manager)` function exists
- Check startup logs for plugin load messages

---

## 🆚 Agent Ayazdy vs Copilot-Ralph

[copilot-ralph](https://github.com/ashiqsultan/copilot-ralph) is a desktop application that uses GitHub Copilot CLI to build projects task by task. Here is a comparison:

| Feature | Agent Ayazdy | Copilot-Ralph |
|---|---|---|
| **Platform** | Python REST API server (FastAPI) | Electron desktop app (React + Vite) |
| **LLM providers** | Ollama, OpenAI, OpenRouter, LM Studio, **GitHub Copilot CLI** | GitHub Copilot CLI only |
| **Per-task git commit** | ✅ Optional (`auto_git_commit=true` or `AUTO_GIT_COMMIT=true`) | ✅ Always on |
| **Git diff view** | ✅ `GET /project/git-diff` endpoint | ✅ Built-in UI panel |
| **Context isolation** | Memory-augmented prompts (default); Copilot CLI provider uses fresh context per call | Each task call is isolated (no context rot) |
| **Approval workflow** | ✅ Token-based (approve/reject before execution) | ❌ Not present |
| **Risk scoring** | ✅ 1-10 scale with SAFE/CONTROLLED/AUTONOMOUS modes | ❌ Not present |
| **RBAC** | ✅ Admin/Operator/Viewer roles | ❌ Not present |
| **Audit log** | ✅ Immutable JSONL audit trail | ❌ Not present |
| **Plugin system** | ✅ 4 lifecycle hooks | ❌ Not present |
| **Telegram bot** | ✅ 15+ commands | ❌ Not present |
| **Web dashboard** | ✅ Real-time React dashboard | ✅ Electron UI |
| **Task queue** | ✅ File-based queue/completed/later | Plain JSON files |
| **Storage** | SQLite memory + JSONL audit | Plain JSON + txt files |
| **Plan mode** | ✅ Planner agent generates structured plan | ✅ Optional plan mode |
| **Retry on failure** | ✅ Auto-retry in AUTONOMOUS mode | ❌ Not present |

### Features Added Inspired by Copilot-Ralph

The following features were added to agent-ayaz based on the copilot-ralph comparison:

#### 1. GitHub Copilot CLI as LLM Provider

GitHub Copilot CLI (`gh copilot suggest`) is now supported as a fallback LLM provider. It auto-detects if `gh` CLI is installed and authenticated.

**Priority order:** Ollama → OpenAI → OpenRouter → LM Studio → **GitHub Copilot CLI** → Mock

Each `gh copilot suggest` call is isolated (fresh context, no accumulated history) — the same approach copilot-ralph uses to prevent LLM context rot.

**Requirement:** Install [GitHub CLI](https://cli.github.com/) and authenticate with `gh auth login`.

#### 2. Auto Git-Commit After Task Execution

After each successful task execution, agent-ayaz can automatically commit all project changes with a semantic commit message — the same model used by copilot-ralph's per-task commits.

**Enable globally** in `.env`:
```env
AUTO_GIT_COMMIT=true
```

**Enable per-request** in the request body:
```json
{ "task": "build.ps1", "auto_git_commit": true }
```

The response includes a `git_commit` field with the result:
```json
{
  "task": "build.ps1",
  "exit_code": 0,
  "git_commit": {
    "success": true,
    "commit_hash": "abc1234",
    "branch": "main"
  }
}
```

#### 3. Git Diff View

New endpoint `GET /project/git-diff` returns the full git diff and status for a project — like copilot-ralph's per-task diff panel.

```bash
curl -H "X-Api-Key: $KEY" "http://localhost:9234/project/git-diff?project=my-project"
```

Response:
```json
{
  "project": "my-project",
  "branch": "main",
  "staged": false,
  "status": { "modified": ["app.py"], "added": [], "deleted": [], "total": 1 },
  "diff_stat": " app.py | 5 +++++\n 1 file changed, 5 insertions(+)",
  "diff": "diff --git a/app.py b/app.py\n..."
}
```

Use `?staged=true` to view staged changes instead.

#### 4. `/project/run-custom` Route Registration

The `/project/run-custom` endpoint was previously defined as a function but never registered as a route. It is now properly exposed as `POST /project/run-custom`, also supporting `auto_git_commit`.

---

## 📚 Further Reading

- **Dashboard Guide:** `dashboard/README.md`
- **Task Queue Specs:** `agent-task/completed/01-07` (phase implementation specs)
- **Plugin Development:** See `plugins/logger_plugin.py` for example
- **API Client Reference:** `cli/client.py`

---

## 🗂 Legacy Archive

Legacy files and historical artifacts were moved to `temp/legacy` to keep the active runtime surface clean.
This folder is archival only and is not part of the current application startup path.
