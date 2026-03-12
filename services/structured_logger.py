"""Structured logging service for AgentAyazDaddy.

Writes four log files:
  logs/agent.log        — general agent lifecycle events
  logs/tasks.log        — task start / completion / failure records
  logs/errors.log       — error events only
  logs/ai-analysis.log  — AI/Ollama analysis results and suggestions

Each entry is a JSON line: { timestamp, level, task, status, duration_ms, message, ... }
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── Log directory ─────────────────────────────────────────────────────────────

_LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))


def _ensure_log_dir() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Internal JSONL writer ─────────────────────────────────────────────────────

_write_lock = threading.Lock()


def _write_jsonl(filepath: Path, record: dict) -> None:
    _ensure_log_dir()
    with _write_lock:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Public logging functions ──────────────────────────────────────────────────

def log_agent_event(
    message: str,
    level: str = "INFO",
    extra: Optional[dict] = None,
) -> None:
    """Log a general agent lifecycle event."""
    record = {
        "timestamp": _now_iso(),
        "level": level.upper(),
        "message": message,
        **(extra or {}),
    }
    _write_jsonl(_LOG_DIR / "agent.log", record)


def log_task_event(
    task: str,
    status: str,
    duration_ms: Optional[float] = None,
    message: str = "",
    project: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Log a task lifecycle event (queued / running / completed / failed)."""
    record = {
        "timestamp": _now_iso(),
        "task": task,
        "status": status,
        "project": project,
        "duration_ms": duration_ms,
        "message": message,
        **(extra or {}),
    }
    _write_jsonl(_LOG_DIR / "tasks.log", record)
    if status == "failed":
        log_error(task=task, message=message or f"Task '{task}' failed", extra=extra)


def log_ai_analysis(
    task: str,
    analysis: str,
    model: Optional[str] = None,
    trigger: str = "manual",
    suggestions: Optional[list] = None,
    extra: Optional[dict] = None,
) -> None:
    """Log an AI/Ollama analysis result to ai-analysis.log."""
    record = {
        "timestamp": _now_iso(),
        "task": task,
        "model": model,
        "trigger": trigger,
        "analysis": analysis,
        "suggestions": suggestions or [],
        **(extra or {}),
    }
    _write_jsonl(_LOG_DIR / "ai-analysis.log", record)


def log_error(
    message: str,
    task: Optional[str] = None,
    exc: Optional[Exception] = None,
    extra: Optional[dict] = None,
) -> None:
    """Log an error event."""
    record = {
        "timestamp": _now_iso(),
        "level": "ERROR",
        "task": task,
        "message": message,
        "exception": str(exc) if exc else None,
        **(extra or {}),
    }
    _write_jsonl(_LOG_DIR / "errors.log", record)


# ── Log reader ────────────────────────────────────────────────────────────────

def read_log(
    log_type: str = "tasks",
    limit: int = 50,
) -> list[dict]:
    """Read the last `limit` lines from a log file.

    log_type: 'agent' | 'tasks' | 'errors' | 'ai-analysis'
    """
    path = _LOG_DIR / f"{log_type}.log"
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        records = []
        for line in reversed(lines[-limit * 2:]):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(records) >= limit:
                break
        return records
    except Exception:
        return []


# ── Stdlib logging bridge ─────────────────────────────────────────────────────

class StructuredHandler(logging.Handler):
    """Bridges stdlib logging → structured JSONL files."""

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        level = record.levelname
        msg = self.format(record)
        if level == "ERROR" or level == "CRITICAL":
            log_error(message=msg)
        else:
            log_agent_event(message=msg, level=level)


def setup_stdlib_bridge(logger_name: str = "agent_ayaz") -> logging.Logger:
    """Attach the structured handler to a named stdlib logger."""
    logger = logging.getLogger(logger_name)
    if not any(isinstance(h, StructuredHandler) for h in logger.handlers):
        logger.addHandler(StructuredHandler())
    logger.setLevel(logging.DEBUG)
    return logger
