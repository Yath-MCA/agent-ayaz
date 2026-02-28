import subprocess
from typing import Optional

from security.command_filter import validate_command_policy


def execute_command(cmd: str, cwd: Optional[str] = None) -> str:
    policy_error = validate_command_policy(cmd)
    if policy_error:
        return policy_error

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        output = result.stdout or result.stderr or "(no output)"
        return output[:3000]
    except Exception as error:
        return f"Execution error: {error}"
