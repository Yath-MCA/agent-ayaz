# 🤖 Agent Ayazdy — AI DevOps Agent

**14-Phase Production-Grade Agent Architecture** — FastAPI + Telegram + Ollama + React Dashboard

Full multi-agent system with planning, validation, execution auditing, approval workflows, memory layer, plugin system, RBAC, CLI control, and web-based monitoring.

---

## 📌 Overview

**Agent Ayazdy** is a sophisticated AI DevOps agent that provides:

- 🤖 **AgentAyazDaddy CLI** — `agent` command with Rich UI, workflow verification, APScheduler, structured logs
- 🧠 **Multi-agent architecture** — Planner → Validator → Executor → Auditor pipeline
- 🔐 **Token-based approval workflow** — Review plans before execution
- 📊 **SQLite memory layer** — Execution history, stats, retry suggestions
- 🎯 **Risk scoring** — 1-10 scale with autonomous mode controls
- 🔌 **Plugin system** — 4 lifecycle hooks (before_plan, after_validation, after_execution, on_error)
- 👥 **RBAC** — Admin/Operator/Viewer roles
- 🖥️ **React dashboard** — Real-time monitoring, approvals, logs, SSE streaming
- 📋 **Task queue system** — File-based queue/completed/later lifecycle
- 🛠️ **CLI wrapper** — `ayazdy` command for terminal control
- 📡 **Telegram bot** — Remote control with 15+ commands
- 🌐 **REST API** — 40+ endpoints for full programmatic control

It complements IDE workflows (including GitHub Copilot) and focuses on **controlled, auditable, intelligent automation**.

---

## 🧠 Architecture

```text
agent-ayazdy/
├── main.py                      # FastAPI app + agent pipeline composition
├── config/
│   └── settings.py              # Environment/config loading
├── security/
│   ├── command_filter.py        # Command policy/validation
│   └── rbac.py                  # Role-based access control
├── agents/                      # 🔥 Multi-agent system
│   ├── planner.py               # LLM → ExecutionPlan JSON
│   ├── validator.py             # Policy gate (approve/reject)
│   ├── executor.py              # Validated plan execution
│   ├── auditor.py               # Immutable JSONL audit log
│   ├── approval.py              # Token-based approval store
│   ├── task_dsl.py              # YAML task DSL loader/validator
│   ├── risk.py                  # Risk scoring engine (1-10 scale)
│   ├── replay.py                # Replay execution by ID
│   ├── optimizer.py             # Memory-driven prompt augmentation
│   ├── mode.py                  # SAFE/CONTROLLED/AUTONOMOUS modes
│   ├── workflow_verifier.py     # Pre-run checks (new — AgentAyazDaddy)
│   └── nodes.py                 # Distributed node registry
├── services/
│   ├── llm_provider.py          # 🤖 Multi-provider LLM with auto-fallback
│   ├── ollama_service.py        # Ollama HTTP integration (legacy)
│   ├── telegram_service.py      # Telegram bot (15+ commands)
│   ├── execution_service.py     # Command execution wrapper
│   ├── memory_service.py        # SQLite execution history (logs/memory.db)
│   ├── task_queue_service.py    # File-based task queue lifecycle
│   ├── scheduler_service.py     # APScheduler cron integration (new)
│   └── structured_logger.py     # Structured log writer (new)
├── plugins/                     # 🔌 Plugin system
│   ├── __init__.py              # PluginManager with 4 lifecycle hooks
│   └── logger_plugin.py         # Example plugin
├── cli/                         # 🛠️ CLI control interfaces
│   ├── agent_cli.py             # AgentAyazDaddy CLI — typer + rich (new)
│   ├── terminal_ui.py           # Rich UI components (new)
│   ├── cli.py                   # Legacy ayazdy argparse entrypoint
│   ├── client.py                # REST API wrapper
│   └── commands.py              # Command implementations
├── config/
│   ├── settings.py              # Environment/config loading
│   ├── projects.json            # Central project config (new)
│   └── schedule.json            # Cron-like schedule config (new)
├── tasks/                       # 📋 Task module definitions (new)
│   ├── build.task.json
│   ├── deploy.task.json
│   └── htmlCompare.task.json
├── dashboard/                   # 🖥️ React Control Center
│   ├── index.html               # CDN-based React app (zero build)
│   ├── js/app.js                # Dashboard UI (~350 lines)
│   └── README.md                # Dashboard setup guide
├── tools/                       # 🔧 Utility tools (active)
│   └── git_service.py           # Git automation service (used by main.py)
├── temp/                        # 📦 Archive (non-runtime)
│   ├── bat/                     # Archived batch scripts
│   ├── build-specs/             # PyInstaller .spec files
│   ├── legacy/                  # Orphaned modules (dashboard_server, ide_runner, task_queue_system)
│   └── standalone-tools/        # Standalone CLIs/GUIs (ayazgitdy, check_llm, control_center)
├── agent-task/                  # 📋 Task queue folders
│   ├── queue/                   # Tasks to process
│   ├── completed/               # Completed tasks
│   └── later/                   # Deferred tasks
├── logs/                        # Log output
│   ├── agent.log                # Agent lifecycle events (new)
│   ├── tasks.log                # Task start/complete/failed (new)
│   ├── errors.log               # Error events (new)
│   ├── audit.log                # Immutable JSONL audit trail
│   └── memory.db                # SQLite execution history
├── project_utils.py             # PROJECT_ROOT utilities (env-var-based, no hardcoded paths)
├── agent.bat                    # AgentAyazDaddy CLI wrapper (new)
├── ayazdy.bat                   # Legacy CLI wrapper
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🤖 AgentAyazDaddy — CLI Task Runner

The new primary CLI interface with Rich terminal UI.

### Commands

```bash
agent status                            # Full system status
agent run <task> [--project P]          # Run a task
agent run <task> --verify               # With pre-flight checks
agent run <task> --dry-run              # Simulate without executing
agent queue                             # Queue status
agent queue --run                       # Execute queue now
agent queue --promote                   # Promote later/ → queue/
agent projects                          # Projects from API
agent projects --local                  # Projects from config/projects.json
agent schedule                          # Scheduler status
agent logs tasks                        # Task logs
agent logs errors                       # Error logs
agent analyze "summarize failures"      # AI analysis via LLM
agent ask "explain this error"          # Direct Ollama query
agent verify <task> --project impact    # Workflow pre-run checks
agent dashboard <task> <status>         # Post status to dashboard
```

### Scheduler (APScheduler)

Edit `config/schedule.json` to define cron jobs:

```json
{
  "tasks": [
    { "task": "nightly-build", "time": "02:00",          "enabled": false, "type": "queue-run" },
    { "task": "queue-check",   "time": "08:00",          "enabled": true,  "type": "queue-run" },
    { "task": "health-check",  "cron": "*/15 * * * *",   "enabled": true,  "type": "health-check" }
  ]
}
```

Start scheduler:

```bash
python -m services.scheduler_service
# or
agent schedule --start
```

### Project config

Edit `config/projects.json`:

```json
{
  "projects": [
    {
      "name": "impact",
      "path": "C:/_IMPACT/tomcat/webapps/impact_vite",
      "tasks": ["build", "deploy", "compare-html"]
    }
  ]
}
```

### Structured logs

```bash
agent logs tasks --limit 20   # logs/tasks.log
agent logs errors             # logs/errors.log
agent logs agent              # logs/agent.log
```

---

## 🚀 Setup (Windows)

### 1) Choose Your LLM Provider

The system supports **multiple LLM providers** with automatic fallback:

#### Option A: Ollama (Recommended - Free, Local, Private)

Download: <https://ollama.com/download/windows>

```bash
ollama pull phi3
ollama list
```

#### Option B: OpenAI (Cloud, Paid)

Get API key: <https://platform.openai.com/api-keys>

Add to `.env`:
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

#### Option C: OpenRouter (Cloud, Free/Paid Models)

Get API key: <https://openrouter.ai/keys>

Add to `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

#### Option D: LM Studio (Local Alternative)

Download: <https://lmstudio.ai>

Start server on port 1234, then add to `.env`:
```env
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model
```

**Auto-Fallback:** System tries providers in order: Ollama → OpenAI → OpenRouter → LM Studio → Mock

**Diagnostic Tool:** Run `check_llm.bat` to check which providers are available.

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

Copy `.env.example` to `.env` and set values:

```env
# Core
PROJECT_ROOT=D:/PERSONAL/LIVE_PROJECTS

# LLM Provider (configure what you have)
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434
OLLAMA_BIN=D:/Program Files/Ollama/ollama.exe

# Optional: OpenAI
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# Optional: OpenRouter
# OPENROUTER_API_KEY=sk-or-v1-...
# OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Telegram & API
TELEGRAM_TOKEN=your_bot_token
API_SECRET_KEY=your_super_secret_key
ALLOWED_TELEGRAM_USER_ID=your_telegram_user_id
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost,http://127.0.0.1

# Agent Mode (SAFE | CONTROLLED | AUTONOMOUS)
AGENT_MODE=CONTROLLED
AUTONOMOUS_RISK_THRESHOLD=3
AUTONOMOUS_MAX_RETRIES=2

# RBAC (optional: admin/operator/viewer)
# RBAC_ROLES=api_key_1:admin,api_key_2:operator,api_key_3:viewer
```

If Ollama is installed in a custom folder, set `OLLAMA_BIN` to the full executable path.
Example on Windows: `D:/Program Files/Ollama/ollama.exe`

> Use `.env` only for runtime configuration. Do not commit secrets.

### 4) Run

```bash
python main.py
```

---

## 🚀 Quick Start

### Terminal Control (CLI)

```bash
# Health check
ayazdy health

# List projects
ayazdy projects

# Select project
ayazdy select my-project

# Check queue status
ayazdy qstatus

# Run queue tasks
ayazdy qrun

# View execution history
ayazdy history

# View stats
ayazdy stats

# Self-check diagnostics
ayazdy self-check
```

### Web Dashboard

Start the server and open **http://localhost:8000/dashboard/**

**Features:**
- Health + Stats panels
- Project selector
- Execution history with risk badges
- Approval queue (approve/reject buttons)
- Audit log viewer
- Live SSE log stream
- Self-check runner
- Retry suggestions

**First-time setup:** Click ⚙️ Settings → enter API URL + API Key

---

## 🔐 API Endpoints

### Core Endpoints
- `GET /` - basic service status
- `GET /status` - runtime status (model, LLM provider, Telegram configured/started)
- `GET /health` - dependency health (all LLM providers, service state)
- `GET /llm-providers` - detailed status of all LLM providers (Ollama, OpenAI, OpenRouter, LM Studio, Mock)
- `POST /chat` - public chat (no command execution)
- `WS /ws/chat` - real-time token streaming chat (`[DONE]` marks completion)

### Project Management (Protected)
- `GET /projects` - list projects under `PROJECT_ROOT`
- `POST /project/select` - choose project, open in VS Code
- `GET /project/current` - get current selected project for API key
- `GET /project/tasks?project=<name>` - list files in project `run-task/`
- `POST /project/run-task` - execute one file from project `run-task/`
- `POST /project/run-custom` - execute custom command in selected project
- `POST /project/run-all-tasks` - run all tasks in order

### Agent System (Protected)
- `POST /run-task` - execute task via agent pipeline (Planner→Validator→Executor→Auditor)
- `POST /run-project` - execute task in selected project via agent pipeline

### Monitoring (Protected)
- `GET /monitor/health` - agent health (mode, plugins, nodes, queue, memory)
- `GET /monitor/logs?limit=N` - audit log entries
- `GET /monitor/history?project=X&limit=N` - execution history
- `GET /monitor/stats` - total executions, failures, avg duration, top project/task
- `GET /monitor/approvals` - pending/approved/rejected approval tokens
- `POST /monitor/approve/{token}` - approve pending plan
- `POST /monitor/reject/{token}` - reject pending plan
- `GET /monitor/stream/logs` - SSE live log stream
- `GET /monitor/timeline` - chronological activity timeline
- `GET /monitor/self-check` - validate Ollama, DB, approval store, DSL
- `GET /monitor/risk?project=X&task=Y` - get risk score for task
- `GET /monitor/replay/{execution_id}` - replay execution by ID
- `GET /monitor/mode` - get current agent mode (SAFE/CONTROLLED/AUTONOMOUS)
- `GET /monitor/heatmap` - dashboard visualization data
- `GET /monitor/nodes` - list registered nodes
- `POST /monitor/nodes` - register new node
- `DELETE /monitor/nodes/{node_id}` - deregister node

### Task Queue (Protected)
- `GET /queue/status` - queue/completed/later folder status
- `POST /queue/run` - process queue tasks in order
- `POST /queue/promote-later` - move tasks from later/ to queue/
- `POST /api/agent/task-status` - receive agent task status updates (`agent`, `task`, `status` fields)
- `GET /api/agent/task-status` - retrieve recent agent task status history



**Core:**
- `/start`, `/help` - welcome + command list
- `/status` - runtime status
- `/id` - your Telegram user ID

**Projects:**
- `/projects` - list project folders
- `/project <name>` - select project, open VS Code
- `/current` - show current selected project
- `/tasks` - list available files in `run-task/`
- `/task <file_name>` - run one task file
- `/custom <command>` - run custom command in selected project
- `/runtasks` - run all tasks in order

**Agent:**
- `/approve <token>` - approve pending plan
- `/reject <token>` - reject pending plan

**Queue:**
- `/qstatus` - queue status (queue/completed/later counts)
- `/qrun` - run queue tasks
- `/qlater` - promote later/ tasks to queue/

## 🔧 REST Examples (Windows)

Set your API key once in terminal:

```bat
set API_KEY=your_super_secret_key
```

List projects:

```bat
curl -X GET "http://localhost:8000/projects" -H "X-Api-Key: %API_KEY%"
```

Select a project (opens VS Code and returns run-task availability):

```bat
curl -X POST "http://localhost:8000/project/select" ^
  -H "Content-Type: application/json" ^
  -H "X-Api-Key: %API_KEY%" ^
  -d "{\"project\":\"my-project\"}"
```

List run-task files for a selected project:

```bat
curl -X GET "http://localhost:8000/project/tasks?project=my-project" -H "X-Api-Key: %API_KEY%"
```

Get current selected project for this API key:

```bat
curl -X GET "http://localhost:8000/project/current" -H "X-Api-Key: %API_KEY%"
```

Run a task file from `run-task/`:

```bat
curl -X POST "http://localhost:8000/project/run-task" ^
  -H "Content-Type: application/json" ^
  -H "X-Api-Key: %API_KEY%" ^
  -d "{\"project\":\"my-project\",\"task\":\"build.ps1\",\"dry_run\":false,\"auto_approve\":true,\"delay_seconds\":0}"
```

Run a custom command when no run-task files are available:

```bat
curl -X POST "http://localhost:8000/project/run-custom" ^
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
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/projects" -Headers $headers
```

Select project (opens VS Code + returns run-task availability):

```powershell
$body = @{ project = "my-project" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/project/select" -Headers $headers -ContentType "application/json" -Body $body
```

List run-task files:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/project/tasks?project=my-project" -Headers $headers
```

Get current selected project:

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/project/current" -Headers $headers
```

Run a task file from run-task folder:

```powershell
$body = @{ project = "my-project"; task = "build.ps1"; dry_run = $false; auto_approve = $true; delay_seconds = 0 } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/project/run-task" -Headers $headers -ContentType "application/json" -Body $body
```

Run a custom command:

```powershell
$body = @{ project = "my-project"; command = "python --version"; dry_run = $false; auto_approve = $true; delay_seconds = 0 } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/project/run-custom" -Headers $headers -ContentType "application/json" -Body $body
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

### Core Settings
- `COMMAND_TIMEOUT`, `TASK_TIMEOUT` - execution timeout in seconds
- `MAX_OUTPUT_CHARS` - output truncation limit
- `STRICT_COMMAND_MODE` + `ALLOWED_COMMAND_PREFIXES` - enforce strict command prefix policy
- `RATE_LIMIT_PER_MINUTE` - per key/client/endpoint request cap
- `API_SECRET_KEYS` - comma-separated keys for key rotation
- `AUTO_APPROVE` + `DEFAULT_EXECUTION_DELAY_SECONDS` - default auto approval and delay behavior

### Agent Mode Settings
- `AGENT_MODE` - `SAFE` | `CONTROLLED` | `AUTONOMOUS`
  - **SAFE** — requires approval for all tasks
  - **CONTROLLED** — auto-approves low-risk tasks (≤3), requires approval for high-risk
  - **AUTONOMOUS** — auto-approves, auto-retries failures (up to `AUTONOMOUS_MAX_RETRIES`)
- `AUTONOMOUS_RISK_THRESHOLD` - max risk score for auto-approval (default: 3)
- `AUTONOMOUS_MAX_RETRIES` - retry attempts in autonomous mode (default: 2)

### RBAC Settings
- `RBAC_ROLES` - comma-separated `api_key:role` pairs
  - Roles: `admin` (full access), `operator` (execute + monitor), `viewer` (read-only)
  - Example: `key1:admin,key2:operator,key3:viewer`
  - If not set, all keys default to `admin`

---

## 🔌 Plugin System

Create custom plugins in `plugins/` directory:

```python
# plugins/my_plugin.py
def register(manager):
    manager.register("before_plan", lambda ctx: print(f"Planning {ctx['task']}..."))
    manager.register("after_validation", lambda ctx: print(f"Validated: {ctx['approved']}"))
    manager.register("after_execution", lambda ctx: print(f"Executed: {ctx['status']}"))
    manager.register("on_error", lambda ctx: print(f"Error: {ctx['error']}"))
```

Plugins are auto-loaded on startup. Context dict includes: `project`, `task`, `plan`, `approved`, `status`, `error`, etc.

---

## 📋 Task Queue System

Place `.md` or `.yaml` task files in `agent-task/queue/`:

**Lifecycle:**
1. Tasks in `queue/` are processed alphabetically
2. Completed tasks move to `completed/`
3. When queue is empty, system prompts to promote tasks from `later/` to `queue/`

**YAML DSL Example:**

```yaml
# agent-task/queue/build_project.yaml
type: command
project: my-project
task: Build and test
command: npm run build && npm test
auto_approve: false
delay_seconds: 5
```

**CLI:**
```bash
ayazdy qstatus   # Check queue status
ayazdy qrun      # Process queue
ayazdy qlater    # Promote later/ to queue/
```

---

## 🎯 Risk Scoring

Every task is assigned a risk score (1-10):

| Score | Level | Examples |
|---|---|---|
| 1-3 | 🟢 Low | Read-only, info commands (`git status`, `ls`) |
| 4-6 | 🟡 Medium | Build, test, install deps |
| 7-9 | 🔴 High | Deploy, db migrations, file deletions |
| 10 | 🚨 Critical | Production writes, system changes |

**Agent Mode Behavior:**
- **SAFE:** All tasks require approval
- **CONTROLLED:** Auto-approves ≤3, requires approval >3
- **AUTONOMOUS:** Auto-approves all, auto-retries failures

---

## 📊 Memory Layer

SQLite database at `logs/memory.db` tracks:
- Execution history (project, task, status, duration, risk score)
- Stats (total executions, failures, avg duration)
- Retry suggestions (failed tasks per project)

**Endpoints:**
- `GET /monitor/history?project=X&limit=N`
- `GET /monitor/stats`
- `GET /monitor/replay/{execution_id}` - replay past execution

---

## 🛡 Security Notes

- Protected endpoints require `X-Api-Key` header
- Telegram access is restricted by `ALLOWED_TELEGRAM_USER_ID`
- Command execution is filtered by allow/deny policy in `security/command_filter.py`
- Project execution path is constrained to folders under `PROJECT_ROOT`
- **Approval workflow:** High-risk tasks require explicit approval (token-based state machine)
- **RBAC:** Role-based access control (admin/operator/viewer)
- **Audit logging:** Immutable JSONL audit trail in `logs/agent_audit.log`
- **Risk scoring:** Every task is scored 1-10 to guide approval decisions

---

## 🧪 Reference Client & Examples

Python reference client is available at `cli/client.py`.

### WebSocket Real-time Chat

Connect to `ws://localhost:PORT/ws/chat` and send plain text prompts. Server streams response chunks and sends `[DONE]` when complete.

### Client Error Handling

| Condition | Meaning | Client action |
|---|---|---|
| `401 Unauthorized` | API key missing/invalid | Prompt for API key, retry |
| `403 Forbidden` | Insufficient RBAC role | Request admin access or switch endpoint |
| `400 Project not found` | Invalid project name | Call `GET /projects`, reselect |
| `400 Task file not found` | Missing task file | Call `GET /project/tasks`, choose valid file |
| `500 Server error` | Server config issue | Check logs, fix `.env`, restart |

**Retry policy:** Only retry transient transport failures. Do not retry `400/401/403/500` without fixing root cause.

---

## 📖 14-Phase Architecture Details

<details>
<summary><b>Phase 1: Multi-Agent Split</b></summary>

- **Planner** (`agents/planner.py`) — LLM generates structured ExecutionPlan JSON
- **Validator** (`agents/validator.py`) — Policy gate, approves/rejects plans
- **Executor** (`agents/executor.py`) — Executes validated plans only
- **Auditor** (`agents/auditor.py`) — Immutable JSONL audit log

</details>

<details>
<summary><b>Phase 2: Task DSL System</b></summary>

- YAML task definitions (`agents/task_dsl.py`)
- Validation and loading of `.yaml` task files
- Example tasks in `agent-task/examples/`

</details>

<details>
<summary><b>Phase 3: Approval Workflow</b></summary>

- Token-based approval store (`agents/approval.py`)
- State machine: pending → approved/rejected/timed_out
- `/monitor/approve/{token}`, `/monitor/reject/{token}` endpoints

</details>

<details>
<summary><b>Phase 4: Memory Layer</b></summary>

- SQLite database at `logs/memory.db` (`services/memory_service.py`)
- Execution history with project, task, status, duration, risk score
- Stats aggregation, retry suggestions

</details>

<details>
<summary><b>Phase 5: Advanced Isolation & Monitoring</b></summary>

- Health, logs, history, approvals endpoints
- `/monitor/health`, `/monitor/logs`, `/monitor/history`, `/monitor/approvals`

</details>

<details>
<summary><b>Phase 6: CLI + Dashboard Control Center</b></summary>

- **CLI:** `ayazdy` command (`cli/cli.py`) with 15+ subcommands
- **OS wrapper:** `ayazdy.bat` for Windows PATH integration
- **SSE streaming:** `/monitor/stream/logs` for live events
- **Stats endpoint:** `/monitor/stats` (executions, failures, avg duration)
- **Self-check:** `/monitor/self-check` (Ollama, DB, approval store, DSL)
- **React dashboard:** CDN-based UI at `/dashboard/` (zero build step)
  - Overview: Health + Stats + Project selector
  - History: Execution table with risk badges
  - Approvals: Approve/Reject buttons
  - Logs: Audit log viewer
  - Live Stream: SSE log stream
  - Tools: Self-check + retry suggestions

</details>

<details>
<summary><b>Phase 7: Risk Scoring</b></summary>

- Risk engine (`agents/risk.py`) — scores tasks 1-10
- `/monitor/risk?project=X&task=Y` endpoint
- Integrated into agent pipeline for approval decisions

</details>

<details>
<summary><b>Phase 8: Replay Execution</b></summary>

- Replay past executions by ID (`agents/replay.py`)
- `/monitor/replay/{execution_id}` endpoint
- Deterministic re-execution with diff comparison

</details>

<details>
<summary><b>Phase 9: Memory-Driven Optimizer</b></summary>

- Prompt augmentation based on execution history (`agents/optimizer.py`)
- Injects context about past failures/successes into planner prompts

</details>

<details>
<summary><b>Phase 10: Agent Mode Control</b></summary>

- 3 modes: SAFE, CONTROLLED, AUTONOMOUS (`agents/mode.py`)
- `/monitor/mode` endpoint
- Controls auto-approval, auto-retry behavior

</details>

<details>
<summary><b>Phase 11: Plugin System</b></summary>

- 4 lifecycle hooks: `before_plan`, `after_validation`, `after_execution`, `on_error`
- Auto-discovery from `plugins/` directory (`plugins/__init__.py`)
- Example: `plugins/logger_plugin.py`

</details>

<details>
<summary><b>Phase 12: Heatmap Data</b></summary>

- `/monitor/heatmap` endpoint for dashboard visualization
- Execution frequency, failure hotspots, risk distribution

</details>

<details>
<summary><b>Phase 13: Distributed Node Registry</b></summary>

- Node registration system (`agents/nodes.py`)
- `/monitor/nodes/*` endpoints for distributed execution

</details>

<details>
<summary><b>Phase 14: RBAC</b></summary>

- Role-based access control (`security/rbac.py`)
- 3 roles: admin, operator, viewer
- Enforced via `require_protected_access()` in all protected endpoints

</details>

---

## 🌍 Optional External Access

```bash
cloudflared tunnel --url http://localhost:8000
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
- [ ] Test approval workflow: reject high-risk task, approve low-risk
- [ ] Verify queue processing: place test `.yaml` in `agent-task/queue/`, run `ayazdy qrun`

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

## 📚 Further Reading

- **Dashboard Guide:** `dashboard/README.md`
- **Task Queue Specs:** `agent-task/completed/01-07` (phase implementation specs)
- **Plugin Development:** See `plugins/logger_plugin.py` for example
- **API Client Reference:** `cli/client.py`

---

## 🗂 Legacy Archive

Legacy files and historical artifacts were moved to `temp/legacy` to keep the active runtime surface clean.
This folder is archival only and is not part of the current application startup path.
