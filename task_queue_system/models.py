"""Task Queue Models - Data structures for task queue system"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Result of a task execution"""
    name: str
    status: str  # "executed" | "planned" | "skipped" | "failed"
    output: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: Optional[int] = None
    moved_to: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    worker_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class QueueStatus:
    """Current state of the task queue"""
    queue: List[str] = field(default_factory=list)
    completed: List[str] = field(default_factory=list)
    later: List[str] = field(default_factory=list)
    queue_empty: bool = True
    later_available: bool = False
    total_tasks: int = 0
    success_rate: float = 0.0
    last_run: Optional[datetime] = None


@dataclass
class TaskDefinition:
    """Task definition from YAML/DSL"""
    name: str
    description: Optional[str] = None
    task_type: str = "command"  # command | task_file | workflow
    command: Optional[str] = None
    task_file: Optional[str] = None
    timeout: int = 300
    retry_count: int = 0
    retry_delay: int = 30
    approval_required: bool = False
    dependencies: List[str] = field(default_factory=list)
    notification_on_success: Optional[str] = None
    notification_on_failure: Optional[str] = None


@dataclass
class QueueMetrics:
    """Queue system metrics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    throughput_tasks_per_hour: float = 0.0
    queue_depth: int = 0
    oldest_task_age_minutes: int = 0
    most_common_failure: Optional[str] = None
