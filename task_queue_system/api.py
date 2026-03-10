"""FastAPI Integration for Task Queue System"""

import os
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from .core import TaskQueueManager
from .models import TaskResult, QueueStatus, QueueMetrics

try:
    from config.settings import config
    API_PORT = config.service_ports.queue_api
except ImportError:
    API_PORT = int(os.getenv("API_PORT", "9234"))


class TaskQueueAPI:
    """FastAPI wrapper for Task Queue System"""

    def __init__(self, queue_root: str = None):
        # Use environment variable or default
        if queue_root is None:
            queue_root = os.getenv("QUEUE_PATH", "agent-task")
        
        self.queue_root = queue_root
        self.queue = None
        self._validate_queue_path()
        self.router = self._create_router()

    def _validate_queue_path(self):
        """Validate and create queue path if needed"""
        if not os.path.exists(self.queue_root):
            try:
                os.makedirs(self.queue_root, exist_ok=True)
                os.makedirs(os.path.join(self.queue_root, "queue"), exist_ok=True)
                os.makedirs(os.path.join(self.queue_root, "completed"), exist_ok=True)
                os.makedirs(os.path.join(self.queue_root, "later"), exist_ok=True)
            except Exception as e:
                raise RuntimeError(f"Cannot create queue path {self.queue_root}: {e}")
        
        self.queue = TaskQueueManager(self.queue_root)

    def _create_router(self) -> APIRouter:
        """Create FastAPI router with queue endpoints"""
        router = APIRouter(prefix="/api/queue", tags=["queue"])

        @router.get("/config", response_model=dict)
        def get_config():
            """Get queue configuration"""
            return {
                "queue_root": self.queue_root,
                "queue_path": os.path.abspath(self.queue_root),
                "exists": os.path.exists(self.queue_root),
            }

        @router.post("/config/set", response_model=dict)
        def set_config(queue_path: str):
            """Set queue root path"""
            if not os.path.exists(queue_path):
                return {
                    "error": "Path does not exist",
                    "path": queue_path,
                    "suggestion": "Please create the directory first or provide a valid path"
                }
            
            self.queue_root = queue_path
            self._validate_queue_path()
            return {
                "status": "configured",
                "queue_root": self.queue_root,
                "message": "Queue path configured successfully"
            }

        @router.get("/status", response_model=dict)
        def get_status():
            """Get queue status"""
            try:
                status = self.queue.status()
                return {
                    "status": "ok",
                    "queue": status.queue,
                    "completed": status.completed,
                    "later": status.later,
                    "queue_empty": status.queue_empty,
                    "later_available": status.later_available,
                    "total_tasks": status.total_tasks,
                    "success_rate": status.success_rate,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "message": "Please configure queue path using POST /api/queue/config/set",
                    "queue_root": self.queue_root
                }

        @router.post("/run", response_model=list)
        def run_queue(limit: Optional[int] = None, timeout: int = 60):
            """Run all queued tasks"""
            try:
                results = self.queue.run_queue(limit=limit, timeout_seconds=timeout)
                return [
                    {
                        "name": r.name,
                        "status": r.status,
                        "exit_code": r.exit_code,
                        "duration_ms": r.duration_ms,
                    }
                    for r in results
                ]
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @router.post("/tasks", response_model=dict)
        def add_task(
            name: str,
            command: str,
            task_type: str = "command",
            timeout: int = 300,
            priority: int = 1,
        ):
            """Add task to queue"""
            try:
                task_id = self.queue.add_task(
                    name=name,
                    task_type=task_type,
                    command=command,
                    timeout=timeout,
                    priority=priority,
                )
                return {"task_id": task_id, "status": "queued"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @router.get("/metrics", response_model=dict)
        def get_metrics():
            """Get queue metrics"""
            try:
                metrics = self.queue.get_metrics()
                return {
                    "total_tasks": metrics.total_tasks,
                    "completed_tasks": metrics.completed_tasks,
                    "failed_tasks": metrics.failed_tasks,
                    "success_rate": metrics.success_rate,
                    "queue_depth": metrics.queue_depth,
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @router.post("/promote", response_model=dict)
        def promote_later():
            """Promote tasks from later/ to queue/"""
            try:
                moved = self.queue.promote_later_to_queue()
                return {"moved": moved, "count": len(moved)}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @router.get("/history", response_model=list)
        def get_history(limit: int = 100):
            """Get completed task history"""
            try:
                status = self.queue.status()
                return status.completed[:limit]
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        return router


def create_app(queue_root: str = None) -> FastAPI:
    """Create FastAPI application with queue integration"""
    app = FastAPI(
        title="Task Queue System",
        description="Standalone file-based task queue for distributed systems",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    queue_api = TaskQueueAPI(queue_root=queue_root)
    app.include_router(queue_api.router)

    # Health check
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "task-queue"}

    # Configuration info endpoint
    @app.get("/config")
    def get_system_config():
        """Get system configuration"""
        return {
            "queue_root": queue_api.queue_root,
            "message": "Use POST /api/queue/config/set to configure queue path",
            "example": {
                "POST": "/api/queue/config/set",
                "body": {"queue_path": "/path/to/agent-task"}
            }
        }

    return app
