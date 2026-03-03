# Phase 2 -- Structured Task DSL System

## Objective

Replace raw shell execution with a YAML-based task definition layer.

## Instructions for Agent Ayazdy

1.  Design a task DSL format (YAML).
2.  Support fields:
    -   task
    -   type
    -   command
    -   timeout
    -   auto_approve
    -   delay_seconds
3.  Modify execution service to accept only DSL-based input.
4.  Validator must enforce allowed command prefixes.
5.  Reject direct shell execution when STRICT_MODE=true.

## Deliverables

-   DSL schema definition
-   Example task YAML files
-   Validation logic design
-   Execution adapter implementation outline
