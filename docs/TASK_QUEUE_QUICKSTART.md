# Task Queue System - Quick Start Guide

## 🚀 Quick Start

### 1. Standalone (Local)

```bash
# Initialize
python -m task_queue_system init

# Create a task
cat > agent-task/queue/01-test.yaml << 'EOF'
name: "Hello World"
type: "command"
timeout: 30
command: |
  echo "Task started"
  sleep 2
  echo "Task completed"
EOF

# Run
python -m task_queue_system run

# Check status
python -m task_queue_system status
```

### 2. Docker (Single Container)

```bash
# Build
docker build -f Dockerfile.queue -t task-queue:latest .

# Run
docker run -v $(pwd)/agent-task:/queue-data task-queue:latest

# Check status
docker exec $(docker ps -q -f "ancestor=task-queue:latest") \
  python -m task_queue_system status --path /queue-data
```

### 3. Docker Compose (Full Stack)

```bash
# Start
docker-compose -f docker-compose-queue.yml up -d

# Monitor logs
docker-compose -f docker-compose-queue.yml logs -f task-queue

# Stop
docker-compose -f docker-compose-queue.yml down
```

### 4. REST API

```bash
# Get status
curl http://localhost:8000/api/queue/status

# Add task
curl -X POST http://localhost:8000/api/queue/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-task",
    "command": "echo hello",
    "timeout": 30,
    "priority": 1
  }'

# Run queue
curl -X POST http://localhost:8000/api/queue/run \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "timeout": 60}'

# Get metrics
curl http://localhost:8000/api/queue/metrics
```

## 📋 Task Format

### Simple Command Task

```yaml
name: "Deploy App"
type: "command"
command: |
  docker build -t myapp .
  docker run -d myapp
timeout: 300
```

### Task File Reference

```yaml
name: "Run Script"
type: "task_file"
task_file: "./deploy.sh"
timeout: 600
```

### With Approval

```yaml
name: "Production Deploy"
type: "command"
command: "./deploy-prod.sh"
approval:
  required: true
  timeout: 3600
```

### With Dependencies

```yaml
name: "Deploy Phase 3"
type: "command"
command: "./phase-3.sh"
dependencies:
  - "01-phase-1.yaml"
  - "02-phase-2.yaml"
```

## 🔧 Configuration

Edit `config/queue.yaml`:

```yaml
queue:
  root: ./agent-task
  max_tasks_per_run: 10
  task_timeout: 300

policy:
  strict_mode: false
  require_approval: true
  allowed_commands: ["docker", "kubectl"]

notifications:
  enabled: true
  handlers:
    - type: "slack"
      webhook_url: "${SLACK_WEBHOOK_URL}"
```

## 📊 Monitoring

### CLI Status

```bash
python -m task_queue_system status
python -m task_queue_system metrics
```

### Docker Logs

```bash
docker-compose logs -f task-queue
docker-compose logs task-queue --tail 100
```

### REST API

```bash
# Queue status
curl http://localhost:8000/api/queue/status

# Metrics
curl http://localhost:8000/api/queue/metrics

# History
curl http://localhost:8000/api/queue/history?limit=20
```

## 🐳 Multi-Machine Setup

### Shared NFS Queue

```bash
# Mount shared queue
mount -t nfs nfs-server:/queue /mnt/queue

# Run on Machine 1
docker run -v /mnt/queue:/queue-data \
  -e WORKER_ID=machine-1 \
  task-queue:latest

# Run on Machine 2
docker run -v /mnt/queue:/queue-data \
  -e WORKER_ID=machine-2 \
  task-queue:latest
```

### Docker Swarm

```bash
# Deploy service
docker service create \
  --name task-queue \
  --mount type=bind,source=/mnt/queue,destination=/queue-data \
  task-queue:latest

# Check status
docker service logs task-queue -f
```

### Kubernetes

```bash
kubectl apply -f k8s/task-queue-deployment.yaml
kubectl logs -f deploy/task-queue
```

## 🎯 Common Patterns

### CI/CD Pipeline

1. Create task on push: `01-test.yaml`, `02-build.yaml`, `03-deploy.yaml`
2. Run: `python -m task_queue_system run`
3. Check: `curl http://localhost:8000/api/queue/status`

### Scheduled Tasks

```bash
# Cron job - add tasks daily
0 2 * * * echo "name: daily-backup" > /path/to/queue/99-backup.yaml
```

### Event-Driven Tasks

```bash
# Webhook handler
curl -X POST http://localhost:8000/api/queue/tasks \
  -d '{"name": "webhook-event", "command": "./handle-event.sh"}'
```

## 🔍 Troubleshooting

### Task Stuck in Queue

```bash
# Check permissions
ls -la agent-task/queue/

# Check logs
tail -f logs/task-queue.log

# Move to later/ for review
mv agent-task/queue/stuck-task.yaml agent-task/later/
```

### High Memory Usage

```yaml
resources:
  memory_limit_mb: 1024
  max_tasks_per_run: 5
```

### Docker Won't Start

```bash
# Check permissions
sudo chown -R $(whoami):$(whoami) agent-task

# Check volume mount
docker run -it -v $(pwd)/agent-task:/queue-data ubuntu ls -la /queue-data

# Check logs
docker-compose logs task-queue
```

## 📚 Documentation

- **Full Guide**: `TASK_QUEUE_SYSTEM.md`
- **API Reference**: `REST API` section
- **Configuration**: `config/queue.yaml`
- **Examples**: `examples/` directory

