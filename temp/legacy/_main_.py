"""
AI Agent - FastAPI REST API + Telegram Bot + Ollama
Optimized for: Windows 10/11 + Official Ollama Installer (ollama.com)

Run:
    pip install -r requirements.txt
    python main.py
"""

import asyncio
import logging
import subprocess
import os
import shutil
import platform
import time
import socket
import re
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from update_engine import CodeUpdater

from ide_runner import run_with_fallback
from project_utils import list_projects, get_project_path

# Prefer standard .env, but also support a file named `env`.
if not load_dotenv():
    load_dotenv("env")

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


PROJECT_ROOT = os.getenv("PROJECT_ROOT")



updater = CodeUpdater(
    project_root=PROJECT_ROOT,
    allowed_files=[
        "src/routes.js",
        "gulpfile.js",
        "main.py"
    ]
)

success, message = updater.update_file(
    relative_path="src/routes.js",
    new_code="app.get('/health', (req,res)=>res.send('OK'));",
    marker="AI:ROUTES",
    mode="INSERT_AFTER"
)

print(message)

# ══════════════════════════════════════════════════════════════════════════════
#  WINDOWS OLLAMA PATH DETECTION
#  Official installer (ollama.com) puts ollama.exe here:
#    C:\Users\<YOU>\AppData\Local\Programs\Ollama\ollama.exe
# ══════════════════════════════════════════════════════════════════════════════

def find_ollama_binary_windows() -> str:
    """
    Find ollama.exe on Windows.
    Checks .env override → PATH → all known Windows install locations.
    """

    # 1. .env / environment override
    env_bin = os.getenv("OLLAMA_BIN", "")
    if env_bin:
        expanded = os.path.expandvars(env_bin)
        if os.path.isfile(expanded):
            log.info(f"✅ Ollama [.env override]: {expanded}")
            return expanded

    # 2. Already in system PATH (works if Windows installer added it)
    in_path = shutil.which("ollama")
    if in_path:
        log.info(f"✅ Ollama [PATH]: {in_path}")
        return in_path

    # 3. Official installer default locations (tries current user + common users)
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    user_profile   = os.environ.get("USERPROFILE", "")
    program_files  = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    program_files86= os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")

    candidates = [
        # ✅ Official installer default (most common)
        os.path.join(local_app_data, r"Programs\Ollama\ollama.exe"),

        # Other possible locations
        os.path.join(program_files, r"Ollama\ollama.exe"),
        os.path.join(program_files86, r"Ollama\ollama.exe"),
        os.path.join(user_profile, r"Ollama\ollama.exe"),
        r"C:\ollama\ollama.exe",
        r"C:\tools\ollama\ollama.exe",
    ]

    for path in candidates:
        if os.path.isfile(path):
            log.info(f"✅ Ollama [found]: {path}")
            return path

    # 4. Search common drives as last resort
    for drive in ["C:", "D:"]:
        for sub in [r"\ollama\ollama.exe", r"\Program Files\Ollama\ollama.exe"]:
            p = drive + sub
            if os.path.isfile(p):
                log.info(f"✅ Ollama [drive search]: {p}")
                return p

    log.error("❌ ollama.exe NOT FOUND on this system!")
    log.error("   → Download from: https://ollama.com/download/windows")
    log.error("   → Or set OLLAMA_BIN=C:\\path\\to\\ollama.exe in .env")
    return "ollama"  # last-ditch fallback


def find_ollama_models_dir_windows() -> Optional[str]:
    """
    Find where Ollama stores models on Windows.
    Default: C:\\Users\\<YOU>\\.ollama\\models
    """
    # Env override
    env_path = os.getenv("OLLAMA_MODELS", "")
    if env_path and os.path.isdir(env_path):
        return env_path

    user_profile = os.environ.get("USERPROFILE", "")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    candidates = [
        os.path.join(user_profile, ".ollama", "models"),       # default
        os.path.join(local_app_data, "Ollama", "models"),
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return None


def get_installed_models(ollama_bin: str) -> list:
    """Run `ollama list` → return list of model names."""
    try:
        result = subprocess.run(
            [ollama_bin, "list"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW  # hide console popup on Windows
        )
        lines = result.stdout.strip().splitlines()
        return [line.split()[0] for line in lines[1:] if line.strip()]
    except Exception as e:
        log.warning(f"Could not list models: {e}")
        return []


def ensure_ollama_running(ollama_bin: str) -> bool:
    """Check if Ollama server is up; if not, launch it silently on Windows."""
    try:
        import httpx as _h
        _h.get("http://localhost:11434", timeout=2)
        log.info("✅ Ollama server already running")
        return True
    except Exception:
        pass

    log.info("🚀 Starting Ollama server (background)...")
    try:
        subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        )
        time.sleep(4)   # give it a moment to bind port
        log.info("✅ Ollama server started")
        return True
    except Exception as e:
        log.error(f"❌ Could not start Ollama: {e}")
        return False


# ─── Detect at startup ────────────────────────────────────────────────────────
OLLAMA_BIN    = find_ollama_binary_windows()
OLLAMA_MODELS = find_ollama_models_dir_windows()
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

# Optional free-tier provider (OpenAI-compatible API).
FREE_AI_ENABLED = os.getenv("FREE_AI_ENABLED", "false").lower() == "true"
FREE_AI_BASE_URL = os.getenv("FREE_AI_BASE_URL", "")
FREE_AI_API_KEY = os.getenv("FREE_AI_API_KEY", "")
FREE_AI_MODEL = os.getenv("FREE_AI_MODEL", "")
FREE_AI_TIMEOUT = int(os.getenv("FREE_AI_TIMEOUT", "60"))
USE_FREE_AI_FALLBACK = os.getenv("USE_FREE_AI_FALLBACK", "true").lower() == "true"

# Project task runner settings.
PROJECT_DIR = os.getenv("PROJECT_DIR", r"C:\_IMPACT\tomcat\webapps\impact_vite")
OPENCODE_CMD_TEMPLATE = os.getenv("OPENCODE_CMD_TEMPLATE", 'opencode run --prompt "{prompt}"')
CURSOR_CMD_TEMPLATE = os.getenv("CURSOR_CMD_TEMPLATE", 'cursor-agent "{prompt}"')

ALLOWED_TELEGRAM_USER_ID = int(os.getenv("ALLOWED_TELEGRAM_USER_ID", "0"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "mysecretkey123")
HOST           = os.getenv("HOST", "0.0.0.0")
PORT           = int(os.getenv("PORT", 8000))

log.info(f"🖥️  OS            : {platform.system()} {platform.release()} {platform.machine()}")
log.info(f"📂 Ollama binary : {OLLAMA_BIN}")
log.info(f"📂 Models dir    : {OLLAMA_MODELS or 'not found'}")
log.info(f"🤖 Default model : {OLLAMA_MODEL}")


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a powerful AI assistant running locally on Windows.
You help users write code, explain concepts, debug issues, and automate tasks.
When the user asks you to run a shell command, respond with: RUN_CMD: <command>
Be concise, accurate, and helpful."""


# ══════════════════════════════════════════════════════════════════════════════
#  FASTAPI APP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Ollama AI Agent",
    description="Local AI Agent - REST API + Telegram Bot (Windows + Ollama)",
    version="2.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None  # ollama | free
    execute_commands: bool = False   # allow agent to run shell cmds

class AgentResponse(BaseModel):
    reply: str
    command_output: Optional[str] = None
    model_used: str


class ProjectTaskRequest(BaseModel):
    prompt: str
    runner: str = "opencode"  # opencode | cursor | shell
    project_dir: Optional[str] = None
    command: Optional[str] = None  # required for runner=shell


class ProjectTaskResponse(BaseModel):
    ok: bool
    runner: str
    command: str
    cwd: str
    output: str


# ─── Core: Ollama call ────────────────────────────────────────────────────────

async def call_ollama(prompt: str, model: str = None) -> str:
    model = model or OLLAMA_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "keep_alive": OLLAMA_KEEP_ALIVE
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            r.raise_for_status()
            return r.json().get("response", "").strip()

    except httpx.ConnectError:
        # Auto-start Ollama if not running
        if ensure_ollama_running(OLLAMA_BIN):
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
                return r.json().get("response", "").strip()
        raise HTTPException(503,
            f"Ollama is not running.\n"
            f"Start it manually: open CMD and run:\n"
            f'  "{OLLAMA_BIN}" serve'
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(500, f"Ollama API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {e}")


async def call_free_ai(prompt: str, model: str = None) -> str:
    """Call an OpenAI-compatible chat-completions endpoint."""
    if not FREE_AI_ENABLED:
        raise HTTPException(503, "Free AI provider disabled (FREE_AI_ENABLED=false)")
    if not FREE_AI_BASE_URL or not FREE_AI_API_KEY or not (model or FREE_AI_MODEL):
        raise HTTPException(
            503,
            "Free AI provider is not configured. Set FREE_AI_BASE_URL, FREE_AI_API_KEY, FREE_AI_MODEL."
        )

    base = FREE_AI_BASE_URL.rstrip("/")
    payload = {
        "model": model or FREE_AI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    headers = {"Authorization": f"Bearer {FREE_AI_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=FREE_AI_TIMEOUT) as client:
            r = await client.post(f"{base}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        raise HTTPException(500, f"Free AI API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(500, f"Free AI request failed: {e}")


async def call_model(prompt: str, model: str = None, provider: Optional[str] = None) -> str:
    """Route inference to Ollama or free-tier provider with optional fallback."""
    selected = (provider or "ollama").strip().lower()
    if selected == "free":
        return await call_free_ai(prompt, model)
    if selected == "ollama":
        try:
            return await call_ollama(prompt, model)
        except Exception as ollama_error:
            if FREE_AI_ENABLED and USE_FREE_AI_FALLBACK:
                log.warning(f"⚠️  Ollama failed, using free fallback: {ollama_error}")
                return await call_free_ai(prompt, model)
            raise
    raise HTTPException(400, "Invalid provider. Use 'ollama' or 'free'.")


def fast_local_reply(prompt: str) -> Optional[str]:
    """
    Return an instant local reply for very short social prompts.
    This avoids model round-trips for messages like "hi".
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", prompt).strip().lower()
    if not cleaned:
        return None

    quick_map = {
        "hi": "Hi. How can I help?",
        "hello": "Hello. What do you need help with?",
        "hey": "Hey. What should I work on?",
        "yo": "Hi. What do you want to build or fix?",
        "thanks": "You're welcome.",
        "thank you": "You're welcome.",
        "ok": "Okay.",
    }
    return quick_map.get(cleaned)


async def warmup_ollama_model():
    """Preload the model once so first real request is faster."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "hi",
        "system": "Reply with one short word.",
        "stream": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {"num_predict": 1}
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            r.raise_for_status()
        log.info("✅ Ollama model warm-up complete")
    except Exception as e:
        log.warning(f"⚠️  Warm-up skipped: {e}")


# ─── Core: Shell command (PowerShell on Windows) ──────────────────────────────

def execute_command(cmd: str, cwd: Optional[str] = None) -> str:
    try:
        # Use PowerShell on Windows for better command support
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=cwd
        )
        output = result.stdout or result.stderr or "(no output)"
        return output[:2000]
    except subprocess.TimeoutExpired:
        return "⚠️ Command timed out after 30 seconds."
    except FileNotFoundError:
        # Fallback to cmd.exe if PowerShell not available
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=cwd
            )
            return (result.stdout or result.stderr or "(no output)")[:2000]
        except Exception as e:
            return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


# ─── Core: Agent logic ────────────────────────────────────────────────────────

async def run_agent(
    prompt: str,
    model: str = None,
    provider: str = None,
    execute: bool = False
) -> AgentResponse:
    instant = fast_local_reply(prompt)
    if instant:
        return AgentResponse(
            reply=instant,
            command_output=None,
            model_used="local-fast-reply"
        )

    reply = await call_model(prompt, model, provider)
    cmd_output = None

    if "RUN_CMD:" in reply and execute:
        for line in reply.split("\n"):
            if line.strip().startswith("RUN_CMD:"):
                cmd = line.replace("RUN_CMD:", "").strip()
                log.info(f"⚙️  Executing (PowerShell): {cmd}")
                cmd_output = execute_command(cmd)
                break

    return AgentResponse(
        reply=reply,
        command_output=cmd_output,
        model_used=(model or (FREE_AI_MODEL if (provider or "ollama").lower() == "free" else OLLAMA_MODEL))
    )


def build_runner_command(
    runner: str,
    prompt: str,
    project_dir: str,
    custom_command: Optional[str]
) -> str:
    runner = runner.lower().strip()
    prompt_escaped = prompt.replace('"', '\\"')
    project_dir_escaped = project_dir.replace('"', '\\"')
    if runner == "opencode":
        return OPENCODE_CMD_TEMPLATE.format(prompt=prompt_escaped, project_dir=project_dir_escaped)
    if runner == "cursor":
        return CURSOR_CMD_TEMPLATE.format(prompt=prompt_escaped, project_dir=project_dir_escaped)
    if runner == "shell":
        if not custom_command:
            raise HTTPException(400, "runner='shell' requires 'command'")
        return custom_command
    raise HTTPException(400, "Invalid runner. Use 'opencode', 'cursor', or 'shell'.")

def try_runner(runner_name, prompt, project_dir):
    try:
        cmd = build_runner_command(runner_name, prompt, project_dir, None)
        output = execute_command(cmd, cwd=project_dir)

        if "error" in output.lower():
            return False, output

        return True, output
    except Exception as e:
        return False, str(e)
    
    
# ══════════════════════════════════════════════════════════════════════════════
#  REST API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", summary="Status")
async def root():
    return {
        "status": "running 🤖",
        "model": OLLAMA_MODEL,
        "ollama_binary": OLLAMA_BIN,
        "docs": f"http://localhost:{PORT}/docs"
    }


@app.get("/health", summary="Health check + Ollama info")
async def health():
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    models = get_installed_models(OLLAMA_BIN)
    return {
        "status": "ok" if ollama_ok else "degraded (Ollama not running)",
        "ollama_running": ollama_ok,
        "ollama_binary": OLLAMA_BIN,
        "models_dir": OLLAMA_MODELS,
        "installed_models": models,
        "active_model": OLLAMA_MODEL,
        "platform": f"Windows {platform.release()} {platform.machine()}"
    }


@app.get("/models", summary="List installed Ollama models")
async def list_models():
    return {
        "installed_models": get_installed_models(OLLAMA_BIN),
        "models_dir": OLLAMA_MODELS,
        "ollama_binary": OLLAMA_BIN
    }


@app.post("/chat", response_model=AgentResponse, summary="Simple chat — no auth needed")
async def chat(body: PromptRequest):
    """Public chat endpoint. No authentication, no command execution."""
    return await run_agent(body.prompt, body.model, body.provider, execute=False)


@app.post("/run-task", response_model=AgentResponse, summary="Protected task runner")
async def run_task(
    body: PromptRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Full agent endpoint. Requires X-Api-Key header.
    Set execute_commands=true to allow shell (PowerShell) execution.
    """
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(401, "Invalid or missing X-Api-Key header")
    return await run_agent(body.prompt, body.model, body.provider, body.execute_commands)


@app.post("/pull-model", summary="Download an Ollama model")
async def pull_model(model: str, x_api_key: Optional[str] = Header(None)):
    """Download a new model. Example: model=mistral  or  model=codellama"""
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(401, "Unauthorized")
    log.info(f"📦 Pulling model: {model}")
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/pull",
                json={"name": model, "stream": False}
            )
            return {"pulled": model, "response": r.json()}
    except Exception as e:
        raise HTTPException(500, f"Pull failed: {e}")


@app.post("/run-project-task", response_model=ProjectTaskResponse, summary="Run opencode/cursor task in project folder")
async def run_project_task(body: ProjectTaskRequest, x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(401, "Unauthorized")

    project_dir = body.project_dir or PROJECT_DIR
    if not os.path.isdir(project_dir):
        raise HTTPException(400, f"Project folder not found: {project_dir}")

    cmd = build_runner_command(body.runner, body.prompt, project_dir, body.command)
    log.info(f"🧰 Project task [{body.runner}] in {project_dir}: {cmd}")
    output = execute_command(cmd, cwd=project_dir)
    return ProjectTaskResponse(
        ok=not output.lower().startswith("error:"),
        runner=body.runner,
        command=cmd,
        cwd=project_dir,
        output=output
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TELEGRAM BOT
# ══════════════════════════════════════════════════════════════════════════════

async def tg_start(update, ctx):
    models = get_installed_models(OLLAMA_BIN)
    model_list = "\n".join(f"  • {m}" for m in models) if models else "  ⚠️ None installed"
    await update.message.reply_text(
        f"👋 *AI Agent — Windows + Ollama*\n\n"
        f"🤖 Model: `{OLLAMA_MODEL}`\n"
        f"📂 Binary: `{OLLAMA_BIN}`\n"
        f"📂 Models: `{OLLAMA_MODELS}`\n\n"
        f"📦 *Installed models:*\n{model_list}\n\n"
        f"✅ Just send me any task or question!",
        parse_mode="Markdown"
    )

async def tg_help(update, ctx):
    await update.message.reply_text(
        "💡 *What can I do?*\n\n"
        "• Write code in any language\n"
        "• Debug and fix errors\n"
        "• Explain technical concepts\n"
        "• Help with Windows scripts (PowerShell/Batch)\n"
        "• Answer any question\n\n"
        "*Commands:*\n"
        "/start — Bot info & models\n"
        "/model — Current model\n"
        "/models — All installed models\n"
        "/help — This message",
        
        parse_mode="Markdown"
    )

async def tg_model(update, ctx):
    await update.message.reply_text(
        f"🤖 Active model: `{OLLAMA_MODEL}`\n"
        f"📂 Binary path: `{OLLAMA_BIN}`",
        parse_mode="Markdown"
    )

async def tg_models(update, ctx):
    models = get_installed_models(OLLAMA_BIN)
    if models:
        text = "📦 *Installed Ollama models:*\n" + "\n".join(f"  • `{m}`" for m in models)
        text += f"\n\n📂 Stored at: `{OLLAMA_MODELS}`"
    else:
        text = (
            "⚠️ *No models installed.*\n\n"
            "Open Command Prompt and run:\n"
            f"`{OLLAMA_BIN} pull llama3.2`"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def tg_message(update, ctx):
    user_msg = update.message.text
    user = update.effective_user.first_name
    log.info(f"📱 Telegram [{user}]: {user_msg[:80]}")

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    try:
        result = await run_agent(user_msg, execute=False)
        reply = result.reply
        if len(reply) > 4096:
            reply = reply[:4090] + "\n..."
        await update.message.reply_text(reply)
    except HTTPException as e:
        await update.message.reply_text(f"❌ Error: {e.detail}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error: {e}")
async def tg_ai(update, ctx):
    text = update.message.text.split(" ", 2)

    if len(text) < 3:
        await update.message.reply_text("Usage:\n/ai <project> <prompt>")
        return

    project_name = text[1]
    prompt = text[2]

    project_path = get_project_path(project_name)
    if not project_path:
        await update.message.reply_text("Project not found.")
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    runner_used, output = await run_with_fallback(prompt, str(project_path))

    if len(output) > 4000:
        output = output[:4000] + "\n...truncated"

    await update.message.reply_text(
        f"🤖 Runner: {runner_used}\n\n{output}"
    )

def build_telegram_app():
    from telegram.ext import Application, CommandHandler, MessageHandler, filters

    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        log.warning("⚠️  TELEGRAM_TOKEN not set — Telegram bot disabled.")
        log.warning("    Add your token to .env to enable it.")
        return None

    tg = Application.builder().token(TELEGRAM_TOKEN).build()
    tg.add_handler(CommandHandler("start",  tg_start))
    tg.add_handler(CommandHandler("help",   tg_help))
    tg.add_handler(CommandHandler("model",  tg_model))
    tg.add_handler(CommandHandler("models", tg_models))
    tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_message))
    tg.add_handler(CommandHandler("projects", tg_projects))
    tg.add_handler(CommandHandler("run", tg_run))
    tg.add_handler(CommandHandler("ai", tg_ai))
    return tg


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def startup_checks():
    log.info("=" * 60)
    log.info("   🤖  AI Agent — Windows Startup Checks")
    log.info("=" * 60)

    # Check binary exists
    if not os.path.isfile(OLLAMA_BIN) and not shutil.which(OLLAMA_BIN):
        log.error(f"❌ ollama.exe not found: {OLLAMA_BIN}")
        log.error("   Download: https://ollama.com/download/windows")
        log.error("   Or set OLLAMA_BIN=C:\\path\\to\\ollama.exe in .env")
    else:
        log.info(f"✅ ollama.exe     : {OLLAMA_BIN}")

    # Check models
    models = get_installed_models(OLLAMA_BIN)
    if models:
        log.info(f"✅ Models found   : {', '.join(models)}")
        if not any(OLLAMA_MODEL.split(":")[0] in m for m in models):
            log.warning(f"⚠️  Model '{OLLAMA_MODEL}' not installed.")
            log.warning(f"   Run in CMD: ollama pull {OLLAMA_MODEL}")
    else:
        log.warning("⚠️  No models installed.")
        log.warning(f"   Run in CMD: ollama pull {OLLAMA_MODEL}")

    # Auto-start Ollama server
    ensure_ollama_running(OLLAMA_BIN)

    log.info(f"✅ Models dir     : {OLLAMA_MODELS or 'not found'}")
    log.info(f"🌐 REST API       : http://localhost:{PORT}")
    log.info(f"📖 API Docs       : http://localhost:{PORT}/docs")
    log.info("=" * 60)


def is_port_in_use(host: str, port: int) -> bool:
    """Return True if a TCP port is already bound."""
    bind_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((bind_host, port))
            return False
        except OSError:
            return True


def find_available_port(host: str, start_port: int, attempts: int = 50) -> int:
    """Find the first available TCP port from start_port to start_port+attempts."""
    for p in range(start_port, start_port + attempts + 1):
        if not is_port_in_use(host, p):
            return p
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + attempts}")


PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "D:/Projects"))
active_project = None

def list_projects():
    if not PROJECT_ROOT.exists():
        return "Project root not found."

    projects = [p.name for p in PROJECT_ROOT.iterdir() if p.is_dir()]
    if not projects:
        return "No projects found."

    return "Available Projects:\n" + "\n".join(f"- {p}" for p in projects)

def update_file(file_path, marker, new_code, mode="INSERT_AFTER"):
    path = Path(file_path)

    if not path.exists():
        return "File not found."

    content = path.read_text()

    if marker not in content:
        return "Marker not found."

    if mode == "INSERT_AFTER":
        updated = content.replace(marker, marker + "\n" + new_code)

    elif mode == "INSERT_BEFORE":
        updated = content.replace(marker, new_code + "\n" + marker)

    elif mode == "REPLACE_BLOCK":
        start = f"{marker}_START"
        end = f"{marker}_END"

        if start in content and end in content:
            before = content.split(start)[0]
            after = content.split(end)[1]
            updated = before + start + "\n" + new_code + "\n" + end + after
        else:
            return "Block markers not found."
    else:
        return "Invalid mode."

    path.write_text(updated)
    return "File updated successfully."

def is_allowed(update):
    return update.effective_user.id == ALLOWED_TELEGRAM_USER_ID

async def tg_projects(update, ctx):
    if not is_allowed(update):
        return
    projects = list_projects()
    if not projects:
        await update.message.reply_text("No projects found.")
        return

    text = "📂 Projects:\n\n" + "\n".join(f"- {p}" for p in projects)
    await update.message.reply_text(text)

    if not PROJECT_ROOT.exists():
        await update.message.reply_text("❌ Project root not found.")
        return

    projects = [p.name for p in PROJECT_ROOT.iterdir() if p.is_dir()]
    if not projects:
        await update.message.reply_text("No projects found.")
        return

    text = "📂 Available Projects:\n\n" + "\n".join(f"- {p}" for p in projects)
    await update.message.reply_text(text)

async def tg_run(update, ctx):
    if not is_allowed(update):
        return

    text = update.message.text

    parts = text.split(" ", 2)
    if len(parts) < 3:
        await update.message.reply_text("Usage:\n/run <project> <command>")
        return

    project = parts[1]
    command = parts[2]

    project_path = PROJECT_ROOT / project

    if not project_path.exists():
        await update.message.reply_text(f"❌ Project '{project}' not found.")
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    output = execute_command(command, cwd=str(project_path))

    if len(output) > 4000:
        output = output[:4000] + "\n...truncated"

    await update.message.reply_text(f"▶ {project}\n\n{output}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    global PORT
    if is_port_in_use(HOST, PORT):
        original_port = PORT
        PORT = find_available_port(HOST, PORT + 1)
        log.warning(f"⚠️  Port {original_port} is in use. Switching to port {PORT}.")

    startup_checks()
    await warmup_ollama_model()

    tg_app = build_telegram_app()
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)

    if tg_app:
        log.info("📱 Telegram bot starting...")
        await tg_app.initialize()
        await tg_app.start()
        await tg_app.updater.start_polling(drop_pending_updates=True)
        log.info("✅ Telegram bot running! Open your bot and send /start")
        await server.serve()
        # Graceful shutdown
        await tg_app.updater.stop()
        await tg_app.stop()
        await tg_app.shutdown()
    else:
        await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

