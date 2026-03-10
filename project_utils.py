from pathlib import Path
import os
import json

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "D:/PERSONAL/LIVE_PROJECTS"))
OFFICIAL_PROJECTS_DIR = {"C:\\_IMPACT\\tomcat\\webapps\\"}


ALLOWED_TASK_SUFFIXES = {".ps1", ".bat", ".cmd", ".py", ".sh"}


def _extra_project_roots_from_env() -> list[Path]:
    raw = os.getenv("PROJECT_ROOTS", "")
    if not raw.strip():
        return []

    # Support both Windows ';' and comma separated lists.
    normalized = raw.replace(",", ";")
    items = [item.strip() for item in normalized.split(";") if item.strip()]
    return [Path(item) for item in items]


def get_project_roots() -> list[Path]:
    roots = [PROJECT_ROOT, *_extra_project_roots_from_env(), *(Path(p) for p in OFFICIAL_PROJECTS_DIR)]
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(root)
    return deduped


def list_projects():
    names: list[str] = []
    seen: set[str] = set()

    for root in get_project_roots():
        if not root.exists() or not root.is_dir():
            continue
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            lowered = entry.name.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            names.append(entry.name)

    return sorted(names)


def get_project_path(project_name: str) -> Path | None:
    if not project_name:
        return None

    if any(sep in project_name for sep in ("/", "\\")) or ".." in project_name:
        return None

    for root in get_project_roots():
        if not root.exists() or not root.is_dir():
            continue

        resolved_root = root.resolve()
        project_path = (resolved_root / project_name).resolve()

        if project_path.parent != resolved_root:
            continue

        if project_path.exists() and project_path.is_dir():
            return project_path

    return None


def get_run_task_dir(project_path: Path) -> Path:
    return project_path / "run-task"


def ensure_run_task_dir(project_path: Path) -> Path:
    task_dir = get_run_task_dir(project_path)
    task_dir.mkdir(exist_ok=True)
    return task_dir


def list_run_tasks(project_path: Path) -> list[str]:
    task_dir = get_run_task_dir(project_path)
    if not task_dir.exists() or not task_dir.is_dir():
        return []

    tasks: list[str] = []
    for entry in task_dir.iterdir():
        if entry.is_file() and entry.suffix.lower() in ALLOWED_TASK_SUFFIXES:
            tasks.append(entry.name)
    return sorted(tasks)


def load_task_metadata(project_path: Path) -> dict[str, dict]:
    metadata_file = get_run_task_dir(project_path) / "tasks.json"
    if not metadata_file.exists() or not metadata_file.is_file():
        return {}

    try:
        data = json.loads(metadata_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    normalized: dict[str, dict] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, dict):
            normalized[key] = value
    return normalized


def get_run_task_catalog(project_path: Path) -> list[dict]:
    task_names = list_run_tasks(project_path)
    metadata = load_task_metadata(project_path)

    catalog: list[dict] = []
    for name in task_names:
        meta = metadata.get(name, {})
        catalog.append(
            {
                "name": name,
                "description": str(meta.get("description", "")).strip() if meta else "",
                "auto_approve": bool(meta.get("auto_approve", True)) if meta else True,
                "delay_seconds": int(meta.get("delay_seconds", 0)) if meta and str(meta.get("delay_seconds", "0")).isdigit() else 0,
            }
        )
    return catalog


def get_task_file(project_path: Path, task_name: str) -> Path | None:
    if not task_name:
        return None

    if any(sep in task_name for sep in ("/", "\\")) or ".." in task_name:
        return None

    task_file = (get_run_task_dir(project_path) / task_name).resolve()

    task_dir = get_run_task_dir(project_path).resolve()
    if task_file.parent != task_dir:
        return None

    if not task_file.exists() or not task_file.is_file():
        return None

    if task_file.suffix.lower() not in ALLOWED_TASK_SUFFIXES:
        return None

    return task_file