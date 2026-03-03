"""RBAC — Role-Based Access Control for API keys (Phase 14).

Roles:
  admin   — full access (all endpoints)
  operator— project execution + monitoring, no key management
  viewer  — read-only (GET endpoints only)

Configure via environment:
  RBAC_ROLES=key1:admin,key2:operator,key3:viewer
  (falls back to admin for all keys if not set)
"""

import os
from enum import Enum
from typing import Optional


class Role(str, Enum):
    ADMIN    = "admin"
    OPERATOR = "operator"
    VIEWER   = "viewer"


# Endpoint permission matrix
_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN:    {"*"},   # all
    Role.OPERATOR: {
        "/run-task", "/run-project", "/project/select", "/project/run-task",
        "/project/run-custom", "/project/run-all-tasks",
        "/queue/run", "/queue/promote-later",
        "/monitor/approve", "/monitor/reject",
        "/monitor/health", "/monitor/logs", "/monitor/history",
        "/monitor/approvals", "/monitor/stats", "/monitor/timeline",
        "/monitor/self-check",
    },
    Role.VIEWER: {
        "/status", "/health", "/projects", "/project/current",
        "/project/tasks", "/queue/status",
        "/monitor/health", "/monitor/logs", "/monitor/history",
        "/monitor/approvals", "/monitor/stats", "/monitor/timeline",
    },
}


def _load_role_map() -> dict[str, Role]:
    raw = os.getenv("RBAC_ROLES", "")
    role_map: dict[str, Role] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        key, role_str = pair.split(":", 1)
        key, role_str = key.strip(), role_str.strip().lower()
        try:
            role_map[key] = Role(role_str)
        except ValueError:
            pass
    return role_map


_ROLE_MAP = _load_role_map()


def get_role(api_key: str) -> Role:
    return _ROLE_MAP.get(api_key, Role.ADMIN)  # default admin if RBAC_ROLES not configured


def is_permitted(api_key: str, endpoint: str) -> bool:
    role = get_role(api_key)
    perms = _PERMISSIONS.get(role, set())
    if "*" in perms:
        return True
    # Check exact or prefix match
    return any(endpoint.startswith(p) for p in perms)


def require_role(api_key: str, endpoint: str) -> Optional[str]:
    """Returns an error string if access is denied, None if permitted."""
    if not is_permitted(api_key, endpoint):
        role = get_role(api_key)
        return f"Role '{role.value}' is not permitted to access '{endpoint}'"
    return None
