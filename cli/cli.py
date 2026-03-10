"""ayazdy — CLI control interface for Agent Ayazdy.

Usage:
    ayazdy health
    ayazdy projects
    ayazdy select <project>
    ayazdy run <task> [--project P] [--dry-run]
    ayazdy analyze "<prompt>" [--project P]
    ayazdy exec "<command>" [--project P]
    ayazdy runall [--project P] [--dry-run]
    ayazdy history [--project P]
    ayazdy approvals
    ayazdy approve <token>
    ayazdy reject <token>
    ayazdy qstatus
    ayazdy qrun
    ayazdy qlater
    ayazdy qrun-text [--include-later] [--limit N]
    ayazdy stats
    ayazdy self-check
    ayazdy gitcommit [--path /repo] [--jira ABC-123] [--remark "note"] [--no-push]
    ayazdy desktop
"""

import argparse
import sys

from cli.client import AgentClient
from cli import commands


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ayazdy", description="Agent Ayazdy CLI")
    p.add_argument("--url", default=None, help="Agent base URL (default: $AYAZDY_URL or http://localhost:9234)")
    p.add_argument("--key", default=None, help="API key (default: $API_SECRET_KEY)")
    p.add_argument("--json", action="store_true", dest="raw", help="Output raw JSON")

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health",    help="Check agent health")
    sub.add_parser("status",    help="Runtime status")
    sub.add_parser("projects",  help="List projects")
    sub.add_parser("current",   help="Show selected project")
    sub.add_parser("stats",     help="Execution metrics")
    sub.add_parser("self-check",help="Run self-diagnostic")
    sub.add_parser("desktop",   help="Launch desktop Git assistant")
    sub.add_parser("approvals", help="List pending approvals")
    sub.add_parser("qstatus",   help="Queue / later / completed status")
    sub.add_parser("qrun",      help="Process all tasks in queue/")
    sub.add_parser("qlater",    help="Promote later/ tasks into queue/")
    qrt = sub.add_parser("qrun-text", help="Run .txt/.md prompts from queue via GitHub Copilot first")
    qrt.add_argument("--include-later", action="store_true", help="Include later/ folder prompts")
    qrt.add_argument("--limit", type=int, default=20, help="Max prompt files to process")

    git = sub.add_parser("gitcommit", help="Auto-commit Git changes")
    git.add_argument("--path", default=None, help="Repository path (default: current dir)")
    git.add_argument("--jira", default=None, help="Jira ticket (e.g., ABC-123)")
    git.add_argument("--remark", default=None, help="Developer remark")
    git.add_argument("--no-push", action="store_true", help="Commit only, don't push")

    sel = sub.add_parser("select", help="Select a project")
    sel.add_argument("project")

    run = sub.add_parser("run", help="Run a task file")
    run.add_argument("task")
    run.add_argument("--project", default=None)
    run.add_argument("--dry-run", action="store_true")

    analyze = sub.add_parser("analyze", help="Analyze a prompt in selected project context")
    analyze.add_argument("prompt")
    analyze.add_argument("--project", default=None)

    ex = sub.add_parser("exec", help="Execute custom command in selected project")
    ex.add_argument("command")
    ex.add_argument("--project", default=None)

    ra = sub.add_parser("runall", help="Run all tasks in order")
    ra.add_argument("--project", default=None)
    ra.add_argument("--dry-run", action="store_true")

    hist = sub.add_parser("history", help="Execution history")
    hist.add_argument("--project", default=None)

    appr = sub.add_parser("approve", help="Approve a pending task")
    appr.add_argument("token")

    rej = sub.add_parser("reject", help="Reject a pending task")
    rej.add_argument("token")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    client = AgentClient(base_url=args.url, api_key=args.key)
    raw = args.raw

    match args.cmd:
        case "health":     commands.cmd_health(client, raw)
        case "status":     commands.cmd_status(client, raw)
        case "projects":   commands.cmd_projects(client, raw)
        case "current":    print(client.current())
        case "select":     commands.cmd_select(client, args.project, raw)
        case "run":        commands.cmd_run(client, args.task, args.project, args.dry_run, raw)
        case "analyze":    commands.cmd_analyze(client, args.prompt, args.project, raw)
        case "exec":       commands.cmd_exec(client, args.command, args.project, raw)
        case "runall":     commands.cmd_run_all(client, args.project, args.dry_run, raw)
        case "history":    commands.cmd_history(client, args.project, raw)
        case "approvals":  commands.cmd_approvals(client, raw)
        case "approve":    commands.cmd_approve(client, args.token, raw)
        case "reject":     commands.cmd_reject(client, args.token, raw)
        case "qstatus":    commands.cmd_queue_status(client, raw)
        case "qrun":       commands.cmd_queue_run(client, raw)
        case "qlater":     commands.cmd_queue_promote(client, raw)
        case "qrun-text":  commands.cmd_queue_run_text(client, args.include_later, args.limit, raw)
        case "stats":      commands.cmd_stats(client, raw)
        case "self-check": commands.cmd_self_check(client, raw)
        case "desktop":    commands.cmd_desktop(raw)
        case "gitcommit":  commands.cmd_gitcommit(args.path, args.jira, args.remark, args.no_push, raw)
        case _:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
