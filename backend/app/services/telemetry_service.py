"""In-memory telemetry store for deterministic pipeline runs.

Block 8.2 keeps telemetry lightweight and demo-safe: records are summary-level
only, process-local, and best-effort. No prompts, raw inputs, generated email
bodies, secrets, or provider raw responses are stored here.
"""

from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Any

from app.schemas.agents import AgentContractResult
from app.schemas.telemetry import (
    RunTelemetryDetail,
    RunTelemetryEntry,
    RunTelemetrySummary,
)

_DEFAULT_RECENT_LIMIT = 25
_RISK_RANK: dict[str, int] = {"Low": 1, "Medium": 2, "High": 3}


def _parse_latency_ms(latency: str | None) -> int | None:
    if not latency:
        return None
    value = latency.strip().lower()
    try:
        if value.endswith("ms"):
            return max(0, int(round(float(value[:-2]))))
        if value.endswith("s"):
            return max(0, int(round(float(value[:-1]) * 1000)))
    except ValueError:
        return None
    return None


def _parse_cost_usd(cost: str | None) -> float | None:
    if not cost:
        return None
    normalized = cost.strip().replace("$", "").replace(",", "")
    try:
        return max(0.0, float(normalized))
    except ValueError:
        return None


def _result_from_output(agent_output: Any) -> AgentContractResult:
    result = getattr(agent_output, "result", None)
    if not isinstance(result, AgentContractResult):
        raise TypeError("agent output does not expose AgentContractResult")
    return result


def _is_fallback(result: AgentContractResult) -> bool:
    prompt_version = result.metadata.prompt_version or ""
    return "fallback" in prompt_version.lower()


def build_pipeline_step_entry(
    *,
    run_id: str,
    lead_id: str | None,
    agent_name: str,
    agent_output: Any,
    run_mode: str = "deterministic_pipeline",
    model_mode: str = "mock",
) -> RunTelemetryEntry:
    """Build a safe telemetry entry from an already-returned agent output."""

    result = _result_from_output(agent_output)
    metadata = result.metadata
    fallback_used = _is_fallback(result)
    status = "failed"
    if result.success:
        status = "warning" if fallback_used else "success"
    error_category = result.error.code if result.error is not None else None
    total_tokens = metadata.tokens

    return RunTelemetryEntry(
        run_id=run_id,
        lead_id=lead_id,
        agent_name=agent_name,
        status=status,
        run_mode=run_mode,
        model_mode=model_mode,
        model_used=metadata.model or None,
        prompt_version=metadata.prompt_version or None,
        latency_ms=_parse_latency_ms(metadata.latency),
        total_tokens_estimate=total_tokens,
        estimated_cost_usd=_parse_cost_usd(metadata.cost),
        parse_success=result.success and not fallback_used,
        fallback_used=fallback_used,
        qa_score=getattr(agent_output, "qa_score", None),
        hallucination_risk=getattr(
            getattr(agent_output, "hallucination_risk", None), "value", None
        ),
        recommendation=getattr(
            getattr(agent_output, "recommendation", None), "value", None
        ),
        warning_count=1 if fallback_used else 0,
        error_category=error_category,
    )


class InMemoryTelemetryService:
    """Small process-local telemetry store for demo and test runs."""

    def __init__(self) -> None:
        self._entries: list[RunTelemetryEntry] = []
        self._lock = Lock()

    def record(self, entry: RunTelemetryEntry) -> None:
        with self._lock:
            self._entries.append(entry.model_copy(deep=True))

    def recent_run_summaries(
        self, limit: int = _DEFAULT_RECENT_LIMIT
    ) -> list[RunTelemetrySummary]:
        with self._lock:
            entries = [entry.model_copy(deep=True) for entry in self._entries]
        summaries = _summaries_from_entries(entries)
        return summaries[: max(0, limit)]

    def get_run_detail(self, run_id: str) -> RunTelemetryDetail | None:
        entries = self.get_entries_for_run(run_id)
        if not entries:
            return None
        summary = _summary_for_run(run_id, entries)
        return RunTelemetryDetail(run_id=run_id, summary=summary, entries=entries)

    def get_entries_for_run(self, run_id: str) -> list[RunTelemetryEntry]:
        with self._lock:
            return [
                entry.model_copy(deep=True)
                for entry in self._entries
                if entry.run_id == run_id
            ]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


def _summaries_from_entries(
    entries: list[RunTelemetryEntry],
) -> list[RunTelemetrySummary]:
    grouped: dict[str, list[RunTelemetryEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.run_id].append(entry)
    summaries = [
        _summary_for_run(run_id, run_entries)
        for run_id, run_entries in grouped.items()
    ]
    return sorted(summaries, key=lambda summary: summary.created_at, reverse=True)


def _summary_for_run(
    run_id: str, entries: list[RunTelemetryEntry]
) -> RunTelemetrySummary:
    lead_ids = {entry.lead_id for entry in entries if entry.lead_id is not None}
    latency_values = [
        entry.latency_ms for entry in entries if entry.latency_ms is not None
    ]
    qa_scores = [entry.qa_score for entry in entries if entry.qa_score is not None]
    risks = [
        entry.hallucination_risk
        for entry in entries
        if entry.hallucination_risk is not None
    ]
    highest_risk = max(risks, key=lambda risk: _RISK_RANK.get(risk, 0), default=None)

    return RunTelemetrySummary(
        run_id=run_id,
        lead_count=len(lead_ids),
        agent_step_count=len(entries),
        success_count=sum(1 for entry in entries if entry.status == "success"),
        warning_count=sum(1 for entry in entries if entry.status == "warning"),
        failed_count=sum(1 for entry in entries if entry.status == "failed"),
        total_latency_ms=sum(latency_values) if latency_values else None,
        estimated_total_cost_usd=sum(
            entry.estimated_cost_usd or 0.0 for entry in entries
        ),
        average_qa_score=sum(qa_scores) / len(qa_scores) if qa_scores else None,
        highest_hallucination_risk=highest_risk,
        model_modes=sorted({entry.model_mode for entry in entries}),
        run_mode=entries[0].run_mode,
        created_at=min(entry.created_at for entry in entries),
    )


telemetry_service = InMemoryTelemetryService()


def record_pipeline_step(
    *,
    run_id: str,
    lead_id: str | None,
    agent_name: str,
    agent_output: Any,
) -> None:
    """Best-effort telemetry hook for pipeline orchestration boundaries."""

    try:
        entry = build_pipeline_step_entry(
            run_id=run_id,
            lead_id=lead_id,
            agent_name=agent_name,
            agent_output=agent_output,
        )
    except Exception:
        return

    try:
        telemetry_service.record(entry)
    except Exception:
        pass  # telemetry failure must never break the pipeline


def clear_telemetry() -> None:
    telemetry_service.clear()


def recent_run_summaries(limit: int = _DEFAULT_RECENT_LIMIT) -> list[RunTelemetrySummary]:
    return telemetry_service.recent_run_summaries(limit=limit)


def get_run_detail(run_id: str) -> RunTelemetryDetail | None:
    return telemetry_service.get_run_detail(run_id)
