from pathlib import Path
import os

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "D:/PERSONAL/LIVE_PROJECTS"))

def list_projects():
    if not PROJECT_ROOT.exists():
        return []
    return [p.name for p in PROJECT_ROOT.iterdir() if p.is_dir()]


def get_project_path(project_name: str) -> Path | None:
    if not project_name:
        return None

    if any(sep in project_name for sep in ("/", "\\")) or ".." in project_name:
        return None

    root = PROJECT_ROOT.resolve()
    project_path = (PROJECT_ROOT / project_name).resolve()

    if project_path.parent != root:
        return None

    if not project_path.exists() or not project_path.is_dir():
        return None

    return project_path