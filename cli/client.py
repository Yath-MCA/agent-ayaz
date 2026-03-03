"""API client for Agent Ayazdy REST endpoints."""

import os
from typing import Any, Optional

import requests

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30


class AgentClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.base_url = (base_url or os.getenv("AYAZDY_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.getenv("API_SECRET_KEY") or os.getenv("AYAZDY_API_KEY", "")

    def _headers(self) -> dict:
        return {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            return {"error": True, "status_code": e.response.status_code, "detail": e.response.json()}
        except requests.RequestException as e:
            return {"error": True, "detail": str(e)}

    def _post(self, path: str, body: Optional[dict] = None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            r = requests.post(url, headers=self._headers(), json=body or {}, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            return {"error": True, "status_code": e.response.status_code, "detail": e.response.json()}
        except requests.RequestException as e:
            return {"error": True, "detail": str(e)}

    def health(self) -> dict:        return self._get("/health")
    def monitor_health(self) -> dict: return self._get("/monitor/health")
    def status(self) -> dict:         return self._get("/status")

    def projects(self) -> dict:       return self._get("/projects")
    def select(self, project: str) -> dict: return self._post("/project/select", {"project": project})
    def current(self) -> dict:        return self._get("/project/current")
    def tasks(self, project: Optional[str] = None) -> dict:
        params = {"project": project} if project else {}
        return self._get("/project/tasks", params)

    def run_task(self, task: str, project: Optional[str] = None, dry_run: bool = False, auto_approve: bool = True) -> dict:
        return self._post("/project/run-task", {"task": task, "project": project, "dry_run": dry_run, "auto_approve": auto_approve})

    def run_custom(self, command: str, project: Optional[str] = None, auto_approve: bool = True) -> dict:
        return self._post("/project/run-custom", {"command": command, "project": project, "auto_approve": auto_approve})

    def run_all(self, project: Optional[str] = None, dry_run: bool = False) -> dict:
        return self._post("/project/run-all-tasks", {"project": project, "dry_run": dry_run})

    def history(self, project: Optional[str] = None) -> dict:
        params = {"project": project} if project else {}
        return self._get("/monitor/history", params)

    def logs(self, limit: int = 20) -> dict:
        return self._get("/monitor/logs", {"limit": limit})

    def stats(self) -> dict:          return self._get("/monitor/stats")
    def self_check(self) -> dict:     return self._get("/monitor/self-check")

    def approvals(self) -> dict:      return self._get("/monitor/approvals")
    def approve(self, token: str) -> dict: return self._post(f"/monitor/approve/{token}")
    def reject(self, token: str) -> dict:  return self._post(f"/monitor/reject/{token}")

    def queue_status(self) -> dict:   return self._get("/queue/status")
    def queue_run(self) -> dict:      return self._post("/queue/run")
    def queue_promote(self) -> dict:  return self._post("/queue/promote-later")
