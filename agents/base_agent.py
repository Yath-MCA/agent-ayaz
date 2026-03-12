"""Multi-agent base class for AgentAyazDaddy v2.

Sub-agents specialize in categories of tasks:
  DevAgent    — development: build, lint, format
  QAAgent     — quality: test, coverage, compare
  BuildAgent  — pipeline: compile, bundle, package
  DeployAgent — deployment: docker, remote, publish
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class AgentTask:
    name: str
    task_type: str = "shell"       # shell | node | python | api | bot | ollama
    script: Optional[str] = None
    command: Optional[str] = None
    project: Optional[str] = None
    timeout: int = 300
    retry: int = 1
    env: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    task: str
    status: str                    # queued | running | completed | failed
    output: str = ""
    error: str = ""
    retries_used: int = 0
    ai_analysis: Optional[str] = None
    duration_ms: Optional[float] = None


class BaseAgent:
    """Base class shared by all AgentAyazDaddy sub-agents."""

    name: str = "BaseAgent"
    supported_types: list[str] = []

    def __init__(self) -> None:
        from services.structured_logger import log_agent_event
        self._log = log_agent_event

    def can_handle(self, task: AgentTask) -> bool:
        return not self.supported_types or task.task_type in self.supported_types

    def run(self, task: AgentTask) -> AgentResult:
        raise NotImplementedError

    def _log_start(self, task: AgentTask) -> None:
        self._log(f"[{self.name}] Starting task: {task.name}", level="INFO",
                  extra={"agent": self.name, "task": task.name, "type": task.task_type})

    def _log_done(self, result: AgentResult) -> None:
        level = "INFO" if result.status == "completed" else "ERROR"
        self._log(f"[{self.name}] Task {result.status}: {result.task}", level=level,
                  extra={"agent": self.name, "task": result.task, "status": result.status})

    @staticmethod
    def load_config() -> dict:
        cfg_path = Path("config/agent.json")
        if cfg_path.exists():
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        return {}
