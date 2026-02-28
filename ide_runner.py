import shutil
import asyncio
import logging

from main import execute_command, call_ollama

log = logging.getLogger(__name__)

CANDIDATE_RUNNERS = {
    "opencode": "opencode run --prompt \"{prompt}\"",
    "cursor": "cursor-agent \"{prompt}\"",
    "windsurf": "windsurf \"{prompt}\"",
    "antigravity": "antigravity \"{prompt}\"",
}


def is_command_available(command):
    return shutil.which(command) is not None


def quota_error_detected(output: str) -> bool:
    keywords = [
        "quota",
        "rate limit",
        "payment required",
        "exceeded",
        "billing"
    ]
    return any(k in output.lower() for k in keywords)


async def run_smart(prompt: str, project_dir: str):

    for name, template in CANDIDATE_RUNNERS.items():

        executable = template.split()[0]

        if not is_command_available(executable):
            log.info(f"{name} not installed.")
            continue

        log.info(f"Trying {name}...")

        cmd = template.format(prompt=prompt.replace('"', '\\"'))
        output = execute_command(cmd, cwd=project_dir)

        if quota_error_detected(output):
            log.warning(f"{name} quota exceeded.")
            continue

        if output and "error" not in output.lower():
            return name, output

    # Final fallback
    log.info("Falling back to local Ollama")
    result = await call_ollama(prompt)
    return "ollama", result