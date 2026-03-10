# Task Queue System - Real World Examples

## Example 1: Complete CI/CD Pipeline with Approval

### Use Case
Deploy application through multiple stages: Test → Build → Deploy to Staging → Approval → Deploy to Production

### Task Queue Setup

```yaml
# agent-task/queue/01-test.yaml
name: "Run All Tests"
description: "Execute unit tests, integration tests, and code coverage"
type: "command"
command: |
  set -e
  echo "Running unit tests..."
  pytest tests/unit/ --cov=src/ --cov-report=xml
  
  echo "Running integration tests..."
  pytest tests/integration/ -v
  
  echo "Checking code coverage..."
  coverage report --fail-under=80

timeout: 600
retry_count: 2
retry_delay: 30

notifications:
  on_failure: "test-failure"

---
# agent-task/queue/02-build.yaml
name: "Build Docker Image"
description: "Build and tag Docker image, push to registry"
type: "command"
command: |
  set -e
  export IMAGE_TAG=$(git rev-parse --short HEAD)
  export IMAGE_NAME="myapp"
  
  echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
  docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
  docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
  
  echo "Pushing to registry..."
  docker push ${IMAGE_NAME}:${IMAGE_TAG}
  docker push ${IMAGE_NAME}:latest
  
  echo "Image pushed: ${IMAGE_NAME}:${IMAGE_TAG}"

timeout: 900
dependencies:
  - "01-test.yaml"

---
# agent-task/queue/03-deploy-staging.yaml
name: "Deploy to Staging"
description: "Rolling deployment to staging environment"
type: "command"
command: |
  set -e
  export IMAGE_TAG=$(git rev-parse --short HEAD)
  
  echo "Deploying to staging..."
  kubectl set image deployment/myapp-staging \
    myapp=myapp:${IMAGE_TAG} --record -n staging
  
  echo "Waiting for rollout..."
  kubectl rollout status deployment/myapp-staging -n staging --timeout=5m
  
  echo "Running smoke tests..."
  ./tests/smoke-tests.sh https://staging.myapp.com
  
  echo "✓ Staging deployment successful"

timeout: 600
dependencies:
  - "02-build.yaml"

notifications:
  on_success: "staging-deployed"
  on_failure: "staging-deploy-failed"

---
# agent-task/queue/04-wait-approval.yaml
name: "Manual Approval - Production Deployment"
description: "Waiting for manual approval before deploying to production"
type: "command"
command: |
  echo "⚠️ WAITING FOR APPROVAL ⚠️"
  echo ""
  echo "Staging deployment successful. Ready to deploy to production?"
  echo ""
  echo "Deployment details:"
  echo "  Repository: $(git config --get remote.origin.url)"
  echo "  Commit: $(git rev-parse --short HEAD)"
  echo "  Branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "  Author: $(git log -1 --pretty=format:'%an')"
  echo "  Message: $(git log -1 --pretty=format:'%s')"
  echo ""
  echo "This task will NOT proceed without manual approval"

timeout: 3600
dependencies:
  - "03-deploy-staging.yaml"

approval:
  required: true
  approvers:
    - "platform-lead@company.com"
    - "devops-team@company.com"
  timeout: 3600
  notification: "slack"
  notification_channel: "#deployments"

---
# agent-task/queue/05-deploy-prod.yaml
name: "Deploy to Production"
description: "Blue-green deployment to production with health checks"
type: "command"
command: |
  set -e
  export IMAGE_TAG=$(git rev-parse --short HEAD)
  
  echo "🚀 PRODUCTION DEPLOYMENT"
  echo ""
  echo "Image: myapp:${IMAGE_TAG}"
  
  # Blue-green deployment
  echo "1. Updating green environment..."
  kubectl set image deployment/myapp-green \
    myapp=myapp:${IMAGE_TAG} --record -n production
  
  echo "2. Waiting for green rollout..."
  kubectl rollout status deployment/myapp-green -n production --timeout=5m
  
  echo "3. Running health checks on green..."
  ./tests/health-check.sh https://green.myapp.com
  
  echo "4. Switching load balancer to green..."
  kubectl patch service myapp-lb -p '{"spec":{"selector":{"environment":"green"}}}' -n production
  
  echo "5. Final verification..."
  sleep 10
  curl -f https://myapp.com/health || exit 1
  
  echo ""
  echo "✅ Production deployment successful!"

timeout: 1800
dependencies:
  - "04-wait-approval.yaml"

notifications:
  on_success: "prod-deployed"
  on_failure: "prod-deploy-failed-rollback"

failure_handlers:
  - condition: "exit_code != 0"
    action: "rollback"
    command: |
      echo "Deployment failed, rolling back to blue..."
      kubectl patch service myapp-lb \
        -p '{"spec":{"selector":{"environment":"blue"}}}' \
        -n production

---
# agent-task/queue/06-post-deploy-checks.yaml
name: "Post-Deployment Monitoring"
description: "Monitor application for 10 minutes after deployment"
type: "command"
command: |
  echo "Monitoring production deployment..."
  
  for i in {1..60}; do
    HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' https://myapp.com)
    ERROR_RATE=$(curl -s https://myapp.com/metrics | grep http_requests_error)
    
    echo "[$i/60] HTTP: $HTTP_CODE | Error Rate: $ERROR_RATE"
    
    if [ "$HTTP_CODE" != "200" ]; then
      echo "❌ Health check failed!"
      exit 1
    fi
    
    sleep 10
  done
  
  echo "✅ Application stable after deployment"

timeout: 900
dependencies:
  - "05-deploy-prod.yaml"
```

### Running the Pipeline

```bash
# Create all tasks
cp pipeline-example.yaml agent-task/queue/

# Run the queue
python -m task_queue_system run

# Monitor status
python -m task_queue_system status

# Check REST API
curl http://localhost:8000/api/queue/status
```

### Expected Output

```
✓ 01-test.yaml (executed) - Tests passed in 245ms
✓ 02-build.yaml (executed) - Image built and pushed in 456ms
✓ 03-deploy-staging.yaml (executed) - Deployed in 234ms
⏳ 04-wait-approval.yaml (running) - Waiting for approval...
  (manual approval given at 2:34 PM by platform-lead@company.com)
✓ 05-deploy-prod.yaml (executed) - Deployed in 567ms
✓ 06-post-deploy-checks.yaml (executed) - Monitoring passed in 678ms

Pipeline completed successfully in 5 minutes 12 seconds!
```

---

## Example 2: Multi-Agent Orchestration

### Use Case
Implement 14-phase agent architecture with planning, execution, and auditing

```yaml
# agent-task/queue/00-initialize.yaml
name: "Initialize Infrastructure"
type: "command"
command: |
  mkdir -p ./workspace/{plans,logs,reports}
  echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > ./workspace/session.env
  source ./workspace/session.env
  echo "✓ Workspace initialized: $timestamp"
timeout: 60

---
# agent-task/queue/01-planning.yaml
name: "Planning Phase - Agent Decomposition"
description: "Planner agent breaks down task into subtasks"
type: "command"
command: |
  source ./workspace/session.env
  python -m agents.planner \
    --task "Deploy microservices with zero-downtime" \
    --agents 4 \
    --parallelism 2 \
    --output "./workspace/plans/plan-$timestamp.yaml" \
    --log-level DEBUG
timeout: 600
dependencies:
  - "00-initialize.yaml"

---
# agent-task/queue/02-validator.yaml
name: "Validation Phase - Plan Review"
description: "Validator checks plan safety and compliance"
type: "command"
command: |
  source ./workspace/session.env
  python -m agents.validator \
    --plan "./workspace/plans/plan-$timestamp.yaml" \
    --strict-mode true \
    --check-security true \
    --check-resources true
timeout: 300
dependencies:
  - "01-planning.yaml"

approval:
  required: true
  approvers: ["security@company.com"]
  timeout: 1800

---
# agent-task/queue/03-execution.yaml
name: "Execution Phase - Agent Workers"
description: "Executor agents parallelize task execution"
type: "command"
command: |
  source ./workspace/session.env
  python -m agents.executor \
    --plan "./workspace/plans/plan-$timestamp.yaml" \
    --workers 4 \
    --log-dir "./workspace/logs" \
    --failure-strategy "circuit-breaker"
timeout: 1800
dependencies:
  - "02-validator.yaml"

resources:
  memory_limit_mb: 4096
  cpu_limit_cores: 4

---
# agent-task/queue/04-auditor.yaml
name: "Audit Phase - Compliance Check"
description: "Auditor reviews execution for compliance"
type: "command"
command: |
  source ./workspace/session.env
  python -m agents.auditor \
    --execution-log "./workspace/logs/execution-$timestamp.log" \
    --check-sla true \
    --check-compliance true \
    --generate-report "./workspace/reports/audit-$timestamp.md"
timeout: 600
dependencies:
  - "03-execution.yaml"

---
# agent-task/queue/05-optimizer.yaml
name: "Optimization Phase - Performance Tuning"
description: "Optimizer suggests improvements"
type: "command"
command: |
  source ./workspace/session.env
  python -m agents.optimizer \
    --execution-log "./workspace/logs/execution-$timestamp.log" \
    --metrics-file "./workspace/reports/metrics-$timestamp.json" \
    --output "./workspace/reports/optimizations-$timestamp.md"
timeout: 300
dependencies:
  - "04-auditor.yaml"

---
# agent-task/queue/06-reporter.yaml
name: "Reporting Phase - Summary"
description: "Generate final report"
type: "command"
command: |
  source ./workspace/session.env
  python -m agents.reporter \
    --audit-report "./workspace/reports/audit-$timestamp.md" \
    --optimizations "./workspace/reports/optimizations-$timestamp.md" \
    --output "./workspace/reports/final-report-$timestamp.md" \
    --notify-slack true
timeout: 300
dependencies:
  - "05-optimizer.yaml"

notifications:
  on_success: "phase-complete-success"
  on_failure: "phase-complete-failure"
```

---

## Example 3: Distributed Backup System

### Use Case
Backup multiple services across different servers

```yaml
# agent-task/queue/01-db-backup.yaml
name: "Backup MySQL Database"
type: "command"
command: |
  BACKUP_FILE="/backups/mysql/backup-$(date +%Y%m%d-%H%M%S).sql"
  
  mysqldump -u backup_user -p$BACKUP_PASSWORD \
    --all-databases \
    --single-transaction \
    > "$BACKUP_FILE"
  
  # Compress
  gzip "$BACKUP_FILE"
  
  # Upload to S3
  aws s3 cp "${BACKUP_FILE}.gz" s3://backups/mysql/
  
  echo "✓ Database backup: ${BACKUP_FILE}.gz"

timeout: 1800
retry_count: 3

---
# agent-task/queue/02-app-backup.yaml
name: "Backup Application Data"
type: "command"
command: |
  BACKUP_FILE="/backups/appdata/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
  
  tar -czf "$BACKUP_FILE" /var/app/data
  
  # Upload
  aws s3 cp "$BACKUP_FILE" s3://backups/appdata/
  
  echo "✓ Application backup: $BACKUP_FILE"

timeout: 900
dependencies:
  - "01-db-backup.yaml"

---
# agent-task/queue/03-verify-backups.yaml
name: "Verify Backup Integrity"
type: "command"
command: |
  echo "Verifying backups..."
  
  # Check DB backup
  aws s3api head-object --bucket backups --key mysql/backup-*.gz
  
  # Check app backup
  aws s3api head-object --bucket backups --key appdata/backup-*.tar.gz
  
  # Verify recent backups exist
  DB_COUNT=$(aws s3 ls s3://backups/mysql/ | wc -l)
  APP_COUNT=$(aws s3 ls s3://backups/appdata/ | wc -l)
  
  if [ "$DB_COUNT" -lt 3 ] || [ "$APP_COUNT" -lt 3 ]; then
    echo "❌ Backup count too low!"
    exit 1
  fi
  
  echo "✓ Backups verified: $DB_COUNT DB backups, $APP_COUNT app backups"

timeout: 300
dependencies:
  - "02-app-backup.yaml"

notifications:
  on_success: "daily-backup-complete"
  on_failure: "backup-failed-alert"
```

---

## Example 4: Multi-Project Deployment

### Use Case
Deploy 3 microservices with coordinated rollout

```yaml
# agent-task/queue/project-frontend/01-test.yaml
name: "[Frontend] Run Tests"
command: "cd frontend && npm test && npm run build"
timeout: 600

# agent-task/queue/project-backend/01-test.yaml
name: "[Backend] Run Tests"
command: "cd backend && python -m pytest tests/ && python -m build"
timeout: 600

# agent-task/queue/project-infra/01-validate.yaml
name: "[Infrastructure] Validate Config"
command: "cd infra && terraform validate && terraform plan"
timeout: 600

# All test in parallel...

# agent-task/queue/00-deploy-all.yaml
name: "[Orchestration] Deploy All Services"
command: |
  echo "Deploying frontend..."
  kubectl apply -f frontend/k8s/
  
  echo "Deploying backend..."
  kubectl apply -f backend/k8s/
  
  echo "Applying infrastructure changes..."
  cd infra && terraform apply -auto-approve
  
  echo "Verifying all services..."
  kubectl rollout status deployment/frontend -n prod
  kubectl rollout status deployment/backend -n prod

timeout: 1200
dependencies:
  - "project-frontend/01-test.yaml"
  - "project-backend/01-test.yaml"
  - "project-infra/01-validate.yaml"

approval:
  required: true
  approvers: ["devops@company.com"]
```

---

## Example 5: Webhook-Triggered Tasks

### Integration with GitHub

```python
# webhook_handler.py
from fastapi import FastAPI, Request
from task_queue_system import TaskQueueManager

app = FastAPI()
queue = TaskQueueManager()

@app.post("/webhook/github/push")
async def on_github_push(request: Request):
    """Triggered by GitHub push webhook"""
    payload = await request.json()
    
    if payload.get("ref") == "refs/heads/main":
        queue.add_task(
            name=f"github-push-{payload['commits'][0]['id'][:7]}",
            command=f"./ci-pipeline.sh {payload['commits'][0]['id']}"
        )
    
    return {"accepted": True}

@app.post("/webhook/slack/command")
async def on_slack_slash_command(request: Request):
    """Handle Slack /deploy command"""
    payload = await request.json()
    
    if payload["text"].startswith("deploy"):
        args = payload["text"].split()
        env = args[1] if len(args) > 1 else "staging"
        
        queue.add_task(
            name=f"slack-deploy-{env}",
            command=f"./deploy.sh {env}"
        )
    
    return {"text": f"Task queued for {env} deployment"}
```

---

## Quick Test - Run Locally

```bash
# Create simple test task
cat > agent-task/queue/00-test.yaml << 'EOF'
name: "Test Task"
type: "command"
command: |
  echo "Hello from Task Queue!"
  sleep 2
  echo "Task completed successfully"
timeout: 30
EOF

# Run
python -m task_queue_system run

# Check results
python -m task_queue_system status
```

---

See TASK_QUEUE_SYSTEM.md for more examples and patterns.

