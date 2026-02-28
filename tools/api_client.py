import time
from typing import Any

import requests


class AgentApiClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"X-Api-Key": api_key}

    def _request(self, method: str, path: str, *, json_body: dict | None = None, retries: int = 2) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        for attempt in range(retries + 1):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=self.headers,
                    json=json_body,
                    timeout=self.timeout,
                )
            except requests.RequestException as error:
                if attempt < retries:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"Transport failure: {error}") from error

            if response.status_code < 400:
                return response.json()

            try:
                detail = response.json().get("detail", {})
            except Exception:
                detail = {}

            code = detail.get("code") if isinstance(detail, dict) else None
            message = detail.get("message") if isinstance(detail, dict) else response.text

            if response.status_code in {400, 401, 500}:
                raise RuntimeError(f"{response.status_code} {code or 'ERROR'}: {message}")

            if response.status_code == 429 and attempt < retries:
                time.sleep(2)
                continue

            response.raise_for_status()

        raise RuntimeError("Unexpected request handling state")

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def list_projects(self) -> dict[str, Any]:
        return self._request("GET", "/projects")

    def select_project(self, project: str) -> dict[str, Any]:
        return self._request("POST", "/project/select", json_body={"project": project})

    def current_project(self) -> dict[str, Any]:
        return self._request("GET", "/project/current")

    def list_tasks(self, project: str | None = None) -> dict[str, Any]:
        path = f"/project/tasks?project={project}" if project else "/project/tasks"
        return self._request("GET", path)

    def run_task(self, task: str, project: str | None = None, dry_run: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {"task": task, "dry_run": dry_run}
        if project:
            payload["project"] = project
        return self._request("POST", "/project/run-task", json_body=payload)

    def run_custom(self, command: str, project: str | None = None, dry_run: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {"command": command, "dry_run": dry_run}
        if project:
            payload["project"] = project
        return self._request("POST", "/project/run-custom", json_body=payload)


if __name__ == "__main__":
    import os

    base_url = os.getenv("AGENT_BASE_URL", "http://localhost:8000")
    api_key = os.getenv("AGENT_API_KEY", "")
    project = os.getenv("AGENT_PROJECT", "")

    if not api_key:
        raise SystemExit("Set AGENT_API_KEY before running this client")

    client = AgentApiClient(base_url=base_url, api_key=api_key)
    print(client.list_projects())
    if project:
        print(client.select_project(project))
        print(client.current_project())
        print(client.list_tasks())
