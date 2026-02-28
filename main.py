import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config.settings import get_settings
from project_utils import get_project_path, get_run_task_catalog, get_task_file, list_projects
from services.execution_service import execute_command_result, execute_task_file_result
from services.ollama_service import call_ollama as ollama_call, stream_ollama
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
AUDIT_LOG_PATH = Path("logs") / "audit.log"
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# FastAPI Setup
# ─────────────────────────────────────────────
app = FastAPI(title="AI DevOps Agent")
app.state.telegram_configured = bool(settings.telegram_token)
app.state.telegram_started = False
app.state.selected_projects = {}
app.state.rate_limit_hits = {}
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
    prompt: str = Field(..., examples=["Summarize release notes"])
    execute_commands: bool = False


class AgentResponse(BaseModel):
    reply: str
    command_output: Optional[str] = None


class ProjectSelectRequest(BaseModel):
    project: str = Field(..., examples=["my-project"])


class ProjectTaskRequest(BaseModel):
    project: Optional[str] = Field(default=None, examples=["my-project"])
    task: str = Field(..., examples=["build.ps1"])
    dry_run: bool = False
    auto_approve: Optional[bool] = None
    delay_seconds: Optional[int] = Field(default=None, ge=0)


class ProjectCustomCommandRequest(BaseModel):
    project: Optional[str] = Field(default=None, examples=["my-project"])
    command: str = Field(..., examples=["python --version"])
    dry_run: bool = False
    auto_approve: Optional[bool] = None
    delay_seconds: Optional[int] = Field(default=None, ge=0)

# ─────────────────────────────────────────────
# Ollama Call
# ─────────────────────────────────────────────
async def call_ollama(prompt: str) -> str:
    return await ollama_call(prompt, settings.ollama_model, settings.ollama_url)


def fail(status_code: int, code: str, message: str, hint: str = "") -> None:
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "hint": hint,
        },
    )


def audit_log(event: dict) -> None:
    payload = {
        "ts": int(time.time()),
        **event,
    }
    try:
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        log.exception("Failed to write audit log")


def validate_api_key(x_api_key: Optional[str]) -> str:
    if not settings.api_secret_keys:
        fail(
            500,
            "API_SECRET_MISSING",
            "Server API secret is not configured",
            "Set API_SECRET_KEY or API_SECRET_KEYS in .env",
        )
    if not x_api_key or x_api_key not in settings.api_secret_keys:
        fail(
            401,
            "UNAUTHORIZED",
            "Unauthorized",
            "Provide valid X-Api-Key",
        )
    return x_api_key


def enforce_rate_limit(identity: str) -> None:
    now = time.time()
    window_seconds = 60
    state: dict[str, list[float]] = app.state.rate_limit_hits
    current = [stamp for stamp in state.get(identity, []) if now - stamp < window_seconds]
    if len(current) >= settings.rate_limit_per_minute:
        fail(
            429,
            "RATE_LIMITED",
            "Rate limit exceeded",
            "Retry after a short delay",
        )
    current.append(now)
    state[identity] = current


def require_protected_access(request: Request, x_api_key: Optional[str], endpoint: str) -> str:
    api_key = validate_api_key(x_api_key)
    client_host = request.client.host if request.client else "unknown"
    enforce_rate_limit(f"{api_key}:{client_host}:{endpoint}")
    return api_key


def resolve_project_context(project_name: Optional[str], api_key: str) -> tuple[str, Path]:
    selected_map: dict[str, str] = app.state.selected_projects
    selected_name = project_name or selected_map.get(api_key)
    if not selected_name:
        fail(400, "PROJECT_NOT_SELECTED", "No project selected", "Provide project or call /project/select first")

    project_path = get_project_path(selected_name)
    if not project_path:
        fail(400, "PROJECT_NOT_FOUND", "Project not found", "Call /projects and choose a valid project name")

    return selected_name, project_path

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
                execution = execute_command_result(
                    cmd,
                    timeout_seconds=settings.command_timeout_seconds,
                    max_output_chars=settings.max_output_chars,
                    strict_mode=settings.strict_command_mode,
                    allowed_prefixes=settings.allowed_command_prefixes,
                )
                cmd_output = execution.output
                break

    return AgentResponse(reply=reply, command_output=cmd_output)

# ─────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "running", "model": settings.ollama_model}


@app.get("/status")
async def status():
    return {
        "status": "running",
        "model": settings.ollama_model,
        "telegram_configured": app.state.telegram_configured,
        "telegram_started": app.state.telegram_started,
        "host": settings.host,
        "port": settings.port,
    }


@app.get("/health")
async def health():
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            ollama_ok = response.status_code == 200
    except Exception:
        ollama_ok = False

    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama_url": settings.ollama_url,
        "ollama_running": ollama_ok,
        "telegram_configured": app.state.telegram_configured,
        "telegram_started": app.state.telegram_started,
    }

@app.post("/chat", response_model=AgentResponse)
async def chat(body: PromptRequest):
    return await run_agent(body.prompt, execute=False)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            prompt = (await websocket.receive_text()).strip()
            if not prompt:
                await websocket.send_text("❌ Empty prompt")
                continue

            async for chunk in stream_ollama(prompt, settings.ollama_model, settings.ollama_url):
                await websocket.send_text(chunk)

            await websocket.send_text("[DONE]")
    except WebSocketDisconnect:
        return

@app.post("/run-task", response_model=AgentResponse)
async def run_task(body: PromptRequest, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/run-task")
    return await run_agent(body.prompt, execute=body.execute_commands)

# ─────────────────────────────────────────────
# Project Execution
# ─────────────────────────────────────────────
@app.post("/run-project")
async def run_project(project: str, command: str, request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/run-project")

    project_path = get_project_path(project)
    if not project_path:
        fail(400, "PROJECT_NOT_FOUND", "Project not found", "Call /projects and choose a valid project name")

    execution = execute_command_result(
        command,
        cwd=str(project_path),
        timeout_seconds=settings.command_timeout_seconds,
        max_output_chars=settings.max_output_chars,
        strict_mode=settings.strict_command_mode,
        allowed_prefixes=settings.allowed_command_prefixes,
    )
    audit_log(
        {
            "kind": "run-project",
            "api_key": api_key[-4:],
            "project": project,
            "command": command,
            "exit_code": execution.exit_code,
            "duration_ms": execution.duration_ms,
        }
    )
    return {
        "project": project,
        "command": command,
        "output": execution.output,
        "exit_code": execution.exit_code,
        "started_at": execution.started_at,
        "duration_ms": execution.duration_ms,
    }


def try_open_in_vscode(project_path: str) -> tuple[bool, str]:
    try:
        subprocess.Popen(["code", project_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "Opened in VS Code."
    except Exception:
        return False, "Could not open VS Code automatically (ensure `code` is in PATH)."


@app.get("/projects")
async def get_projects(request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/projects")
    projects = list_projects()
    return {
        "projects": projects,
        "count": len(projects),
        "message": "Use POST /project/select with a project name.",
    }


@app.post("/project/select")
async def select_project(body: ProjectSelectRequest, request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/select")

    project_path = get_project_path(body.project)
    if not project_path:
        fail(400, "PROJECT_NOT_FOUND", "Project not found", "Call /projects and choose a valid project name")

    _, open_message = try_open_in_vscode(str(project_path))
    tasks = get_run_task_catalog(project_path)
    app.state.selected_projects[api_key] = body.project

    if tasks:
        message = "run-task files available. Use POST /project/run-task to execute one."
    else:
        message = "No run-task files found. Use POST /project/run-custom to run a custom command."

    return {
        "project": body.project,
        "path": str(project_path),
        "open_vscode": open_message,
        "tasks": tasks,
        "message": message,
    }


@app.get("/project/current")
async def get_current_project(request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/current")
    selected_name = app.state.selected_projects.get(api_key)
    if not selected_name:
        return {"project": None, "path": None, "tasks": []}

    project_path = get_project_path(selected_name)
    if not project_path:
        app.state.selected_projects.pop(api_key, None)
        return {"project": None, "path": None, "tasks": []}

    return {
        "project": selected_name,
        "path": str(project_path),
        "tasks": get_run_task_catalog(project_path),
    }


@app.get("/project/tasks")
async def get_project_tasks(request: Request, project: Optional[str] = None, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/tasks")

    selected_name, project_path = resolve_project_context(project, api_key)
    tasks = get_run_task_catalog(project_path)
    return {
        "project": selected_name,
        "path": str(project_path),
        "tasks": tasks,
        "count": len(tasks),
    }


@app.post("/project/run-task")
async def run_project_task(body: ProjectTaskRequest, request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/run-task")

    selected_name, project_path = resolve_project_context(body.project, api_key)

    task_file = get_task_file(project_path, body.task)
    if not task_file:
        fail(400, "TASK_NOT_FOUND", "Task file not found in run-task folder", "Call /project/tasks to list valid tasks")

    metadata_map = {item["name"]: item for item in get_run_task_catalog(project_path)}
    metadata = metadata_map.get(task_file.name, {})

    auto_approve = (
        body.auto_approve
        if body.auto_approve is not None
        else bool(metadata.get("auto_approve", settings.auto_approve_default))
    )
    if not auto_approve:
        fail(400, "APPROVAL_REQUIRED", "Task requires manual approval", "Set auto_approve=true for this request")

    delay_seconds = (
        body.delay_seconds
        if body.delay_seconds is not None
        else int(metadata.get("delay_seconds", settings.default_execution_delay_seconds))
    )

    if body.dry_run:
        return {
            "project": selected_name,
            "task": task_file.name,
            "dry_run": True,
            "auto_approve": auto_approve,
            "delay_seconds": delay_seconds,
            "message": "Dry-run only. No task execution performed.",
        }

    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)

    execution = execute_task_file_result(
        task_file,
        cwd=str(project_path),
        timeout_seconds=settings.task_timeout_seconds,
        max_output_chars=settings.max_output_chars,
    )
    audit_log(
        {
            "kind": "run-task",
            "api_key": api_key[-4:],
            "project": selected_name,
            "task": task_file.name,
            "exit_code": execution.exit_code,
            "duration_ms": execution.duration_ms,
        }
    )
    return {
        "project": selected_name,
        "task": task_file.name,
        "output": execution.output,
        "exit_code": execution.exit_code,
        "started_at": execution.started_at,
        "duration_ms": execution.duration_ms,
        "auto_approve": auto_approve,
        "delay_seconds": delay_seconds,
    }


@app.post("/project/run-custom")
async def run_project_custom(body: ProjectCustomCommandRequest, request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/run-custom")

    selected_name, project_path = resolve_project_context(body.project, api_key)

    auto_approve = body.auto_approve if body.auto_approve is not None else settings.auto_approve_default
    if not auto_approve:
        fail(400, "APPROVAL_REQUIRED", "Custom command requires manual approval", "Set auto_approve=true for this request")

    delay_seconds = body.delay_seconds if body.delay_seconds is not None else settings.default_execution_delay_seconds
    if body.dry_run:
        return {
            "project": selected_name,
            "command": body.command,
            "dry_run": True,
            "auto_approve": auto_approve,
            "delay_seconds": delay_seconds,
            "message": "Dry-run only. No command execution performed.",
        }

    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)

    execution = execute_command_result(
        body.command,
        cwd=str(project_path),
        timeout_seconds=settings.command_timeout_seconds,
        max_output_chars=settings.max_output_chars,
        strict_mode=settings.strict_command_mode,
        allowed_prefixes=settings.allowed_command_prefixes,
    )
    audit_log(
        {
            "kind": "run-custom",
            "api_key": api_key[-4:],
            "project": selected_name,
            "command": body.command,
            "exit_code": execution.exit_code,
            "duration_ms": execution.duration_ms,
        }
    )
    return {
        "project": selected_name,
        "command": body.command,
        "output": execution.output,
        "exit_code": execution.exit_code,
        "started_at": execution.started_at,
        "duration_ms": execution.duration_ms,
        "auto_approve": auto_approve,
        "delay_seconds": delay_seconds,
    }

def build_telegram():
    selected_project: dict[str, Optional[str]] = {"name": None, "path": None}

    async def handle_message_text(text: str) -> str:
        result = await run_agent(text, execute=False)
        return result.reply

    def handle_projects() -> str:
        projects = list_projects()
        if not projects:
            return "No projects found under PROJECT_ROOT."
        return (
            "📂 Projects:\n"
            + "\n".join(f"- {name}" for name in projects[:100])
            + "\n\nUse /project <name> to select one."
        )

    def handle_select_project(project_name: str) -> str:
        project_path = get_project_path(project_name)
        if not project_path:
            return "❌ Project not found. Use /projects to see valid names."

        selected_project["name"] = project_name
        selected_project["path"] = str(project_path)

        _, open_message = try_open_in_vscode(str(project_path))
        tasks = get_run_task_catalog(project_path)

        if tasks:
            tasks_message = "\n".join(
                f"- {item['name']}{' — ' + item['description'] if item.get('description') else ''}" for item in tasks[:40]
            )
            return (
                f"✅ Selected project: {project_name}\n"
                f"📁 Path: {project_path}\n"
                f"🧩 run-task files:\n{tasks_message}\n\n"
                f"Use /task <file_name> to run one. {open_message}"
            )

        return (
            f"✅ Selected project: {project_name}\n"
            f"📁 Path: {project_path}\n"
            "ℹ️ No run-task files found in run-task/.\n"
            f"Use /custom <command> to run a custom task in this project. {open_message}"
        )

    def handle_tasks() -> str:
        if not selected_project.get("path"):
            return "ℹ️ No project selected. Use /projects then /project <name>."

        project_name = selected_project["name"]
        project_path = get_project_path(project_name or "")
        if not project_path:
            selected_project["name"] = None
            selected_project["path"] = None
            return "❌ Selected project is no longer available. Choose again with /project <name>."

        tasks = get_run_task_catalog(project_path)
        if not tasks:
            return "ℹ️ No run-task files found. Use /custom <command> to run a custom task."

        return "🧩 Available run-task files:\n" + "\n".join(
            f"- {item['name']}{' — ' + item['description'] if item.get('description') else ''}" for item in tasks[:100]
        )

    def handle_current_project() -> str:
        if not selected_project.get("path"):
            return "ℹ️ No project selected. Use /projects then /project <name>."
        return f"📌 Current project: {selected_project['name']}\n📁 Path: {selected_project['path']}"

    def handle_run_task(task_name: str) -> str:
        if not selected_project.get("path"):
            return "ℹ️ No project selected. Use /projects then /project <name>."

        project_name = selected_project["name"]
        project_path = get_project_path(project_name or "")
        if not project_path:
            selected_project["name"] = None
            selected_project["path"] = None
            return "❌ Selected project is no longer available. Choose again with /project <name>."

        task_file = get_task_file(project_path, task_name)
        if not task_file:
            return "❌ Task file not found in run-task/. Use /tasks to see available files."

        metadata = {item["name"]: item for item in get_run_task_catalog(project_path)}.get(task_file.name, {})
        auto_approve = bool(metadata.get("auto_approve", settings.auto_approve_default))
        if not auto_approve:
            return "❌ Task requires manual approval and strict flow is enabled."

        delay_seconds = int(metadata.get("delay_seconds", settings.default_execution_delay_seconds))
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        execution = execute_task_file_result(
            task_file,
            cwd=str(project_path),
            timeout_seconds=settings.task_timeout_seconds,
            max_output_chars=settings.max_output_chars,
        )
        return (
            f"▶ Task: {task_file.name}\n"
            f"Project: {project_name}\n"
            f"Exit: {execution.exit_code} | Duration: {execution.duration_ms}ms\n\n"
            f"{execution.output}"
        )

    def handle_run_custom(command: str) -> str:
        if not selected_project.get("path"):
            return "ℹ️ No project selected. Use /projects then /project <name>."

        project_name = selected_project["name"]
        project_path = get_project_path(project_name or "")
        if not project_path:
            selected_project["name"] = None
            selected_project["path"] = None
            return "❌ Selected project is no longer available. Choose again with /project <name>."

        if not settings.auto_approve_default:
            return "❌ Custom command requires manual approval and strict flow is enabled."

        if settings.default_execution_delay_seconds > 0:
            time.sleep(settings.default_execution_delay_seconds)

        execution = execute_command_result(
            command,
            cwd=str(project_path),
            timeout_seconds=settings.command_timeout_seconds,
            max_output_chars=settings.max_output_chars,
            strict_mode=settings.strict_command_mode,
            allowed_prefixes=settings.allowed_command_prefixes,
        )
        return (
            f"▶ Custom command in {project_name}:\n{command}\n"
            f"Exit: {execution.exit_code} | Duration: {execution.duration_ms}ms\n\n"
            f"{execution.output}"
        )

    def handle_status() -> str:
        return (
            "✅ Runtime Status\n"
            f"Model: {settings.ollama_model}\n"
            f"Ollama URL: {settings.ollama_url}\n"
            f"Host/Port: {settings.host}:{settings.port}\n"
            f"PROJECT_ROOT: {settings.project_root}"
        )

    service = TelegramService(
        token=settings.telegram_token,
        allowed_user_id=settings.allowed_telegram_user_id,
        message_handler=handle_message_text,
        projects_handler=handle_projects,
        status_handler=handle_status,
        select_project_handler=handle_select_project,
        current_project_handler=handle_current_project,
        tasks_handler=handle_tasks,
        run_task_handler=handle_run_task,
        run_custom_handler=handle_run_custom,
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
            app.state.telegram_started = True
            log.info("Telegram bot connected")
        except Exception as error:
            app.state.telegram_started = False
            log.exception(f"Telegram startup failed, continuing with REST API only: {error}")

    await server.serve()

    if tg and telegram_started:
        await tg.updater.stop()
        await tg.stop()
        await tg.shutdown()
        app.state.telegram_started = False

if __name__ == "__main__":
    asyncio.run(main())
