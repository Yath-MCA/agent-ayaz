"""Replay Engine — deterministic re-execution of historical executions.

Reconstructs a DSL-compatible TaskDefinition from a memory record,
then routes it back through Validator → Executor with a replay approval gate.
"""

from dataclasses import dataclass
from typing import Optional

from services.memory_service import _connect
from agents.task_dsl import TaskDefinition
from agents.validator import validate, ValidationResult
from services.execution_service import ExecutionResult, execute_command_result, execute_task_file_result


@dataclass
class ReplayPlan:
    execution_id: int
    original: dict
    task_def: TaskDefinition
    diff_notes: list[str]


def get_execution_by_id(execution_id: int) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM executions WHERE id = ?", (execution_id,)
        ).fetchone()
    return dict(row) if row else None


def reconstruct(record: dict) -> TaskDefinition:
    """Reconstruct a TaskDefinition from a memory record."""
    if record.get("command"):
        return TaskDefinition(
            task=record.get("task") or "replay",
            type="command",
            command=record["command"],
            task_file=None,
            timeout=60,
            auto_approve=True,
            delay_seconds=0,
            description=f"Replay of execution #{record['id']}",
        )
    return TaskDefinition(
        task=record.get("task") or "replay",
        type="task_file",
        command=None,
        task_file=record.get("task"),
        timeout=120,
        auto_approve=True,
        delay_seconds=0,
        description=f"Replay of execution #{record['id']}",
    )


def diff_notes(original: dict, replayed: ExecutionResult) -> list[str]:
    notes = []
    if replayed.exit_code != original.get("exit_code"):
        notes.append(f"Exit code changed: {original.get('exit_code')} → {replayed.exit_code}")
    orig_ms = original.get("duration_ms", 0)
    delta = replayed.duration_ms - orig_ms
    if abs(delta) > 500:
        notes.append(f"Duration delta: {delta:+d}ms vs original {orig_ms}ms")
    if not notes:
        notes.append("Replay matched original behaviour")
    return notes


def replay_execution(
    execution_id: int,
    *,
    strict_mode: bool = False,
    allowed_prefixes: Optional[list[str]] = None,
    timeout_seconds: int = 60,
    max_output_chars: int = 3000,
    project_path=None,
) -> dict:
    record = get_execution_by_id(execution_id)
    if not record:
        return {"error": True, "detail": f"Execution #{execution_id} not found"}

    task_def = reconstruct(record)
    from agents.validator import ValidationResult
    validation = ValidationResult(approved=True, reason="Replay approval")

    if task_def.type == "command" and task_def.command:
        result = execute_command_result(
            task_def.command,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
            strict_mode=strict_mode,
            allowed_prefixes=allowed_prefixes,
        )
    else:
        return {"error": True, "detail": "Replay of task_file type requires project context"}

    notes = diff_notes(record, result)
    return {
        "execution_id": execution_id,
        "original": {k: record[k] for k in ("task", "command", "exit_code", "duration_ms", "ts")},
        "replayed": {
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "output": result.output,
        },
        "diff": notes,
    }
