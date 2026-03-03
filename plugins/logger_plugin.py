"""Example plugin: log hook events to console (Phase 11 demo)."""

import logging

log = logging.getLogger("plugin.logger")


def _before_plan(prompt: str = "", project: str = "", **_):
    log.info(f"[plugin:logger] before_plan  project={project!r}  prompt={prompt[:60]!r}")


def _after_execution(plan=None, result=None, **_):
    if result:
        log.info(f"[plugin:logger] after_execution  exit={result.exit_code}  {result.duration_ms}ms")


def register(manager) -> None:
    manager.register("before_plan", _before_plan)
    manager.register("after_execution", _after_execution)
