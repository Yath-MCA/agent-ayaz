"""AI Plan Optimizer — memory-driven planner augmentation (Phase 9).

Augments ExecutionPlans with:
- failure pattern detection
- retry suggestions from history
- inefficiency warnings
"""

from typing import Optional
from services.memory_service import get_recent_failures, get_execution_stats


def augment_plan_context(plan_task: str, project: Optional[str]) -> dict:
    """Return optimization hints to prepend to the planner prompt."""
    hints: list[str] = []
    suggestion: Optional[str] = None

    stats = get_execution_stats(project)
    total = int(stats.get("total", 0) or 0)
    failures = int(stats.get("failures", 0) or 0)
    failure_rate = round((failures / total) * 100, 1) if total else 0.0
    success_rate = float(stats.get("success_rate", 0) or 0)

    if total > 0 and failure_rate > 30:
        hints.append(f"Warning: {failure_rate}% failure rate for project '{project}'.")

    failures = get_recent_failures(project, limit=5)
    for f in failures:
        if f.get("task") == plan_task or f.get("command", "").startswith(plan_task):
            hints.append(f"This task previously failed (exit={f['exit_code']}). Consider alternative approach.")
            suggestion = f.get("command") or f.get("task")
            break

    # Detect high avg duration
    recent = stats.get("recent", [])
    if recent:
        avg = sum(r.get("duration_ms", 0) for r in recent) / len(recent)
        if avg > 30_000:
            hints.append(f"Recent executions averaged {avg/1000:.1f}s — consider caching or splitting the task.")

    return {
        "hints": hints,
        "retry_suggestion": suggestion,
        "stats_summary": {
            "total": total,
            "failure_rate": failure_rate,
            "success_rate": success_rate,
        },
    }


def build_optimized_prompt(original_prompt: str, project: Optional[str]) -> str:
    """Inject memory context into the planner prompt."""
    ctx = augment_plan_context(original_prompt[:60], project)
    if not ctx["hints"]:
        return original_prompt
    hints_block = "\n".join(f"[MEMORY] {h}" for h in ctx["hints"])
    if ctx["retry_suggestion"]:
        hints_block += f"\n[MEMORY] Last known working command: {ctx['retry_suggestion']}"
    return f"{hints_block}\n\n{original_prompt}"
