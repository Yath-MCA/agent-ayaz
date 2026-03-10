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
    _print(client.health(), raw)


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
    if not raw and data.get("error") and data.get("status_code") == 409:
        detail = data.get("detail", {})
        info = detail.get("detail") if isinstance(detail, dict) else None
        if isinstance(info, dict) and info.get("code") == "CONFIRMATION_REQUIRED":
            print(f"⚠️ {info.get('message', 'Confirmation required')}")
            ans = input("Continue with project selection? (y/N): ").strip().lower()
            if ans in {"y", "yes"}:
                data = client.select(project, confirm_agent_tasks=True)

    if not raw and not data.get("error"):
        run_task_count = data.get("run_task_count", 0)
        print(f"✅ Selected: {data.get('project')}")
        print(f"   {data.get('open_vscode', '')}")
        if run_task_count:
            print(f"   run-task files available: {run_task_count}")
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


def cmd_analyze(client: AgentClient, prompt: str, project: Optional[str], raw: bool) -> None:
    selected_project = project
    if not selected_project:
        current = client.current()
        selected_project = current.get("project") if isinstance(current, dict) else None

    if not selected_project:
        if raw:
            _print({"error": True, "detail": "No project selected. Use select <project> or pass --project."}, raw)
        else:
            print("❌ No project selected. Use `select <project>` or pass `--project`.")
        return

    data = client.analyze(prompt, project=selected_project)
    if not raw and not data.get("error"):
        print(f"🧠 Analysis for project: {selected_project}")
        print(data.get("reply", "(no reply)"))
        return
    _print(data, raw)


def cmd_exec(client: AgentClient, command: str, project: Optional[str], raw: bool) -> None:
    selected_project = project
    if not selected_project:
        current = client.current()
        selected_project = current.get("project") if isinstance(current, dict) else None

    if not selected_project:
        if raw:
            _print({"error": True, "detail": "No project selected. Use select <project> or pass --project."}, raw)
        else:
            print("❌ No project selected. Use `select <project>` or pass `--project`.")
        return

    data = client.run_custom(command, project=selected_project, auto_approve=True)
    if not raw and not data.get("error"):
        print(f"▶ Command in project: {selected_project}")
        print(f"   exit={data.get('exit_code')}  duration={data.get('duration_ms')}ms")
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


def cmd_queue_run_text(client: AgentClient, include_later: bool, limit: int, raw: bool) -> None:
    data = client.queue_run_text_prompts(include_later=include_later, limit=limit)
    if not raw and not data.get("error"):
        mode = "queue+later" if include_later else "queue"
        print(f"▶ Processed {data.get('processed', 0)} text prompt file(s) from {mode}")
        print(f"   GitHub Copilot available: {data.get('copilot_available')}")
        for item in data.get("results", []):
            if item.get("status") == "executed":
                print(f"  ✅ {item.get('file')}  provider={item.get('provider')}  result={item.get('result_file')}")
            elif item.get("status") == "skipped":
                print(f"  ⏭ {item.get('file')}  {item.get('reason')}")
            else:
                print(f"  ❌ {item.get('file')}  {item.get('error', 'failed')}")
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


def cmd_desktop(raw: bool) -> None:
    """Launch the local desktop Git assistant (tkinter GUI)."""
    import subprocess
    import sys
    from pathlib import Path

    root_dir = Path(__file__).resolve().parents[1]
    script_path = root_dir / "tools" / "ayazgitdy_gui.py"
    if not script_path.exists():
        _print({"error": True, "detail": f"Desktop launcher not found: {script_path}"}, raw)
        return

    subprocess.Popen([sys.executable, str(script_path)])
    if raw:
        _print({"status": "ok", "launched": str(script_path)}, raw)
    else:
        print("🖥️  Desktop window launched.")


def cmd_gitcommit(path: Optional[str], jira: Optional[str], remark: Optional[str], no_push: bool, raw: bool) -> None:
    """Run standalone Git commit automation."""
    import sys
    import subprocess
    from pathlib import Path
    
    root_dir = Path(__file__).resolve().parents[1]
    script_path = root_dir / "tools" / "ayazgitdy.py"

    args = [sys.executable, str(script_path)]
    
    if path:
        args.extend(["--path", path])
    if jira:
        args.extend(["--jira", jira])
    if remark:
        args.extend(["--remark", remark])
    if no_push:
        args.append("--no-push")
    
    # Run standalone script with the current interpreter for portability.
    result = subprocess.run(args, capture_output=False, text=True)
    sys.exit(result.returncode)

