# Phase 1 -- Multi-Agent Architecture Upgrade

## Objective

Refactor Agent Ayazdy into a structured multi-agent system.

## Instructions for Agent Ayazdy

1.  Create four logical agents:
    -   Planner Agent (LLM reasoning only, no execution rights)
    -   Validator Agent (policy + command filter enforcement)
    -   Executor Agent (secure execution wrapper)
    -   Auditor Agent (immutable logging + metadata tracking)
2.  Ensure strict separation of responsibility.
3.  Planner must output structured JSON plans.
4.  Validator must approve or reject before execution.
5.  Executor must never accept raw natural language input.
6.  Auditor must log:
    -   user
    -   timestamp
    -   project
    -   command
    -   exit_code
    -   duration

## Deliverables

-   Updated folder structure
-   Agent interface contracts
-   JSON execution plan format
-   Sample flow diagram (text-based)
