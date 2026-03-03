"""Autonomous Mode Controller — SAFE / CONTROLLED / AUTONOMOUS (Phase 10).

Reads AGENT_MODE from environment. Controls auto-retry and auto-approval behaviour.

SAFE_MODE:       Only predefined DSL task files allowed. No custom commands.
CONTROLLED_MODE: Prefix-based custom commands allowed. Manual approval required.
AUTONOMOUS_MODE: Low-risk tasks auto-approved and auto-retried.
"""

import os
from enum import Enum
from typing import Optional


class AgentMode(str, Enum):
    SAFE        = "SAFE"
    CONTROLLED  = "CONTROLLED"
    AUTONOMOUS  = "AUTONOMOUS"


_RISK_AUTO_APPROVE_THRESHOLD = int(os.getenv("AUTONOMOUS_RISK_THRESHOLD", "3"))
_MAX_AUTO_RETRIES = int(os.getenv("AUTONOMOUS_MAX_RETRIES", "2"))


def current_mode() -> AgentMode:
    raw = os.getenv("AGENT_MODE", "CONTROLLED").strip().upper()
    try:
        return AgentMode(raw)
    except ValueError:
        return AgentMode.CONTROLLED


def can_execute_custom_command(mode: Optional[AgentMode] = None) -> bool:
    """SAFE mode blocks all custom commands."""
    m = mode or current_mode()
    return m != AgentMode.SAFE


def should_auto_approve(risk_score: int, mode: Optional[AgentMode] = None) -> bool:
    """AUTONOMOUS mode auto-approves low-risk tasks."""
    m = mode or current_mode()
    if m == AgentMode.SAFE:
        return False
    if m == AgentMode.CONTROLLED:
        return False
    # AUTONOMOUS: approve if risk is within threshold
    return risk_score <= _RISK_AUTO_APPROVE_THRESHOLD


def should_auto_retry(exit_code: int, attempt: int, mode: Optional[AgentMode] = None) -> bool:
    """AUTONOMOUS mode retries low-exit-code failures up to max retries."""
    m = mode or current_mode()
    if m != AgentMode.AUTONOMOUS:
        return False
    return exit_code != 0 and attempt < _MAX_AUTO_RETRIES


def mode_info() -> dict:
    m = current_mode()
    return {
        "mode": m.value,
        "can_execute_custom": can_execute_custom_command(m),
        "risk_auto_approve_threshold": _RISK_AUTO_APPROVE_THRESHOLD if m == AgentMode.AUTONOMOUS else None,
        "max_auto_retries": _MAX_AUTO_RETRIES if m == AgentMode.AUTONOMOUS else 0,
        "description": {
            AgentMode.SAFE:        "Only DSL task files allowed. No custom commands.",
            AgentMode.CONTROLLED:  "Custom commands allowed with manual approval.",
            AgentMode.AUTONOMOUS:  f"Low-risk tasks (score ≤ {_RISK_AUTO_APPROVE_THRESHOLD}) auto-approved and retried.",
        }[m],
    }
