import asyncio
import logging
import os
import subprocess
import shutil
import socket
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# ─────────────────────────────────────────────
# Load Environment
# ─────────────────────────────────────────────
load_dotenv()

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "D:/PERSONAL/LIVE_PROJECTS"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
ALLOWED_TELEGRAM_USER_ID = int(os.getenv("ALLOWED_TELEGRAM_USER_ID", "0"))
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# FastAPI Setup
# ─────────────────────────────────────────────
app = FastAPI(title="AI DevOps Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class PromptRequest(BaseModel):
    prompt: str
    execute_commands: bool = False

class AgentResponse(BaseModel):
    reply: str
    command_output: Optional[str] = None

# ─────────────────────────────────────────────
# Ollama Call
# ─────────────────────────────────────────────
async def call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response", "")

# ─────────────────────────────────────────────
# Secure Shell Execution
# ─────────────────────────────────────────────
FORBIDDEN_COMMANDS = [
    "format",
    "shutdown",
    "restart",
    "rm ",
    "del ",
    "rd ",
]

def execute_command(cmd: str, cwd: Optional[str] = None) -> str:
    if any(bad in cmd.lower() for bad in FORBIDDEN_COMMANDS):
        return "❌ Forbidden command detected."

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd
        )
        output = result.stdout or result.stderr or "(no output)"
        return output[:3000]
    except Exception as e:
        return f"Execution error: {e}"

# ─────────────────────────────────────────────
# Agent Core
# ─────────────────────────────────────────────
async def run_agent(prompt: str, execute: bool):
    reply = await call_ollama(prompt)
    cmd_output = None

    if execute and "RUN_CMD:" in reply:
        for line in reply.splitlines():
            if line.startswith("RUN_CMD:"):
                cmd = line.replace("RUN_CMD:", "").strip()
                cmd_output = execute_command(cmd)
                break

    return AgentResponse(reply=reply, command_output=cmd_output)

# ─────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "running", "model": OLLAMA_MODEL}

@app.post("/chat", response_model=AgentResponse)
async def chat(body: PromptRequest):
    return await run_agent(body.prompt, execute=False)

@app.post("/run-task", response_model=AgentResponse)
async def run_task(body: PromptRequest, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(401, "Unauthorized")
    return await run_agent(body.prompt, execute=body.execute_commands)

# ─────────────────────────────────────────────
# Project Execution
# ─────────────────────────────────────────────
@app.post("/run-project")
async def run_project(project: str, command: str, x_api_key: str = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(401, "Unauthorized")

    project_path = PROJECT_ROOT / project

    if not project_path.exists():
        raise HTTPException(400, "Project not found")

    output = execute_command(command, cwd=str(project_path))
    return {"project": project, "output": output}

# ─────────────────────────────────────────────
# Telegram
# ─────────────────────────────────────────────
def is_allowed(update):
    return update.effective_user.id == ALLOWED_TELEGRAM_USER_ID

async def tg_message(update, ctx):
    if not is_allowed(update):
        return

    text = update.message.text
    result = await run_agent(text, execute=False)

    reply = result.reply[:4000]
    await update.message.reply_text(reply)

def build_telegram():
    from telegram.ext import Application, MessageHandler, CommandHandler, filters

    if not TELEGRAM_TOKEN:
        return None

    app_tg = Application.builder().token(TELEGRAM_TOKEN).build()
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message))
    return app_tg

# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────
async def main():
    tg = build_telegram()

    config = uvicorn.Config(app, host=HOST, port=PORT)
    server = uvicorn.Server(config)

    if tg:
        await tg.initialize()
        await tg.start()
        await tg.updater.start_polling()
        await server.serve()
    else:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())