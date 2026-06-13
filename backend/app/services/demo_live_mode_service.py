"""Controlled Groq Live Demo Mode service.

Provides status, unlock validation, rate limiting, and a thin wrapper
around the existing single-lead live Groq pipeline. Replay and
deterministic paths are never modified here.
"""

from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.schemas.lead import LeadIn
from app.schemas.live_demo import (
    LiveDemoLeadResult,
    LiveDemoLimits,
    LiveDemoRunMetadata,
    LiveDemoRunResponse,
    LiveDemoStatusResponse,
    LiveDemoUnlockResponse,
)
from app.schemas.live_pipeline import LivePipelineResponse
from app.schemas.model import ModelConfig, ModelProvider
from app.services.live_pipeline_service import (
    LivePipelineDisabledError,
    LivePipelineKeyMissingError,
    LivePipelineLeadNotFoundError,
    run_live_groq_pipeline_for_lead,
)
from app.services.model_service import estimate_model_cost, estimate_token_count

LIVE_SESSION_HEADER = "X-LeadForge-Live-Session"

_SESSION_TTL_SECONDS = 86_400


@dataclass
class _LiveSession:
    token: str
    created_at: float
    runs_today: int = 0
    day_key: str = ""


@dataclass
class _DailyCounters:
    session_runs: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    ip_runs: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    estimated_spend_usd: float = 0.0
    day_key: str = ""


class DemoLiveModeStore:
    """In-process unlock sessions and daily counters.

    Resets on process restart by design — suitable for portfolio demo
    deployments only.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, _LiveSession] = {}
        self._daily = _DailyCounters()
        self._active_runs = 0
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()
            self._daily = _DailyCounters()
            self._active_runs = 0

    def _today_key(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _roll_daily(self) -> None:
        today = self._today_key()
        if self._daily.day_key != today:
            self._daily = _DailyCounters(day_key=today)

    def create_session(self) -> str:
        token = uuid4().hex
        today = self._today_key()
        with self._lock:
            self._roll_daily()
            self._sessions[token] = _LiveSession(
                token=token,
                created_at=time.time(),
                day_key=today,
            )
        return token

    def is_valid_session(self, token: str | None) -> bool:
        if not token:
            return False
        with self._lock:
            session = self._sessions.get(token.strip())
            if session is None:
                return False
            if time.time() - session.created_at > _SESSION_TTL_SECONDS:
                del self._sessions[token.strip()]
                return False
            return True

    def session_runs_today(self, token: str | None) -> int:
        if not token:
            return 0
        with self._lock:
            self._roll_daily()
            session = self._sessions.get(token.strip())
            if session is None:
                return 0
            if session.day_key != self._today_key():
                session.day_key = self._today_key()
                session.runs_today = 0
            return session.runs_today

    def ip_runs_today(self, ip_address: str) -> int:
        with self._lock:
            self._roll_daily()
            return self._daily.ip_runs.get(ip_address, 0)

    def daily_spend_usd(self) -> float:
        with self._lock:
            self._roll_daily()
            return self._daily.estimated_spend_usd

    def record_run(
        self,
        *,
        session_token: str | None,
        ip_address: str,
        estimated_cost_usd: float,
    ) -> None:
        today = self._today_key()
        with self._lock:
            self._roll_daily()
            self._daily.ip_runs[ip_address] = self._daily.ip_runs.get(ip_address, 0) + 1
            self._daily.estimated_spend_usd += max(0.0, estimated_cost_usd)
            if session_token:
                session = self._sessions.get(session_token.strip())
                if session is not None:
                    if session.day_key != today:
                        session.day_key = today
                        session.runs_today = 0
                    session.runs_today += 1

    def try_acquire_concurrency(self, limit: int) -> bool:
        with self._lock:
            if self._active_runs >= limit:
                return False
            self._active_runs += 1
            return True

    def release_concurrency(self) -> None:
        with self._lock:
            self._active_runs = max(0, self._active_runs - 1)


demo_live_mode_store = DemoLiveModeStore()


def _limits_snapshot(settings: Settings) -> LiveDemoLimits:
    return LiveDemoLimits(
        max_live_leads_per_run=settings.max_live_leads_per_run,
        max_live_runs_per_session_per_day=settings.max_live_runs_per_session_per_day,
        max_live_runs_per_ip_per_day=settings.max_live_runs_per_ip_per_day,
        max_live_agent_steps_per_lead=settings.max_live_agent_steps_per_lead,
        max_live_tokens_per_lead=settings.max_live_tokens_per_lead,
        daily_live_demo_budget_usd=settings.daily_live_demo_budget_usd,
        live_model_timeout_seconds=settings.live_model_timeout_seconds,
        live_concurrency_limit=settings.live_concurrency_limit,
    )


def _unavailable_reasons(settings: Settings) -> list[str]:
    reasons: list[str] = []
    if not settings.live_mode_enabled:
        reasons.append("live_mode_disabled")
    if not settings.groq_api_key:
        reasons.append("groq_api_key_missing")
    return reasons


def build_live_demo_status(
    *,
    settings: Settings | None = None,
    session_token: str | None = None,
    ip_address: str | None = None,
) -> LiveDemoStatusResponse:
    settings = settings or get_settings()
    reasons = _unavailable_reasons(settings)
    unlocked = demo_live_mode_store.is_valid_session(session_token)
    available = not reasons and unlocked

    session_remaining: int | None = None
    ip_remaining: int | None = None
    budget_remaining: float | None = None
    if settings.live_mode_enabled and settings.groq_api_key:
        session_runs = demo_live_mode_store.session_runs_today(session_token)
        session_remaining = max(
            0,
            settings.max_live_runs_per_session_per_day - session_runs,
        )
        if ip_address:
            ip_runs = demo_live_mode_store.ip_runs_today(ip_address)
            ip_remaining = max(
                0,
                settings.max_live_runs_per_ip_per_day - ip_runs,
            )
        spent = demo_live_mode_store.daily_spend_usd()
        budget_remaining = max(0.0, settings.daily_live_demo_budget_usd - spent)

    return LiveDemoStatusResponse(
        available=available,
        groq_api_key_configured=bool(settings.groq_api_key),
        live_mode_enabled=settings.live_mode_enabled,
        live_mode_unlocked=unlocked,
        unlock_required=True,
        model_name=settings.groq_default_model if settings.groq_api_key else None,
        limits=_limits_snapshot(settings),
        unavailable_reasons=reasons if not unlocked else reasons,
        session_runs_remaining_today=session_remaining,
        ip_runs_remaining_today=ip_remaining,
        daily_budget_remaining_usd=budget_remaining,
    )


def unlock_live_demo(
    unlock_code: str,
    *,
    settings: Settings | None = None,
) -> LiveDemoUnlockResponse:
    settings = settings or get_settings()
    expected = (settings.live_demo_unlock_code or "").strip()
    provided = (unlock_code or "").strip()

    if not expected:
        return LiveDemoUnlockResponse(
            unlocked=False,
            session_token=None,
            message="Live demo unlock is not configured on this backend.",
        )

    if not hmac.compare_digest(provided, expected):
        return LiveDemoUnlockResponse(
            unlocked=False,
            session_token=None,
            message="Incorrect unlock code. Replay mode remains available.",
        )

    token = demo_live_mode_store.create_session()
    return LiveDemoUnlockResponse(
        unlocked=True,
        session_token=token,
        message=(
            "Groq Live Demo Mode unlocked for this browser session. "
            "Runs are rate-limited and intended for small demos only."
        ),
    )


def _estimate_pipeline_cost(pipeline: LivePipelineResponse) -> tuple[int, float]:
    tokens = 0
    if pipeline.live_result is not None:
        for entry in pipeline.live_result.trace:
            tokens += int(entry.tokens or 0)
    elif pipeline.deterministic_result is not None:
        for entry in pipeline.deterministic_result.trace:
            tokens += int(entry.tokens or 0)
    if tokens <= 0:
        tokens = estimate_token_count("live demo pipeline estimate")
    cost_config = ModelConfig(
        provider=ModelProvider.GROQ,
        model=pipeline.live_model_used,
    )
    cost = estimate_model_cost(
        input_tokens=max(1, tokens // 2),
        output_tokens=max(1, tokens // 2),
        config=cost_config,
    )
    return tokens, float(cost.total_cost)


def _metadata_from_pipeline(
    pipeline: LivePipelineResponse,
    *,
    latency_ms: float,
    unlocked: bool,
    limits_applied: list[str],
) -> LiveDemoRunMetadata:
    tokens, cost_usd = _estimate_pipeline_cost(pipeline)
    if pipeline.live_success:
        run_mode = "groq_live"
    elif pipeline.fallback_used:
        run_mode = "fallback"
    else:
        run_mode = "deterministic"

    warnings: list[str] = []
    if pipeline.fallback_used and pipeline.fallback_reason:
        warnings.append(pipeline.fallback_reason)

    return LiveDemoRunMetadata(
        run_mode=run_mode,
        model_provider="groq" if pipeline.live_model_used else None,
        model_name=pipeline.live_model_used or None,
        estimated_tokens=tokens,
        estimated_cost_usd=round(cost_usd, 6),
        latency_ms=round(latency_ms, 2),
        parse_success=pipeline.live_success,
        fallback_used=pipeline.fallback_used,
        warnings=warnings,
        limits_applied=limits_applied,
        live_mode_unlocked=unlocked,
    )


def _check_rate_limits(
    *,
    settings: Settings,
    session_token: str | None,
    ip_address: str,
    lead_count: int,
) -> tuple[bool, str, list[str]]:
    limits_applied: list[str] = []

    if lead_count > settings.max_live_leads_per_run:
        return (
            False,
            f"Too many leads selected. Max {settings.max_live_leads_per_run} per live run.",
            ["max_live_leads_per_run"],
        )

    session_runs = demo_live_mode_store.session_runs_today(session_token)
    if session_runs + lead_count > settings.max_live_runs_per_session_per_day:
        limits_applied.append("max_live_runs_per_session_per_day")
        return (
            False,
            "Session daily live run limit exceeded. Try again tomorrow or use Replay mode.",
            limits_applied,
        )

    ip_runs = demo_live_mode_store.ip_runs_today(ip_address)
    if ip_runs + lead_count > settings.max_live_runs_per_ip_per_day:
        limits_applied.append("max_live_runs_per_ip_per_day")
        return (
            False,
            "IP daily live run limit exceeded.",
            limits_applied,
        )

    spent = demo_live_mode_store.daily_spend_usd()
    if spent >= settings.daily_live_demo_budget_usd:
        limits_applied.append("daily_live_demo_budget_usd")
        return (
            False,
            "Daily live demo budget exhausted.",
            limits_applied,
        )

    if not demo_live_mode_store.try_acquire_concurrency(
        settings.live_concurrency_limit
    ):
        limits_applied.append("live_concurrency_limit")
        return (
            False,
            "Another live demo run is in progress. Please wait.",
            limits_applied,
        )

    return True, "", limits_applied


def run_live_demo(
    *,
    lead_ids: list[str],
    leads: list[LeadIn] | None,
    session_token: str | None,
    ip_address: str,
    settings: Settings | None = None,
    pipeline_runner: Any | None = None,
) -> LiveDemoRunResponse:
    settings = settings or get_settings()
    unlocked = demo_live_mode_store.is_valid_session(session_token)
    limits = _limits_snapshot(settings)

    if not settings.live_mode_enabled:
        return LiveDemoRunResponse(
            results=[],
            message="Live mode is disabled on this backend.",
        )
    if not settings.groq_api_key:
        return LiveDemoRunResponse(
            results=[],
            message="GROQ_API_KEY is not configured.",
        )
    if not unlocked:
        return LiveDemoRunResponse(
            results=[],
            message="Live demo unlock required. Enter the demo unlock code first.",
        )

    unique_ids = list(dict.fromkeys(lead_ids))
    allowed, limit_message, pre_limits = _check_rate_limits(
        settings=settings,
        session_token=session_token,
        ip_address=ip_address,
        lead_count=len(unique_ids),
    )
    if not allowed:
        demo_live_mode_store.release_concurrency()
        return LiveDemoRunResponse(results=[], message=limit_message)

    if leads is not None:
        known_ids = {lead.lead_id for lead in leads}
        invalid = [lead_id for lead_id in unique_ids if lead_id not in known_ids]
        if invalid:
            demo_live_mode_store.release_concurrency()
            return LiveDemoRunResponse(
                results=[],
                rejected_lead_ids=invalid,
                message="One or more lead IDs are not present in the submitted payload.",
            )

    runner = pipeline_runner or run_live_groq_pipeline_for_lead
    results: list[LiveDemoLeadResult] = []

    try:
        for lead_id in unique_ids:
            start = time.perf_counter()
            try:
                pipeline: LivePipelineResponse = runner(
                    lead_id,
                    require_enable_flag=False,
                )
            except LivePipelineLeadNotFoundError as exc:
                results.append(
                    LiveDemoLeadResult(
                        lead_id=lead_id,
                        pipeline=None,
                        metadata=LiveDemoRunMetadata(
                            run_mode="fallback",
                            fallback_used=True,
                            warnings=[str(exc)],
                            limits_applied=pre_limits,
                            live_mode_unlocked=unlocked,
                        ),
                        error=str(exc),
                    )
                )
                continue
            except (LivePipelineDisabledError, LivePipelineKeyMissingError) as exc:
                results.append(
                    LiveDemoLeadResult(
                        lead_id=lead_id,
                        pipeline=None,
                        metadata=LiveDemoRunMetadata(
                            run_mode="fallback",
                            fallback_used=True,
                            warnings=[str(exc)],
                            limits_applied=pre_limits,
                            live_mode_unlocked=unlocked,
                        ),
                        error=str(exc),
                    )
                )
                continue

            latency_ms = (time.perf_counter() - start) * 1000
            metadata = _metadata_from_pipeline(
                pipeline,
                latency_ms=latency_ms,
                unlocked=unlocked,
                limits_applied=pre_limits + [f"max_live_tokens_per_lead={limits.max_live_tokens_per_lead}"],
            )
            demo_live_mode_store.record_run(
                session_token=session_token,
                ip_address=ip_address,
                estimated_cost_usd=metadata.estimated_cost_usd or 0.0,
            )
            results.append(
                LiveDemoLeadResult(
                    lead_id=lead_id,
                    pipeline=pipeline,
                    metadata=metadata,
                )
            )
    finally:
        demo_live_mode_store.release_concurrency()

    return LiveDemoRunResponse(results=results)


__all__ = [
    "LIVE_SESSION_HEADER",
    "DemoLiveModeStore",
    "build_live_demo_status",
    "demo_live_mode_store",
    "run_live_demo",
    "unlock_live_demo",
]
