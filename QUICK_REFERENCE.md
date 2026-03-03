# Agent Ayazdy — Quick Reference

## 🖥️ Dashboard

**URL:** http://localhost:8000/dashboard/

**First-time setup:**
1. Click **⚙️ Settings** (top-right)
2. Enter API URL: `http://127.0.0.1:8000`
3. Enter API Key: (from `.env` → `API_SECRET_KEY`)
4. Click **Save**

## 🛠️ CLI Commands

```bash
# Health & Status
ayazdy health          # System health check
ayazdy stats           # Execution statistics
ayazdy self-check      # Full diagnostics

# Projects
ayazdy projects        # List all projects
ayazdy select <name>   # Select project

# Tasks & Execution
ayazdy run <task>      # Run specific task
ayazdy runall          # Run all tasks in order
ayazdy history         # Execution history

# Queue Management
ayazdy qstatus         # Queue status (queue/completed/later counts)
ayazdy qrun            # Process queue tasks
ayazdy qlater          # Promote later/ to queue/

# Approvals
ayazdy approvals       # List pending approvals
ayazdy approve <token> # Approve pending plan
ayazdy reject <token>  # Reject pending plan
```

## 📱 Telegram Commands

```
/start              Welcome + help
/status             Runtime status
/projects           List projects
/project <name>     Select project
/current            Show selected project
/tasks              List run-task files
/task <file>        Run task file
/custom <cmd>       Run custom command
/runtasks           Run all tasks
/approve <token>    Approve plan
/reject <token>     Reject plan
/qstatus            Queue status
/qrun               Run queue
/qlater             Promote later/ tasks
```

## 🔐 API Endpoints (curl)

**Set API key:**
```bash
export API_KEY="your_api_key"
```

**Health check:**
```bash
curl -H "X-Api-Key: $API_KEY" http://localhost:8000/monitor/health
```

**List projects:**
```bash
curl -H "X-Api-Key: $API_KEY" http://localhost:8000/projects
```

**Select project:**
```bash
curl -X POST -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-project"}' \
  http://localhost:8000/project/select
```

**Execution history:**
```bash
curl -H "X-Api-Key: $API_KEY" \
  "http://localhost:8000/monitor/history?limit=10"
```

**Queue status:**
```bash
curl -H "X-Api-Key: $API_KEY" http://localhost:8000/queue/status
```

**Approve plan:**
```bash
curl -X POST -H "X-Api-Key: $API_KEY" \
  http://localhost:8000/monitor/approve/<token>
```

## 🎯 Risk Levels

| Score | Level | Auto-Approve (CONTROLLED) |
|---|---|---|
| 1-3 | 🟢 Low | ✅ Yes |
| 4-6 | 🟡 Medium | ❌ Requires approval |
| 7-9 | 🔴 High | ❌ Requires approval |
| 10 | 🚨 Critical | ❌ Requires approval |

## 🤖 Agent Modes

| Mode | Auto-Approve | Auto-Retry | Use Case |
|---|---|---|---|
| `SAFE` | ❌ Never | ❌ No | Production (max control) |
| `CONTROLLED` | ✅ If risk ≤3 | ❌ No | Development (balanced) |
| `AUTONOMOUS` | ✅ Always | ✅ Yes | Testing (max automation) |

Set in `.env`: `AGENT_MODE=CONTROLLED`

## 👥 RBAC Roles

| Role | Permissions |
|---|---|
| **admin** | Full access (execute, approve, monitor, configure) |
| **operator** | Execute tasks + monitor (no config changes) |
| **viewer** | Read-only (monitor, history, logs) |

Set in `.env`:
```
RBAC_ROLES=key1:admin,key2:operator,key3:viewer
```

## 📋 Task Queue Folders

```
agent-task/
├── queue/      ← Place .md or .yaml files here (processed alphabetically)
├── completed/  ← Auto-moved after execution
└── later/      ← Future tasks (promoted to queue when queue empty)
```

**YAML Task Example:**
```yaml
type: command
project: my-project
task: Build and test
command: npm run build && npm test
auto_approve: false
delay_seconds: 5
```

## 🔌 Plugin Hooks

Create `plugins/my_plugin.py`:
```python
def register(manager):
    @manager.register("before_plan")
    def on_before_plan(ctx):
        print(f"Planning: {ctx['task']}")
    
    @manager.register("after_execution")
    def on_after_execution(ctx):
        if ctx["status"] == "failed":
            print(f"Failed: {ctx['error']}")
```

**Available hooks:**
- `before_plan` — Before planner generates plan
- `after_validation` — After validator approves/rejects
- `after_execution` — After executor completes
- `on_error` — On any pipeline error

## 🚨 Troubleshooting

**Dashboard can't connect:**
- Settings → API URL = `http://127.0.0.1:8000`
- Settings → API Key = matches `.env` `API_SECRET_KEY`

**Telegram not responding:**
- Verify `TELEGRAM_TOKEN` in `.env`
- Check `ALLOWED_TELEGRAM_USER_ID` (use `/id` to get yours)

**Ollama not running:**
```bash
ollama serve  # Start Ollama
ollama list   # Verify models installed
```

**Reset memory database:**
```bash
rm logs/memory.db  # Auto-recreates on next run
```

## 📚 More Info

- Full docs: `README.md`
- Version history: `CHANGELOG.md`
- Contribution guide: `CONTRIBUTING.md`
- Dashboard guide: `dashboard/README.md`
