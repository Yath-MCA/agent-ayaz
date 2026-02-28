import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config.settings import get_settings
from project_utils import get_project_path
from services.execution_service import execute_command
from services.ollama_service import call_ollama as ollama_call
from services.telegram_service import TelegramService

# ─────────────────────────────────────────────
# Load Environment
# ─────────────────────────────────────────────
settings = get_settings()

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
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["X-Api-Key", "Content-Type", "Authorization"],
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
    return await ollama_call(prompt, settings.ollama_model, settings.ollama_url)


def validate_api_key(x_api_key: Optional[str]) -> None:
    if not settings.api_secret_key:
        raise HTTPException(500, "Server API secret is not configured")
    if not x_api_key or x_api_key != settings.api_secret_key:
        raise HTTPException(401, "Unauthorized")

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
    return {"status": "running", "model": settings.ollama_model}

@app.post("/chat", response_model=AgentResponse)
async def chat(body: PromptRequest):
    return await run_agent(body.prompt, execute=False)

@app.post("/run-task", response_model=AgentResponse)
async def run_task(body: PromptRequest, x_api_key: str = Header(None)):
    validate_api_key(x_api_key)
    return await run_agent(body.prompt, execute=body.execute_commands)

# ─────────────────────────────────────────────
# Project Execution
# ─────────────────────────────────────────────
@app.post("/run-project")
async def run_project(project: str, command: str, x_api_key: str = Header(None)):
    validate_api_key(x_api_key)

    project_path = get_project_path(project)
    if not project_path:
        raise HTTPException(400, "Project not found")

    output = execute_command(command, cwd=str(project_path))
    return {"project": project, "output": output}

def build_telegram():
    async def handle_message_text(text: str) -> str:
        result = await run_agent(text, execute=False)
        return result.reply

    service = TelegramService(
        token=settings.telegram_token,
        allowed_user_id=settings.allowed_telegram_user_id,
        message_handler=handle_message_text,
    )
    return service.build_application()

# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────
async def main():
    tg = build_telegram()

    config = uvicorn.Config(app, host=settings.host, port=settings.port)
    server = uvicorn.Server(config)

    telegram_started = False
    if tg:
        try:
            await tg.initialize()
            await tg.start()
            await tg.updater.start_polling()
            telegram_started = True
            log.info("Telegram bot connected")
        except Exception as error:
            log.exception(f"Telegram startup failed, continuing with REST API only: {error}")

    await server.serve()

    if tg and telegram_started:
        await tg.updater.stop()
        await tg.stop()
        await tg.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
