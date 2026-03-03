# Changelog

All notable changes to Agent Ayazdy are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2026-03-03

### 🎉 Major Release: 14-Phase Agent Architecture

Complete rewrite with production-grade multi-agent system, approval workflows, memory layer, plugin system, RBAC, CLI, and React dashboard.

### Added

#### Phase 1-5: Core Agent System
- **Multi-agent architecture** (Planner → Validator → Executor → Auditor pipeline)
  - `agents/planner.py` — LLM generates structured ExecutionPlan JSON
  - `agents/validator.py` — Policy gate for plan approval/rejection
  - `agents/executor.py` — Validated plan execution only
  - `agents/auditor.py` — Immutable JSONL audit trail (`logs/agent_audit.log`)
- **YAML Task DSL** (`agents/task_dsl.py`)
  - Define tasks in `.yaml` files with validation
  - Example tasks in `agent-task/examples/`
- **Token-based approval workflow** (`agents/approval.py`)
  - State machine: pending → approved/rejected/timed_out
  - Endpoints: `/monitor/approve/{token}`, `/monitor/reject/{token}`
- **SQLite memory layer** (`services/memory_service.py`)
  - Execution history database at `logs/memory.db`
  - Track project, task, status, duration, risk score
  - Stats aggregation, retry suggestions
- **Monitoring endpoints**
  - `/monitor/health` — agent health (mode, plugins, nodes, queue, memory)
  - `/monitor/logs` — audit log entries
  - `/monitor/history` — execution history
  - `/monitor/approvals` — pending/approved/rejected approvals

#### Phase 6: CLI + Dashboard Control Center
- **CLI wrapper** (`cli/cli.py`, `cli/client.py`, `cli/commands.py`)
  - `ayazdy` command with 15+ subcommands
  - Commands: health, projects, select, run, runall, history, approvals, approve, reject, qstatus, qrun, qlater, stats, self-check
- **OS-level wrapper** (`ayazdy.bat`) for Windows PATH integration
- **SSE log streaming** (`/monitor/stream/logs`) for real-time event streaming
- **Stats endpoint** (`/monitor/stats`)
  - Total executions, failures, failure rate
  - Most-used project/task, average duration
- **Self-check diagnostics** (`/monitor/self-check`)
  - Validates Ollama, DB, approval store, DSL
- **Timeline endpoint** (`/monitor/timeline`) for chronological activity
- **React dashboard** (`dashboard/`)
  - CDN-based React 18 app (zero build step)
  - Tailwind CSS Play CDN styling
  - 6 tabs: Overview, History, Approvals, Logs, Live Stream, Tools
  - Features:
    - Health + Stats panels
    - Project selector
    - Execution history with risk badges (🟢🟡🔴)
    - Approval queue with approve/reject buttons
    - Audit log viewer
    - Live SSE log stream with start/stop controls
    - Self-check runner
    - Retry suggestions per project
  - Accessible at `/dashboard/` when server is running
  - Settings modal for API URL + API key (stored in localStorage)

#### Phase 7-14: Advanced Features
- **Risk scoring engine** (`agents/risk.py`)
  - 1-10 risk scale for every task
  - Endpoint: `/monitor/risk?project=X&task=Y`
  - Integrated into agent pipeline for approval decisions
- **Replay execution** (`agents/replay.py`)
  - Replay past executions by ID
  - Endpoint: `/monitor/replay/{execution_id}`
  - Deterministic re-execution with diff comparison
- **Memory-driven optimizer** (`agents/optimizer.py`)
  - Prompt augmentation based on execution history
  - Injects context about past failures/successes
- **Agent mode control** (`agents/mode.py`)
  - 3 modes: SAFE, CONTROLLED, AUTONOMOUS
  - Endpoint: `/monitor/mode`
  - Controls auto-approval and auto-retry behavior
  - Env vars: `AGENT_MODE`, `AUTONOMOUS_RISK_THRESHOLD`, `AUTONOMOUS_MAX_RETRIES`
- **Plugin system** (`plugins/__init__.py`)
  - 4 lifecycle hooks: `before_plan`, `after_validation`, `after_execution`, `on_error`
  - Auto-discovery from `plugins/` directory
  - Example plugin: `plugins/logger_plugin.py`
- **Heatmap data** (`/monitor/heatmap`)
  - Dashboard visualization data (execution frequency, failure hotspots)
- **Distributed node registry** (`agents/nodes.py`)
  - Node registration for distributed execution
  - Endpoints: `/monitor/nodes/*` (GET, POST, DELETE)
- **RBAC** (`security/rbac.py`)
  - Role-based access control (admin/operator/viewer)
  - Enforced in `require_protected_access()` on all protected endpoints
  - Env var: `RBAC_ROLES=key1:admin,key2:operator,key3:viewer`

#### Task Queue System (`services/task_queue_service.py`)
- File-based queue/completed/later lifecycle
- Folders: `agent-task/queue/`, `agent-task/completed/`, `agent-task/later/`
- Alphabetical processing order
- Endpoints: `/queue/status`, `/queue/run`, `/queue/promote-later`
- CLI: `ayazdy qstatus`, `ayazdy qrun`, `ayazdy qlater`
- Telegram: `/qstatus`, `/qrun`, `/qlater`

### Changed
- **`main.py`** — Major refactor
  - Added full agent pipeline in `run_agent()` (Planner→Validator→Executor→Auditor)
  - Integrated risk scoring, optimizer, plugins, autonomous mode
  - Added 30+ new endpoints (monitoring, queue, agent features)
  - Plugin auto-load on startup via `plugin_manager.load_plugins_from_dir()`
  - RBAC enforcement in `require_protected_access()`
  - Static file mount for `/dashboard/` route
- **`services/telegram_service.py`** — Extended with 6 new command handlers
  - `/runtasks` — run all tasks in order
  - `/approve <token>`, `/reject <token>` — approval workflow
  - `/qstatus`, `/qrun`, `/qlater` — queue management
  - Updated `/help` with new commands
- **`project_utils.py`** — Added `ensure_run_task_dir()` function
- **`requirements.txt`** — Added `pyyaml>=6.0.0` for YAML DSL
- **`ayazdy.bat`** — Updated to delegate to `cli/cli.py`

### Documentation
- **README.md** — Complete rewrite
  - 14-phase architecture overview
  - Comprehensive endpoint reference (40+ endpoints)
  - Telegram command reference (15+ commands)
  - CLI usage guide
  - Dashboard guide
  - Plugin system documentation
  - Task queue system guide
  - Risk scoring reference
  - RBAC setup guide
  - Production checklist
  - Troubleshooting section
- **`.env.example`** — Updated with agent system settings
  - `AGENT_MODE`, `AUTONOMOUS_RISK_THRESHOLD`, `AUTONOMOUS_MAX_RETRIES`
  - `RBAC_ROLES` with examples
- **`dashboard/README.md`** — Dashboard setup and usage guide
- **`CHANGELOG.md`** — This file (comprehensive version history)

### Migration Notes
**From v1.x to v2.0:**
1. Update `.env` with new agent settings (see `.env.example`)
2. Run `pip install -r requirements.txt` to install `pyyaml`
3. Database auto-creates at `logs/memory.db` on first run
4. Audit log auto-creates at `logs/agent_audit.log`
5. Plugins auto-load from `plugins/` directory (optional)
6. Dashboard available at `/dashboard/` (no build step needed)

**Breaking Changes:**
- None — fully backward compatible with v1.x `.env` files
- New endpoints are additive, all v1.x endpoints remain unchanged

---

## [1.0.0] - 2026-03-01

### Initial Release

#### Core Features
- FastAPI REST API server
- Ollama integration for local LLM inference
- Telegram bot for remote control
- Project management (list, select, execute tasks)
- Command execution with policy filtering
- API key protection for sensitive endpoints

#### Endpoints
- `GET /`, `/status`, `/health`
- `POST /chat`, `WS /ws/chat`
- `POST /run-task`, `/run-project`
- `GET /projects`, `POST /project/select`
- `GET /project/current`, `/project/tasks`
- `POST /project/run-task`, `/project/run-custom`

#### Telegram Commands
- `/start`, `/help`, `/status`, `/id`
- `/projects`, `/project`, `/current`
- `/tasks`, `/task`, `/custom`

#### Security
- API key authentication (`X-Api-Key`)
- Command policy filtering (`security/command_filter.py`)
- Telegram user ID whitelist
- Project path sandboxing (`PROJECT_ROOT`)

#### Services
- `ollama_service.py` — Ollama HTTP client
- `telegram_service.py` — Telegram bot integration
- `execution_service.py` — Command execution wrapper

---

## Legend

- 🎉 Major release
- ✨ New feature
- 🔧 Enhancement
- 🐛 Bug fix
- 📚 Documentation
- ⚠️ Breaking change
- 🔒 Security fix
