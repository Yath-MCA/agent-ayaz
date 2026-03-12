"""DeployAgent — handles deployment: Docker, remote push, API calls.

Deploy tasks are disabled by default in config/agent.json (enabled: false).
Enable with: "deploy": { "enabled": true } in config/agent.json
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from agents.base_agent import AgentTask, AgentResult, BaseAgent


class DeployAgent(BaseAgent):
    name = "DeployAgent"
    supported_types = ["shell", "api"]

    def run(self, task: AgentTask) -> AgentResult:
        cfg = self.load_config()
        if not cfg.get("sub_agents", {}).get("deploy", {}).get("enabled", False):
            return AgentResult(
                task=task.name, status="failed",
                error="DeployAgent is disabled. Set sub_agents.deploy.enabled=true in config/agent.json"
            )

        self._log_start(task)
        start = time.monotonic()

        if task.task_type == "api":
            return self._run_api_task(task, start)

        cmd = task.command or task.script or ""
        if not cmd:
            return AgentResult(task=task.name, status="failed", error="No command or script specified")

        cwd = str(Path(task.project).resolve()) if task.project and Path(task.project).exists() else None

        try:
            proc = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=task.timeout, cwd=cwd, env={**__import__("os").environ, **task.env}
            )
            duration = (time.monotonic() - start) * 1000
            status = "completed" if proc.returncode == 0 else "failed"
            result = AgentResult(task=task.name, status=status,
                                  output=proc.stdout, error=proc.stderr,
                                  duration_ms=duration)
        except subprocess.TimeoutExpired:
            duration = (time.monotonic() - start) * 1000
            result = AgentResult(task=task.name, status="failed",
                                  error=f"Timeout after {task.timeout}s", duration_ms=duration)

        self._log_done(result)
        return result

    def _run_api_task(self, task: AgentTask, start: float) -> AgentResult:
        import requests
        url = task.metadata.get("url", "")
        method = task.metadata.get("method", "POST").upper()
        payload = task.metadata.get("payload", {})
        headers = task.metadata.get("headers", {})

        if not url:
            return AgentResult(task=task.name, status="failed", error="No API URL in task metadata")
        try:
            resp = requests.request(method, url, json=payload, headers=headers, timeout=task.timeout)
            duration = (__import__("time").monotonic() - start) * 1000
            if resp.ok:
                result = AgentResult(task=task.name, status="completed",
                                      output=resp.text[:500], duration_ms=duration)
            else:
                result = AgentResult(task=task.name, status="failed",
                                      error=f"HTTP {resp.status_code}: {resp.text[:200]}", duration_ms=duration)
        except Exception as exc:
            result = AgentResult(task=task.name, status="failed", error=str(exc))

        self._log_done(result)
        return result
