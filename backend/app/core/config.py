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
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # Fase 4.2: filesystem anchors for demo data and knowledge files.
    # Default to the repository root so the backend can be run from any CWD.
    repo_root: Path = Field(default_factory=_default_repo_root)

    # Phase 5.5B: optional Groq provider settings. ``groq_api_key`` is the
    # only credential read by the backend; it is OPTIONAL — when missing,
    # the app starts normally and ``GroqModelService`` simply cannot be
    # instantiated (a 503 is surfaced by the ``/groq-check`` route).
    # ``llama-3.1-8b-instant`` is the Phase 5.5B default model; do NOT
    # default to ``llama-3.3-70b-versatile`` in this phase.
    groq_api_key: str | None = None
    groq_default_model: str = "llama-3.1-8b-instant"
    groq_timeout_seconds: int = 30

    # Block 8.3: live model pipeline opt-in. ``False`` by default; the
    # POST /api/demo/pipeline/live-groq/{lead_id} endpoint refuses to
    # call Groq unless this flag is explicitly enabled AND a
    # ``GROQ_API_KEY`` is present. There is no other entry point for
    # live model pipeline behaviour in this phase.
    enable_live_model_pipeline: bool = False

    # Block 10E — Live Web Research MVP (Exa).
    #
    # All four settings are intentionally inert when ``enable_live_research``
    # is False (the default). The Exa API key is backend-only — it must
    # never be referenced from any frontend / Next.js code. The daily
    # limit is enforced via an in-process counter (see
    # ``app.services.live_research_service``) and resets on backend
    # restart by design (no Redis, DB, or file persistence).
    enable_live_research: bool = False
    exa_api_key: str | None = None
    live_research_max_results: int = Field(default=3, ge=1, le=10)
    live_research_timeout_seconds: float = Field(default=8.0, gt=0.0, le=30.0)
    live_research_daily_limit: int = Field(default=20, ge=1, le=10_000)

    # Block 10F-A — intake file extraction safety limit.
    # Uploads are processed from FastAPI UploadFile in memory only and are
    # rejected after one byte beyond this cap is read.
    intake_max_upload_mb: int = Field(default=2, ge=1, le=10)

    # Block 10G — Contextual LLM Lead Assistant.
    #
    # OFF by default. When enabled, the assistant calls the existing
    # backend Groq provider with grounded lead context only. The Groq
    # model and API key are reused from the ``GROQ_*`` settings above —
    # there is intentionally no parallel ``LLM_ASSISTANT_*`` API-key
    # variable. ``llm_assistant_model`` is the pinned Groq model name;
    # leave it equal to ``groq_default_model`` to reuse the live pipeline
    # model. The daily/per-IP/length/timeout caps are enforced by
    # in-process counters in ``app.services.assistant_service`` — no
    # Redis, no DB.
    enable_llm_assistant: bool = False
    llm_assistant_provider: Literal["groq"] = "groq"
    llm_assistant_model: str = "llama-3.1-8b-instant"
    llm_assistant_max_question_chars: int = Field(default=300, ge=20, le=2_000)
    llm_assistant_timeout_seconds: float = Field(default=12.0, gt=0.0, le=60.0)
    llm_assistant_daily_limit: int = Field(default=30, ge=1, le=10_000)
    llm_assistant_per_ip_limit: int = Field(default=5, ge=1, le=100)
    llm_assistant_per_ip_window_seconds: int = Field(
        default=600, ge=10, le=86_400
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [
                item.strip().rstrip("/")
                for item in value
                if isinstance(item, str) and item.strip()
            ]
        return value

    @model_validator(mode="after")
    def _validate_public_cors(self) -> "Settings":
        if self.app_env.strip().lower() in {"production", "prod"}:
            if "*" in self.cors_origins:
                raise ValueError(
                    "CORS_ORIGINS must list explicit origins in production; "
                    "wildcard '*' is not allowed."
                )
        return self

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
