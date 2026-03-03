"""CLI commands for Agent Ayazdy — one function per command."""

import json
from typing import Any, Optional

from cli.client import AgentClient


def _print(data: Any, raw: bool = False) -> None:
    if raw:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if isinstance(data, dict) and data.get("error"):
        detail = data.get("detail", data)
        if isinstance(detail, dict):
            code = detail.get("detail", {})
            if isinstance(code, dict):
                print(f"❌ {code.get('message', detail)} — {code.get('hint', '')}")
            else:
                print(f"❌ HTTP {data.get('status_code', '?')}: {detail}")
        else:
            print(f"❌ {detail}")
        return
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_health(client: AgentClient, raw: bool) -> None:
    _print(client.monitor_health(), raw)


def cmd_status(client: AgentClient, raw: bool) -> None:
    _print(client.status(), raw)


def cmd_projects(client: AgentClient, raw: bool) -> None:
    data = client.projects()
    if not raw and not data.get("error"):
        projects = data.get("projects", [])
        print(f"📂 {len(projects)} project(s):")
        for p in projects:
            print(f"  • {p}")
        return
    _print(data, raw)


def cmd_select(client: AgentClient, project: str, raw: bool) -> None:
    data = client.select(project)
    if not raw and not data.get("error"):
        tasks = data.get("tasks", [])
        print(f"✅ Selected: {data.get('project')}  →  {data.get('path')}")
        print(f"   {data.get('open_vscode', '')}")
        if tasks:
            print(f"   Tasks: {', '.join(t['name'] for t in tasks)}")
        else:
            print("   No run-task files found.")
        return
    _print(data, raw)


def cmd_run(client: AgentClient, task: str, project: Optional[str], dry_run: bool, raw: bool) -> None:
    data = client.run_task(task, project=project, dry_run=dry_run)
    if not raw and not data.get("error"):
        print(f"{'[DRY-RUN] ' if dry_run else ''}▶ {data.get('task')}  exit={data.get('exit_code')}  {data.get('duration_ms')}ms")
        if data.get("output"):
            print(data["output"])
        return
    _print(data, raw)


def cmd_run_all(client: AgentClient, project: Optional[str], dry_run: bool, raw: bool) -> None:
    data = client.run_all(project=project, dry_run=dry_run)
    if not raw and not data.get("error"):
        results = data.get("results", [])
        print(f"▶ Ran {data.get('processed', len(results))} task(s):")
        for r in results:
            icon = "✅" if r.get("exit_code") == 0 else "❌"
            print(f"  {icon} {r['task']}  exit={r.get('exit_code')}  {r.get('duration_ms')}ms")
        return
    _print(data, raw)


def cmd_history(client: AgentClient, project: Optional[str], raw: bool) -> None:
    data = client.history(project=project)
    if not raw and not data.get("error"):
        stats = data.get("stats", {})
        print(f"📊 {data.get('project', 'global')}  total={stats.get('total')}  failures={stats.get('failures')}  success={stats.get('success_rate')}%")
        retry = data.get("retry_suggestion")
        if retry:
            print(f"   💡 Retry suggestion: {retry}")
        for e in data.get("history", [])[:10]:
            icon = "✅" if e.get("exit_code") == 0 else "❌"
            print(f"  {icon} {e.get('task') or e.get('command')}  exit={e.get('exit_code')}  {e.get('duration_ms')}ms")
        return
    _print(data, raw)


def cmd_approvals(client: AgentClient, raw: bool) -> None:
    data = client.approvals()
    if not raw and not data.get("error"):
        pending = data.get("pending", [])
        if not pending:
            print("✅ No pending approvals.")
            return
        for r in pending:
            print(f"⏳ [{r['token']}] {r['task']}  type={r['type']}  user={r['user']}")
        return
    _print(data, raw)


def cmd_approve(client: AgentClient, token: str, raw: bool) -> None:
    _print(client.approve(token), raw)


def cmd_reject(client: AgentClient, token: str, raw: bool) -> None:
    _print(client.reject(token), raw)


def cmd_queue_status(client: AgentClient, raw: bool) -> None:
    data = client.queue_status()
    if not raw and not data.get("error"):
        print(f"📋 Queue   ({len(data['queue'])}): {', '.join(data['queue']) or 'empty'}")
        print(f"⏳ Later   ({len(data['later'])}): {', '.join(data['later']) or 'none'}")
        print(f"✅ Done    ({len(data['completed'])}): {len(data['completed'])} completed")
        if data.get("admin_prompt"):
            print(f"\n⚠️  {data['admin_prompt']}")
        return
    _print(data, raw)


def cmd_queue_run(client: AgentClient, raw: bool) -> None:
    data = client.queue_run()
    if not raw and not data.get("error"):
        print(f"▶ Processed {data.get('processed', 0)} task(s)")
        for r in data.get("results", []):
            icon = "✅" if r.get("status") in ("executed", "planned") else "❌"
            print(f"  {icon} {r['task']}  {r['status']}  exit={r.get('exit_code')}")
        if data.get("admin_prompt"):
            print(f"\n⚠️  {data['admin_prompt']}")
        return
    _print(data, raw)


def cmd_queue_promote(client: AgentClient, raw: bool) -> None:
    data = client.queue_promote()
    if not raw and not data.get("error"):
        moved = data.get("moved", [])
        if not moved:
            print("ℹ️  No tasks in 'later' folder.")
            return
        print(f"✅ Promoted {len(moved)} task(s) to queue:")
        for name in moved:
            print(f"  • {name}")
        return
    _print(data, raw)


def cmd_stats(client: AgentClient, raw: bool) -> None:
    _print(client.stats(), raw)


def cmd_self_check(client: AgentClient, raw: bool) -> None:
    data = client.self_check()
    if not raw and not data.get("error"):
        for key, val in data.items():
            icon = "✅" if val is True or val == "ok" else "❌" if val is False else "ℹ️"
            print(f"  {icon} {key}: {val}")
        return
    _print(data, raw)
