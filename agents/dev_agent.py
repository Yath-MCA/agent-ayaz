"""DevAgent — handles development tasks: build, lint, format, install."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from agents.base_agent import AgentTask, AgentResult, BaseAgent


class DevAgent(BaseAgent):
    name = "DevAgent"
    supported_types = ["shell", "python", "node"]

    def run(self, task: AgentTask) -> AgentResult:
        self._log_start(task)
        start = time.monotonic()

        cmd = task.command or (f"python {task.script}" if task.task_type == "python"
                               else f"node {task.script}" if task.task_type == "node"
                               else task.script or "")
        if not cmd:
            return AgentResult(task=task.name, status="failed", error="No command or script specified")

        cwd = str(Path(task.project).resolve()) if task.project and Path(task.project).exists() else None

        for attempt in range(max(1, task.retry)):
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=task.timeout, cwd=cwd, env={**__import__("os").environ, **task.env}
                )
                duration = (time.monotonic() - start) * 1000
                if proc.returncode == 0:
                    result = AgentResult(task=task.name, status="completed",
                                         output=proc.stdout, retries_used=attempt,
                                         duration_ms=duration)
                    self._log_done(result)
                    return result
                # Failed — will retry
            except subprocess.TimeoutExpired:
                duration = (time.monotonic() - start) * 1000
                result = AgentResult(task=task.name, status="failed",
                                     error=f"Timeout after {task.timeout}s",
                                     retries_used=attempt, duration_ms=duration)
                self._log_done(result)
                return result

        duration = (time.monotonic() - start) * 1000
        result = AgentResult(task=task.name, status="failed",
                             error=proc.stderr if proc else "Unknown error",
                             retries_used=task.retry - 1, duration_ms=duration)
        self._log_done(result)
        return result
