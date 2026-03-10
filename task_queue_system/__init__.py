"""Task Queue System - Standalone & Distributed

A production-ready task queue that works standalone or integrated with Docker,
agents, and multiple projects. File-based, stateless, multi-format support.
"""

__version__ = "1.0.0"
__author__ = "Agent Team"

from .core import TaskQueueManager
from .models import TaskResult, TaskStatus
from .api import TaskQueueAPI

__all__ = [
    "TaskQueueManager",
    "TaskResult",
    "TaskStatus",
    "TaskQueueAPI",
]
