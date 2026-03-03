"""ayazdy — CLI control interface for Agent Ayazdy.

Usage:
    ayazdy health
    ayazdy projects
    ayazdy select <project>
    ayazdy run <task> [--project P] [--dry-run]
    ayazdy runall [--project P] [--dry-run]
    ayazdy history [--project P]
    ayazdy approvals
    ayazdy approve <token>
    ayazdy reject <token>
    ayazdy qstatus
    ayazdy qrun
    ayazdy qlater
    ayazdy stats
    ayazdy self-check
"""

import argparse
import sys

from cli.client import AgentClient
from cli import commands


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ayazdy", description="Agent Ayazdy CLI")
    p.add_argument("--url", default=None, help="Agent base URL (default: $AYAZDY_URL or http://localhost:8000)")
    p.add_argument("--key", default=None, help="API key (default: $API_SECRET_KEY)")
    p.add_argument("--json", action="store_true", dest="raw", help="Output raw JSON")

    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health",    help="Check agent health")
    sub.add_parser("status",    help="Runtime status")
    sub.add_parser("projects",  help="List projects")
    sub.add_parser("current",   help="Show selected project")
    sub.add_parser("stats",     help="Execution metrics")
    sub.add_parser("self-check",help="Run self-diagnostic")
    sub.add_parser("approvals", help="List pending approvals")
    sub.add_parser("qstatus",   help="Queue / later / completed status")
    sub.add_parser("qrun",      help="Process all tasks in queue/")
    sub.add_parser("qlater",    help="Promote later/ tasks into queue/")

    sel = sub.add_parser("select", help="Select a project")
    sel.add_argument("project")

    run = sub.add_parser("run", help="Run a task file")
    run.add_argument("task")
    run.add_argument("--project", default=None)
    run.add_argument("--dry-run", action="store_true")

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
        case "runall":     commands.cmd_run_all(client, args.project, args.dry_run, raw)
        case "history":    commands.cmd_history(client, args.project, raw)
        case "approvals":  commands.cmd_approvals(client, raw)
        case "approve":    commands.cmd_approve(client, args.token, raw)
        case "reject":     commands.cmd_reject(client, args.token, raw)
        case "qstatus":    commands.cmd_queue_status(client, raw)
        case "qrun":       commands.cmd_queue_run(client, raw)
        case "qlater":     commands.cmd_queue_promote(client, raw)
        case "stats":      commands.cmd_stats(client, raw)
        case "self-check": commands.cmd_self_check(client, raw)
        case _:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
