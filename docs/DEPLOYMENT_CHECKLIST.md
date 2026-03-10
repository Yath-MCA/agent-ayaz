# Production Deployment Checklist

## ✅ Pre-Deployment (Before First Run)

### System Requirements
- [ ] Docker Desktop installed
- [ ] 5GB free disk space available
- [ ] Internet connection (for pulling Docker images)
- [ ] Ports 9234, 9890, 9543, 9654 available (not in use)

### Files Check
- [ ] `run-production.bat` exists (Windows)
- [ ] `run-production.sh` exists (Linux/Mac)
- [ ] `.env.production` template exists
- [ ] `docker-compose-production.yml` exists
- [ ] `Dockerfile.production` exists
- [ ] `dashboard_server.py` exists
- [ ] `task_queue_system/` directory exists with Python modules

### Directory Structure
- [ ] `agent-task/` directory exists
- [ ] `agent-task/queue/` subdirectory exists
- [ ] `agent-task/completed/` subdirectory exists
- [ ] `agent-task/later/` subdirectory exists
- [ ] `logs/` directory exists
- [ ] `config/` directory exists

---

## 🚀 First Run (Deployment)

### Step 1: Verify Setup (Optional)
```bash
python verify-setup.py
```
- [ ] All checks pass

### Step 2: Start Production
```bash
# Windows
run-production.bat

# Linux/Mac
bash run-production.sh
```

### Step 3: Verify Services Running
```bash
docker-compose -f docker-compose-production.yml ps
```
- [ ] All 5 services showing as UP
- [ ] No EXITED or ERROR states
- [ ] Health checks passing (STATUS column shows healthy)

### Step 4: Access Dashboard
```
Open: http://localhost:9890
```
- [ ] Dashboard loads successfully
- [ ] Displays project selector dropdown
- [ ] Shows "Trigger Queue" button
- [ ] Real-time status visible

### Step 5: Test API Health
```bash
curl http://localhost:9234/health
```
- [ ] Returns 200 OK
- [ ] Contains service status

### Step 6: Check Monitoring
```
Open: http://localhost:9543
Login: admin / AyazDy2024!
```
- [ ] Grafana loads successfully
- [ ] Dashboards visible
- [ ] Data being collected

---

## 📝 Configuration

### .env Setup (Only if Using AI APIs)
- [ ] Copy `.env.production` to `.env` (startup script does this)
- [ ] Add OPENAI_API_KEY if using ChatGPT
- [ ] Add ANTHROPIC_API_KEY if using Claude
- [ ] Add GITHUB_TOKEN if using GitHub CLI
- [ ] Add OPENROUTER_API_KEY if using OpenRouter
- [ ] Leave OLLAMA_URL if using local Ollama

### AI Agent Validation
- [ ] At least ONE AI provider configured (or using default mock)
- [ ] Ollama running on localhost:11434 if using local
- [ ] API keys valid and have sufficient quota

---

## 🧪 Functionality Tests

### Test 1: Create Task
```bash
cat > agent-task/queue/01-test.yaml << 'EOF'
name: "Hello World"
type: "command"
timeout: 30
command: "echo Hello from Production!"
EOF
```
- [ ] File created in queue/

### Test 2: Trigger from Dashboard
```
1. Open http://localhost:9890
2. Click "Trigger Queue" button
3. Wait 10 seconds
```
- [ ] Task appears in Real-time Status
- [ ] Task moves to completed/ folder
- [ ] Status shows as "Completed"

### Test 3: REST API Task Trigger
```bash
curl -X POST http://localhost:9234/api/queue/run
```
- [ ] Returns 200 OK
- [ ] Response contains task status

### Test 4: Check Logs
```bash
docker-compose -f docker-compose-production.yml logs -f queue-api
```
- [ ] No ERROR messages
- [ ] Tasks being processed correctly
- [ ] API responding to requests

### Test 5: Verify Monitoring
```
Open: http://localhost:9543/dashboards
```
- [ ] Dashboard shows task metrics
- [ ] Graph displays task execution timeline
- [ ] Success/failure counts visible

---

## 📊 Performance Baseline

### After 10 Tasks
- [ ] Average task execution time < 5 seconds
- [ ] CPU usage < 30%
- [ ] Memory usage < 500MB
- [ ] No errors in logs

### After 100 Tasks
- [ ] System still responsive
- [ ] Dashboard updates within 5 seconds
- [ ] API response time < 1 second
- [ ] All services healthy

---

## 🔒 Security Check

- [ ] No secrets in git history
- [ ] .env file not committed
- [ ] API keys in environment variables only
- [ ] Docker network isolated
- [ ] Firewall allows only necessary ports
- [ ] All services require authentication where applicable

---

## 📦 Backup & Recovery

- [ ] Backup procedure documented
- [ ] agent-task/ folder backed up regularly
- [ ] logs/ folder monitored for size
- [ ] Prometheus data backed up weekly
- [ ] Grafana dashboards exported

---

## 🚨 Troubleshooting Guide

### Services Won't Start
```bash
# Check Docker running
docker ps

# View detailed logs
docker-compose -f docker-compose-production.yml logs

# Rebuild from scratch
docker-compose -f docker-compose-production.yml build --no-cache
docker-compose -f docker-compose-production.yml up -d
```
- [ ] Issue resolved

### Port Already in Use
```bash
# Check what's using the port
lsof -i :9890

# Kill the process or change port in docker-compose-production.yml
```
- [ ] Port conflict resolved

### Out of Memory
```bash
# Check memory limits in docker-compose-production.yml
# Increase Docker Desktop memory limit

# Or increase system RAM available
```
- [ ] Memory increased

### Logs Growing Too Large
```bash
# Check log configuration in docker-compose-production.yml
# Max size: 50MB, retention: 5 files

docker-compose -f docker-compose-production.yml logs --help
```
- [ ] Logs under control

---

## 📈 Post-Deployment

### Week 1
- [ ] Monitor dashboard daily
- [ ] Check error logs
- [ ] Verify AI agent responses quality
- [ ] Test task creation workflow
- [ ] Document any issues

### Month 1
- [ ] Monitor resource usage trends
- [ ] Verify backup strategy works
- [ ] Test disaster recovery (delete container, rebuild)
- [ ] Check if monitoring alerts are working
- [ ] Optimize task queue settings if needed

### Ongoing
- [ ] Weekly backup verification
- [ ] Monthly performance review
- [ ] Quarterly Docker image updates
- [ ] Document all customizations
- [ ] Train team on usage

---

## ✨ Success Criteria

Production deployment is successful when:

- [x] All services start automatically
- [x] Dashboard accessible and responsive
- [x] Tasks queue and execute correctly
- [x] Monitoring shows real-time data
- [x] No errors in logs (only info/debug)
- [x] AI agents responding (at least 1)
- [x] Team can create and trigger tasks
- [x] Backup strategy in place

---

## 🆘 Support

If issues occur:

1. **Check logs:** `docker-compose -f docker-compose-production.yml logs -f`
2. **Review dashboard:** http://localhost:9543 (Grafana)
3. **Check metrics:** http://localhost:9654 (Prometheus)
4. **Verify configuration:** Check .env file
5. **Restart services:** `docker-compose -f docker-compose-production.yml restart`

---

**Production Ready! 🎉**
