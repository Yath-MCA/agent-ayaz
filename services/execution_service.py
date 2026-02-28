import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from security.command_filter import validate_command_policy


@dataclass
class ExecutionResult:
    output: str
    exit_code: int
    started_at: float
    duration_ms: int

    def to_dict(self) -> dict:
        return asdict(self)


def _finalize_output(text: str, max_output_chars: int) -> str:
    if not text:
        return "(no output)"
    return text[:max_output_chars]


def execute_command_result(
    cmd: str,
    cwd: Optional[str] = None,
    *,
    timeout_seconds: int = 60,
    max_output_chars: int = 3000,
    strict_mode: bool = False,
    allowed_prefixes: list[str] | None = None,
) -> ExecutionResult:
    started_at = time.time()
    policy_error = validate_command_policy(
        cmd,
        strict_mode=strict_mode,
        allowed_prefixes=allowed_prefixes,
    )
    if policy_error:
        return ExecutionResult(
            output=policy_error,
            exit_code=2,
            started_at=started_at,
            duration_ms=int((time.time() - started_at) * 1000),
        )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=cwd,
        )
        output = _finalize_output(result.stdout or result.stderr, max_output_chars)
        return ExecutionResult(
            output=output,
            exit_code=result.returncode,
            started_at=started_at,
            duration_ms=int((time.time() - started_at) * 1000),
        )
    except Exception as error:
        return ExecutionResult(
            output=f"Execution error: {error}",
            exit_code=1,
            started_at=started_at,
            duration_ms=int((time.time() - started_at) * 1000),
        )


def execute_command(
    cmd: str,
    cwd: Optional[str] = None,
    *,
    timeout_seconds: int = 60,
    max_output_chars: int = 3000,
    strict_mode: bool = False,
    allowed_prefixes: list[str] | None = None,
) -> str:
    return execute_command_result(
        cmd,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
        strict_mode=strict_mode,
        allowed_prefixes=allowed_prefixes,
    ).output


def execute_task_file_result(
    task_file: Path,
    cwd: Optional[str] = None,
    *,
    timeout_seconds: int = 120,
    max_output_chars: int = 3000,
) -> ExecutionResult:
    started_at = time.time()
    suffix = task_file.suffix.lower()

    command_map = {
        ".ps1": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(task_file)],
        ".bat": ["cmd", "/c", str(task_file)],
        ".cmd": ["cmd", "/c", str(task_file)],
        ".py": ["python", str(task_file)],
        ".sh": ["bash", str(task_file)],
    }

    command = command_map.get(suffix)
    if not command:
        return ExecutionResult(
            output=f"❌ Unsupported task file type: {suffix}",
            exit_code=2,
            started_at=started_at,
            duration_ms=int((time.time() - started_at) * 1000),
        )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=cwd,
        )
        output = _finalize_output(result.stdout or result.stderr, max_output_chars)
        return ExecutionResult(
            output=output,
            exit_code=result.returncode,
            started_at=started_at,
            duration_ms=int((time.time() - started_at) * 1000),
        )
    except Exception as error:
        return ExecutionResult(
            output=f"Execution error: {error}",
            exit_code=1,
            started_at=started_at,
            duration_ms=int((time.time() - started_at) * 1000),
        )


def execute_task_file(
    task_file: Path,
    cwd: Optional[str] = None,
    *,
    timeout_seconds: int = 120,
    max_output_chars: int = 3000,
) -> str:
    return execute_task_file_result(
        task_file,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        max_output_chars=max_output_chars,
    ).output
