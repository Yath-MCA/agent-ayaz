import asyncio
import json
import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from config.settings import get_settings
from project_utils import get_project_path, get_run_task_catalog, get_task_file, list_projects, ensure_run_task_dir
from services.execution_service import execute_command_result, execute_task_file_result
from services.memory_service import init_db, record_execution, get_project_history, get_recent_failures, get_execution_stats, suggest_retry
from services.task_queue_service import queue_status, run_queue, promote_later_to_queue, ensure_dirs as ensure_queue_dirs
from services.ollama_service import call_ollama as ollama_call, stream_ollama
from services.llm_provider import get_llm_service, LLMProvider
from services.telegram_service import TelegramService
from agents import planner as planner_agent, validator as validator_agent, executor as executor_agent
from agents.auditor import record as auditor_record, tail as auditor_tail
from agents.approval import ApprovalStore, ApprovalStatus
from agents.risk import score_plan
from agents.mode import mode_info, current_mode, AgentMode, should_auto_approve, can_execute_custom_command
from agents.optimizer import build_optimized_prompt
from agents.replay import replay_execution
from agents.nodes import node_registry
from plugins import plugin_manager
from security.rbac import get_role, require_role
from tools.git_service import GitService

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
app.state.approval_store = ApprovalStore(default_timeout_seconds=300)
app.state.llm_service = get_llm_service()  # Initialize LLM provider service
init_db()
ensure_queue_dirs()
plugin_manager.load_plugins_from_dir(Path("plugins"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["X-Api-Key", "Content-Type", "Authorization"],
)

# Serve React dashboard at /dashboard (static files)
_dashboard_dir = Path("dashboard")
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class PromptRequest(BaseModel):
    prompt: str = Field(..., examples=["Summarize release notes"])
    execute_commands: bool = False
    project: Optional[str] = Field(default=None, examples=["impact_vite"])


class AgentResponse(BaseModel):
    reply: str
    command_output: Optional[str] = None


class ProjectSelectRequest(BaseModel):
    project: str = Field(..., examples=["my-project"])
    confirm_agent_tasks: bool = False


class ProjectTaskRequest(BaseModel):
    project: Optional[str] = Field(default=None, examples=["my-project"])
    task: str = Field(..., examples=["build.ps1"])
    dry_run: bool = False
    auto_approve: Optional[bool] = None
    delay_seconds: Optional[int] = Field(default=None, ge=0)
    auto_git_commit: Optional[bool] = Field(default=None, description="Auto-commit project changes after successful execution (like copilot-ralph per-task commits)")


class ProjectRunAllTasksRequest(BaseModel):
    project: Optional[str] = Field(default=None, examples=["my-project"])
    dry_run: bool = False
    auto_git_commit: Optional[bool] = Field(default=None, description="Auto-commit project changes after each successful task execution")


class ProjectCustomCommandRequest(BaseModel):
    project: Optional[str] = Field(default=None, examples=["my-project"])
    command: str = Field(..., examples=["python --version"])
    dry_run: bool = False
    auto_approve: Optional[bool] = None
    delay_seconds: Optional[int] = Field(default=None, ge=0)
    auto_git_commit: Optional[bool] = Field(default=None, description="Auto-commit project changes after successful execution")


class QueueTextPromptRequest(BaseModel):
    include_later: bool = False
    limit: int = Field(default=20, ge=1, le=200)

# ─────────────────────────────────────────────
# LLM Call with Auto-Fallback
# ─────────────────────────────────────────────
async def call_ollama(prompt: str) -> str:
    """
    Call LLM with automatic provider fallback.
    Tries: Ollama > OpenAI > OpenRouter > LM Studio > Mock
    """
    llm_service = get_llm_service()
    return await llm_service.call_llm(prompt)


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
    rbac_error = require_role(api_key, endpoint)
    if rbac_error:
        fail(403, "FORBIDDEN", rbac_error, "Check RBAC_ROLES configuration")
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


def detect_pending_agent_text_tasks() -> dict[str, list[str]]:
    """Find .txt/.md tasks pending in agent-task queue and later folders."""
    pending = {"queue": [], "later": []}
    root = Path("agent-task")

    for bucket in ("queue", "later"):
        folder = root / bucket
        if not folder.exists() or not folder.is_dir():
            continue
        for file in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if not file.is_file():
                continue
            if file.suffix.lower() in {".txt", ".md"}:
                pending[bucket].append(file.name)

    return pending


def maybe_git_commit(project_path: Path, task_label: str, do_commit: bool, exit_code: int = 0) -> Optional[dict]:
    """
    Auto-commit project changes after task execution (inspired by copilot-ralph).

    Each successful task gets its own commit, preventing context rot and providing
    a clean audit trail of changes — the same model used by copilot-ralph.

    Args:
        project_path: Path to the project repository
        task_label: Short label used in the commit message (task name or command)
        do_commit: Whether to actually commit
        exit_code: Task exit code — commit is skipped when non-zero (task failed)

    Returns:
        Dict with commit result info, or None if skipped
    """
    if not do_commit or exit_code != 0:
        return None
    try:
        git = GitService(repo_path=str(project_path))
        is_valid, err = git.validate_repository()
        if not is_valid:
            return {"skipped": True, "reason": err}

        status = git.get_status()
        if status["total"] == 0:
            return {"skipped": True, "reason": "no changes to commit"}

        diff = git.get_diff()
        commit_type = git.detect_commit_type(status, diff)
        summary = git.generate_commit_summary(status, git.get_diff_stat())
        message = git.format_commit_message(commit_type, summary, status, remark=f"task: {task_label}")
        result = git.commit_and_push(message, push=False)
        return result
    except Exception as exc:
        log.warning("Auto git-commit failed: %s", exc)
        return {"skipped": True, "reason": str(exc)}

# ─────────────────────────────────────────────
# Agent Core
# ─────────────────────────────────────────────
async def _get_project_precheck(project: Optional[str]) -> dict:
    project_path = get_project_path(project) if project else None
    agent_tasks_available = bool(project_path and get_run_task_catalog(project_path))
    pending_agent_tasks = detect_pending_agent_text_tasks()
    has_pending_md_txt = bool(pending_agent_tasks["queue"] or pending_agent_tasks["later"])

    llm_service = get_llm_service()
    copilot_available = await llm_service.check_provider_health(LLMProvider.GITHUB_COPILOT)

    return {
        "agent_tasks_available": agent_tasks_available,
        "has_pending_md_txt": has_pending_md_txt,
        "pending_agent_tasks": pending_agent_tasks,
        "copilot_available": copilot_available,
        "prefer_copilot": bool(project and agent_tasks_available and has_pending_md_txt and copilot_available),
    }


async def run_agent(prompt: str, execute: bool, user: str = "api", project: Optional[str] = None):
    mode = current_mode()

    precheck = await _get_project_precheck(project)

    llm_service = get_llm_service()

    async def llm_call(prompt_text: str) -> str:
        # If agent-task checks pass and Copilot access exists, run Copilot first.
        if precheck["prefer_copilot"]:
            return await llm_service.call_llm(prompt_text, provider=LLMProvider.GITHUB_COPILOT)
        return await llm_service.call_llm(prompt_text)

    # Phase 9: optimizer injects memory context into prompt
    enriched_prompt = build_optimized_prompt(prompt, project=project)

    # Phase 11: before_plan hook
    plugin_manager.fire("before_plan", prompt=prompt, project=project)

    # Planner → structured JSON plan
    exec_plan = await planner_agent.plan(enriched_prompt, llm_call)

    # Phase 7: risk scoring
    risk = score_plan(exec_plan.command, exec_plan.project, exec_plan.type, exec_plan.auto_approve)

    cmd_output = None
    if execute and exec_plan.type == "command" and exec_plan.command:
        # Phase 10: SAFE mode blocks custom commands
        if not can_execute_custom_command(mode):
            return AgentResponse(reply=exec_plan.raw_reply, command_output="⛔ SAFE_MODE: custom commands are not allowed.")

        # Phase 10: AUTONOMOUS mode can auto-approve low-risk plans
        auto = should_auto_approve(risk.score, mode)

        # Validator gate
        validation = validator_agent.validate(
            exec_plan,
            strict_mode=settings.strict_command_mode,
            allowed_prefixes=settings.allowed_command_prefixes,
        )
        plugin_manager.fire("after_validation", plan=exec_plan, result=validation)

        if validation.approved:
            plugin_manager.fire("before_execution", plan=exec_plan)
            attempt = 0
            from agents.mode import should_auto_retry
            while True:
                execution = executor_agent.execute(
                    exec_plan, validation,
                    timeout_seconds=settings.command_timeout_seconds,
                    max_output_chars=settings.max_output_chars,
                    strict_mode=settings.strict_command_mode,
                    allowed_prefixes=settings.allowed_command_prefixes,
                )
                plugin_manager.fire("after_execution", plan=exec_plan, result=execution)
                cmd_output = execution.output
                if not should_auto_retry(execution.exit_code, attempt, mode):
                    break
                attempt += 1

            auditor_record(user=user, project=exec_plan.project, command=exec_plan.command,
                           task=exec_plan.task, exit_code=execution.exit_code,
                           duration_ms=execution.duration_ms, approved=True,
                           plan_type=exec_plan.type, reasoning=exec_plan.reasoning)
            record_execution(user=user, project=exec_plan.project, task=exec_plan.task,
                             command=exec_plan.command, plan_type=exec_plan.type,
                             exit_code=execution.exit_code, duration_ms=execution.duration_ms, approved=True)
        else:
            cmd_output = f"⛔ Blocked: {validation.reason}"
            auditor_record(user=user, project=exec_plan.project, command=exec_plan.command,
                           task=exec_plan.task, exit_code=2, duration_ms=0, approved=False,
                           plan_type=exec_plan.type, reasoning=validation.reason)
    elif execute and "RUN_CMD:" in exec_plan.raw_reply:
        for line in exec_plan.raw_reply.splitlines():
            if line.startswith("RUN_CMD:"):
                cmd = line.replace("RUN_CMD:", "").strip()
                execution = execute_command_result(cmd,
                    timeout_seconds=settings.command_timeout_seconds,
                    max_output_chars=settings.max_output_chars,
                    strict_mode=settings.strict_command_mode,
                    allowed_prefixes=settings.allowed_command_prefixes)
                cmd_output = execution.output
                break

    return AgentResponse(reply=exec_plan.raw_reply, command_output=cmd_output)

# ─────────────────────────────────────────────
# REST Endpoints
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "running", "model": settings.ollama_model}


@app.get("/status")
async def status():
    llm_service = get_llm_service()
    current_provider = await llm_service.get_available_provider()
    
    return {
        "status": "running",
        "llm_provider": current_provider,
        "model": settings.ollama_model,
        "telegram_configured": app.state.telegram_configured,
        "telegram_started": app.state.telegram_started,
        "host": settings.host,
        "port": settings.port,
    }


@app.get("/health")
async def health():
    llm_service = get_llm_service()
    llm_status = await llm_service.get_status()
    
    # Check if any provider is available
    any_available = any(
        provider_info["available"] 
        for provider_info in llm_status["providers"].values()
    )
    
    return {
        "status": "ok" if any_available else "degraded",
        "llm_providers": llm_status,
        "telegram_configured": app.state.telegram_configured,
        "telegram_started": app.state.telegram_started,
    }

@app.get("/llm-providers")
async def llm_providers():
    """Get detailed status of all LLM providers."""
    llm_service = get_llm_service()
    return await llm_service.get_status()

@app.post("/chat", response_model=AgentResponse)
async def chat(body: PromptRequest):
    return await run_agent(body.prompt, execute=False, project=body.project)


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    llm_service = get_llm_service()
    
    try:
        while True:
            prompt = (await websocket.receive_text()).strip()
            if not prompt:
                await websocket.send_text("❌ Empty prompt")
                continue

            async for chunk in llm_service.stream_llm(prompt):
                await websocket.send_text(chunk)

            await websocket.send_text("[DONE]")
    except WebSocketDisconnect:
        return


@app.post("/run-task", response_model=AgentResponse)
async def run_task(body: PromptRequest, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/run-task")
    return await run_agent(body.prompt, execute=body.execute_commands, project=body.project)

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
    if not settings.auto_open_vscode:
        return False, "Skipping VS Code auto-open (AUTO_OPEN_VSCODE=false)."
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

    pending_agent_tasks = detect_pending_agent_text_tasks()
    has_pending_agent_tasks = bool(pending_agent_tasks["queue"] or pending_agent_tasks["later"])
    agent_tasks_available = bool(get_run_task_catalog(project_path))
    llm_service = get_llm_service()
    github_copilot_available = await llm_service.check_provider_health(LLMProvider.GITHUB_COPILOT)
    if has_pending_agent_tasks and not body.confirm_agent_tasks:
        fail(
            409,
            "CONFIRMATION_REQUIRED",
            "Pending .txt/.md files found in agent-task queue/later.",
            "Resend /project/select with confirm_agent_tasks=true after manual confirmation.",
        )

    _, open_message = try_open_in_vscode(str(project_path))
    ensure_run_task_dir(project_path)
    tasks = get_run_task_catalog(project_path)
    app.state.selected_projects[api_key] = body.project

    if tasks:
        message = "run-task files available. Use POST /project/run-task to execute one."
    else:
        message = "No run-task files found. Use POST /project/run-custom to run a custom command."

    return {
        "project": body.project,
        "run_task_count": len(tasks),
        "open_vscode": open_message,
        "agent_task_confirmation": {
            "required": has_pending_agent_tasks,
            "queue_md_txt": pending_agent_tasks["queue"],
            "later_md_txt": pending_agent_tasks["later"],
        },
        "project_checks": {
            "agent_tasks_available": agent_tasks_available,
            "queue_or_later_md_txt_found": has_pending_agent_tasks,
            "github_copilot_available": github_copilot_available,
            "run_github_copilot_first": bool(agent_tasks_available and has_pending_agent_tasks and github_copilot_available),
        },
        "message": message,
    }


def _move_task_file_to_completed(source_file: Path) -> Path:
    completed_dir = Path("agent-task") / "completed"
    completed_dir.mkdir(parents=True, exist_ok=True)

    dest = completed_dir / source_file.name
    if dest.exists():
        dest = completed_dir / f"{source_file.stem}_{int(time.time())}{source_file.suffix}"

    shutil.move(str(source_file), str(dest))
    return dest


@app.post("/queue/run-text-prompts")
async def run_text_prompts(body: QueueTextPromptRequest, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/queue/run-text-prompts")

    queue_root = Path("agent-task")
    queue_dir = queue_root / "queue"
    later_dir = queue_root / "later"
    candidates: list[Path] = []

    if queue_dir.exists():
        candidates.extend([f for f in sorted(queue_dir.iterdir(), key=lambda p: p.name.lower()) if f.is_file()])
    if body.include_later and later_dir.exists():
        candidates.extend([f for f in sorted(later_dir.iterdir(), key=lambda p: p.name.lower()) if f.is_file()])

    prompt_files = [f for f in candidates if f.suffix.lower() in {".txt", ".md"}][: body.limit]
    llm_service = get_llm_service()
    copilot_available = await llm_service.check_provider_health(LLMProvider.GITHUB_COPILOT)

    results = []
    for f in prompt_files:
        prompt_text = f.read_text(encoding="utf-8", errors="ignore").strip()
        if not prompt_text:
            _move_task_file_to_completed(f)
            results.append({"file": f.name, "status": "skipped", "reason": "empty prompt"})
            continue

        try:
            if copilot_available:
                answer = await llm_service.call_llm(prompt_text, provider=LLMProvider.GITHUB_COPILOT)
                provider_used = "github_copilot"
            else:
                answer = await llm_service.call_llm(prompt_text)
                provider_used = str(await llm_service.get_available_provider() or "unknown")

            completed_file = _move_task_file_to_completed(f)
            result_file = completed_file.with_suffix(completed_file.suffix + ".result.txt")
            result_file.write_text(answer or "", encoding="utf-8")

            results.append(
                {
                    "file": f.name,
                    "status": "executed",
                    "provider": provider_used,
                    "result_file": result_file.name,
                }
            )
        except Exception as exc:
            results.append({"file": f.name, "status": "failed", "error": str(exc)})

    return {
        "processed": len(results),
        "copilot_available": copilot_available,
        "results": results,
        "message": "Processed text/markdown prompts from queue/later using GitHub Copilot first when available.",
    }


@app.get("/project/current")
async def get_current_project(request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/current")
    selected_name = app.state.selected_projects.get(api_key)
    if not selected_name:
        return {"project": None, "run_task_count": 0}

    project_path = get_project_path(selected_name)
    if not project_path:
        app.state.selected_projects.pop(api_key, None)
        return {"project": None, "run_task_count": 0}

    return {
        "project": selected_name,
        "run_task_count": len(get_run_task_catalog(project_path)),
    }


@app.get("/project/tasks")
async def get_project_tasks(request: Request, project: Optional[str] = None, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/tasks")

    selected_name, project_path = resolve_project_context(project, api_key)
    tasks = get_run_task_catalog(project_path)
    return {
        "project": selected_name,
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

    do_commit = body.auto_git_commit if body.auto_git_commit is not None else settings.auto_git_commit_on_task
    git_commit = maybe_git_commit(project_path, task_file.name, do_commit, execution.exit_code)

    response = {
        "project": selected_name,
        "task": task_file.name,
        "output": execution.output,
        "exit_code": execution.exit_code,
        "started_at": execution.started_at,
        "duration_ms": execution.duration_ms,
        "auto_approve": auto_approve,
        "delay_seconds": delay_seconds,
    }
    if git_commit is not None:
        response["git_commit"] = git_commit
    return response


@app.post("/project/run-all-tasks")
async def run_all_project_tasks(body: ProjectRunAllTasksRequest, request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/project/run-all-tasks")

    selected_name, project_path = resolve_project_context(body.project, api_key)

    tasks = get_run_task_catalog(project_path)
    if not tasks:
        return {"project": selected_name, "results": [], "count": 0, "message": "No tasks found in run-task folder."}

    if body.dry_run:
        return {
            "project": selected_name,
            "dry_run": True,
            "tasks": [item["name"] for item in tasks],
            "count": len(tasks),
            "message": "Dry-run only. Tasks would execute in this order.",
        }

    results = []
    for item in tasks:
        task_file = get_task_file(project_path, item["name"])
        if not task_file:
            results.append({"task": item["name"], "skipped": True, "reason": "file_not_found"})
            continue

        auto_approve = bool(item.get("auto_approve", settings.auto_approve_default))
        if not auto_approve:
            results.append({"task": item["name"], "skipped": True, "reason": "approval_required"})
            continue

        delay_seconds = int(item.get("delay_seconds", settings.default_execution_delay_seconds))
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        execution = execute_task_file_result(
            task_file,
            cwd=str(project_path),
            timeout_seconds=settings.task_timeout_seconds,
            max_output_chars=settings.max_output_chars,
        )
        audit_log({
            "kind": "run-all-tasks",
            "api_key": api_key[-4:],
            "project": selected_name,
            "task": item["name"],
            "exit_code": execution.exit_code,
            "duration_ms": execution.duration_ms,
        })

        do_commit = body.auto_git_commit if body.auto_git_commit is not None else settings.auto_git_commit_on_task
        git_commit = maybe_git_commit(project_path, item["name"], do_commit, execution.exit_code)

        task_result = {
            "task": item["name"],
            "output": execution.output,
            "exit_code": execution.exit_code,
            "started_at": execution.started_at,
            "duration_ms": execution.duration_ms,
        }
        if git_commit is not None:
            task_result["git_commit"] = git_commit
        results.append(task_result)

    return {"project": selected_name, "results": results, "count": len(results)}


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

    do_commit = body.auto_git_commit if body.auto_git_commit is not None else settings.auto_git_commit_on_task
    git_commit = maybe_git_commit(project_path, body.command, do_commit, execution.exit_code)

    response = {
        "project": selected_name,
        "command": body.command,
        "output": execution.output,
        "exit_code": execution.exit_code,
        "started_at": execution.started_at,
        "duration_ms": execution.duration_ms,
        "auto_approve": auto_approve,
        "delay_seconds": delay_seconds,
    }
    if git_commit is not None:
        response["git_commit"] = git_commit
    return response


@app.get("/project/git-diff")
async def get_project_git_diff(
    request: Request,
    project: Optional[str] = None,
    staged: bool = False,
    x_api_key: str = Header(None),
):
    """
    Get git diff for the selected project.

    Returns the full diff and diff statistics, enabling a git-diff view
    similar to copilot-ralph's per-task change viewer.

    Query params:
        project: Project name (optional, uses selected project if omitted)
        staged:  If true, returns staged diff; otherwise unstaged diff
    """
    api_key = require_protected_access(request, x_api_key, "/project/git-diff")
    selected_name, project_path = resolve_project_context(project, api_key)

    git = GitService(repo_path=str(project_path))
    is_valid, err = git.validate_repository()
    if not is_valid:
        fail(400, "NOT_A_GIT_REPO", err, "Ensure the project directory is a git repository")

    status = git.get_status()
    diff_stat = git.get_diff_stat()
    diff = git.get_diff(staged=staged)
    branch = git.get_current_branch()

    return {
        "project": selected_name,
        "branch": branch,
        "staged": staged,
        "status": status,
        "diff_stat": diff_stat,
        "diff": diff,
    }

# ─────────────────────────────────────────────
# Monitoring & Memory Endpoints (Phase 5)
# ─────────────────────────────────────────────
@app.get("/monitor/health")
async def monitor_health(request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/health")
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass
    pending = app.state.approval_store.pending()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama_running": ollama_ok,
        "telegram_started": app.state.telegram_started,
        "pending_approvals": len(pending),
    }


@app.get("/monitor/telegram-config")
async def monitor_telegram_config(request: Request, x_api_key: str = Header(None)):
    """Expose Telegram readiness so dashboard can explain why bot is not responding."""
    require_protected_access(request, x_api_key, "/monitor/telegram-config")

    token_configured = bool(settings.telegram_token)
    allowed_user_id_valid = settings.allowed_telegram_user_id > 0
    can_start = token_configured and allowed_user_id_valid

    hints = []
    if not token_configured:
        hints.append("Set TELEGRAM_TOKEN in .env to a real bot token.")
    if not allowed_user_id_valid:
        hints.append("Set ALLOWED_TELEGRAM_USER_ID in .env to a numeric Telegram user id.")

    return {
        "configured": can_start,
        "telegram_started": app.state.telegram_started,
        "token_configured": token_configured,
        "allowed_user_id_valid": allowed_user_id_valid,
        "allowed_user_id": settings.allowed_telegram_user_id,
        "hints": hints,
    }


@app.get("/monitor/logs")
async def monitor_logs(request: Request, limit: int = 50, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/logs")
    return {"entries": auditor_tail(limit)}


@app.get("/monitor/history")
async def monitor_history(request: Request, project: Optional[str] = None, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/monitor/history")
    selected_name, project_path = resolve_project_context(project, api_key)
    return {
        "project": selected_name,
        "history": get_project_history(selected_name),
        "stats": get_execution_stats(selected_name),
        "retry_suggestion": suggest_retry(selected_name),
    }


@app.get("/monitor/approvals")
async def monitor_approvals(request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/approvals")
    return {"pending": [r.to_dict() for r in app.state.approval_store.pending()]}


@app.post("/monitor/approve/{token}")
async def approve_task(token: str, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/approve")
    req = app.state.approval_store.resolve(token, approved=True)
    if not req:
        fail(404, "NOT_FOUND", "Approval token not found", "")
    return {"token": token, "status": req.status.value}


@app.post("/monitor/reject/{token}")
async def reject_task(token: str, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/reject")
    req = app.state.approval_store.resolve(token, approved=False)
    if not req:
        fail(404, "NOT_FOUND", "Approval token not found", "")
    return {"token": token, "status": req.status.value}


# ─────────────────────────────────────────────
# Phase 6 — SSE Streaming, Stats, Self-check, Timeline
# ─────────────────────────────────────────────
@app.get("/monitor/stream/logs")
async def stream_logs(request: Request, x_api_key: str = Header(None), api_key: Optional[str] = None):
    """Server-Sent Events: streams new audit log entries as they arrive."""
    require_protected_access(request, x_api_key or api_key, "/monitor/stream/logs")

    async def event_generator():
        seen = 0
        while True:
            if await request.is_disconnected():
                break
            entries = auditor_tail(200)
            new_entries = entries[seen:]
            for entry in new_entries:
                data = json.dumps(entry, ensure_ascii=False)
                yield f"data: {data}\n\n"
            seen = len(entries)
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/monitor/stats")
async def monitor_stats(request: Request, x_api_key: str = Header(None)):
    """Enhanced execution metrics across all projects."""
    require_protected_access(request, x_api_key, "/monitor/stats")
    from services.memory_service import _connect
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM executions").fetchone()[0]
        failures = conn.execute("SELECT COUNT(*) FROM executions WHERE exit_code != 0").fetchone()[0]
        avg_duration = conn.execute("SELECT AVG(duration_ms) FROM executions").fetchone()[0]
        most_project = conn.execute(
            "SELECT project, COUNT(*) as c FROM executions WHERE project IS NOT NULL GROUP BY project ORDER BY c DESC LIMIT 1"
        ).fetchone()
        most_task = conn.execute(
            "SELECT task, COUNT(*) as c FROM executions WHERE task IS NOT NULL GROUP BY task ORDER BY c DESC LIMIT 1"
        ).fetchone()

    return {
        "total_executions": total,
        "total_failures": failures,
        "failure_rate": round(failures / total * 100, 1) if total else 0,
        "success_rate": round((total - failures) / total * 100, 1) if total else 0,
        "average_execution_ms": round(avg_duration or 0, 1),
        "most_used_project": most_project[0] if most_project else None,
        "most_used_task": most_task[0] if most_task else None,
    }


@app.get("/monitor/self-check")
async def self_check(request: Request, x_api_key: str = Header(None)):
    """Validate all subsystems: Ollama, DB, approval store, DSL."""
    require_protected_access(request, x_api_key, "/monitor/self-check")
    results = {}

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            results["ollama"] = "ok" if r.status_code == 200 else "unreachable"
    except Exception:
        results["ollama"] = "unreachable"

    # DB write/read
    try:
        from services.memory_service import record_execution, get_execution_stats
        record_execution(user="self-check", project=None, task="self-check", command=None,
                         plan_type="chat", exit_code=0, duration_ms=0, approved=True)
        stats = get_execution_stats()
        results["database"] = "ok" if stats["total"] >= 0 else "error"
    except Exception as e:
        results["database"] = f"error: {e}"

    # Approval store
    try:
        store = app.state.approval_store
        results["approval_store"] = f"ok ({len(store.list_all())} total)"
    except Exception as e:
        results["approval_store"] = f"error: {e}"

    # DSL validation
    try:
        from agents.task_dsl import TaskDefinition, validate_task_definition
        test_def = TaskDefinition(task="test", type="command", command="echo ok",
                                  task_file=None, timeout=10, auto_approve=True,
                                  delay_seconds=0, description="")
        err = validate_task_definition(test_def)
        results["dsl_validation"] = "ok" if err is None else f"error: {err}"
    except Exception as e:
        results["dsl_validation"] = f"error: {e}"

    results["overall"] = "ok" if all(v == "ok" or str(v).startswith("ok") for v in results.values()) else "degraded"
    return results


@app.get("/monitor/timeline")
async def monitor_timeline(request: Request, limit: int = 50, x_api_key: str = Header(None)):
    """Chronological execution activity feed."""
    require_protected_access(request, x_api_key, "/monitor/timeline")
    from services.memory_service import _connect
    with _connect() as conn:
        rows = conn.execute(
            "SELECT ts, user, project, task, command, plan_type, exit_code, duration_ms FROM executions ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"timeline": [dict(r) for r in rows], "count": len(rows)}


@app.get("/queue/status")
async def get_queue_status(request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/queue/status")
    status = queue_status()
    if status["queue_empty"] and status["later_available"]:
        status["admin_prompt"] = "Queue is empty but 'later' tasks are available. POST /queue/promote-later to move them into queue, then POST /queue/run."
    return status


@app.post("/queue/run")
async def api_run_queue(request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/queue/run")
    results = run_queue(
        timeout_seconds=settings.command_timeout_seconds,
        task_timeout_seconds=settings.task_timeout_seconds,
        max_output_chars=settings.max_output_chars,
        strict_mode=settings.strict_command_mode,
        allowed_prefixes=settings.allowed_command_prefixes,
    )
    for r in results:
        audit_log({"kind": "queue-run", "api_key": api_key[-4:], "task": r.name, "status": r.status, "exit_code": r.exit_code})

    status = queue_status()
    response = {
        "processed": len(results),
        "results": [{"task": r.name, "status": r.status, "exit_code": r.exit_code, "duration_ms": r.duration_ms, "output": r.output} for r in results],
    }
    if status["queue_empty"] and status["later_available"]:
        response["admin_prompt"] = "Queue is now empty. 'later' tasks are available — POST /queue/promote-later to schedule them."
    return response


@app.post("/queue/promote-later")
async def api_promote_later(request: Request, x_api_key: str = Header(None)):
    api_key = require_protected_access(request, x_api_key, "/queue/promote-later")
    moved = promote_later_to_queue()
    if not moved:
        return {"moved": [], "message": "No tasks in 'later' folder."}
    audit_log({"kind": "promote-later", "api_key": api_key[-4:], "moved": moved})
    return {
        "moved": moved,
        "count": len(moved),
        "message": f"Moved {len(moved)} task(s) from later/ to queue/. POST /queue/run to process.",
    }


# ─────────────────────────────────────────────
# Phase 7–14 Endpoints
# ─────────────────────────────────────────────
@app.get("/monitor/mode")
async def get_mode(request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/mode")
    return mode_info()


@app.get("/monitor/risk")
async def get_risk(command: str, project: Optional[str] = None, request: Request = None, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/risk")
    risk = score_plan(command, project, "command", auto_approve=True)
    return risk.to_dict()


@app.get("/monitor/replay/{execution_id}")
async def replay(execution_id: int, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/replay")
    return replay_execution(
        execution_id,
        strict_mode=settings.strict_command_mode,
        allowed_prefixes=settings.allowed_command_prefixes,
        timeout_seconds=settings.command_timeout_seconds,
        max_output_chars=settings.max_output_chars,
    )


@app.get("/monitor/nodes")
async def get_nodes(request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/nodes")
    return {"nodes": [n.to_dict() for n in node_registry.all_nodes()], "alive": len(node_registry.alive_nodes())}


@app.post("/monitor/nodes/register")
async def register_node(node_id: str, host: str, port: int, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/nodes/register")
    node = node_registry.register(node_id, host, port)
    return node.to_dict()


@app.post("/monitor/nodes/{node_id}/heartbeat")
async def node_heartbeat(node_id: str, request: Request, x_api_key: str = Header(None)):
    require_protected_access(request, x_api_key, "/monitor/nodes")
    ok = node_registry.heartbeat(node_id)
    return {"node_id": node_id, "updated": ok}


@app.get("/monitor/heatmap")
async def heatmap(request: Request, x_api_key: str = Header(None)):
    """Execution frequency by project and hour for visualization."""
    require_protected_access(request, x_api_key, "/monitor/heatmap")
    from services.memory_service import _connect
    with _connect() as conn:
        rows = conn.execute("""
            SELECT project,
                   strftime('%H', datetime(ts, 'unixepoch')) as hour,
                   COUNT(*) as count
            FROM executions
            WHERE project IS NOT NULL
            GROUP BY project, hour
            ORDER BY project, hour
        """).fetchall()
    return {"heatmap": [dict(r) for r in rows]}


def build_telegram():
    selected_project: dict[str, Optional[str]] = {"name": None, "path": None}

    async def handle_message_text(text: str) -> str:
        result = await run_agent(text, execute=False)
        return result.reply

    def handle_projects() -> str:
        projects = list_projects()
        if not projects:
            return "No projects found under configured PROJECT_ROOT/PROJECT_ROOTS."
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
            return (
                f"✅ Selected project: {project_name}\n"
                f"🧩 run-task files available: {len(tasks)}\n\n"
                f"Use /task <file_name> to run one. {open_message}"
            )

        return (
            f"✅ Selected project: {project_name}\n"
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
        return f"📌 Current project: {selected_project['name']}"

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
        roots_text = ", ".join(settings.project_roots) if settings.project_roots else settings.project_root
        return (
            "✅ Runtime Status\n"
            f"Model: {settings.ollama_model}\n"
            f"Ollama URL: {settings.ollama_url}\n"
            f"Host/Port: {settings.host}:{settings.port}\n"
            f"PROJECT_ROOTS: {roots_text}"
        )

    async def handle_run_all_tasks() -> str:
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
            return "ℹ️ No tasks found in run-task folder."

        lines = []
        for item in tasks:
            task_file = get_task_file(project_path, item["name"])
            if not task_file:
                lines.append(f"⏭ {item['name']}: skipped (file not found)")
                continue

            auto_approve = bool(item.get("auto_approve", settings.auto_approve_default))
            if not auto_approve:
                lines.append(f"⏭ {item['name']}: skipped (approval required)")
                continue

            delay = int(item.get("delay_seconds", settings.default_execution_delay_seconds))
            if delay > 0:
                await asyncio.sleep(delay)

            execution = execute_task_file_result(
                task_file,
                cwd=str(project_path),
                timeout_seconds=settings.task_timeout_seconds,
                max_output_chars=500,
            )
            status = "✅" if execution.exit_code == 0 else "❌"
            lines.append(f"{status} {item['name']} (exit={execution.exit_code}, {execution.duration_ms}ms)")

        return "\n".join(lines) if lines else "No tasks executed."

    def handle_approve(token: str) -> str:
        req = app.state.approval_store.resolve(token, approved=True)
        if not req:
            return f"❌ Token '{token}' not found."
        return f"✅ Approved: {req.plan.task} (token={token})"

    def handle_reject(token: str) -> str:
        req = app.state.approval_store.resolve(token, approved=False)
        if not req:
            return f"❌ Token '{token}' not found."
        return f"🚫 Rejected: {req.plan.task} (token={token})"

    def handle_queue_status() -> str:
        status = queue_status()
        lines = [
            f"📋 Queue ({len(status['queue'])} tasks): " + (", ".join(status['queue']) or "empty"),
            f"⏳ Later ({len(status['later'])} tasks): " + (", ".join(status['later']) or "none"),
            f"✅ Completed: {len(status['completed'])} tasks",
        ]
        if status["queue_empty"] and status["later_available"]:
            lines.append("\n⚠️ Queue is empty but 'later' tasks exist. Use /qlater to promote them.")
        return "\n".join(lines)

    async def handle_queue_run() -> str:
        status = queue_status()
        if status["queue_empty"]:
            msg = "ℹ️ Queue is empty."
            if status["later_available"]:
                msg += " 'later' tasks are available — use /qlater to promote them into the queue."
            return msg

        results = run_queue(
            timeout_seconds=settings.command_timeout_seconds,
            task_timeout_seconds=settings.task_timeout_seconds,
            max_output_chars=500,
            strict_mode=settings.strict_command_mode,
            allowed_prefixes=settings.allowed_command_prefixes,
        )

        lines = [f"▶ Processed {len(results)} task(s):"]
        for r in results:
            icon = "✅" if r.status in ("executed", "planned") else "❌" if r.status == "failed" else "⏭"
            lines.append(f"{icon} {r.name} — {r.status} (exit={r.exit_code}, {r.duration_ms}ms)")

        after = queue_status()
        if after["queue_empty"] and after["later_available"]:
            lines.append("\n⚠️ Queue now empty. 'later' tasks are available — use /qlater to schedule them.")

        return "\n".join(lines)

    def handle_promote_later() -> str:
        moved = promote_later_to_queue()
        if not moved:
            return "ℹ️ No tasks in 'later' folder."
        return (
            f"✅ Moved {len(moved)} task(s) from later/ → queue/:\n"
            + "\n".join(f"  • {name}" for name in moved)
            + "\n\nUse /qrun to process them."
        )

    def handle_git_commit(path: str, jira: str, remark: str, no_push: bool) -> str:
        from tools.git_service import GitService
        
        # Use selected project path if no path provided
        if not path and selected_project["path"]:
            path = selected_project["path"]
        
        git = GitService(path)
        
        # Validate repository
        is_valid, error = git.validate_repository()
        if not is_valid:
            return f"❌ {error}"
        
        # Get current branch
        branch = git.get_current_branch()
        
        # Warn if protected branch
        if git.is_protected_branch(branch):
            return f"⚠️ Protected branch '{branch}'. Use CLI for manual control: python tools/ayazgitdy.py"
        
        # Get changes
        changes = git.get_status()
        if changes["total"] == 0:
            return "ℹ️ No changes detected. Nothing to commit."
        
        # Detect commit type and generate message
        diff = git.get_diff()
        diff_stat = git.get_diff_stat()
        commit_type = git.detect_commit_type(changes, diff)
        summary = git.generate_commit_summary(changes, diff_stat)
        
        # Validate Jira if provided
        if jira and not git.validate_jira_ticket(jira):
            return f"❌ Invalid Jira format: {jira} (expected: ABC-123)"
        
        # Generate commit message
        message = git.format_commit_message(
            commit_type=commit_type,
            summary=summary,
            changes=changes,
            jira_ticket=jira.upper() if jira else None,
            remark=remark
        )
        
        # Execute commit and push
        should_push = not no_push
        result = git.commit_and_push(message, push=should_push)
        
        if not result["success"]:
            return f"❌ Commit failed: {result['error']}"
        
        response_lines = [
            f"✅ Branch: {result['branch']}",
            f"✅ Commit: {result['commit_hash']}",
            f"✅ Files: {changes['total']} changed",
        ]
        
        if result["pushed"]:
            response_lines.append(f"✅ Pushed to origin/{result['branch']}")
        else:
            response_lines.append("ℹ️ Committed locally (not pushed)")
        
        response_lines.append(f"\n📝 Message:\n{message[:200]}...")
        
        return "\n".join(response_lines)

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
        run_all_tasks_handler=handle_run_all_tasks,
        approve_handler=handle_approve,
        reject_handler=handle_reject,
        queue_status_handler=handle_queue_status,
        queue_run_handler=handle_queue_run,
        promote_later_handler=handle_promote_later,
        git_commit_handler=handle_git_commit,
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
