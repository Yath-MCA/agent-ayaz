"""Workflow verification layer for AgentAyazDaddy.

Performs pre-run checks before executing any task:
- Project path exists
- Script/task file exists
- Required interpreters available (Python, Node, etc.)
- Key dependencies installed
- Environment ready
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ── Result types ─────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    label: str
    passed: bool
    detail: str = ""
    warning: bool = False  # True = ⚠ instead of ✘


@dataclass
class VerificationReport:
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed or c.warning for c in self.checks)

    @property
    def has_warnings(self) -> bool:
        return any(c.warning and not c.passed for c in self.checks)

    def add(self, label: str, passed: bool, detail: str = "", warning: bool = False) -> None:
        self.checks.append(CheckResult(label=label, passed=passed, detail=detail, warning=warning))

    def print_rich(self) -> None:
        """Render a Rich-formatted report to stdout."""
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box

            console = Console()
            table = Table(title="[bold cyan]Workflow Verification[/bold cyan]", box=box.ROUNDED, show_header=False)
            table.add_column("Icon", width=3)
            table.add_column("Check", style="bold")
            table.add_column("Detail", style="dim")

            for c in self.checks:
                if c.passed:
                    icon = "[green]✔[/green]"
                elif c.warning:
                    icon = "[yellow]⚠[/yellow]"
                else:
                    icon = "[red]✘[/red]"
                table.add_row(icon, c.label, c.detail)

            console.print(table)

            if self.passed:
                console.print("[green bold]✔ All checks passed — ready to execute.[/green bold]")
            else:
                console.print("[red bold]✘ Some checks failed — execution blocked.[/red bold]")

        except ImportError:
            # Fallback to plain text
            print("\n── Workflow Verification ──")
            for c in self.checks:
                if c.passed:
                    symbol = "✔"
                elif c.warning:
                    symbol = "⚠"
                else:
                    symbol = "✘"
                suffix = f"  ({c.detail})" if c.detail else ""
                print(f"  {symbol} {c.label}{suffix}")
            print()


# ── Individual checks ─────────────────────────────────────────────────────────

def _check_project_path(project_path: Optional[str]) -> CheckResult:
    if not project_path:
        return CheckResult("Project path configured", False, "No path provided")
    p = Path(project_path)
    if p.exists():
        return CheckResult("Project path found", True, str(p))
    return CheckResult("Project path found", False, f"Missing: {project_path}")


def _check_script_exists(script: Optional[str], project_path: Optional[str]) -> CheckResult:
    if not script:
        return CheckResult("Script file specified", False, "No script configured")
    candidates = [Path(script)]
    if project_path:
        candidates.append(Path(project_path) / script)
    for c in candidates:
        if c.exists():
            return CheckResult("Script file detected", True, str(c))
    return CheckResult("Script file detected", False, f"Not found: {script}")


def _check_interpreter(interpreter: str) -> CheckResult:
    path = shutil.which(interpreter)
    if path:
        try:
            result = subprocess.run(
                [interpreter, "--version"],
                capture_output=True, text=True, timeout=5
            )
            version = (result.stdout or result.stderr).strip().splitlines()[0]
            return CheckResult(f"{interpreter.capitalize()} installed", True, version)
        except Exception:
            return CheckResult(f"{interpreter.capitalize()} installed", True, path)
    return CheckResult(f"{interpreter.capitalize()} installed", False, "Not found in PATH")


def _check_python_package(package: str) -> CheckResult:
    try:
        import importlib
        mod = importlib.import_module(package.replace("-", "_"))
        ver = getattr(mod, "__version__", "?")
        return CheckResult(f"Package: {package}", True, f"v{ver}")
    except ImportError:
        return CheckResult(f"Package: {package}", False, "Not installed", warning=True)


def _check_env_var(var: str, required: bool = True) -> CheckResult:
    val = os.getenv(var)
    if val:
        masked = val[:4] + "…" if len(val) > 4 else "set"
        return CheckResult(f"Env: {var}", True, masked)
    if required:
        return CheckResult(f"Env: {var}", False, "Not set")
    return CheckResult(f"Env: {var}", False, "Not set (optional)", warning=True)


def _check_agent_api(base_url: str = "http://localhost:9234") -> CheckResult:
    try:
        import requests
        r = requests.get(f"{base_url}/health", timeout=5)
        if r.status_code == 200:
            return CheckResult("Agent API reachable", True, base_url)
        return CheckResult("Agent API reachable", False, f"HTTP {r.status_code}", warning=True)
    except Exception as e:
        return CheckResult("Agent API reachable", False, str(e), warning=True)


def _check_ollama(base_url: str = "http://localhost:11434") -> CheckResult:
    try:
        import requests
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        if r.status_code == 200:
            models = r.json().get("models", [])
            names = ", ".join(m.get("name", "") for m in models[:3])
            return CheckResult("Ollama running", True, names or "no models loaded")
        return CheckResult("Ollama running", False, f"HTTP {r.status_code}", warning=True)
    except Exception:
        return CheckResult("Ollama running", False, "Not reachable", warning=True)


# ── Public interface ──────────────────────────────────────────────────────────

def verify_task(
    task_name: str,
    project_path: Optional[str] = None,
    script: Optional[str] = None,
    check_ollama: bool = False,
    extra_packages: Optional[List[str]] = None,
    base_url: str = "http://localhost:9234",
) -> VerificationReport:
    """Run all relevant pre-execution checks and return a VerificationReport."""
    report = VerificationReport()

    report.add("Task specified", bool(task_name), task_name or "none")
    report.checks.append(_check_project_path(project_path))
    if script:
        report.checks.append(_check_script_exists(script, project_path))
    report.checks.append(_check_interpreter("python"))
    report.checks.append(_check_agent_api(base_url))
    if check_ollama:
        report.checks.append(_check_ollama())
    for pkg in (extra_packages or []):
        report.checks.append(_check_python_package(pkg))

    return report


def verify_project_from_config(
    project_name: str,
    projects_config: str = "config/projects.json",
    base_url: str = "http://localhost:9234",
) -> VerificationReport:
    """Load project from projects.json and verify its readiness."""
    report = VerificationReport()

    config_path = Path(projects_config)
    if not config_path.exists():
        report.add("projects.json found", False, str(config_path))
        return report
    report.add("projects.json found", True, str(config_path))

    try:
        with open(config_path) as f:
            data = json.load(f)
        projects = {p["name"]: p for p in data.get("projects", [])}
    except Exception as e:
        report.add("projects.json readable", False, str(e))
        return report
    report.add("projects.json readable", True)

    project = projects.get(project_name)
    if not project:
        report.add("Project in config", False, f"'{project_name}' not found")
        return report
    report.add("Project in config", True, project_name)

    report.checks.append(_check_project_path(project.get("path")))
    report.checks.append(_check_interpreter("python"))
    report.checks.append(_check_agent_api(base_url))

    return report
