# AyazDy Task Queue - Docker Setup & Usage Guide

## 🚀 Custom Port Configuration

All services use **7000-7999 range** to avoid conflicts with standard ports:

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Dashboard** | **9890** | http://localhost:9890 | 🌐 Web UI (Project selector, task trigger) |
| **REST API** | **9234** | http://localhost:9234 | 🔌 API endpoints |
| **Grafana** | **9543** | http://localhost:9543 | 📊 Monitoring dashboard |
| **Prometheus** | **9654** | http://localhost:9654 | 📈 Metrics database |
| **Queue Processor** | Internal | N/A | ⚙️ Task executor (no external port) |

---

## 🐳 Docker Compose Setup

### Step 1: Start All Services

```bash
# Navigate to project directory
cd /path/to/agent-ayaz

# Start all services
docker-compose -f docker-compose-queue.yml up -d

# Wait for services to start (about 30 seconds)
sleep 30

# Verify all services are running
docker-compose -f docker-compose-queue.yml ps
```

### Step 2: Access the Dashboard

**Browser:** Open http://localhost:9890

You should see:
- 🌐 Beautiful web dashboard
- 🔷 Project selector dropdown
- 📌 Queued tasks list
- ▶️ "Trigger Queue" button
- 🔄 "Refresh Status" button

### Step 3: Create a Test Task

```bash
# Create a simple test task
cat > agent-task/queue/01-hello-docker.yaml << 'EOF'
name: "Hello Docker"
type: "command"
timeout: 30
command: "echo 'Task running in Docker!' && sleep 2 && echo 'Done!'"
EOF
```

### Step 4: Trigger from Dashboard or Terminal

#### Option A: Via Web Dashboard (Recommended for GUI)
1. Open http://localhost:9890
2. Select project from dropdown
3. See "01-hello-docker.yaml" in the task list
4. Click "▶️ Trigger Queue"
5. Watch status update in real-time

#### Option B: Via Terminal (CLI)
```bash
# Run tasks via CLI
python -m task_queue_system run --path agent-task

# Or use REST API
curl -X POST http://localhost:9234/api/queue/run

# Check status
curl http://localhost:9234/api/queue/status
```

#### Option C: Via REST API
```bash
# Trigger queue execution
curl -X POST "http://localhost:9234/api/queue/run?limit=5&timeout=300"

# Get queue status
curl http://localhost:9234/api/queue/status

# Get metrics
curl http://localhost:9234/api/queue/metrics

# Get history
curl http://localhost:9234/api/queue/history?limit=20
```

---

## 📊 Access All Services

### 1. Task Queue Dashboard (Web UI)
```
👉 http://localhost:9890
   - Select projects
   - View queued tasks
   - Trigger execution
   - Monitor status
```

### 2. REST API Documentation
```
👉 http://localhost:9234/docs
   - Interactive API explorer
   - Try endpoints
   - See response formats
```

### 3. Grafana Monitoring
```
👉 http://localhost:9543
   Username: admin
   Password: AyazDy2024!
   
   - View metrics
   - Create dashboards
   - Set up alerts
```

### 4. Prometheus Metrics
```
👉 http://localhost:9654
   - Raw metrics data
   - Query interface
   - Alert configuration
```

---

## 🎯 Complete Workflow Example

### 1. Setup (First Time Only)
```bash
# Navigate to project
cd /path/to/agent-ayaz

# Start Docker Compose
docker-compose -f docker-compose-queue.yml up -d

# Wait for services
sleep 30

# Verify all running
docker-compose -f docker-compose-queue.yml ps
```

### 2. Create Task
```bash
# Option A: Simple task
cat > agent-task/queue/01-test.yaml << 'EOF'
name: "Test Task"
type: "command"
timeout: 30
command: "echo Hello from Docker!"
EOF

# Option B: Real task (with approval)
cat > agent-task/queue/02-deploy.yaml << 'EOF'
name: "Deploy App"
type: "command"
timeout: 300
command: "./deploy.sh"
approval:
  required: true
  timeout: 3600
EOF
```

### 3. Trigger Execution

**Best Method: Web Dashboard**
```
1. Open: http://localhost:9890
2. Select: Project from dropdown
3. View: Queued tasks (01-test.yaml, 02-deploy.yaml)
4. Click: ▶️ Trigger Queue
5. Watch: Real-time status updates
6. See: Tasks in Completed section after execution
```

**Alternative Method: CLI**
```bash
python -m task_queue_system run --path agent-task
```

**Alternative Method: REST API**
```bash
curl -X POST http://localhost:9234/api/queue/run
```

### 4. Monitor Results

**Dashboard:**
```
http://localhost:9890 (refresh automatically)
Shows:
- Number of queued tasks
- Number of completed tasks  
- Success rate percentage
- Individual task status
```

**Check Files:**
```bash
# View completed tasks
ls agent-task/completed/

# View task output
cat agent-task/logs/*.log
```

**View Metrics:**
```
http://localhost:9543 (Grafana)
- Task execution timeline
- Success/failure rates
- Performance metrics
```

---

## 🛑 Stop All Services

```bash
# Stop all containers
docker-compose -f docker-compose-queue.yml down

# Stop and remove volumes
docker-compose -f docker-compose-queue.yml down -v

# View logs before stopping
docker-compose -f docker-compose-queue.yml logs -f

# Stop specific service
docker-compose -f docker-compose-queue.yml stop task-queue-api
```

---

## 🔍 Troubleshooting

### Problem: Dashboard won't load (localhost:9890 refused)

**Solution:**
```bash
# Check if services are running
docker-compose -f docker-compose-queue.yml ps

# View logs
docker-compose -f docker-compose-queue.yml logs task-queue-dashboard

# Restart dashboard
docker-compose -f docker-compose-queue.yml restart task-queue-dashboard
```

### Problem: API returns "Connection refused"

**Solution:**
```bash
# Check if API container is healthy
docker ps | grep ayazdy-queue-api

# Verify API is listening on port 9234
docker-compose -f docker-compose-queue.yml logs task-queue-api

# Test API health
curl http://localhost:9234/health
```

### Problem: Tasks not moving to completed/

**Solution:**
```bash
# Check queue processor logs
docker-compose -f docker-compose-queue.yml logs task-queue-processor

# Verify queue folder permissions
ls -la agent-task/

# Check task file format
cat agent-task/queue/01-hello.yaml

# Manually trigger
python -m task_queue_system run --path agent-task
```

### Problem: Port already in use

**Solution:**
```bash
# Check which process is using the port
lsof -i :9890  # Check dashboard port
lsof -i :9234  # Check API port
lsof -i :9543  # Check Grafana port

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
# Change "9890:9890" to "7891:9890" for example
```

---

## 📋 Dashboard Features Explained

### Project Selector
- **Dropdown menu** at top
- Shows all projects with queued tasks
- Default: Shows root-level tasks

### Task Display
- **Multi-select list** showing:
  - Task filenames (e.g., "01-hello.yaml")
  - All queued tasks in current project
  - Sorted alphabetically (execution order)

### Execution Controls
- **▶️ Trigger Queue** - Start execution
- **🔄 Refresh Status** - Update metrics
- **Max Tasks** - Optional limit on how many to run

### Status Display
- **Real-time updates** every 5 seconds
- Shows:
  - Number of queued tasks
  - Number of completed tasks
  - Deferred tasks count
  - Success rate percentage
- Individual task status after execution

---

## 🔌 API Endpoints (All on port 9234)

```bash
# Get current queue status
GET http://localhost:9234/api/queue/status

# Run all queued tasks
POST http://localhost:9234/api/queue/run
    ?limit=5
    &timeout=300

# Add a new task
POST http://localhost:9234/api/queue/tasks
    -H "Content-Type: application/json"
    -d '{"name": "task-name", "command": "echo test", "timeout": 30}'

# Get queue metrics
GET http://localhost:9234/api/queue/metrics

# Get task history
GET http://localhost:9234/api/queue/history?days=30&limit=100

# Promote deferred tasks
POST http://localhost:9234/api/queue/promote

# Health check
GET http://localhost:9234/health
```

---

## 📊 Multi-Project Support

### Structure
```
agent-task/
├── queue/
│   ├── 01-shared-task.yaml
│   ├── project-a/
│   │   ├── 01-test.yaml
│   │   └── 02-deploy.yaml
│   ├── project-b/
│   │   ├── 01-build.yaml
│   │   └── 02-deploy.yaml
│   └── project-c/
│       └── 01-backup.yaml
├── completed/
│   ├── 01-shared-task.yaml
│   ├── project-a/
│   ├── project-b/
│   └── project-c/
└── later/
```

### Select from Dashboard
1. Open http://localhost:9890
2. Click project dropdown
3. Select: "default", "project-a", "project-b", etc.
4. See only that project's tasks
5. Trigger execution for selected project

---

## 🎯 Common Workflows

### Workflow 1: Quick Test
```bash
# 1. Start services
docker-compose -f docker-compose-queue.yml up -d && sleep 30

# 2. Create task
echo 'name: "Quick Test"
type: "command"
timeout: 30
command: "echo Hello"' > agent-task/queue/01-quick.yaml

# 3. Open dashboard
# http://localhost:9890

# 4. Click Trigger Queue
# Done! Task executed and moved to completed/
```

### Workflow 2: CI/CD Integration
```bash
# 1. Start services (once)
docker-compose -f docker-compose-queue.yml up -d

# 2. GitHub Actions or webhook creates task:
echo 'name: "Deploy"
type: "command"
timeout: 600
command: "./deploy.sh"' > agent-task/queue/03-deploy.yaml

# 3. Dashboard automatically shows new task
# 4. Click Trigger Queue or use REST API
# 5. Task executes, result logged, moved to completed/
```

### Workflow 3: Scheduled Tasks
```bash
# Use cron to create tasks periodically
# /etc/cron.d/queue-tasks
# 0 2 * * * echo "name: daily-backup..." > agent-task/queue/99-backup.yaml
# 5 2 * * * curl -X POST http://localhost:9234/api/queue/run
```

---

## 🎓 Tips & Best Practices

1. **Task Naming**: Use prefixes (01-, 02-, 03-) for sequential execution
2. **Dashboard**: Best for manual/ad-hoc task triggering
3. **REST API**: Best for automation and integrations
4. **CLI**: Best for development and debugging
5. **Monitoring**: Use Grafana for long-term metrics
6. **Logs**: Check `docker-compose logs` for troubleshooting

---

## 📞 Quick Reference

| Need | Do This |
|------|---------|
| Start services | `docker-compose -f docker-compose-queue.yml up -d` |
| Stop services | `docker-compose -f docker-compose-queue.yml down` |
| View logs | `docker-compose -f docker-compose-queue.yml logs -f` |
| Access dashboard | http://localhost:9890 |
| Access API | http://localhost:9234 |
| Check Grafana | http://localhost:9543 (admin/AyazDy2024!) |
| Create task | `echo '...' > agent-task/queue/01-task.yaml` |
| Run tasks (CLI) | `python -m task_queue_system run` |
| Run tasks (API) | `curl -X POST http://localhost:9234/api/queue/run` |
| View completed | `ls agent-task/completed/` |
| Check status | `curl http://localhost:9234/api/queue/status` |

---

**You're all set! Open http://localhost:9890 and start managing tasks!** 🎉
