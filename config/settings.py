import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_root: str
    ollama_model: str
    ollama_url: str
    telegram_token: str | None
    api_secret_key: str | None
    api_secret_keys: list[str]
    allowed_telegram_user_id: int
    host: str
    port: int
    cors_origins: list[str]
    command_timeout_seconds: int
    task_timeout_seconds: int
    max_output_chars: int
    strict_command_mode: bool
    allowed_command_prefixes: list[str]
    rate_limit_per_minute: int
    auto_approve_default: bool
    default_execution_delay_seconds: int
    auto_git_commit_on_task: bool


def get_settings() -> Settings:
    cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1")
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
    api_secret_key = os.getenv("API_SECRET_KEY")

    api_secret_keys_raw = os.getenv("API_SECRET_KEYS", "")
    api_secret_keys = [key.strip() for key in api_secret_keys_raw.split(",") if key.strip()]
    if api_secret_key and api_secret_key not in api_secret_keys:
        api_secret_keys.insert(0, api_secret_key)

    allowed_prefixes_raw = os.getenv(
        "ALLOWED_COMMAND_PREFIXES",
        "python,pip,pytest,uv,poetry,npm,pnpm,yarn,node,git,mvn,gradle,dotnet,go,cargo,ruff,black,isort,echo,dir,type,ls",
    )
    allowed_command_prefixes = [prefix.strip().lower() for prefix in allowed_prefixes_raw.split(",") if prefix.strip()]

    return Settings(
        project_root=os.getenv("PROJECT_ROOT", "D:/PERSONAL/LIVE_PROJECTS"),
        ollama_model=os.getenv("OLLAMA_MODEL", "phi3"),
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        telegram_token=os.getenv("TELEGRAM_TOKEN"),
        api_secret_key=api_secret_key,
        api_secret_keys=api_secret_keys,
        allowed_telegram_user_id=int(os.getenv("ALLOWED_TELEGRAM_USER_ID", "0")),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        cors_origins=cors_origins,
        command_timeout_seconds=int(os.getenv("COMMAND_TIMEOUT", "60")),
        task_timeout_seconds=int(os.getenv("TASK_TIMEOUT", "120")),
        max_output_chars=int(os.getenv("MAX_OUTPUT_CHARS", "3000")),
        strict_command_mode=os.getenv("STRICT_COMMAND_MODE", "false").strip().lower() in {"1", "true", "yes", "on"},
        allowed_command_prefixes=allowed_command_prefixes,
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
        auto_approve_default=os.getenv("AUTO_APPROVE", "true").strip().lower() in {"1", "true", "yes", "on"},
        default_execution_delay_seconds=int(os.getenv("DEFAULT_EXECUTION_DELAY_SECONDS", "0")),
        auto_git_commit_on_task=os.getenv("AUTO_GIT_COMMIT", "false").strip().lower() in {"1", "true", "yes", "on"},
    )
