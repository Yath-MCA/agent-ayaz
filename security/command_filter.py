from typing import Iterable


FORBIDDEN_COMMANDS = [
    "format",
    "shutdown",
    "restart",
    "rm ",
    "del ",
    "rd ",
]

FORBIDDEN_PATTERNS = ["&&", "||", "|", ";", "`", "$(", ">", "<"]

DEFAULT_ALLOWED_COMMAND_PREFIXES = {
    "python",
    "pip",
    "pytest",
    "uv",
    "poetry",
    "npm",
    "pnpm",
    "yarn",
    "node",
    "git",
    "mvn",
    "gradle",
    "dotnet",
    "go",
    "cargo",
    "ruff",
    "black",
    "isort",
    "echo",
    "dir",
    "type",
    "ls",
}


def validate_command_policy(
    cmd: str,
    *,
    strict_mode: bool = False,
    allowed_prefixes: Iterable[str] | None = None,
) -> str | None:
    cmd_clean = cmd.strip()
    if not cmd_clean:
        return "❌ Empty command is not allowed."

    cmd_lower = cmd_clean.lower()

    if any(bad in cmd_lower for bad in FORBIDDEN_COMMANDS):
        return "❌ Forbidden command detected."

    if any(pattern in cmd_clean for pattern in FORBIDDEN_PATTERNS):
        return "❌ Chained or redirected commands are not allowed."

    first_token = cmd_clean.split()[0].lower()

    if strict_mode:
        allow_set = {prefix.lower() for prefix in (allowed_prefixes or []) if prefix}
    else:
        allow_set = DEFAULT_ALLOWED_COMMAND_PREFIXES

    if first_token not in allow_set:
        return f"❌ Command prefix '{first_token}' is not allowed."

    return None
