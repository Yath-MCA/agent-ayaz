# AgentAyazDaddy v2
Autonomous CLI AI Agent for Developer Automation

You are designing an advanced autonomous development agent named:

AgentAyazDaddy

The ecosystem already exists and includes:

- Bot services
- Internal APIs
- Local AI models via Ollama
- Multiple local project repositories
- Existing scripts and automation tasks

Your task is to **upgrade the system into an intelligent autonomous DevOps agent**.

The agent must analyze the existing ecosystem, refactor workflows, and provide a CLI-based automation system with AI reasoning.

---

# Primary Responsibilities

AgentAyazDaddy must act as:

Task Runner  
Workflow Analyzer  
Automation Scheduler  
AI Assistant  
DevOps Automation Agent  

The system must work entirely from the terminal but connect to a web dashboard.

---

# Core Capabilities

AgentAyazDaddy must support:

CLI task execution  
Sequential task queues  
Project discovery  
AI-assisted debugging  
Workflow optimization  
Dashboard reporting  
Self-healing automation  
Multi-agent orchestration  

---

# Architecture

AgentAyazDaddy
│
├ CLI Interface
├ Task Queue Engine
├ Workflow Analyzer
├ Scheduler
├ Project Scanner
├ AI Reasoning Engine (Ollama)
├ Dashboard Connector
├ Bot Connector
├ API Connector
└ Logging System

---

# CLI Interface

The CLI is the primary control interface.

Commands:

agent run <task>
agent queue
agent projects
agent analyze
agent optimize
agent schedule
agent logs
agent status
agent doctor

Example:

agent run build
agent run compare-html
agent analyze workflow
agent optimize tasks

---

# Project Discovery

Agent must automatically detect projects.

Scan configured paths for:

package.json
pyproject.toml
requirements.txt
gulpfile.js
Makefile

Register tasks automatically.

Example output:

Discovered Project:
impact-proofing

Available Tasks:
build
deploy
compare-html

---

# Task Definition System

Convert scripts into structured tasks.

tasks/
compareHtml.task.js
buildDocs.task.js
deploy.task.js

Task Schema:

{
  "name": "compare-html",
  "project": "impact",
  "type": "python",
  "script": "compare_html.py",
  "timeout": 300,
  "retry": 2
}

Supported Task Types:

shell
node
python
api
bot
ollama

---

# Task Queue Engine

Tasks must run sequentially.

Rules:

one active task at a time
configurable delay between tasks
retry failed tasks
queue persistence
prevent duplicate execution

Queue Flow:

User → Queue → Worker → Execute → Report → Next Task

---

# AI Reasoning Layer (Ollama)

AgentAyazDaddy must use local AI to assist development tasks.

Capabilities:

log summarization
failure analysis
code debugging
dependency suggestions
workflow optimization

Example CLI:

agent ask "why did the build fail"
agent analyze logs
agent suggest fixes

Internally call:

ollama run <model>

---

# Workflow Analyzer

The agent must verify the environment before executing tasks.

Checks:

project path
dependencies
scripts
environment variables
ports
services

Example output:

Workflow Verification

✔ Project detected
✔ Python installed
✔ Script found
⚠ Missing dependency

---

# Self-Healing Mechanism

If a task fails:

retry automatically
ask Ollama for analysis
suggest fixes
optionally patch configuration

Example:

Task failed: compare-html

AI Analysis:
Missing dependency "lxml"

Suggested Fix:
pip install lxml

---

# Dashboard Integration

Agent must communicate with a dashboard.

POST /api/agent/task-status

Payload:

{
 "agent": "AgentAyazDaddy",
 "task": "compare-html",
 "status": "running"
}

States:

queued
running
completed
failed

Dashboard must show:

task queue
current task
system health
last runs

---

# Scheduler

Support automated task execution.

Example config:

schedule.json

{
 "tasks": [
  {
   "task": "nightly-build",
   "cron": "0 2 * * *"
  }
 ]
}

Scheduler loop must run continuously.

---

# Logging System

Create structured logs.

logs/

agent.log  
tasks.log  
errors.log  
ai-analysis.log  

Each entry must contain:

timestamp
task
duration
status
project

---

# Multi-Agent Extension

AgentAyazDaddy must support sub-agents.

DevAgent  
QAAgent  
BuildAgent  
DeployAgent  

Example:

AgentAyazDaddy
│
├ DevAgent
├ QAAgent
├ BuildAgent
└ DeployAgent

Each agent specializes in specific tasks.

---

# Terminal Dashboard

The CLI should provide a live dashboard.

Example:

AgentAyazDaddy v2

Running Task:
compare-html

Queue:
build-docs
deploy

System Status:
Ollama: connected
API: connected
Bots: active

Next task in 30s

---

# Configuration System

config/

projects.json
schedule.json
agent.json

Example projects.json

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

---

# Safety Requirements

Add protections:

task timeout
retry limit
queue locking
duplicate prevention
graceful shutdown

---

# Technology Stack

Preferred:

Node.js

Libraries:

commander
chalk
ora
axios
node-cron
lowdb

Alternative:

Python

Libraries:

typer
rich
schedule
requests

---

# Deliverables

Generate a complete project including:

CLI framework
task queue engine
workflow analyzer
ollama connector
dashboard connector
scheduler
multi-agent architecture
logging system
documentation

The result must be a production-ready automation agent.