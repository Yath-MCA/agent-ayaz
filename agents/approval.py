"""Approval Workflow — confirmation-based execution state machine.

States: pending → approved | rejected | timed_out

Usage:
    store = ApprovalStore()
    token = store.request(plan, user="api_key_xxxx")
    # ... send Telegram message with /approve <token> or /reject <token>
    result = store.resolve(token, approved=True)
"""

import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from agents.planner import ExecutionPlan


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


@dataclass
class ApprovalRequest:
    token: str
    plan: ExecutionPlan
    user: str
    created_at: float
    timeout_seconds: int
    status: ApprovalStatus = ApprovalStatus.PENDING
    resolved_at: Optional[float] = None

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_seconds

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "task": self.plan.task,
            "type": self.plan.type,
            "command": self.plan.command,
            "task_file": self.plan.task_file,
            "project": self.plan.project,
            "user": self.user,
            "status": self.status.value,
            "created_at": self.created_at,
            "timeout_seconds": self.timeout_seconds,
            "resolved_at": self.resolved_at,
        }


class ApprovalStore:
    """In-memory approval request registry."""

    def __init__(self, default_timeout_seconds: int = 300) -> None:
        self._store: dict[str, ApprovalRequest] = {}
        self.default_timeout_seconds = default_timeout_seconds

    def request(
        self,
        plan: ExecutionPlan,
        user: str,
        timeout_seconds: Optional[int] = None,
    ) -> str:
        token = secrets.token_hex(6)
        self._store[token] = ApprovalRequest(
            token=token,
            plan=plan,
            user=user,
            created_at=time.time(),
            timeout_seconds=timeout_seconds or self.default_timeout_seconds,
        )
        return token

    def get(self, token: str) -> Optional[ApprovalRequest]:
        req = self._store.get(token)
        if req and req.status == ApprovalStatus.PENDING and req.is_expired():
            req.status = ApprovalStatus.TIMED_OUT
            req.resolved_at = time.time()
        return req

    def resolve(self, token: str, *, approved: bool) -> Optional[ApprovalRequest]:
        req = self.get(token)
        if req is None:
            return None
        if req.status != ApprovalStatus.PENDING:
            return req
        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        req.resolved_at = time.time()
        return req

    def pending(self) -> list[ApprovalRequest]:
        return [r for r in self._store.values() if r.status == ApprovalStatus.PENDING and not r.is_expired()]

    def list_all(self) -> list[ApprovalRequest]:
        return list(self._store.values())
