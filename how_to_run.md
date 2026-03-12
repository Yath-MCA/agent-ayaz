# How To Run

Practical commands to run AyazDy / AgentAyazDaddy using the `agent` CLI, legacy `ayazdy` CLI, Dashboard, and Telegram bot.

---

## 0) Start Ollama (Required for AI features)

Ollama must be running before starting the agent. Choose one option:

### Option A — Local Ollama (Recommended for dev)

```bash
# Start Ollama and pull default model automatically
ollama-start.bat

# Or with a specific model
ollama-start.bat mistral
ollama-start.bat qwen3:4b

# Force re-pull a model
ollama-start.bat mistral --pull
```

Manual equivalent:
```bash
ollama serve
ollama pull mistral
```

Verify it's running:
```bash
curl http://localhost:11434/api/tags
```

`.env` setting for local:
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

### Option B — Ollama in Docker

```bash
# Start Ollama container only
docker-compose -f docker-compose-ollama.yml up -d

# Check status
ollama-docker.bat status

# Pull a model inside Docker
ollama-docker.bat pull mistral

# List models in Docker
ollama-docker.bat list

# Stop
ollama-docker.bat stop
```

`.env` setting for Docker Ollama:
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```
> Port `11434` is forwarded from the container so the same URL works for both local and Docker Ollama.

---

### Available models (already downloaded locally)

| Model | Size | Best for |
|-------|------|----------|
| `qwen3.5:0.8b` | 1 GB | Fastest responses |
| `mistral:latest` | 4.4 GB | Best general use ✅ |
| `llama3.2:latest` | 2 GB | Good general use |
| `qwen3:4b` | 2.5 GB | Balanced |
| `codellama:latest` | 3.8 GB | Code tasks |

Set in `.env`:
```env
OLLAMA_MODEL=mistral
```

---

## 1) Start Server (Required)

Run from `d:\agent-ayaz`:

```bash
python main.py
```

Or use the launcher:

```bash
start.bat
```

Default local endpoints:

| Service | URL |
|---------|-----|
| REST API | `http://localhost:9234` |
| API Docs (Swagger) | `http://localhost:9234/docs` |
| Dashboard | `http://localhost:9234/dashboard` |

---

## 2) AgentAyazDaddy CLI (`agent`) — New

The primary CLI entry point. Uses Rich terminal UI with colorized output.

```bash
agent <command> [options]
# or
python -m cli.agent_cli <command> [options]
```

### Quick reference

```bash
# System status (health + queue + LLM)
agent status

# List projects (from config/projects.json)
agent projects --local

# List projects (from API)
agent projects

# Run a task
agent run build.ps1 --project my-project

# Run with pre-flight verification
agent run build.ps1 --project my-project --verify

# Run dry-run (simulate only)
agent run build.ps1 --project my-project --dry-run

# Queue status
agent queue

# Run queue now
agent queue --run

# Promote later/ tasks into queue/
agent queue --promote

# Scheduler status
agent schedule

# View task logs
agent logs tasks
agent logs errors
agent logs agent

# Limit log output
agent logs tasks --limit 30

# AI analysis
agent analyze "summarize build failures" --project my-project

# Ask Ollama directly
agent ask "what is the best way to optimize a Python loop?"

# Pre-run workflow verification
agent verify build.ps1 --project impact
agent verify build.ps1 --project impact --ollama

# Post status to dashboard
agent dashboard compare-html running
agent dashboard compare-html completed
```

### Full command list

| Command | Description |
|---------|-------------|
| `agent status` | Health, mode, LLM provider, queue summary |
| `agent run <task>` | Execute task (project context aware) |
| `agent queue` | Show queue status |
| `agent queue --run` | Execute all queued tasks |
| `agent queue --promote` | Move `later/` tasks into `queue/` |
| `agent projects` | List projects from API |
| `agent projects --local` | List projects from `config/projects.json` |
| `agent schedule` | Scheduler status + configured jobs |
| `agent schedule --start` | Start APScheduler |
| `agent schedule --stop` | Stop APScheduler |
| `agent logs [type]` | View logs: `tasks` \| `agent` \| `errors` |
| `agent analyze <text>` | AI analysis via LLM |
| `agent ask <question>` | Direct Ollama query |
| `agent verify <task>` | Pre-run workflow checks |
| `agent dashboard <task> <status>` | Post status to dashboard API |

---

## 3) Legacy `ayazdy` CLI

The original argparse-based CLI. Still fully supported.

```bash
# Health (no API key required)
python -m cli.cli health

# Protected commands
python -m cli.cli --key your_super_secret_key projects
python -m cli.cli --key your_super_secret_key status
python -m cli.cli --key your_super_secret_key qstatus
python -m cli.cli --key your_super_secret_key qrun
python -m cli.cli --key your_super_secret_key qlater
python -m cli.cli --key your_super_secret_key qrun-text --limit 20
python -m cli.cli --key your_super_secret_key select my-project
python -m cli.cli --key your_super_secret_key analyze "summarize current setup" --project my-project
python -m cli.cli --key your_super_secret_key exec "python --version" --project my-project
python -m cli.cli --key your_super_secret_key run build.ps1 --project my-project
python -m cli.cli --key your_super_secret_key runall --project my-project
python -m cli.cli --key your_super_secret_key history --project my-project
```

Desktop Git assistant:

```bash
python -m cli.cli desktop
# or
ayazdy desktop
```

---

## 4) Run Dashboard

Open in browser:

```text
http://localhost:9234/dashboard
```

Dashboard actions:
- Check queue status
- Trigger queue run
- Promote `later/` tasks
- View agent task status (`/api/agent/task-status`)

### GUI Control Center (Click-Based)

```bash
open-control-center.bat
```

Buttons: Start API · Build · Build EXE · Run Production · Docker Build · Check LLM · Git GUI · CLI Health · Queue Status

---

## 5) Run Telegram Bot

Set `.env` values:

```env
TELEGRAM_TOKEN=<your_bot_token>
ALLOWED_TELEGRAM_USER_ID=<your_numeric_telegram_user_id>
```

Restart server, then use bot commands:

```text
/help        — show all commands
/status      — system status
/projects    — list projects
/project <name>  — select project
/current     — current project
/tasks       — list available tasks
/task <file> — run a task
/custom <cmd>— run custom command
/qstatus     — queue status
/qrun        — run queue
/qlater      — promote later tasks
/approve <token>  — approve pending task
/reject <token>   — reject pending task
/gitcommit   — auto-commit changes
```

---

## 6) Queue Task Files

Drop YAML/script/prompt files into:

```text
agent-task/queue/
```

Then run queue:

```bash
# Via new agent CLI
agent queue --run

# Via legacy CLI
python -m cli.cli --key your_key qrun

# Via API
curl -X POST http://localhost:9234/queue/run -H "X-Api-Key: your_key"
```

Run `.txt`/`.md` prompts through LLM:

```bash
python -m cli.cli --key your_key qrun-text --limit 20
python -m cli.cli --key your_key qrun-text --include-later --limit 20
```

### Task naming convention (execution order)

```text
01_build.yaml     ← runs first
02_test.yaml
03_deploy.yaml
99_cleanup.yaml   ← runs last
```

---

## 7) Structured Logs

Logs are written to the `logs/` folder:

| File | Contents |
|------|----------|
| `logs/agent.log` | Agent lifecycle events |
| `logs/tasks.log` | Task start / complete / failed |
| `logs/errors.log` | Error events only |
| `logs/audit.log` | Immutable JSONL audit trail |
| `logs/memory.db` | SQLite execution history |

View via CLI:

```bash
agent logs tasks --limit 20
agent logs errors --limit 10
agent logs agent
```

---

## 8) Scheduler

Cron-like scheduling via `config/schedule.json`.

```bash
# View schedule
agent schedule

# Start scheduler (background)
python -m services.scheduler_service

# Or start from CLI
agent schedule --start
```

---

## 9) Workflow Verification

Before running a task, verify all preconditions are met:

```bash
agent verify build.ps1 --project impact
```

Output:

```
✔ projects.json found
✔ Project in config
✔ Project path found
✔ Python installed      Python 3.13.7
⚠ Agent API reachable   (server not running — warning only)
```

---

## 10) Production (Docker)

Windows:

```bash
run-production.bat
```

Linux/Mac:

```bash
bash run-production.sh
```

Production endpoints:

| Service | URL |
|---------|-----|
| Dashboard | `http://localhost:9890` |
| REST API | `http://localhost:9234` |
| Grafana | `http://localhost:9543` |
| Prometheus | `http://localhost:9654` |
