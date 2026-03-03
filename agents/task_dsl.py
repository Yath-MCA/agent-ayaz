"""Task DSL — YAML-based task definition loader and validator.

Schema:
  task: build-project
  type: command          # command | task_file
  command: python -m pytest
  timeout: 60
  auto_approve: true
  delay_seconds: 0
  description: Run test suite
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from security.command_filter import validate_command_policy

ALLOWED_TASK_SUFFIXES = {".ps1", ".bat", ".cmd", ".py", ".sh"}


@dataclass
class TaskDefinition:
    task: str
    type: str                    # "command" | "task_file"
    command: Optional[str]
    task_file: Optional[str]
    timeout: int
    auto_approve: bool
    delay_seconds: int
    description: str


class TaskDSLError(ValueError):
    pass


def load_task_yaml(path: Path) -> TaskDefinition:
    """Load and validate a YAML task definition file."""
    if not path.exists():
        raise TaskDSLError(f"Task file not found: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise TaskDSLError(f"Invalid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise TaskDSLError("Task YAML must be a mapping at the top level.")

    task_type = str(data.get("type", "command"))
    if task_type not in {"command", "task_file"}:
        raise TaskDSLError(f"Invalid type '{task_type}'. Must be 'command' or 'task_file'.")

    command = data.get("command") or None
    task_file = data.get("task_file") or None

    if task_type == "command" and not command:
        raise TaskDSLError("type=command requires a 'command' field.")
    if task_type == "task_file" and not task_file:
        raise TaskDSLError("type=task_file requires a 'task_file' field.")

    return TaskDefinition(
        task=str(data.get("task", path.stem)),
        type=task_type,
        command=command,
        task_file=task_file,
        timeout=int(data.get("timeout", 60)),
        auto_approve=bool(data.get("auto_approve", True)),
        delay_seconds=int(data.get("delay_seconds", 0)),
        description=str(data.get("description", "")),
    )


def validate_task_definition(
    task_def: TaskDefinition,
    *,
    strict_mode: bool = False,
    allowed_prefixes: Optional[list[str]] = None,
) -> Optional[str]:
    """Returns an error string if invalid, or None if OK."""
    if task_def.type == "command" and task_def.command:
        return validate_command_policy(
            task_def.command,
            strict_mode=strict_mode,
            allowed_prefixes=allowed_prefixes,
        )
    if task_def.type == "task_file" and task_def.task_file:
        suffix = Path(task_def.task_file).suffix.lower()
        if suffix not in ALLOWED_TASK_SUFFIXES:
            return f"❌ Unsupported task file suffix: {suffix}"
    return None


def load_dsl_tasks_from_dir(task_dir: Path) -> list[TaskDefinition]:
    """Load all .yaml/.yml task definitions from a directory, sorted by name."""
    if not task_dir.exists():
        return []
    files = sorted(task_dir.glob("*.yaml")) + sorted(task_dir.glob("*.yml"))
    definitions = []
    for f in files:
        try:
            definitions.append(load_task_yaml(f))
        except TaskDSLError:
            pass
    return definitions
