# AgentAyazDaddy – Workflow Refactor & CLI Task Runner

You are a senior systems engineer improving an existing developer automation ecosystem.

The ecosystem already exists and contains:

- Local AI models (Ollama)
- Internal Bot services
- Internal API services
- Multiple local project repositories
- Basic automation scripts

Your task is NOT to build from scratch.

Your task is to:

1. Analyze the existing workflow
2. Refactor architecture
3. Introduce a CLI task runner
4. Connect to dashboard and API
5. Improve reliability and automation

Agent Name: AgentAyazDaddy

---

# Step 1 — Analyze Existing Ecosystem

First inspect the current system.

Identify:

- Existing scripts
- Bot triggers
- API endpoints
- Automation workflows
- Project paths
- Scheduling mechanisms

Produce a report:

Existing Capabilities
Missing Capabilities
Performance Bottlenecks
Architecture Issues

Do NOT remove working functionality.

Refactor only where necessary.

---

# Step 2 — Introduce CLI Control Layer

Add a CLI interface that becomes the main entry point.

Example commands:

agent run <task>
agent queue
agent projects
agent schedule
agent logs
agent status
agent analyze

Example:

agent run html-compare
agent run deploy
agent queue

The CLI should provide a simplified terminal UI.

Use colorized output and progress indicators.

---

# Step 3 — Convert Scripts into Task Modules

Existing scripts should be converted into structured tasks.

Example:

tasks/
    htmlCompare.task.js
    deploy.task.js
    buildDocs.task.js

Each task must include:

name
project
execution method
timeout
retry count

Example:

{
  "task": "htmlCompare",
  "project": "impact",
  "type": "python",
  "script": "compare_html.py"
}

---

# Step 4 — Implement Task Queue

Tasks must run sequentially.

Rules:

1 task at a time
queue based execution
interval between tasks
retry on failure

Queue Flow:

User → Queue → Worker → Execute → Report → Next Task

Prevent parallel execution unless explicitly enabled.

---

# Step 5 — Project Configuration

Create a central config file.

config/projects.json

Example:

{
  "projects":[
    {
      "name":"impact",
      "path":"/projects/impact",
      "tasks":[
        "build",
        "deploy",
        "compare-html"
      ]
    }
  ]
}

CLI must load projects dynamically.

---

# Step 6 — Workflow Verification Layer

Before running tasks verify:

Project exists
Script exists
Dependencies available
Environment ready

Example CLI output:

Workflow Check

✔ Project path found
✔ Python installed
✔ Script detected
⚠ Dependency outdated

---

# Step 7 — Dashboard Integration

Agent must send status to dashboard API.

Example:

POST /api/agent/task-status

{
 "agent":"AgentAyazDaddy",
 "task":"compare-html",
 "status":"running"
}

Statuses:

queued
running
completed
failed

---

# Step 8 — Ollama Integration

Allow the agent to use Ollama for reasoning.

Examples:

Analyze logs
Debug failures
Suggest fixes
Optimize workflows

Example CLI:

agent ask "analyze last failure"

---

# Step 9 — Scheduling

Add cron-like scheduling.

Example:

config/schedule.json

{
 "tasks":[
  {
   "task":"nightly-build",
   "time":"02:00"
  }
 ]
}

Scheduler loop must run continuously.

---

# Step 10 — Logging

Create structured logs.

logs/

agent.log
tasks.log
errors.log

Each log must contain:

timestamp
task
status
duration

---

# Step 11 — Safety Mechanisms

Add production safety:

task timeout
retry mechanism
lock files
graceful shutdown
error recovery

---

# Step 12 — Terminal UI

Display:

AgentAyazDaddy

Running Task
Task Queue
Next Task
System Status

Example:

AgentAyazDaddy

Running: html-compare

Queue:
1 build
2 deploy

Next run in 30s

---

# Technology Preference

Use one of the following stacks.

Node.js stack:

commander
chalk
ora
axios
node-cron

Python stack:

typer
rich
schedule
requests

---

# Expected Deliverables

Refactored architecture
CLI task runner
task queue manager
workflow verification system
dashboard API integration
ollama connector
scheduler
logging system
documentation