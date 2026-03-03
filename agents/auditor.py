"""Auditor Agent — immutable structured logging + metadata tracking.

All agent-pipeline executions flow through here for audit trail.
Writes JSONL to logs/agent_audit.log.
"""

import json
import time
from pathlib import Path
from typing import Optional

AUDIT_LOG_PATH = Path("logs") / "agent_audit.log"
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def record(
    *,
    user: str,
    project: Optional[str],
    command: Optional[str],
    task: Optional[str],
    exit_code: int,
    duration_ms: int,
    approved: bool,
    plan_type: str,
    reasoning: str = "",
) -> None:
    """Write one immutable audit entry."""
    entry = {
        "ts": int(time.time()),
        "user": user,
        "project": project,
        "command": command,
        "task": task,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "approved": approved,
        "plan_type": plan_type,
        "reasoning": reasoning,
    }
    try:
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tail(limit: int = 50) -> list[dict]:
    """Return last N audit entries."""
    if not AUDIT_LOG_PATH.exists():
        return []
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries
