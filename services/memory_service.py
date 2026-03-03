"""Memory Service — SQLite-backed execution history and failure tracking.

Schema (executions table):
  id, ts, user, project, task, command, plan_type,
  exit_code, duration_ms, approved, error_msg
"""

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DB_PATH = Path("logs") / "memory.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          INTEGER NOT NULL,
                user        TEXT,
                project     TEXT,
                task        TEXT,
                command     TEXT,
                plan_type   TEXT,
                exit_code   INTEGER,
                duration_ms INTEGER,
                approved    INTEGER,
                error_msg   TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_project ON executions(project)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON executions(ts)")
        conn.commit()


def record_execution(
    *,
    user: str,
    project: Optional[str],
    task: Optional[str],
    command: Optional[str],
    plan_type: str,
    exit_code: int,
    duration_ms: int,
    approved: bool,
    error_msg: Optional[str] = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO executions
              (ts, user, project, task, command, plan_type, exit_code, duration_ms, approved, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time()), user, project, task, command,
                plan_type, exit_code, duration_ms, int(approved), error_msg,
            ),
        )
        conn.commit()


def get_project_history(project: str, limit: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM executions WHERE project = ? ORDER BY ts DESC LIMIT ?",
            (project, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_failures(project: Optional[str] = None, limit: int = 10) -> list[dict]:
    with _connect() as conn:
        if project:
            rows = conn.execute(
                "SELECT * FROM executions WHERE exit_code != 0 AND project = ? ORDER BY ts DESC LIMIT ?",
                (project, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM executions WHERE exit_code != 0 ORDER BY ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]


def get_execution_stats(project: Optional[str] = None) -> dict:
    with _connect() as conn:
        if project:
            base = "WHERE project = ?"
            args: tuple = (project,)
        else:
            base, args = "", ()

        total = conn.execute(f"SELECT COUNT(*) FROM executions {base}", args).fetchone()[0]
        failures = conn.execute(f"SELECT COUNT(*) FROM executions {base} {'AND' if base else 'WHERE'} exit_code != 0", args if base else ()).fetchone()[0]
        recent = conn.execute(
            f"SELECT task, command, exit_code, duration_ms, ts FROM executions {base} ORDER BY ts DESC LIMIT 5",
            args,
        ).fetchall()

    return {
        "total": total,
        "failures": failures,
        "success_rate": round((total - failures) / total * 100, 1) if total else 0,
        "recent": [dict(r) for r in recent],
    }


def suggest_retry(project: str) -> Optional[str]:
    """Return the last failed task for a project as a retry suggestion."""
    failures = get_recent_failures(project, limit=1)
    if not failures:
        return None
    last = failures[0]
    return last.get("task") or last.get("command")
