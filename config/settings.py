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
    allowed_telegram_user_id: int
    host: str
    port: int
    cors_origins: list[str]


def get_settings() -> Settings:
    cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1")
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

    return Settings(
        project_root=os.getenv("PROJECT_ROOT", "D:/PERSONAL/LIVE_PROJECTS"),
        ollama_model=os.getenv("OLLAMA_MODEL", "phi3"),
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        telegram_token=os.getenv("TELEGRAM_TOKEN"),
        api_secret_key=os.getenv("API_SECRET_KEY"),
        allowed_telegram_user_id=int(os.getenv("ALLOWED_TELEGRAM_USER_ID", "0")),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        cors_origins=cors_origins,
    )
