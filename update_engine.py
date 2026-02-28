import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


class CodeUpdater:
    def __init__(self, project_root, allowed_files=None):
        self.project_root = Path(project_root)
        self.allowed_files = allowed_files or []

    # ------------------------------
    # Public method
    # ------------------------------
    def update_file(self, relative_path, new_code, marker=None, mode="INSERT_AFTER"):
        target = self.project_root / relative_path

        if not target.exists():
            return False, "File not found."

        if self.allowed_files and relative_path not in self.allowed_files:
            return False, "Modification not allowed for this file."

        # Create backup
        backup_path = self._create_backup(target)

        try:
            content = target.read_text(encoding="utf-8")
            updated = self._apply_update(content, new_code, marker, mode)

            if updated is None:
                return False, "Marker not found or invalid mode."

            target.write_text(updated, encoding="utf-8")

            # Validate syntax
            valid, message = self._validate_syntax(target)

            if not valid:
                shutil.copy(backup_path, target)
                return False, f"Syntax error. Rolled back.\n{message}"

            return True, "File updated successfully."

        except Exception as e:
            shutil.copy(backup_path, target)
            return False, f"Error occurred. Rolled back.\n{str(e)}"

    # ------------------------------
    # Internal update logic
    # ------------------------------
    def _apply_update(self, content, new_code, marker, mode):

        if mode == "APPEND_FILE":
            return content + "\n\n" + new_code

        if not marker:
            return None

        if mode == "INSERT_AFTER":
            if marker in content:
                return content.replace(marker, marker + "\n" + new_code)
            return None

        if mode == "INSERT_BEFORE":
            if marker in content:
                return content.replace(marker, new_code + "\n" + marker)
            return None

        if mode == "REPLACE_BLOCK":
            start_marker = f"{marker}_START"
            end_marker = f"{marker}_END"

            if start_marker in content and end_marker in content:
                before = content.split(start_marker)[0]
                after = content.split(end_marker)[1]
                return (
                    before
                    + start_marker
                    + "\n"
                    + new_code
                    + "\n"
                    + end_marker
                    + after
                )
            return None

        return None

    # ------------------------------
    # Backup
    # ------------------------------
    def _create_backup(self, file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(file_path.suffix + f".bak_{timestamp}")
        shutil.copy(file_path, backup_path)
        return backup_path

    # ------------------------------
    # Syntax validation
    # ------------------------------
    def _validate_syntax(self, file_path):

        if file_path.suffix == ".py":
            result = subprocess.run(
                ["python", "-m", "py_compile", str(file_path)],
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stderr

        if file_path.suffix in [".js", ".mjs", ".cjs"]:
            result = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stderr

        # Skip validation for other file types
        return True, "Validation skipped."