from pathlib import Path
import os

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "D:/PERSONAL/LIVE_PROJECTS"))

def list_projects():
    if not PROJECT_ROOT.exists():
        return []
    return [p.name for p in PROJECT_ROOT.iterdir() if p.is_dir()]