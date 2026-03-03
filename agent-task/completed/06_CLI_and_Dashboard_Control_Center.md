# Phase 6 -- CLI + Dashboard Control Center (Personal Lab Upgrade)

## Objective

Extend Agent Ayazdy with: 1. Local CLI control interface 2. Web-based
monitoring dashboard 3. Live log streaming 4. OS-level command wrapper
5. Enhanced observability layer

------------------------------------------------------------------------

# Part 1 -- CLI Control Interface

## Goal

Create a terminal-based control client that communicates with existing
REST APIs.

## File Structure

cli/ ├── cli.py ├── client.py └── commands.py

## Requirements

-   Use `typer` or `argparse`
-   Use `requests` for API calls
-   Read API key from environment variable

## Commands To Implement

-   ayazdy health
-   ayazdy projects
-   ayazdy select `<project>`{=html}
-   ayazdy run
    ```{=html}
    <task>
    ```
-   ayazdy history
-   ayazdy approvals
-   ayazdy approve `<token>`{=html}
-   ayazdy reject `<token>`{=html}

## Implementation Rules

1.  CLI must never bypass REST security.
2.  All calls must include X-Api-Key.
3.  Handle 400/401/500 errors cleanly.
4.  Display structured JSON responses in formatted output.
5.  Add optional --json flag for raw output.

------------------------------------------------------------------------

# Part 2 -- Web Dashboard (React Control Center)

## Goal

Build lightweight React dashboard connected to /monitor endpoints.

## Suggested Stack

-   Vite + React
-   Axios
-   Tailwind (optional)
-   WebSocket or SSE for live logs

## Pages / Panels

1.  Health Panel
    -   GET /monitor/health
2.  Project Selector
    -   GET /projects
    -   POST /project/select
3.  Execution History
    -   GET /monitor/history
4.  Approval Queue
    -   GET /monitor/approvals
    -   Approve / Reject buttons
5.  Audit Logs Viewer
    -   GET /monitor/logs

## Dashboard Features

-   Auto-refresh toggle
-   Risk badge display
-   Execution duration display
-   Failure rate indicator
-   Retry suggestion panel

------------------------------------------------------------------------

# Part 3 -- Live Log Streaming

## Backend Extension

Add endpoint:

GET /monitor/stream/logs

Options: - Server-Sent Events (SSE) OR - WebSocket stream

Stream events: - plan_created - validation_passed - validation_failed -
execution_started - execution_completed - execution_failed

Each event payload must include: - timestamp - project - task - status -
duration (if available)

------------------------------------------------------------------------

# Part 4 -- OS-Level Command Wrapper (Windows)

## Goal

Allow system-wide command execution.

Create ayazdy.bat:

@echo off python path`\to`{=tex}`\cli`{=tex}.py %\*

Place in system PATH.

Now usable as:

ayazdy health ayazdy run build

------------------------------------------------------------------------

# Part 5 -- Observability Enhancements

## Add Monitoring Metrics

Enhance memory_service to calculate:

-   total_executions
-   total_failures
-   failure_rate
-   most_used_project
-   most_used_task
-   average_execution_time

Expose via:

GET /monitor/stats

------------------------------------------------------------------------

# Part 6 -- Lab Mode Enhancements

Optional features:

1.  Execution Heatmap Data Endpoint
2.  Timeline endpoint returning chronological activity
3.  Self-diagnostic endpoint: GET /monitor/self-check

Self-check must validate: - Ollama connectivity - Database write/read -
Approval store integrity - DSL validation test

------------------------------------------------------------------------

# Execution Order

1.  Implement CLI client
2.  Add OS wrapper
3.  Build basic dashboard UI
4.  Add live log streaming
5.  Add metrics endpoints
6.  Add visual enhancements

------------------------------------------------------------------------

# Operational Rules

-   No execution without validation.
-   CLI and dashboard must use REST only.
-   Keep separation between planner and executor intact.
-   Maintain audit logging for all new features.

------------------------------------------------------------------------

# Completion Criteria

✔ CLI fully functional\
✔ Dashboard displays live health and logs\
✔ Approval actions from UI\
✔ Live execution stream visible\
✔ Monitoring metrics available\
✔ System stable under repeated test cycles

------------------------------------------------------------------------

End of Phase 6 -- Agent Ayazdy Control Center Upgrade
