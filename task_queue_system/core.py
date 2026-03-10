"""Core Task Queue Manager - Main entry point"""

import shutil
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from .models import TaskResult, QueueStatus, TaskStatus, QueueMetrics


class TaskQueueManager:
    """Main Task Queue Manager - File-based, distributed-ready"""

    def __init__(
        self,
        queue_root: str = "agent-task",
        strict_mode: bool = False,
        max_output_chars: int = 3000,
        worker_id: Optional[str] = None,
    ):
        self.queue_root = Path(queue_root)
        self.queue_dir = self.queue_root / "queue"
        self.completed_dir = self.queue_root / "completed"
        self.later_dir = self.queue_root / "later"
        self.logs_dir = self.queue_root / "logs"
        self.reports_dir = self.queue_root / "reports"

        self.strict_mode = strict_mode
        self.max_output_chars = max_output_chars
        self.worker_id = worker_id or "default"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create queue directories if they don't exist"""
        for directory in [
            self.queue_dir,
            self.completed_dir,
            self.later_dir,
            self.logs_dir,
            self.reports_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def status(self) -> QueueStatus:
        """Get current queue status"""
        queue_files = self._sorted_files(self.queue_dir)
        completed_files = self._sorted_files(self.completed_dir)
        later_files = self._sorted_files(self.later_dir)

        total = len(queue_files) + len(completed_files) + len(later_files)
        completed = len(completed_files)
        success_rate = (completed / total * 100) if total > 0 else 0.0

        return QueueStatus(
            queue=[f.name for f in queue_files],
            completed=[f.name for f in completed_files],
            later=[f.name for f in later_files],
            queue_empty=len(queue_files) == 0,
            later_available=len(later_files) > 0,
            total_tasks=total,
            success_rate=success_rate,
            last_run=self._get_last_run_time(),
        )

    def add_task(
        self,
        name: str,
        task_type: str = "command",
        command: Optional[str] = None,
        timeout: int = 300,
        priority: int = 1,
    ) -> str:
        """
        Add task to queue

        Args:
            name: Task name
            task_type: "command" or "task_file"
            command: Command to execute
            timeout: Timeout in seconds
            priority: Priority (0-99, lower = higher priority)

        Returns:
            Task filename
        """
        timestamp = int(time.time() * 1000)
        filename = f"{priority:02d}-{name}-{timestamp}.yaml"
        task_path = self.queue_dir / filename

        yaml_content = f"""name: "{name}"
type: "{task_type}"
timeout: {timeout}
"""
        if command:
            yaml_content += f'command: |\n  {command}\n'

        task_path.write_text(yaml_content)
        return filename

    def run_queue(
        self,
        limit: Optional[int] = None,
        timeout_seconds: int = 60,
    ) -> List[TaskResult]:
        """
        Run all queued tasks in order

        Args:
            limit: Max tasks to run (None = all)
            timeout_seconds: Timeout per task

        Returns:
            List of TaskResult objects
        """
        queue_files = self._sorted_files(self.queue_dir)
        if limit:
            queue_files = queue_files[:limit]

        results = []
        for task_file in queue_files:
            result = self._execute_task(task_file, timeout_seconds)
            results.append(result)
            self._move_to_completed(task_file)

        return results

    def promote_later_to_queue(self) -> List[str]:
        """Move all tasks from later/ to queue/"""
        moved = []
        for task_file in self._sorted_files(self.later_dir):
            dest = self.queue_dir / task_file.name
            if dest.exists():
                stem = task_file.stem
                suffix = task_file.suffix
                dest = self.queue_dir / f"{stem}_{int(time.time())}{suffix}"
            shutil.move(str(task_file), str(dest))
            moved.append(dest.name)
        return moved

    def wait_for_task(
        self,
        task_name: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> Optional[TaskResult]:
        """
        Wait for a task to complete

        Args:
            task_name: Name to search for
            timeout: Max wait time in seconds
            poll_interval: Check interval in seconds

        Returns:
            TaskResult when found, None if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            # Check completed directory
            for f in self._sorted_files(self.completed_dir):
                if task_name in f.name:
                    return self._load_task_result(f)
            time.sleep(poll_interval)
        return None

    def get_metrics(self) -> QueueMetrics:
        """Get queue system metrics"""
        status = self.status()
        completed = len(status.completed)
        total = status.total_tasks

        failed_count = self._count_failed_tasks()
        success_rate = ((completed - failed_count) / completed * 100) if completed > 0 else 0.0

        return QueueMetrics(
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed_count,
            success_rate=success_rate,
            queue_depth=len(status.queue),
        )

    def cleanup_old_completed(self, days: int = 30) -> int:
        """Remove completed tasks older than N days"""
        cutoff = time.time() - (days * 86400)
        removed = 0
        for f in self.completed_dir.glob("*"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        return removed

    def archive_completed(self) -> Path:
        """Archive all completed tasks to a .tar.gz file"""
        import tarfile

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.reports_dir / f"completed_{timestamp}.tar.gz"

        with tarfile.open(archive_path, "w:gz") as tar:
            for f in self.completed_dir.glob("*"):
                tar.add(f, arcname=f.name)

        return archive_path

    # Private methods

    def _sorted_files(self, directory: Path) -> List[Path]:
        """Get sorted file list from directory"""
        if not directory.exists():
            return []
        return sorted(
            [f for f in directory.iterdir() if f.is_file()],
            key=lambda p: p.name.lower(),
        )

    def _execute_task(self, task_file: Path, timeout: int) -> TaskResult:
        """Execute a single task and return result"""
        import subprocess

        try:
            result = subprocess.run(
                ["python", str(task_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = result.stdout + result.stderr
            if len(output) > self.max_output_chars:
                output = output[: self.max_output_chars]

            return TaskResult(
                name=task_file.name,
                status="executed" if result.returncode == 0 else "failed",
                output=output,
                exit_code=result.returncode,
                duration_ms=timeout * 1000,
                worker_id=self.worker_id,
            )
        except subprocess.TimeoutExpired:
            return TaskResult(
                name=task_file.name,
                status="failed",
                output="Task timeout",
                exit_code=-1,
                error_message=f"Timeout after {timeout}s",
                worker_id=self.worker_id,
            )
        except Exception as e:
            return TaskResult(
                name=task_file.name,
                status="failed",
                output=str(e),
                exit_code=-1,
                error_message=str(e),
                worker_id=self.worker_id,
            )

    def _move_to_completed(self, task_file: Path) -> Path:
        """Move task file to completed directory"""
        dest = self.completed_dir / task_file.name
        if dest.exists():
            stem = task_file.stem
            suffix = task_file.suffix
            dest = self.completed_dir / f"{stem}_{int(time.time())}{suffix}"
        shutil.move(str(task_file), str(dest))
        return dest

    def _count_failed_tasks(self) -> int:
        """Count tasks with 'failed' in status log"""
        count = 0
        for f in self._sorted_files(self.completed_dir):
            if "failed" in f.name.lower():
                count += 1
        return count

    def _get_last_run_time(self) -> Optional[datetime]:
        """Get timestamp of last completed task"""
        completed = self._sorted_files(self.completed_dir)
        if completed:
            latest = completed[-1]
            return datetime.fromtimestamp(latest.stat().st_mtime)
        return None

    def _load_task_result(self, task_file: Path) -> TaskResult:
        """Load TaskResult from completed file"""
        # Parse filename for metadata
        return TaskResult(
            name=task_file.name,
            status="completed",
            moved_to=str(task_file),
            timestamp=datetime.fromtimestamp(task_file.stat().st_mtime),
        )
