from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_username: str = "admin"
    auth_password: str = "changeme"

    cases_dir: str = "cases"

    encryption_key: str | None = None

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_model: str = "gpt-4o"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cases_path(self) -> Path:
        return Path(self.cases_dir)

@lru_cache
def get_settings() -> Settings:
    return Settings()
