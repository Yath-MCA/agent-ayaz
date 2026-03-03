"""Task Queue Service — file-based task queue with queue/, completed/, later/ folders.

Lifecycle:
  queue/    → tasks to process now (sorted alphabetically = ordered execution)
  completed/→ tasks moved here after successful processing
  later/    → deferred tasks; when queue is empty, admin is prompted to promote them

Supported task file types:
  .yaml / .yml  → executed via Task DSL (agents/task_dsl.py)
  .md           → planning/instruction only; marked completed without execution
  .ps1/.bat/.cmd/.py/.sh → executed directly via execution_service
"""

import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agents.task_dsl import load_task_yaml, validate_task_definition, TaskDSLError
from services.execution_service import execute_command_result, execute_task_file_result

AGENT_TASK_ROOT = Path("agent-task")
QUEUE_DIR      = AGENT_TASK_ROOT / "queue"
COMPLETED_DIR  = AGENT_TASK_ROOT / "completed"
LATER_DIR      = AGENT_TASK_ROOT / "later"

RUNNABLE_SUFFIXES = {".ps1", ".bat", ".cmd", ".py", ".sh"}
DSL_SUFFIXES      = {".yaml", ".yml"}
PLAN_SUFFIXES     = {".md", ".txt"}


def ensure_dirs() -> None:
    for d in (QUEUE_DIR, COMPLETED_DIR, LATER_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _sorted_files(directory: Path) -> list[Path]:
    """Return files in a directory sorted alphabetically (gives ordered execution)."""
    if not directory.exists():
        return []
    return sorted(
        [f for f in directory.iterdir() if f.is_file()],
        key=lambda p: p.name.lower(),
    )


def queue_status() -> dict:
    ensure_dirs()
    return {
        "queue":     [f.name for f in _sorted_files(QUEUE_DIR)],
        "later":     [f.name for f in _sorted_files(LATER_DIR)],
        "completed": [f.name for f in _sorted_files(COMPLETED_DIR)],
        "queue_empty": not bool(_sorted_files(QUEUE_DIR)),
        "later_available": bool(_sorted_files(LATER_DIR)),
    }


def _move_to_completed(task_file: Path) -> Path:
    dest = COMPLETED_DIR / task_file.name
    # Avoid collision — add suffix if name taken
    if dest.exists():
        stem = task_file.stem
        suffix = task_file.suffix
        dest = COMPLETED_DIR / f"{stem}_{int(time.time())}{suffix}"
    shutil.move(str(task_file), str(dest))
    return dest


@dataclass
class TaskResult:
    name: str
    status: str          # "executed" | "planned" | "skipped" | "failed"
    output: Optional[str]
    exit_code: Optional[int]
    duration_ms: Optional[int]
    moved_to: str


def _run_single_task(
    task_file: Path,
    *,
    timeout_seconds: int = 60,
    task_timeout_seconds: int = 120,
    max_output_chars: int = 3000,
    strict_mode: bool = False,
    allowed_prefixes: Optional[list[str]] = None,
) -> TaskResult:
    suffix = task_file.suffix.lower()

    # Planning / doc files — mark completed without execution
    if suffix in PLAN_SUFFIXES:
        dest = _move_to_completed(task_file)
        return TaskResult(
            name=task_file.name, status="planned",
            output="(planning task — no execution)", exit_code=0,
            duration_ms=0, moved_to=str(dest),
        )

    # YAML DSL tasks
    if suffix in DSL_SUFFIXES:
        try:
            task_def = load_task_yaml(task_file)
        except TaskDSLError as e:
            dest = _move_to_completed(task_file)
            return TaskResult(
                name=task_file.name, status="failed",
                output=f"DSL error: {e}", exit_code=1,
                duration_ms=0, moved_to=str(dest),
            )
        policy_error = validate_task_definition(
            task_def, strict_mode=strict_mode, allowed_prefixes=allowed_prefixes
        )
        if policy_error:
            dest = _move_to_completed(task_file)
            return TaskResult(
                name=task_file.name, status="skipped",
                output=policy_error, exit_code=2,
                duration_ms=0, moved_to=str(dest),
            )

        if task_def.type == "command" and task_def.command:
            result = execute_command_result(
                task_def.command,
                timeout_seconds=task_def.timeout,
                max_output_chars=max_output_chars,
                strict_mode=strict_mode,
                allowed_prefixes=allowed_prefixes,
            )
        elif task_def.type == "task_file" and task_def.task_file:
            tf = QUEUE_DIR / task_def.task_file
            if not tf.exists():
                dest = _move_to_completed(task_file)
                return TaskResult(
                    name=task_file.name, status="failed",
                    output=f"task_file not found: {task_def.task_file}", exit_code=1,
                    duration_ms=0, moved_to=str(dest),
                )
            result = execute_task_file_result(tf, timeout_seconds=task_def.timeout, max_output_chars=max_output_chars)
        else:
            dest = _move_to_completed(task_file)
            return TaskResult(
                name=task_file.name, status="skipped",
                output="No runnable target in DSL", exit_code=0,
                duration_ms=0, moved_to=str(dest),
            )

        dest = _move_to_completed(task_file)
        return TaskResult(
            name=task_file.name,
            status="executed" if result.exit_code == 0 else "failed",
            output=result.output, exit_code=result.exit_code,
            duration_ms=result.duration_ms, moved_to=str(dest),
        )

    # Direct executable scripts (.ps1, .bat, etc.)
    if suffix in RUNNABLE_SUFFIXES:
        result = execute_task_file_result(
            task_file,
            timeout_seconds=task_timeout_seconds,
            max_output_chars=max_output_chars,
        )
        dest = _move_to_completed(task_file)
        return TaskResult(
            name=task_file.name,
            status="executed" if result.exit_code == 0 else "failed",
            output=result.output, exit_code=result.exit_code,
            duration_ms=result.duration_ms, moved_to=str(dest),
        )

    # Unknown type — move to completed as skipped
    dest = _move_to_completed(task_file)
    return TaskResult(
        name=task_file.name, status="skipped",
        output=f"Unsupported file type: {suffix}", exit_code=0,
        duration_ms=0, moved_to=str(dest),
    )


def run_queue(
    *,
    timeout_seconds: int = 60,
    task_timeout_seconds: int = 120,
    max_output_chars: int = 3000,
    strict_mode: bool = False,
    allowed_prefixes: Optional[list[str]] = None,
) -> list[TaskResult]:
    """Process all tasks in queue/ in sorted order, moving each to completed/."""
    ensure_dirs()
    tasks = _sorted_files(QUEUE_DIR)
    results = []
    for task_file in tasks:
        result = _run_single_task(
            task_file,
            timeout_seconds=timeout_seconds,
            task_timeout_seconds=task_timeout_seconds,
            max_output_chars=max_output_chars,
            strict_mode=strict_mode,
            allowed_prefixes=allowed_prefixes,
        )
        results.append(result)
    return results


def promote_later_to_queue() -> list[str]:
    """Move all files from later/ into queue/ and return their names."""
    ensure_dirs()
    moved = []
    for f in _sorted_files(LATER_DIR):
        dest = QUEUE_DIR / f.name
        if dest.exists():
            stem = f.stem
            suffix = f.suffix
            dest = QUEUE_DIR / f"{stem}_{int(time.time())}{suffix}"
        shutil.move(str(f), str(dest))
        moved.append(dest.name)
    return moved
