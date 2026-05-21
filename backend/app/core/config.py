"""Application configuration loaded from environment variables.

Active settings groups:

- App identity / runtime: `app_name`, `app_env`, `app_version`, `app_host`,
  `app_port`, `log_level`.
- Persistence: `database_url` (SQLite by default).
- HTTP: `cors_origins`.
- Filesystem anchors (added in Fase 4.2): `repo_root` plus the derived
  `demo_data_dir`, `demo_leads_csv_path`, and `demo_company_research_path`
  properties used by the demo data loader / `/api/demo/*` endpoints.
- Future use: `knowledge_dir` is exposed as a derived path so callers can
  reference it consistently, but it is NOT consumed by any code in Fase 4.2.
  Knowledge-base loading is reserved for a later phase.

Future-phase variables (model providers, cost caps, feature flags, vector
DB, etc.) are intentionally NOT defined here yet to keep the surface area
small and obvious. They will be introduced when the matching feature is
implemented.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    # backend/app/core/config.py -> parents[3] = repo root
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "leadforge-backend"
    app_env: str = "development"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./leadforge.db"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Fase 4.2: filesystem anchors for demo data and knowledge files.
    # Default to the repository root so the backend can be run from any CWD.
    repo_root: Path = Field(default_factory=_default_repo_root)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("repo_root", mode="before")
    @classmethod
    def _coerce_repo_root(cls, value: object) -> object:
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
        return value

    @property
    def demo_data_dir(self) -> Path:
        return self.repo_root / "data" / "demo"

    @property
    def demo_leads_csv_path(self) -> Path:
        return self.demo_data_dir / "leads.csv"

    @property
    def demo_company_research_path(self) -> Path:
        return self.demo_data_dir / "company_research.json"

    @property
    def knowledge_dir(self) -> Path:
        return self.repo_root / "knowledge"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
