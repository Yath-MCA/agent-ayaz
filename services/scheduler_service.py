"""APScheduler-based scheduler service for AgentAyazDaddy.

Reads config/schedule.json and creates jobs that call the agent API.

Job types:
  queue-run    — POST /queue/run
  health-check — GET /health

Usage (standalone):
  python -m services.scheduler_service

Usage (embedded):
  from services.scheduler_service import start_scheduler, stop_scheduler
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

# APScheduler
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    _HAS_APSCHEDULER = True
except ImportError:
    _HAS_APSCHEDULER = False

from services.structured_logger import log_agent_event, log_error, log_task_event

SCHEDULE_CONFIG = Path(os.getenv("SCHEDULE_CONFIG", "config/schedule.json"))
AGENT_URL = os.getenv("AYAZDY_URL", "http://localhost:9234")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:9890")

_scheduler: Any = None


# ── Job callables ─────────────────────────────────────────────────────────────

def _run_queue_job(task_name: str, project: str | None = None) -> None:
    log_task_event(task=task_name, status="queued", message="Scheduler triggered queue run")
    try:
        resp = requests.post(f"{AGENT_URL}/queue/run", timeout=30)
        if resp.status_code == 200:
            log_task_event(task=task_name, status="completed", message="Scheduled queue run completed")
        else:
            log_task_event(task=task_name, status="failed",
                           message=f"Scheduled queue run returned HTTP {resp.status_code}")
    except Exception as exc:
        log_error(task=task_name, message="Scheduled queue run failed", exc=exc)


def _health_check_job(task_name: str = "health-check") -> None:
    try:
        resp = requests.get(f"{AGENT_URL}/health", timeout=10)
        status = "ok" if resp.status_code == 200 else f"http_{resp.status_code}"
        log_agent_event(message=f"Scheduled health check: {status}")
    except Exception as exc:
        log_error(task=task_name, message="Scheduled health check failed", exc=exc)


# ── Parse cron string ─────────────────────────────────────────────────────────

def _make_trigger(entry: dict) -> Any:
    """Return a CronTrigger from a schedule entry dict."""
    if not _HAS_APSCHEDULER:
        return None

    cron_str: str | None = entry.get("cron")
    time_str: str | None = entry.get("time")  # "HH:MM"

    if cron_str:
        parts = cron_str.split()
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
            return CronTrigger(
                minute=minute, hour=hour,
                day=day, month=month, day_of_week=day_of_week
            )
    elif time_str:
        hh, mm = time_str.split(":")
        return CronTrigger(hour=int(hh), minute=int(mm))

    return None


# ── Scheduler lifecycle ───────────────────────────────────────────────────────

def load_schedule() -> list[dict]:
    """Load schedule entries from config/schedule.json."""
    if not SCHEDULE_CONFIG.exists():
        log_agent_event(f"Schedule config not found: {SCHEDULE_CONFIG}", level="WARNING")
        return []
    try:
        with open(SCHEDULE_CONFIG) as f:
            data = json.load(f)
        return data.get("tasks", [])
    except Exception as exc:
        log_error(message="Failed to load schedule config", exc=exc)
        return []


def start_scheduler() -> Any:
    """Start APScheduler with jobs from config/schedule.json."""
    global _scheduler

    if not _HAS_APSCHEDULER:
        log_error(message="apscheduler not installed — scheduler disabled")
        print("[AgentAyazDaddy] WARNING: apscheduler not installed. Run: pip install apscheduler")
        return None

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler()
    entries = load_schedule()
    added = 0

    for entry in entries:
        if not entry.get("enabled", True):
            continue
        trigger = _make_trigger(entry)
        if trigger is None:
            log_agent_event(f"Skipping schedule entry with no trigger: {entry.get('task')}", level="WARNING")
            continue

        task_name = entry.get("task", "unnamed")
        job_type = entry.get("type", "queue-run")

        if job_type == "queue-run":
            _scheduler.add_job(
                _run_queue_job,
                trigger,
                id=task_name,
                args=[task_name, entry.get("project")],
                replace_existing=True,
            )
        elif job_type == "health-check":
            _scheduler.add_job(
                _health_check_job,
                trigger,
                id=task_name,
                args=[task_name],
                replace_existing=True,
            )

        log_agent_event(f"Scheduled: {task_name} ({job_type})")
        added += 1

    _scheduler.start()
    log_agent_event(f"Scheduler started with {added} job(s)")
    return _scheduler


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log_agent_event("Scheduler stopped")
    _scheduler = None


def scheduler_status() -> dict:
    """Return current scheduler status."""
    if not _HAS_APSCHEDULER:
        return {"running": False, "reason": "apscheduler not installed"}
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}
    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        jobs.append({"id": job.id, "next_run": next_run})
    return {"running": True, "job_count": len(jobs), "jobs": jobs}


# ── Standalone entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[AgentAyazDaddy] Starting scheduler service…")
    sched = start_scheduler()
    if sched:
        status = scheduler_status()
        print(f"[AgentAyazDaddy] Scheduler running — {status['job_count']} job(s)")
        for job in status.get("jobs", []):
            print(f"  • {job['id']}  →  next run: {job['next_run']}")
        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            stop_scheduler()
            print("[AgentAyazDaddy] Scheduler stopped.")
    else:
        print("[AgentAyazDaddy] Scheduler could not start.")
        sys.exit(1)
