# Task Queue System - Standalone & Multi-Project

A production-ready, reusable task queue system that works standalone or integrated with Docker, agents, and multiple projects.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Standalone Mode](#standalone-mode)
4. [Docker Integration](#docker-integration)
5. [Multi-Project Setup](#multi-project-setup)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Suggestions & Best Practices](#suggestions--best-practices)

---

## Architecture Overview

### Design Philosophy

- **File-based task queue** - No database required, works on any filesystem
- **Stateless processing** - Tasks move through folders (queue → completed → later)
- **Multi-format support** - YAML DSL, shell scripts, Python, PowerShell, markdown
- **Docker-ready** - Containerized runner that works across environments
- **Agent-compatible** - Integrates with multi-agent systems
- **Distributed** - Can run on multiple machines pointing to same queue folder (via NFS/SMB)

### Folder Structure

```
task-queue-root/
├── queue/          # Tasks to process now (alphabetically ordered for sequential execution)
├── completed/      # Successfully processed tasks (auto-archived with timestamps)
├── later/          # Deferred tasks (promoted to queue when queue is empty)
├── config/         # Queue configuration
├── logs/           # Execution logs
└── reports/        # Summary reports and analytics
```

### Task Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Lifecycle                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. USER CREATES TASK                                       │
│     └→ places in queue/ folder                              │
│                                                              │
│  2. QUEUE MONITOR detects task                              │
│     └→ validates against policy/permissions                │
│                                                              │
│  3. EXECUTOR processes task                                │
│     ├─ YAML DSL → parses & executes                        │
│     ├─ Script files → runs directly                        │
│     └─ Markdown → marks as completed (planning only)       │
│                                                              │
│  4. RESULT captured                                         │
│     ├─ Output logged to logs/                              │
│     ├─ Exit code recorded                                  │
│     └─ Duration tracked                                    │
│                                                              │
│  5. TASK MOVED to completed/                               │
│     └─ with timestamp suffix for collision avoidance       │
│                                                              │
│  6. LATER PROMOTION (when queue empty)                     │
│     └→ admin prompted to move from later/ to queue/        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Task Queue Service (`task_queue_service.py`)

Main service managing queue lifecycle.

**Key Functions:**

```python
# Queue status
queue_status() → dict
  ├─ queue: [list of task files]
  ├─ later: [list of deferred tasks]
  ├─ completed: [list of processed tasks]
  ├─ queue_empty: bool
  └─ later_available: bool

# Processing
run_queue(
  timeout_seconds=60,
  task_timeout_seconds=120,
  max_output_chars=3000,
  strict_mode=False,
  allowed_prefixes=None
) → list[TaskResult]

# Deferral
promote_later_to_queue() → list[str]  # Move from later/ to queue/
```

**Supported File Types:**

| Extension | Type | Behavior |
|-----------|------|----------|
| `.yaml`, `.yml` | YAML DSL | Parsed and executed via Task DSL |
| `.ps1`, `.bat`, `.cmd` | PowerShell/CMD | Executed directly |
| `.py` | Python | Executed with Python interpreter |
| `.sh` | Shell Script | Executed with shell |
| `.md`, `.txt` | Markdown/Text | Marked completed (planning only) |

### 2. Task Result Model

```python
@dataclass
class TaskResult:
    name: str               # Task filename
    status: str             # "executed" | "planned" | "skipped" | "failed"
    output: Optional[str]   # Captured output (max 3000 chars)
    exit_code: Optional[int]# Exit/return code
    duration_ms: Optional[int]  # Execution time
    moved_to: str           # Path where task was moved
```

### 3. Task DSL (`agents/task_dsl.py`)

YAML-based task definition language for complex workflows.

**Example Task DSL:**

```yaml
name: "Deploy Application"
description: "Full deployment workflow"
type: "command"  # or "task_file"

command: |
  docker build -t myapp:latest .
  docker push myapp:latest
  docker pull myapp:latest
  docker run -d myapp:latest

timeout: 300
retry_count: 3
retry_delay: 30

approval:
  required: true
  approvers:
    - admin@example.com

notifications:
  on_success: "deployment-success"
  on_failure: "deployment-failure"

dependencies:
  - build-task.yaml
  - test-task.yaml
```

### 4. Execution Service (`services/execution_service.py`)

Executes tasks with timeout, output capture, and error handling.

---

## Standalone Mode

### Installation

```bash
# Clone or copy the queue system
git clone <repo> task-queue-system
cd task-queue-system

# Install dependencies
pip install -r requirements.txt

# Create queue directories
python -m task_queue_system init
```

### Quick Start

```bash
# 1. Create a task
cat > agent-task/queue/01-hello.yaml << 'EOF'
name: "Hello World"
type: "command"
command: "echo 'Hello from task queue!'"
timeout: 30
EOF

# 2. Run the queue
python -m task_queue_system run

# 3. Check status
python -m task_queue_system status
```

### Command Line Interface

```bash
# Initialize queue directories
python -m task_queue_system init [--path /custom/path]

# Run all queued tasks
python -m task_queue_system run [--timeout 60] [--strict]

# Check queue status
python -m task_queue_system status

# Promote deferred tasks
python -m task_queue_system promote-later

# Get queue metrics
python -m task_queue_system metrics

# Clean old completed tasks
python -m task_queue_system cleanup --older-than 30d

# Archive completed tasks
python -m task_queue_system archive
```

### REST API (with FastAPI wrapper)

```python
from fastapi import FastAPI
from task_queue_system import TaskQueueAPI

app = FastAPI()
task_api = TaskQueueAPI(queue_root="agent-task")

# Mount API endpoints
app.include_router(task_api.router, prefix="/api/queue")

# Endpoints:
# GET    /api/queue/status       - Queue status
# POST   /api/queue/run          - Run queue
# GET    /api/queue/history      - Completed tasks
# POST   /api/queue/promote      - Promote from later/
# GET    /api/queue/metrics      - Queue metrics
```

---

## Docker Integration

### Standalone Queue Container

**Dockerfile.queue**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy queue system
COPY task_queue_system/ ./task_queue_system/

# Volume for queue data
VOLUME ["/queue-data"]

# Default command
CMD ["python", "-m", "task_queue_system", "run", "--path", "/queue-data"]
```

**docker-compose.yml**

```yaml
version: '3.9'

services:
  task-queue:
    build:
      context: .
      dockerfile: Dockerfile.queue
    volumes:
      - ./agent-task:/queue-data
      - ./logs:/queue-data/logs
    environment:
      - QUEUE_TIMEOUT=120
      - TASK_TIMEOUT=300
      - STRICT_MODE=false
    restart: unless-stopped

  queue-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./agent-task:/app/agent-task
    environment:
      - QUEUE_PATH=/app/agent-task
    depends_on:
      - task-queue
    restart: unless-stopped
```

### Running with Docker

```bash
# Build
docker build -f Dockerfile.queue -t task-queue:latest .

# Run
docker run -v $(pwd)/agent-task:/queue-data task-queue:latest

# With docker-compose
docker-compose up -d

# View logs
docker-compose logs -f task-queue

# Run one-off task
docker run -v $(pwd)/agent-task:/queue-data task-queue:latest \
  python -m task_queue_system run --path /queue-data --limit 1
```

---

## Multi-Project Setup

### Shared Queue Architecture

For teams using same queue system across multiple projects:

```
shared-task-queue/
├── docker-compose.yml       # Central queue service
├── queue/                   # Shared queue folder
│   ├── project-a/
│   ├── project-b/
│   └── project-c/
├── completed/
│   ├── project-a/
│   ├── project-b/
│   └── project-c/
└── config/
    ├── permissions.yaml     # RBAC rules per project
    └── quotas.yaml          # Resource limits per project
```

### Project-Specific Queue

Each project can maintain its own queue:

```
project-a/
├── queue.yaml              # Queue configuration
├── agent-task/
│   ├── queue/
│   ├── completed/
│   └── later/
└── integrations/
    └── task-queue-webhook.py
```

### Configuration Example

**queue.yaml**

```yaml
# Queue System Configuration
queue:
  root: ./agent-task
  max_tasks_per_run: 10
  task_timeout: 300
  inter_task_delay: 5

policy:
  strict_mode: true
  require_approval: true
  allowed_commands:
    - "docker"
    - "kubectl"
    - "terraform"
  blocked_commands:
    - "rm"
    - "del"

notifications:
  enabled: true
  handlers:
    - type: "email"
      recipients: ["ops@example.com"]
    - type: "slack"
      webhook: "https://hooks.slack.com/..."
    - type: "telegram"
      token: "${TELEGRAM_TOKEN}"

monitoring:
  enabled: true
  metrics_endpoint: "http://prometheus:9090"
  log_level: "INFO"

cleanup:
  completed_retention_days: 30
  auto_archive_after_days: 15
```

### Integration with Projects

**Python Project Integration**

```python
from task_queue_system import TaskQueueManager

# In your project
queue = TaskQueueManager(queue_root="./agent-task")

# Submit a task
queue.add_task(
    name="deploy",
    task_type="command",
    command="python deploy.py --env=prod"
)

# Monitor
status = queue.status()
print(f"Queued: {len(status['queue'])}, Completed: {len(status['completed'])}")

# Wait for completion
result = queue.wait_for_task("deploy", timeout=300)
if result.status == "executed":
    print("Deployment successful!")
else:
    print(f"Deployment failed: {result.output}")
```

**Webhook Integration**

```python
from fastapi import FastAPI, HTTPException
from task_queue_system import TaskQueueAPI

app = FastAPI()
queue_api = TaskQueueAPI()

@app.post("/webhook/github-push")
async def github_push(event: dict):
    """Auto-queue deployment on GitHub push"""
    if event.get("ref") == "refs/heads/main":
        queue_api.add_task_from_dict({
            "name": f"deploy-{event['head_commit']['id'][:7]}",
            "type": "command",
            "command": f"./deploy.sh {event['head_commit']['id']}"
        })
        return {"status": "queued"}
    raise HTTPException(400, "Not main branch")

@app.post("/webhook/scheduled")
async def scheduled_task():
    """Cron-triggered task submission"""
    queue_api.add_task_from_dict({
        "name": "daily-backup",
        "type": "command",
        "command": "backup.sh"
    })
    return {"status": "queued"}
```

---

## API Reference

### Python API

```python
# Initialize
from task_queue_system import TaskQueueManager

queue = TaskQueueManager(
    queue_root="./agent-task",
    strict_mode=False,
    max_output_chars=3000
)

# Submit task
task_id = queue.add_task(
    name="task-name",
    task_type="command",  # or "task_file"
    command="docker build .",
    timeout=300,
    priority=1
)

# Status
status = queue.status()
# {
#   'queue': [...],
#   'completed': [...],
#   'later': [...],
#   'queue_empty': False,
#   'later_available': True
# }

# Run queue
results = queue.run_queue(timeout_seconds=60)
# [TaskResult(...), TaskResult(...), ...]

# Wait for task
result = queue.wait_for_task(
    task_name="task-name",
    timeout=300,
    poll_interval=5
)

# History
history = queue.get_completed_tasks(
    project="project-a",
    limit=100,
    days=30
)

# Metrics
metrics = queue.get_metrics()
# {
#   'total_tasks': 100,
#   'success_rate': 0.95,
#   'avg_duration_ms': 5000,
#   'failure_reasons': {...}
# }
```

### REST API

```
# Status
GET /api/queue/status
Response: {
  "queue": [...],
  "completed": [...],
  "later": [...],
  "queue_empty": false,
  "later_available": true
}

# Run queue
POST /api/queue/run
Body: {
  "limit": 5,
  "timeout": 300,
  "strict_mode": false
}
Response: [TaskResult, ...]

# Add task
POST /api/queue/tasks
Body: {
  "name": "task-name",
  "type": "command",
  "command": "echo hello"
}
Response: {
  "task_id": "uuid",
  "status": "queued"
}

# Get task result
GET /api/queue/tasks/{task_id}
Response: TaskResult

# Metrics
GET /api/queue/metrics
Response: {
  "total": 100,
  "success_rate": 0.95,
  "avg_duration_ms": 5000
}

# History
GET /api/queue/history?days=30&limit=100
Response: [TaskResult, ...]

# Promote later tasks
POST /api/queue/promote
Response: {
  "moved": ["task1", "task2"],
  "count": 2
}
```

---

## Usage Examples

### Example 1: CI/CD Pipeline

```yaml
# agent-task/queue/01-test.yaml
name: "Run Tests"
type: "command"
command: |
  pytest tests/ --cov=src/
  coverage report
timeout: 300
---
# agent-task/queue/02-build.yaml
name: "Build Docker Image"
type: "command"
command: |
  docker build -t myapp:latest .
  docker tag myapp:latest myapp:prod
timeout: 600
dependencies:
  - "01-test.yaml"
---
# agent-task/queue/03-deploy.yaml
name: "Deploy to Production"
type: "command"
command: |
  docker push myapp:prod
  kubectl set image deployment/myapp myapp=myapp:prod
timeout: 900
dependencies:
  - "02-build.yaml"
approval:
  required: true
  approvers:
    - devops@example.com
```

**Run:**
```bash
python -m task_queue_system run --timeout 1800
```

### Example 2: Multi-Agent Orchestration

```yaml
# agent-task/queue/planner.yaml
name: "Planning Phase"
type: "command"
command: |
  python -m agents.planner \
    --task "Deploy new feature" \
    --resources "2 agents" \
    --timeline "2 hours"
timeout: 300
---
# agent-task/queue/executor.yaml
name: "Execution Phase"
type: "command"
command: |
  python -m agents.executor \
    --plan ./plans/latest.yaml
timeout: 600
dependencies:
  - "planner.yaml"
approval:
  required: true
---
# agent-task/queue/auditor.yaml
name: "Audit Phase"
type: "command"
command: |
  python -m agents.auditor \
    --execution-log ./logs/latest.log
timeout: 300
dependencies:
  - "executor.yaml"
notifications:
  on_success: "audit-pass"
  on_failure: "audit-fail"
```

### Example 3: Distributed Queue (NFS)

```bash
# Setup on shared NFS
mkdir -p /mnt/shared-queue/{queue,completed,later,logs}
chmod 777 /mnt/shared-queue

# Mount on multiple machines
sudo mount -t nfs nfs-server:/export/queue /mnt/shared-queue

# Run queue service on each machine
# (they all watch the same queue folder)
python -m task_queue_system run --path /mnt/shared-queue --worker-id machine-1

python -m task_queue_system run --path /mnt/shared-queue --worker-id machine-2
```

### Example 4: Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: task-queue-runner
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: queue-runner
            image: task-queue:latest
            volumeMounts:
            - name: queue-data
              mountPath: /queue-data
            env:
            - name: QUEUE_PATH
              value: /queue-data
            - name: TASK_TIMEOUT
              value: "300"
          volumes:
          - name: queue-data
            persistentVolumeClaim:
              claimName: queue-pvc
          restartPolicy: OnFailure
```

---

## Suggestions & Best Practices

### 1. Task Naming Convention

```
<priority>-<component>-<action>.yaml

Examples:
01-database-migration.yaml
02-app-deploy.yaml
03-smoke-tests.yaml
10-cleanup-old-logs.yaml
99-post-deployment-check.yaml

Benefits:
- Alphabetical sorting = execution order
- Easy to identify priority
- Clear component and action
```

### 2. Approval Workflow

```yaml
name: "Production Deployment"
type: "command"
command: "./deploy-prod.sh"

approval:
  required: true
  approvers:
    - "devops@company.com"
    - "platform-lead@company.com"
  timeout: 3600  # Approval window
  notification: "slack"
```

### 3. Error Handling & Retry

```yaml
name: "Deploy with Retries"
type: "command"
command: "./deploy.sh"

retry:
  enabled: true
  max_attempts: 3
  delay_seconds: 30
  backoff_multiplier: 2.0

failure_handlers:
  - condition: "exit_code == 1"
    action: "rollback"
    command: "./rollback.sh"
```

### 4. Logging & Monitoring

```yaml
name: "Task with Enhanced Logging"
type: "command"
command: "./task.sh"

logging:
  level: "DEBUG"
  output: "logs/task-$(date +%s).log"
  compress_after: "30d"

monitoring:
  metrics:
    - "task_duration_ms"
    - "task_status"
  alerts:
    - condition: "duration > 600"
      action: "notify-ops"
```

### 5. Resource Limits

```yaml
name: "Resource-Limited Task"
type: "command"
command: "./heavy-computation.py"

resources:
  memory_limit_mb: 2048
  cpu_limit_cores: 2
  disk_quota_gb: 10
  timeout_seconds: 1800

# In config.yaml, set per-project quotas:
quotas:
  project-a:
    daily_tasks: 100
    concurrent: 5
    max_memory_mb: 8192
  project-b:
    daily_tasks: 50
    concurrent: 2
    max_memory_mb: 4096
```

### 6. Task Dependencies & Workflows

```yaml
name: "Complete Workflow"

tasks:
  - id: build
    command: "./build.sh"
    timeout: 600

  - id: test
    command: "./test.sh"
    depends_on: [build]
    timeout: 600

  - id: deploy-staging
    command: "./deploy-staging.sh"
    depends_on: [test]
    timeout: 300

  - id: smoke-tests
    command: "./smoke-tests.sh"
    depends_on: [deploy-staging]
    timeout: 300

  - id: deploy-prod
    command: "./deploy-prod.sh"
    depends_on: [smoke-tests]
    approval:
      required: true
    timeout: 600

  - id: post-deploy
    command: "./post-deploy-checks.sh"
    depends_on: [deploy-prod]
    timeout: 300
```

### 7. Monitoring Dashboard

**Suggested Metrics:**

- Queue depth (active tasks waiting)
- Throughput (tasks/hour)
- Success rate (%)
- Average duration (ms)
- Most common failures
- Resource utilization per task
- SLA compliance (on-time completion)

**Example Dashboard (Grafana):**

```
┌─────────────────────────────────────────────┐
│ Task Queue System Dashboard                 │
├─────────────────────────────────────────────┤
│ Queue Status: 5 pending | 143 completed     │
│ Success Rate: 94.2% | Avg Duration: 5.2s   │
│                                             │
│ ┌─────────────────────────────────────┐   │
│ │ Task Throughput (last 24h)          │   │
│ │ ████████████░░░░░░░░░░░░░░░░░░░░░░│   │
│ │ 42 tasks/hour                       │   │
│ └─────────────────────────────────────┘   │
│                                             │
│ Recent Failures:                            │
│ - deploy-prod (timeout, 2h ago)           │
│ - backup-db (permission denied, 1h ago)   │
│                                             │
│ Project Quotas:                             │
│ - project-a: 85/100 daily tasks            │
│ - project-b: 42/50 daily tasks             │
│ - project-c: 12/20 daily tasks             │
└─────────────────────────────────────────────┘
```

### 8. Security Best Practices

```yaml
# 1. Command Whitelisting
allowed_commands:
  - "docker"
  - "kubectl"
  - "terraform"
  - "ansible"

blocked_patterns:
  - "rm -rf"
  - "del /s"
  - "; rm"
  - "| rm"

# 2. Approval for Sensitive Tasks
approval:
  required: true
  for_commands: ["delete", "destroy", "drop"]

# 3. Audit Logging
audit:
  enabled: true
  log_all_commands: true
  log_output: true
  retention_days: 90

# 4. RBAC
rbac:
  enabled: true
  roles:
    admin:
      can_run: ["*"]
      can_approve: ["*"]
    developer:
      can_run: ["deploy-staging"]
      can_approve: []
    operator:
      can_run: ["deploy-prod", "backup"]
      can_approve: ["deploy-prod"]
```

### 9. Scaling Considerations

**Single Machine (< 100 tasks/day):**
- File-based queue is sufficient
- No distributed locking needed

**Multiple Machines (100-10k tasks/day):**
- Use NFS/SMB for shared queue folder
- Implement distributed lock mechanism
- Add worker ID tracking
- Monitor for race conditions

**Large Scale (> 10k tasks/day):**
- Consider message queue (RabbitMQ, Redis)
- Distributed database for task state
- Separate queue/worker services
- Horizontal auto-scaling

### 10. Integration Patterns

**Pattern 1: GitHub Actions → Task Queue**
```yaml
# .github/workflows/queue-dispatch.yml
on: [push, pull_request]
jobs:
  queue-task:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Submit to Queue
        run: |
          curl -X POST http://queue-api:8000/api/queue/tasks \
            -H "Content-Type: application/json" \
            -d '{
              "name": "github-"${{ github.event_name }},
              "type": "command",
              "command": "./ci-pipeline.sh"
            }'
```

**Pattern 2: Scheduled (Cron) → Task Queue**
```bash
# /etc/cron.d/queue-tasks
0 2 * * * /usr/local/bin/queue-submit.sh daily-backup
0 */4 * * * /usr/local/bin/queue-submit.sh health-check
```

**Pattern 3: Webhook (GitLab/GitHub) → Task Queue**
```python
@app.post("/webhook/merge-request")
async def on_merge_request(event: dict):
    if event["action"] == "opened":
        queue.add_task(
            name=f"review-{event['id']}",
            command=f"code-review {event['url']}"
        )
    return {"accepted": True}
```

---

## Troubleshooting

### Task Stuck in Queue

```bash
# Check logs
tail -f logs/task-queue.log

# Verify task format
cat agent-task/queue/stuck-task.yaml

# Check if task requires approval
grep -A 5 "approval:" agent-task/queue/stuck-task.yaml

# Move to later/ for review
mv agent-task/queue/stuck-task.yaml agent-task/later/
```

### High Memory Usage

```yaml
# Limit output capture
max_output_chars: 1000  # Default 3000

# Set process memory limits
resources:
  memory_limit_mb: 1024

# Run fewer tasks per batch
max_tasks_per_run: 5
```

### Distributed Lock Issues

```python
# If using NFS with multiple workers, ensure flock is available
# Check: https://www.kernel.org/doc/html/latest/filesystems/nfs/nfs.html#file-locking

# Alternative: Use Redis for distributed locking
from redis import Redis
lock = Redis().lock("queue-processing", timeout=300)
```

---

## Files Reference

### Core System
- `task_queue_system/__init__.py` - Main package
- `task_queue_system/core.py` - TaskQueueManager
- `task_queue_system/executor.py` - Task execution engine
- `task_queue_system/models.py` - Data models (TaskResult, etc.)
- `task_queue_system/api.py` - FastAPI integration
- `task_queue_system/cli.py` - Command-line interface

### Integrations
- `task_queue_system/integrations/docker.py` - Docker support
- `task_queue_system/integrations/kubernetes.py` - K8s integration
- `task_queue_system/integrations/github_actions.py` - GitHub Actions
- `task_queue_system/integrations/webhooks.py` - Generic webhooks

### Configuration
- `config/queue.yaml` - Queue configuration template
- `config/permissions.yaml` - RBAC rules
- `config/quotas.yaml` - Resource limits

### Docker
- `Dockerfile.queue` - Queue runner image
- `docker-compose.yml` - Full stack
- `.dockerignore` - Optimization

---

## Next Steps

1. **Deploy standalone** - Test locally with simple tasks
2. **Add Docker** - Build and run container
3. **Integrate with project** - Connect to your CI/CD pipeline
4. **Setup monitoring** - Add Prometheus/Grafana metrics
5. **Scale** - Deploy to multiple machines if needed
6. **Extend** - Add custom task types and handlers

