"""Planner Agent — LLM reasoning only, no execution rights.

Converts a natural-language prompt into a structured JSON execution plan
that the Validator Agent can inspect before handing off to the Executor.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExecutionPlan:
    task: str
    type: str                    # "command" | "task_file" | "chat"
    command: Optional[str]       # only for type=command
    task_file: Optional[str]     # only for type=task_file
    project: Optional[str]
    auto_approve: bool
    delay_seconds: int
    reasoning: str
    raw_reply: str

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "type": self.type,
            "command": self.command,
            "task_file": self.task_file,
            "project": self.project,
            "auto_approve": self.auto_approve,
            "delay_seconds": self.delay_seconds,
            "reasoning": self.reasoning,
        }


_PLAN_PROMPT_TEMPLATE = """\
You are a DevOps planning assistant. Given the user request below, respond ONLY with a valid JSON object with these fields:
- task (string): short task name
- type (string): one of "command", "task_file", "chat"
- command (string or null): shell command to run if type=command
- task_file (string or null): task file name if type=task_file
- project (string or null): project name if applicable
- auto_approve (bool): whether this is safe to auto-approve
- delay_seconds (int): recommended delay before execution
- reasoning (string): brief explanation of the plan

User request: {prompt}
"""


def _extract_json(text: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def plan(prompt: str, ollama_call) -> ExecutionPlan:
    """Call the LLM and parse a structured execution plan."""
    plan_prompt = _PLAN_PROMPT_TEMPLATE.format(prompt=prompt)
    raw_reply = await ollama_call(plan_prompt)

    data = _extract_json(raw_reply) or {}

    return ExecutionPlan(
        task=str(data.get("task", prompt[:60])),
        type=str(data.get("type", "chat")),
        command=data.get("command") or None,
        task_file=data.get("task_file") or None,
        project=data.get("project") or None,
        auto_approve=bool(data.get("auto_approve", False)),
        delay_seconds=int(data.get("delay_seconds", 0)),
        reasoning=str(data.get("reasoning", "")),
        raw_reply=raw_reply,
    )
