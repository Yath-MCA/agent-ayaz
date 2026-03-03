"""Validator Agent — policy + command filter enforcement.

Approves or rejects an ExecutionPlan before it reaches the Executor.
Never executes anything itself.
"""

from dataclasses import dataclass
from typing import Optional

from security.command_filter import validate_command_policy
from agents.planner import ExecutionPlan

ALLOWED_TYPES = {"command", "task_file", "chat"}


@dataclass
class ValidationResult:
    approved: bool
    reason: str


def validate(
    plan: ExecutionPlan,
    *,
    strict_mode: bool = False,
    allowed_prefixes: Optional[list[str]] = None,
) -> ValidationResult:
    """Validate the execution plan against policy rules."""

    if plan.type not in ALLOWED_TYPES:
        return ValidationResult(False, f"Unknown plan type: '{plan.type}'")

    if plan.type == "command":
        if not plan.command:
            return ValidationResult(False, "Plan type is 'command' but no command specified.")

        policy_error = validate_command_policy(
            plan.command,
            strict_mode=strict_mode,
            allowed_prefixes=allowed_prefixes,
        )
        if policy_error:
            return ValidationResult(False, policy_error)

    if plan.type == "task_file":
        if not plan.task_file:
            return ValidationResult(False, "Plan type is 'task_file' but no task_file specified.")

    return ValidationResult(True, "Approved")
