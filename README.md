# 🤖 AI DevOps Agent

Comprehensive Documentation\
FastAPI + Telegram + Local Ollama (phi3) + GitHub Copilot Integration

------------------------------------------------------------------------

## 📌 Overview

AI DevOps Agent is a secure remote automation controller designed for
Windows environments.

It enables:

-   Remote project command execution
-   Telegram-based DevOps control
-   Local AI fallback using Ollama (phi3)
-   Secure REST API access
-   Seamless integration with GitHub Copilot (IDE-based)

This system does NOT replace IDE AI tools.\
It acts as an orchestration and automation layer.

------------------------------------------------------------------------

## 🧠 System Architecture

VS Code + GitHub Copilot\
↓\
Local Development

Telegram (Remote Control)\
↓\
FastAPI AI-Agent\
↓\
• Secure Project Execution\
• Local Ollama (phi3 fallback)\
• Task Orchestration

------------------------------------------------------------------------

## 📂 Folder Structure

ai-agent/ │ ├── main.py \# Core FastAPI + Telegram + Execution Logic ├──
project_utils.py \# Project root helper utilities ├── requirements.txt
\# Python dependencies ├── .env \# Environment configuration (DO NOT
COMMIT) ├── logs/ \# Optional runtime logs ├── prompts/ \# Optional
reusable AI prompts └── README.md \# Documentation

------------------------------------------------------------------------

## 📁 PROJECT_ROOT Structure Example

D:`\PERSONAL`{=tex}`\LIVE`{=tex}\_PROJECTS │ ├── ai-agent ├── oneconnect
├── client-portal ├── erp-system └── test-project

All execution is restricted to:

PROJECT_ROOT/`<project>`{=html}

------------------------------------------------------------------------

## 🚀 Installation Guide (Windows)

### 1️⃣ Install Ollama

Download: https://ollama.com/download/windows

Pull recommended model:

    ollama pull phi3

Verify:

    ollama list

------------------------------------------------------------------------

### 2️⃣ Install Python Dependencies

    pip install -r requirements.txt

------------------------------------------------------------------------

### 3️⃣ Configure Environment (.env)

PROJECT_ROOT=D:`\PERSONAL`{=tex}`\LIVE`{=tex}\_PROJECTS
OLLAMA_MODEL=phi3 OLLAMA_URL=http://localhost:11434
TELEGRAM_TOKEN=your_bot_token API_SECRET_KEY=your_super_secret_key
ALLOWED_TELEGRAM_USER_ID=your_telegram_user_id HOST=0.0.0.0 PORT=8000

------------------------------------------------------------------------

### 4️⃣ Run the Agent

    python main.py

Access API:

    http://localhost:8000

------------------------------------------------------------------------

## 📱 Telegram Usage

Send any prompt to your bot:

    Generate Playwright test for login page

Agent will use local phi3 model.

------------------------------------------------------------------------

## 🔐 REST API Endpoints

### Public Chat

POST /chat

No command execution allowed.

------------------------------------------------------------------------

### Protected Task Execution

POST /run-task\
Header: X-Api-Key

Allows optional command execution.

------------------------------------------------------------------------

### Run Command in Specific Project

POST /run-project\
Header: X-Api-Key

Parameters: - project - command

------------------------------------------------------------------------

## 🛡 Security Model

-   API key required for protected endpoints
-   Telegram restricted to allowed user ID
-   Forbidden shell commands blocked
-   No public raw shell endpoint
-   No hardcoded credentials
-   No debug mode enabled

------------------------------------------------------------------------

## 🧠 AI Model Recommendation

Use:

    phi3

Why:

-   Fast
-   Lightweight
-   Good reasoning for automation
-   Low resource usage

------------------------------------------------------------------------

## 🌍 Optional: Cloudflare Tunnel

Expose externally:

    cloudflared tunnel --url http://localhost:8000

Telegram works without tunnel.

------------------------------------------------------------------------

## 🧪 Typical Use Cases

-   Run builds remotely
-   Execute test suites
-   Generate automation scripts
-   Debug project modules
-   Run deployment scripts
-   Generate Playwright tests

------------------------------------------------------------------------

## ⚙ Production Readiness Checklist

-   Strong API_SECRET_KEY
-   Correct PROJECT_ROOT path
-   Telegram restricted
-   Ollama running
-   No secrets committed
-   Firewall configured properly

------------------------------------------------------------------------

## 📈 Future Improvements

-   Command whitelist system
-   Execution logs persistence
-   Background job runner
-   Task history tracking
-   Docker deployment
-   CI/CD integration

------------------------------------------------------------------------

## 📌 Final Notes

This AI DevOps Agent:

-   Enhances development workflows
-   Provides secure automation
-   Works alongside GitHub Copilot
-   Enables remote DevOps control

It is designed for controlled environments and personal/team usage.
