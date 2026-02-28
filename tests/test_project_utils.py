from pathlib import Path

import project_utils


def test_get_project_path_and_list_projects(tmp_path, monkeypatch):
    project_root = tmp_path / "root"
    project_root.mkdir()
    (project_root / "a").mkdir()
    (project_root / "b").mkdir()

    monkeypatch.setattr(project_utils, "PROJECT_ROOT", project_root)

    assert sorted(project_utils.list_projects()) == ["a", "b"]
    assert project_utils.get_project_path("a") == project_root / "a"
    assert project_utils.get_project_path("../x") is None


def test_run_task_catalog_with_metadata(tmp_path):
    project = tmp_path / "app"
    task_dir = project / "run-task"
    task_dir.mkdir(parents=True)

    (task_dir / "build.ps1").write_text("Write-Host 'ok'", encoding="utf-8")
    (task_dir / "readme.txt").write_text("ignore", encoding="utf-8")
    (task_dir / "tasks.json").write_text(
        '{"build.ps1": {"description": "Build project", "auto_approve": true, "delay_seconds": 1}}',
        encoding="utf-8",
    )

    catalog = project_utils.get_run_task_catalog(project)
    assert len(catalog) == 1
    assert catalog[0]["name"] == "build.ps1"
    assert catalog[0]["description"] == "Build project"
    assert catalog[0]["auto_approve"] is True
    assert catalog[0]["delay_seconds"] == 1


def test_get_task_file_safety(tmp_path):
    project = tmp_path / "app"
    task_dir = project / "run-task"
    task_dir.mkdir(parents=True)
    task_file = task_dir / "run.py"
    task_file.write_text("print('ok')", encoding="utf-8")

    assert project_utils.get_task_file(project, "run.py") == task_file.resolve()
    assert project_utils.get_task_file(project, "../run.py") is None
    assert project_utils.get_task_file(project, "missing.py") is None
