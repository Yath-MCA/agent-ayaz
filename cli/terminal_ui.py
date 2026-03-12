"""Rich-based terminal UI components for AgentAyazDaddy CLI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table
from rich import box
from rich.text import Text

console = Console()


# ── Banner ────────────────────────────────────────────────────────────────────

def print_banner() -> None:
    banner = Text()
    banner.append("  AgentAyazDaddy\n", style="bold cyan")
    banner.append("  Workflow Refactor & CLI Task Runner\n", style="dim")
    console.print(Panel(banner, border_style="cyan", padding=(0, 2)))


# ── Status panel ─────────────────────────────────────────────────────────────

def print_status(data: Dict[str, Any]) -> None:
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Key", style="bold cyan", width=22)
    table.add_column("Value")

    for k, v in data.items():
        table.add_row(k, str(v))

    console.print(Panel(table, title="[bold]System Status[/bold]", border_style="blue"))


# ── Queue table ──────────────────────────────────────────────────────────────

def print_queue(queue_data: Dict[str, Any]) -> None:
    table = Table(title="Task Queue", box=box.ROUNDED)
    table.add_column("Queue", style="yellow", justify="right")
    table.add_column("Completed", style="green", justify="right")
    table.add_column("Later", style="dim", justify="right")
    table.add_column("Success Rate", justify="right")

    q = str(queue_data.get("queue", 0))
    c = str(queue_data.get("completed", 0))
    later = str(queue_data.get("later", 0))
    rate = queue_data.get("success_rate", 0)
    rate_str = f"{rate:.0%}" if isinstance(rate, float) else str(rate)

    color = "green" if queue_data.get("queue_empty") else "yellow"
    table.add_row(f"[{color}]{q}[/{color}]", c, later, rate_str)

    console.print(table)

    tasks_list: List[str] = queue_data.get("queue_tasks", [])
    if tasks_list:
        t = Table(show_header=True, box=box.SIMPLE)
        t.add_column("#", width=4, justify="right", style="dim")
        t.add_column("Task", style="white")
        for i, task in enumerate(tasks_list, 1):
            t.add_row(str(i), task)
        console.print(Panel(t, title="[bold yellow]Queued Tasks[/bold yellow]", border_style="yellow"))


# ── Projects table ────────────────────────────────────────────────────────────

def print_projects(projects: List[Dict[str, Any]]) -> None:
    table = Table(title="Projects", box=box.ROUNDED)
    table.add_column("Name", style="cyan bold")
    table.add_column("Path", style="dim")
    table.add_column("Tasks")

    for p in projects:
        name = p.get("name") or p.get("project") or "?"
        path = p.get("path", "")
        tasks = ", ".join(p.get("tasks", [])) if isinstance(p.get("tasks"), list) else str(p.get("tasks", ""))
        table.add_row(name, path, tasks)

    console.print(table)


# ── Log table ────────────────────────────────────────────────────────────────

def print_logs(records: List[Dict[str, Any]], title: str = "Recent Logs") -> None:
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Time", style="dim", width=24)
    table.add_column("Task", style="cyan", width=22)
    table.add_column("Status / Level")
    table.add_column("Message", style="dim")

    for r in records:
        ts = str(r.get("timestamp", ""))[:19].replace("T", " ")
        task = str(r.get("task") or r.get("level") or "")
        status = str(r.get("status") or r.get("level") or "")
        msg = str(r.get("message", ""))[:60]

        if status in ("failed", "ERROR", "CRITICAL"):
            status_text = f"[red]{status}[/red]"
        elif status in ("completed", "INFO"):
            status_text = f"[green]{status}[/green]"
        elif status in ("running", "WARNING"):
            status_text = f"[yellow]{status}[/yellow]"
        else:
            status_text = status

        table.add_row(ts, task, status_text, msg)

    console.print(table)


# ── Spinner wrapper ───────────────────────────────────────────────────────────

def spinner(message: str) -> Progress:
    p = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    )
    p.add_task(message)
    return p


# ── Verification report (delegated to workflow_verifier) ──────────────────────

def print_verification(report: Any) -> None:
    """Print a VerificationReport using its built-in rich printer."""
    report.print_rich()


# ── Schedule table ────────────────────────────────────────────────────────────

def print_schedule(status: Dict[str, Any]) -> None:
    running = status.get("running", False)
    jobs: List[Dict] = status.get("jobs", [])

    header = "[green]● Running[/green]" if running else "[red]○ Stopped[/red]"
    console.print(Panel(header, title="[bold]Scheduler[/bold]", border_style="blue", width=40))

    if jobs:
        table = Table(box=box.SIMPLE)
        table.add_column("Job ID", style="cyan")
        table.add_column("Next Run", style="dim")
        for j in jobs:
            table.add_row(j.get("id", "?"), j.get("next_run", "?"))
        console.print(table)
    elif running:
        console.print("  [dim]No jobs scheduled.[/dim]")


# ── Run-task file table ───────────────────────────────────────────────────────

def print_run_tasks(tasks: list, project_name: str = "") -> None:
    title = f"[bold cyan]Run Tasks — {project_name}[/bold cyan]" if project_name else "[bold cyan]Run Tasks[/bold cyan]"

    if not tasks:
        console.print(Panel(
            "[dim]No run-task files found in [bold]run-task/[/bold] folder.\n"
            "Use [bold]agent run --project[/bold] with a custom command instead.[/dim]",
            title=title,
            border_style="yellow",
        ))
        return

    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column("#", width=4, justify="right", style="dim")
    table.add_column("File", style="cyan bold")
    table.add_column("Description", style="dim")
    table.add_column("Auto-approve", justify="center")
    table.add_column("Delay", justify="right", style="dim")

    for i, task in enumerate(tasks, 1):
        auto = "[green]✔[/green]" if task.get("auto_approve", True) else "[red]✘[/red]"
        delay_s = task.get("delay_seconds", 0)
        delay = f"{delay_s}s" if delay_s else "—"
        table.add_row(str(i), task.get("name", "?"), task.get("description", ""), auto, delay)

    hint = f"[dim]Run:[/dim] [bold]agent task <file_name> --project {project_name}[/bold]" if project_name else ""
    console.print(Panel(table, title=f"{title} ({len(tasks)} files)", border_style="cyan"))
    if hint:
        console.print(hint + "\n")


# ── Task run result ───────────────────────────────────────────────────────────

def print_task_result(result: Dict[str, Any]) -> None:
    status = result.get("status", "unknown")
    task = result.get("task", "?")
    output = result.get("output") or result.get("detail") or ""

    if status in ("completed", "success", "ok"):
        color, icon = "green", "✔"
    elif status == "failed":
        color, icon = "red", "✘"
    else:
        color, icon = "yellow", "⚙"

    console.print(f"\n[{color} bold]{icon} {task} — {status}[/{color} bold]")
    if output:
        console.print(Panel(str(output)[:1000], border_style=color, title="Output"))
