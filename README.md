# 🤖 AI DevOps Agent

FastAPI + Telegram + Local Ollama integration for secure DevOps task automation on Windows.

---

## 📌 Overview

AI DevOps Agent provides:

- Remote prompt handling through Telegram and REST
- Local model inference through Ollama
- Protected task execution limited to `PROJECT_ROOT`
- API-key protection for sensitive endpoints

It complements IDE workflows (including GitHub Copilot) and focuses on controlled automation.

---

## 🧠 Architecture

```text
ai-agent/
├── main.py                      # Composition root (FastAPI app + startup)
├── config/
│   └── settings.py              # Environment/config loading
├── security/
│   └── command_filter.py        # Command policy/validation
├── services/
│   ├── ollama_service.py        # Ollama HTTP integration
│   ├── telegram_service.py      # Telegram bot integration
│   └── execution_service.py     # Command execution wrapper
├── project_utils.py             # PROJECT_ROOT project path utilities
├── requirements.txt
├── .env.example                 # Safe env template
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
OLLAMA_MODEL=phi3
OLLAMA_URL=http://localhost:11434
OLLAMA_BIN=D:/Program Files/Ollama/ollama.exe
TELEGRAM_TOKEN=your_bot_token
API_SECRET_KEY=your_super_secret_key
ALLOWED_TELEGRAM_USER_ID=your_telegram_user_id
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost,http://127.0.0.1
```

If Ollama is installed in a custom folder, set `OLLAMA_BIN` to the full executable path.
Example on Windows: `D:/Program Files/Ollama/ollama.exe`

> Use `.env` only for runtime configuration. Do not commit secrets.

### 4) Run

```bash
python main.py
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
- `GET /projects` - protected, list projects under `PROJECT_ROOT`
- `POST /project/select` - protected, choose project, open in VS Code, and return `run-task/` availability
- `GET /project/current` - protected, get current selected project for the current API key
- `GET /project/tasks?project=<name>` - protected, list files in project `run-task/`
- `POST /project/run-task` - protected, execute one file from project `run-task/` (`dry_run`, `auto_approve`, `delay_seconds` supported)
- `POST /project/run-custom` - protected, execute custom command in selected project path (`dry_run`, `auto_approve`, `delay_seconds` supported)

## 🤖 Telegram Commands

- `/projects` - list project folders under `PROJECT_ROOT`
- `/project <name>` - select project, open it in VS Code, and show files inside `run-task/` if available
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

- `COMMAND_TIMEOUT`, `TASK_TIMEOUT` - execution timeout in seconds
- `MAX_OUTPUT_CHARS` - output truncation limit
- `STRICT_COMMAND_MODE` + `ALLOWED_COMMAND_PREFIXES` - enforce strict command prefix policy
- `RATE_LIMIT_PER_MINUTE` - per key/client/endpoint request cap
- `API_SECRET_KEYS` - comma-separated keys for key rotation
- `AUTO_APPROVE` + `DEFAULT_EXECUTION_DELAY_SECONDS` - default auto approval and delay behavior

## 🧪 Reference Client

- Python reference client is available at `tools/api_client.py`
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
- Project execution path is constrained to folders under `PROJECT_ROOT`

---

## 🌍 Optional External Access

```bash
cloudflared tunnel --url http://localhost:8000
```

---

## ✅ Production Checklist

- Strong `API_SECRET_KEY`
- Correct `PROJECT_ROOT`
- Rotated/valid Telegram token
- Ollama running and reachable
- Firewall and reverse-proxy rules verified

---

## 🗂 Legacy Archive

Legacy files and historical artifacts were moved to `temp/legacy` to keep the active runtime surface clean.
This folder is archival only and is not part of the current application startup path.
