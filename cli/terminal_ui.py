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
from rich.columns import Columns

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


# ── Live terminal dashboard ───────────────────────────────────────────────────

def _build_live_layout(
    current_task: str,
    queue_tasks: list,
    status_data: dict,
    next_in: Optional[int] = None,
) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    # Header
    layout["header"].update(Panel(
        Text("  AgentAyazDaddy v2  — Live Dashboard", style="bold cyan"),
        border_style="cyan", padding=(0, 2)
    ))

    # Left — running task + queue
    running_text = Text()
    running_text.append("Running Task:\n", style="bold yellow")
    running_text.append(f"  {current_task or '(idle)'}\n", style="cyan bold")
    if queue_tasks:
        running_text.append("\nQueue:\n", style="bold")
        for t in queue_tasks[:5]:
            running_text.append(f"  · {t}\n", style="dim")
    layout["left"].update(Panel(running_text, title="[bold]Tasks[/bold]", border_style="yellow"))

    # Right — system status
    svc_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    svc_table.add_column("Service", style="bold", width=16)
    svc_table.add_column("Status")

    ollama_ok = not status_data.get("ollama_error")
    api_ok = not status_data.get("error")

    svc_table.add_row("Ollama", "[green]connected[/green]" if ollama_ok else "[red]offline[/red]")
    svc_table.add_row("API", "[green]connected[/green]" if api_ok else "[red]unreachable[/red]")
    svc_table.add_row("Mode", str(status_data.get("mode", "?")))
    svc_table.add_row("LLM", str(status_data.get("llm_provider", "?")))

    layout["right"].update(Panel(svc_table, title="[bold]System Status[/bold]", border_style="blue"))

    # Footer
    footer_text = f"  Queue: {status_data.get('queue', 0)} | Completed: {status_data.get('completed', 0)} | Later: {status_data.get('later', 0)}"
    if next_in is not None:
        footer_text += f"  |  Next task in {next_in}s"
    layout["footer"].update(Panel(Text(footer_text, style="dim"), border_style="dim"))

    return layout


def live_dashboard(
    client: Any,
    refresh_seconds: int = 5,
    duration_seconds: int = 60,
) -> None:
    """Render a live-refreshing terminal dashboard."""
    import time

    with Live(console=console, refresh_per_second=1, screen=True) as live:
        elapsed = 0
        while elapsed < duration_seconds:
            try:
                queue_data = client.queue_status()
                sys_data = client.status()
                current = queue_data.get("running_task") or "(idle)"
                queue_tasks = queue_data.get("queue_tasks", [])
                merged = {**queue_data, **sys_data}
                layout = _build_live_layout(current, queue_tasks, merged, next_in=refresh_seconds)
                live.update(layout)
            except Exception as exc:
                live.update(Panel(f"[red]Dashboard error: {exc}[/red]", border_style="red"))
            time.sleep(refresh_seconds)
            elapsed += refresh_seconds


# ── Agent config panel ────────────────────────────────────────────────────────

def print_agent_config(cfg: Dict[str, Any]) -> None:
    """Display config/agent.json as a Rich panel."""
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Key", style="bold cyan", width=26)
    table.add_column("Value")

    table.add_row("Name", str(cfg.get("name", "?")))
    table.add_row("Version", str(cfg.get("version", "?")))
    table.add_row("Mode", str(cfg.get("mode", "?")))
    table.add_row("Retry Limit", str(cfg.get("retry_limit", "?")))
    table.add_row("Task Timeout", f"{cfg.get('task_timeout_seconds', '?')}s")
    table.add_row("Self Healing", "[green]on[/green]" if cfg.get("self_healing") else "[red]off[/red]")
    table.add_row("AI on Failure", "[green]on[/green]" if cfg.get("ai_analysis_on_failure") else "[red]off[/red]")

    sub = cfg.get("sub_agents", {})
    for agent_key, agent_cfg in sub.items():
        enabled = "[green]enabled[/green]" if agent_cfg.get("enabled") else "[dim]disabled[/dim]"
        types = ", ".join(agent_cfg.get("task_types", []))
        table.add_row(f"  {agent_key.capitalize()}Agent", f"{enabled} — {types}")

    console.print(Panel(table, title="[bold cyan]Agent Configuration[/bold cyan]", border_style="cyan"))


# ── Scan results table ────────────────────────────────────────────────────────

def print_scan_results(results: List[Dict[str, Any]]) -> None:
    """Display auto-discovered project scan results."""
    if not results:
        console.print(Panel("[dim]No projects discovered in configured paths.[/dim]",
                            title="[bold]Project Scan[/bold]", border_style="yellow"))
        return

    table = Table(title=f"[bold]Discovered Projects[/bold] ({len(results)})", box=box.ROUNDED)
    table.add_column("Project", style="cyan bold")
    table.add_column("Path", style="dim")
    table.add_column("Markers Found", style="yellow")
    table.add_column("Tasks")

    for r in results:
        markers = ", ".join(r.get("markers", []))
        tasks = ", ".join(r.get("tasks", [])) or "—"
        table.add_row(r.get("name", "?"), str(r.get("path", "")), markers, tasks)

    console.print(table)
