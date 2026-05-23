"""Unit tests for the lightweight telemetry service."""

from __future__ import annotations

from app.schemas.telemetry import RunTelemetryEntry
from app.services.telemetry_service import InMemoryTelemetryService


def _entry(
    *,
    run_id: str = "run_001",
    lead_id: str = "lead_001",
    agent_name: str = "research_agent",
    status: str = "success",
    qa_score: int | None = None,
    hallucination_risk: str | None = None,
    recommendation: str | None = None,
) -> RunTelemetryEntry:
    return RunTelemetryEntry(
        run_id=run_id,
        lead_id=lead_id,
        agent_name=agent_name,
        status=status,
        run_mode="deterministic_pipeline",
        model_mode="mock",
        model_used="none",
        prompt_version="test_v1",
        latency_ms=0,
        total_tokens_estimate=0,
        estimated_cost_usd=0.0,
        parse_success=True,
        fallback_used=False,
        qa_score=qa_score,
        hallucination_risk=hallucination_risk,
        recommendation=recommendation,
    )


def test_telemetry_service_handles_empty_state() -> None:
    service = InMemoryTelemetryService()

    assert service.recent_run_summaries() == []
    assert service.get_entries_for_run("missing") == []
    assert service.get_run_detail("missing") is None


def test_telemetry_service_records_entries_and_returns_run_detail() -> None:
    service = InMemoryTelemetryService()
    service.record(_entry(agent_name="research_agent"))
    service.record(
        _entry(
            agent_name="qa_evaluator_agent",
            qa_score=92,
            hallucination_risk="Low",
            recommendation="Recommended for approval",
        )
    )

    entries = service.get_entries_for_run("run_001")
    assert [entry.agent_name for entry in entries] == [
        "research_agent",
        "qa_evaluator_agent",
    ]

    detail = service.get_run_detail("run_001")
    assert detail is not None
    assert detail.summary.run_id == "run_001"
    assert detail.summary.lead_count == 1
    assert detail.summary.agent_step_count == 2
    assert detail.summary.success_count == 2
    assert detail.summary.average_qa_score == 92.0
    assert detail.summary.highest_hallucination_risk == "Low"


def test_telemetry_service_returns_recent_run_summaries() -> None:
    service = InMemoryTelemetryService()
    service.record(_entry(run_id="run_001", lead_id="lead_001"))
    service.record(_entry(run_id="run_002", lead_id="lead_002"))

    summaries = service.recent_run_summaries(limit=10)

    assert {summary.run_id for summary in summaries} == {"run_001", "run_002"}
    assert all(summary.agent_step_count == 1 for summary in summaries)
    assert all(summary.estimated_total_cost_usd == 0.0 for summary in summaries)


def test_telemetry_entries_do_not_expose_prompt_or_full_input_fields() -> None:
    entry = _entry()
    dumped = entry.model_dump()

    forbidden = {
        "prompt",
        "prompt_body",
        "raw_input",
        "input",
        "email_body",
        "generated_email_body",
        "api_key",
        "secret",
    }
    assert set(dumped.keys()).isdisjoint(forbidden)
