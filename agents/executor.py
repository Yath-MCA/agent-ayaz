"""Executor Agent — secure execution wrapper.

Only accepts validated ExecutionPlan objects — never raw natural language.
Delegates to execution_service for the actual subprocess call.
"""

from pathlib import Path
from typing import Optional

from agents.planner import ExecutionPlan
from agents.validator import ValidationResult
from services.execution_service import ExecutionResult, execute_command_result, execute_task_file_result


def execute(
    plan: ExecutionPlan,
    validation: ValidationResult,
    *,
    project_path: Optional[Path] = None,
    timeout_seconds: int = 60,
    task_timeout_seconds: int = 120,
    max_output_chars: int = 3000,
    strict_mode: bool = False,
    allowed_prefixes: Optional[list[str]] = None,
) -> ExecutionResult:
    """Execute a validated plan. Raises ValueError if validation was not approved."""

    if not validation.approved:
        raise ValueError(f"Execution blocked by Validator: {validation.reason}")

    cwd = str(project_path) if project_path else None

    if plan.type == "command" and plan.command:
        return execute_command_result(
            plan.command,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
            strict_mode=strict_mode,
            allowed_prefixes=allowed_prefixes,
        )

    if plan.type == "task_file" and plan.task_file and project_path:
        task_path = project_path / "run-task" / plan.task_file
        if not task_path.exists():
            import time
            t = time.time()
            return ExecutionResult(
                output=f"❌ Task file not found: {plan.task_file}",
                exit_code=2,
                started_at=t,
                duration_ms=0,
            )
        return execute_task_file_result(
            task_path,
            cwd=cwd,
            timeout_seconds=task_timeout_seconds,
            max_output_chars=max_output_chars,
        )

    import time
    t = time.time()
    return ExecutionResult(output="(chat — no execution)", exit_code=0, started_at=t, duration_ms=0)
