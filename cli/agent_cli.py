"""AgentAyazDaddy — Main CLI entry point.

Commands:
  agent project <name>      Select project, open in VS Code, show run-task files
  agent projects            List all configured projects
  agent tasks [name]        List run-task files for a project
  agent task <file>         Run a specific run-task file in the selected project
  agent run <task>          Run a task (project context aware)
  agent queue               Show task queue status
  agent schedule            Show/manage scheduler
  agent logs                Tail structured logs
  agent status              Full system status
  agent analyze <prompt>    AI analysis via Ollama/LLM
  agent ask <question>      Ask Ollama a natural language question
  agent verify <task>       Pre-run workflow verification
  agent dashboard           Post task status to dashboard

Usage:
  python -m cli.agent_cli [COMMAND] [OPTIONS]
  agent [COMMAND] [OPTIONS]          (via agent.bat)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.client import AgentClient
from cli import terminal_ui as ui

app = typer.Typer(
    name="agent",
    help="[bold cyan]AgentAyazDaddy[/bold cyan] — Workflow Refactor & CLI Task Runner",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()

# ── Shared state ──────────────────────────────────────────────────────────────

_BASE_URL_DEFAULT = os.getenv("AYAZDY_URL", "http://localhost:9234")
_API_KEY_DEFAULT = os.getenv("API_SECRET_KEY", "")


def _client(base_url: str = _BASE_URL_DEFAULT, api_key: str = _API_KEY_DEFAULT) -> AgentClient:
    return AgentClient(base_url=base_url, api_key=api_key)


# ── Shared options callback ───────────────────────────────────────────────────

_url_option = typer.Option(None, "--url", help="Agent base URL", envvar="AYAZDY_URL")
_key_option  = typer.Option(None, "--key", help="API key", envvar="API_SECRET_KEY")
_raw_option  = typer.Option(False, "--json", help="Output raw JSON")


# ── Commands ──────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        ui.print_banner()
        console.print("Run [bold cyan]agent --help[/bold cyan] to see available commands.\n")


@app.command()
def status(
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
    raw: bool = _raw_option,
) -> None:
    """Show full system status (API health, mode, LLM provider)."""
    ui.print_banner()
    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)

    with ui.spinner("Checking system status…") as prog:
        prog.start()
        health = client.health()
        sys_status = client.status()
        queue_info = client.queue_status()
        prog.stop()

    if raw:
        console.print_json(json.dumps({"health": health, "status": sys_status, "queue": queue_info}))
        return

    # Build status dict
    merged: dict = {}
    if not health.get("error"):
        merged["Health"] = "✔ OK" if health.get("status") == "ok" else "⚠ " + str(health)
    else:
        merged["Health"] = f"✘ {health.get('detail', 'unreachable')}"

    if not sys_status.get("error"):
        merged["Mode"] = sys_status.get("mode", "?")
        merged["LLM Provider"] = sys_status.get("llm_provider", "?")
        merged["Version"] = sys_status.get("version", "?")

    if not queue_info.get("error"):
        merged["Queue"] = queue_info.get("queue", 0)
        merged["Completed"] = queue_info.get("completed", 0)
        merged["Later"] = queue_info.get("later", 0)

    ui.print_status(merged)


@app.command()
def run(
    task: str = typer.Argument(..., help="Task name or file to execute"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project context"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
    verify: bool = typer.Option(False, "--verify", help="Run workflow verification first"),
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
) -> None:
    """Run a task by name. Uses task queue system and project context."""
    ui.print_banner()
    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)

    if verify:
        console.print("\n[bold]Running pre-execution verification…[/bold]")
        from agents.workflow_verifier import verify_task
        from services.structured_logger import log_task_event

        report = verify_task(
            task_name=task,
            base_url=url or _BASE_URL_DEFAULT,
        )
        ui.print_verification(report)
        if not report.passed:
            console.print("[red]Verification failed — aborting.[/red]")
            raise typer.Exit(1)

    console.print(f"\n[cyan]▶ Running task:[/cyan] [bold]{task}[/bold]" +
                  (f"  (project: {project})" if project else "") +
                  ("  [dim][dry-run][/dim]" if dry_run else ""))

    with ui.spinner(f"Executing {task}…") as prog:
        prog.start()
        result = client.run_task(task=task, project=project, dry_run=dry_run)
        prog.stop()

    ui.print_task_result(result)

    # Log to structured logs
    try:
        from services.structured_logger import log_task_event
        status_val = result.get("status", "unknown")
        log_task_event(task=task, status=status_val, project=project,
                       message=str(result.get("output", ""))[:200])
    except Exception:
        pass


@app.command()
def queue(
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
    raw: bool = _raw_option,
    run_now: bool = typer.Option(False, "--run", help="Execute the queue immediately"),
    promote: bool = typer.Option(False, "--promote", help="Promote later/ tasks into queue"),
) -> None:
    """Show queue status, or run/promote tasks."""
    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)

    if promote:
        console.print("[cyan]Promoting later/ tasks into queue/…[/cyan]")
        result = client.queue_promote()
        if raw:
            console.print_json(json.dumps(result))
        else:
            promoted = result.get("promoted", result)
            console.print(f"[green]✔ Promoted:[/green] {promoted}")
        return

    if run_now:
        console.print("[cyan]▶ Running queue…[/cyan]")
        with ui.spinner("Processing queue…") as prog:
            prog.start()
            result = client.queue_run()
            prog.stop()
        if raw:
            console.print_json(json.dumps(result))
        else:
            console.print(f"[green]✔ Queue run completed.[/green]")
            if isinstance(result, dict):
                ui.print_task_result(result)
        return

    with ui.spinner("Fetching queue status…") as prog:
        prog.start()
        data = client.queue_status()
        prog.stop()

    if raw:
        console.print_json(json.dumps(data))
        return

    if data.get("error"):
        console.print(f"[red]✘ {data.get('detail', 'Error fetching queue')}[/red]")
        raise typer.Exit(1)

    ui.print_queue(data)


@app.command()
def projects(
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
    raw: bool = _raw_option,
    local: bool = typer.Option(False, "--local", help="Read from config/projects.json instead of API"),
) -> None:
    """List configured projects."""
    if local:
        config_path = Path("config/projects.json")
        if not config_path.exists():
            console.print("[red]config/projects.json not found.[/red]")
            raise typer.Exit(1)
        with open(config_path) as f:
            data = json.load(f)
        if raw:
            console.print_json(json.dumps(data))
        else:
            ui.print_projects(data.get("projects", []))
        return

    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)
    with ui.spinner("Loading projects…") as prog:
        prog.start()
        data = client.projects()
        prog.stop()

    if raw:
        console.print_json(json.dumps(data))
        return

    if data.get("error"):
        console.print(f"[red]✘ {data.get('detail', 'Error')}[/red]")
        raise typer.Exit(1)

    raw_projects = data.get("projects", [])
    # Normalize to list of dicts
    norm = [{"name": p} if isinstance(p, str) else p for p in raw_projects]
    ui.print_projects(norm)


@app.command()
def project(
    name: str = typer.Argument(..., help="Project name to select"),
    open_vscode: bool = typer.Option(True, "--vscode/--no-vscode", help="Open in VS Code after selecting"),
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
) -> None:
    """Select a project, open in VS Code, and show run-task files."""
    import subprocess
    from project_utils import get_project_path, get_run_task_catalog

    ui.print_banner()

    project_path = get_project_path(name)
    if not project_path:
        console.print(f"[red]✘ Project '{name}' not found.[/red]")
        console.print("[dim]Run [bold]agent projects[/bold] to see available project names.[/dim]")
        raise typer.Exit(1)

    console.print(f"[green]✔ Selected project:[/green] [bold cyan]{name}[/bold cyan]")
    console.print(f"[dim]  Path: {project_path}[/dim]\n")

    # Open in VS Code
    if open_vscode:
        try:
            subprocess.Popen(["code", str(project_path)], shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print("[green]✔ Opened in VS Code[/green]\n")
        except Exception as exc:
            console.print(f"[yellow]⚠ Could not open VS Code: {exc}[/yellow]\n")

    # Show run-task catalog locally (no API required)
    tasks = get_run_task_catalog(project_path)
    ui.print_run_tasks(tasks, project_name=name)

    # Register selection with the API server when reachable
    try:
        client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)
        result = client.select(project=name)
        if not result.get("error"):
            copilot_hint = result.get("project_checks", {}).get("run_github_copilot_first", False)
            console.print("[dim]✔ Project registered with API server[/dim]")
            if copilot_hint:
                console.print("[yellow]⚡ Pending agent-task queue detected — run GitHub Copilot tasks first.[/yellow]")
    except Exception:
        console.print("[dim]ℹ API server unreachable — project selected locally only.[/dim]")


@app.command()
def tasks(
    project_name: Optional[str] = typer.Argument(None, help="Project name (uses current if omitted)"),
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
    raw: bool = _raw_option,
) -> None:
    """List run-task files for a project."""
    from project_utils import get_project_path, get_run_task_catalog

    # Determine project
    name = project_name
    if not name:
        # Try to get current project from API
        try:
            client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)
            current = client.current()
            name = current.get("project")
        except Exception:
            pass

    if not name:
        console.print("[red]✘ No project specified and none currently selected.[/red]")
        console.print("[dim]Usage: [bold]agent tasks <project_name>[/bold] or first run [bold]agent project <name>[/bold][/dim]")
        raise typer.Exit(1)

    project_path = get_project_path(name)
    if not project_path:
        console.print(f"[red]✘ Project '{name}' not found.[/red]")
        raise typer.Exit(1)

    task_list = get_run_task_catalog(project_path)

    if raw:
        console.print_json(json.dumps(task_list))
        return

    ui.print_run_tasks(task_list, project_name=name)


@app.command("task")
def run_task(
    task_name: str = typer.Argument(..., help="run-task file name (e.g. build.ps1)"),
    project_name: Optional[str] = typer.Option(None, "--project", "-p", help="Project name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without executing"),
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
) -> None:
    """Run a specific run-task file in a project via the API."""
    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)

    # Resolve project from API current if not provided
    name = project_name
    if not name:
        try:
            current = client.current()
            name = current.get("project")
        except Exception:
            pass

    if not name:
        console.print("[red]✘ No project specified. Use --project <name> or first run agent project <name>.[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]▶ Running task:[/cyan] [bold]{task_name}[/bold]  (project: {name})" +
                  ("  [dim][dry-run][/dim]" if dry_run else ""))

    with ui.spinner(f"Executing {task_name}…") as prog:
        prog.start()
        result = client.run_task(task=task_name, project=name, dry_run=dry_run)
        prog.stop()

    ui.print_task_result(result)

    # Log result
    try:
        from services.structured_logger import log_task_event
        log_task_event(task=task_name, status=result.get("status", "unknown"),
                       project=name, message=str(result.get("output", ""))[:200])
    except Exception:
        pass


@app.command()
def schedule(
    url: Optional[str] = _url_option,
    start: bool = typer.Option(False, "--start", help="Start the scheduler"),
    stop: bool = typer.Option(False, "--stop", help="Stop the scheduler"),
) -> None:
    """Show scheduler status or manage scheduled tasks."""
    from services.scheduler_service import scheduler_status, start_scheduler, stop_scheduler

    if start:
        console.print("[cyan]Starting scheduler…[/cyan]")
        start_scheduler()
        status_data = scheduler_status()
        ui.print_schedule(status_data)
        return

    if stop:
        console.print("[cyan]Stopping scheduler…[/cyan]")
        stop_scheduler()
        console.print("[yellow]Scheduler stopped.[/yellow]")
        return

    status_data = scheduler_status()
    ui.print_schedule(status_data)

    # Also show config/schedule.json entries
    config_path = Path("config/schedule.json")
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
        tasks = cfg.get("tasks", [])
        if tasks:
            from rich.table import Table
            from rich import box as rbox
            table = Table(title="Configured Schedules", box=rbox.SIMPLE)
            table.add_column("Task", style="cyan")
            table.add_column("Time/Cron", style="yellow")
            table.add_column("Enabled")
            table.add_column("Type", style="dim")
            for t in tasks:
                enabled = "[green]✔[/green]" if t.get("enabled") else "[red]✘[/red]"
                time_val = t.get("cron") or t.get("time") or "?"
                table.add_row(t.get("task", "?"), time_val, enabled, t.get("type", "?"))
            console.print(table)


@app.command()
def logs(
    log_type: str = typer.Argument("tasks", help="Log type: tasks | agent | errors"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of recent entries"),
    raw: bool = _raw_option,
) -> None:
    """View structured logs (tasks.log, agent.log, errors.log)."""
    from services.structured_logger import read_log

    records = read_log(log_type=log_type, limit=limit)
    if not records:
        console.print(f"[dim]No {log_type} log entries found.[/dim]")
        return

    if raw:
        console.print_json(json.dumps(records))
        return

    ui.print_logs(records, title=f"[bold]{log_type.capitalize()} Logs[/bold] (last {len(records)})")


@app.command()
def analyze(
    prompt: str = typer.Argument(..., help="Prompt or question to analyze"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project context"),
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
) -> None:
    """Run AI analysis in project context via LLM."""
    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)
    console.print(f"[cyan]Analyzing:[/cyan] {prompt}\n")

    with ui.spinner("Thinking…") as prog:
        prog.start()
        result = client.analyze(prompt=prompt, project=project)
        prog.stop()

    if result.get("error"):
        console.print(f"[red]✘ {result.get('detail', 'Error')}[/red]")
        raise typer.Exit(1)

    output = result.get("response") or result.get("output") or result.get("result") or str(result)
    from rich.panel import Panel
    console.print(Panel(str(output), title="[bold cyan]Analysis Result[/bold cyan]", border_style="cyan"))


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask Ollama"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model override"),
) -> None:
    """Ask Ollama a natural language question directly."""
    import asyncio

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = model or os.getenv("OLLAMA_MODEL", "mistral")

    console.print(f"[cyan]Asking Ollama ({ollama_model}):[/cyan] {question}\n")

    try:
        from services.ollama_service import call_ollama

        with ui.spinner("Waiting for Ollama…") as prog:
            prog.start()
            answer = asyncio.run(call_ollama(prompt=question, model=ollama_model, base_url=ollama_url))
            prog.stop()

        from rich.panel import Panel
        console.print(Panel(answer or "[dim](no response)[/dim]",
                            title="[bold cyan]Ollama Response[/bold cyan]", border_style="cyan"))
    except Exception as exc:
        console.print(f"[red]✘ Ollama error: {exc}[/red]")
        raise typer.Exit(1)


@app.command()
def verify(
    task: str = typer.Argument(..., help="Task name to verify"),
    project: Optional[str] = typer.Option(None, "--project", "-p"),
    script: Optional[str] = typer.Option(None, "--script", "-s", help="Script file to check"),
    check_ollama: bool = typer.Option(False, "--ollama", help="Also verify Ollama is reachable"),
    url: Optional[str] = _url_option,
) -> None:
    """Run workflow verification checks before executing a task."""
    from agents.workflow_verifier import verify_task, verify_project_from_config

    console.print(f"[cyan]Verifying task:[/cyan] [bold]{task}[/bold]\n")

    if project and not script:
        report = verify_project_from_config(
            project_name=project,
            base_url=url or _BASE_URL_DEFAULT,
        )
    else:
        report = verify_task(
            task_name=task,
            project_path=project,
            script=script,
            check_ollama=check_ollama,
            base_url=url or _BASE_URL_DEFAULT,
        )

    ui.print_verification(report)
    if not report.passed:
        raise typer.Exit(1)


@app.command()
def dashboard(
    task: str = typer.Argument(..., help="Task name to report"),
    task_status: str = typer.Argument("running", help="Status: queued|running|completed|failed"),
    agent_name: str = typer.Option("AgentAyazDaddy", "--agent", help="Agent name"),
    url: Optional[str] = _url_option,
    key: Optional[str] = _key_option,
) -> None:
    """Post task status to the dashboard API."""
    client = _client(url or _BASE_URL_DEFAULT, key or _API_KEY_DEFAULT)

    payload = {"agent": agent_name, "task": task, "status": task_status}
    result = client._post("/api/agent/task-status", payload)

    if result.get("error"):
        console.print(f"[red]✘ Dashboard update failed: {result.get('detail')}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✔ Dashboard updated:[/green] {task} → {task_status}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    app()


if __name__ == "__main__":
    main()
