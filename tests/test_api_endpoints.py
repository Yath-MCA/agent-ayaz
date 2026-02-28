from pathlib import Path

from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def _headers():
    return {"X-Api-Key": "test-key"}


def _setup_settings(monkeypatch):
    object.__setattr__(main.settings, "api_secret_keys", ["test-key"])
    object.__setattr__(main.settings, "rate_limit_per_minute", 1000)
    object.__setattr__(main.settings, "default_execution_delay_seconds", 0)
    object.__setattr__(main.settings, "auto_approve_default", True)
    object.__setattr__(main.settings, "strict_command_mode", False)


def test_select_current_and_tasks(monkeypatch, tmp_path):
    _setup_settings(monkeypatch)

    project = tmp_path / "demo"
    task_dir = project / "run-task"
    task_dir.mkdir(parents=True)
    (task_dir / "build.ps1").write_text("Write-Host 'ok'", encoding="utf-8")

    monkeypatch.setattr(main, "list_projects", lambda: ["demo"])
    monkeypatch.setattr(main, "get_project_path", lambda name: project if name == "demo" else None)
    monkeypatch.setattr(main, "try_open_in_vscode", lambda _: (True, "Opened in VS Code."))

    selected = client.post("/project/select", headers=_headers(), json={"project": "demo"})
    assert selected.status_code == 200
    assert selected.json()["project"] == "demo"

    current = client.get("/project/current", headers=_headers())
    assert current.status_code == 200
    assert current.json()["project"] == "demo"

    tasks = client.get("/project/tasks", headers=_headers())
    assert tasks.status_code == 200
    assert tasks.json()["count"] == 1


def test_run_task_dry_run(monkeypatch, tmp_path):
    _setup_settings(monkeypatch)

    project = tmp_path / "demo"
    task_dir = project / "run-task"
    task_dir.mkdir(parents=True)
    (task_dir / "build.ps1").write_text("Write-Host 'ok'", encoding="utf-8")

    monkeypatch.setattr(main, "get_project_path", lambda name: project if name == "demo" else None)

    selected = client.post("/project/select", headers=_headers(), json={"project": "demo"})
    assert selected.status_code == 200

    response = client.post(
        "/project/run-task",
        headers=_headers(),
        json={"task": "build.ps1", "dry_run": True},
    )
    assert response.status_code == 200
    assert response.json()["dry_run"] is True


def test_invalid_api_key(monkeypatch):
    _setup_settings(monkeypatch)

    response = client.get("/projects", headers={"X-Api-Key": "bad"})
    assert response.status_code == 401
    detail = response.json()["detail"]
    assert detail["code"] == "UNAUTHORIZED"
