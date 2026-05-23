"""Telemetry integration tests for the deterministic pipeline."""

from __future__ import annotations

import pytest

from app.services import pipeline_service
from app.services import telemetry_service

_DEMO_LEAD_ID = "lead_001"
_EXPECTED_AGENTS = [
    "research_agent",
    "qualifier_agent",
    "strategist_agent",
    "email_drafter_agent",
    "qa_evaluator_agent",
]


@pytest.fixture(autouse=True)
def _clear_telemetry() -> None:
    telemetry_service.clear_telemetry()


def test_pipeline_records_telemetry_entries_for_each_agent_step() -> None:
    run_id = "pipeline_test_telemetry_steps"

    pipeline_service.run_pipeline_for_lead(_DEMO_LEAD_ID, run_id=run_id)
    detail = telemetry_service.get_run_detail(run_id)

    assert detail is not None
    assert detail.summary.run_id == run_id
    assert detail.summary.lead_count == 1
    assert detail.summary.agent_step_count == 5
    assert detail.summary.success_count == 5
    assert detail.summary.warning_count == 0
    assert detail.summary.failed_count == 0
    assert detail.summary.model_modes == ["mock"]
    assert [entry.agent_name for entry in detail.entries] == _EXPECTED_AGENTS


def test_pipeline_telemetry_captures_qa_signals_where_available() -> None:
    run_id = "pipeline_test_telemetry_qa"

    output = pipeline_service.run_pipeline_for_lead(_DEMO_LEAD_ID, run_id=run_id)
    detail = telemetry_service.get_run_detail(run_id)

    assert detail is not None
    qa_entry = detail.entries[-1]
    assert qa_entry.agent_name == "qa_evaluator_agent"
    assert qa_entry.qa_score == output.qa.qa_score
    assert qa_entry.hallucination_risk == output.qa.hallucination_risk.value
    assert qa_entry.recommendation == output.qa.recommendation.value
    assert detail.summary.average_qa_score == float(output.qa.qa_score)
    assert (
        detail.summary.highest_hallucination_risk
        == output.qa.hallucination_risk.value
    )


def test_pipeline_output_unchanged_when_telemetry_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = "pipeline_test_telemetry_output_stability"

    with monkeypatch.context() as patch:
        patch.setattr(
            pipeline_service.telemetry_service,
            "record_pipeline_step",
            lambda **_kwargs: None,
        )
        baseline = pipeline_service.run_pipeline_for_lead(
            _DEMO_LEAD_ID, run_id=run_id
        )

    telemetry_service.clear_telemetry()
    observed = pipeline_service.run_pipeline_for_lead(_DEMO_LEAD_ID, run_id=run_id)

    assert observed.model_dump() == baseline.model_dump()
    assert telemetry_service.get_run_detail(run_id) is not None


def test_telemetry_write_failure_does_not_affect_pipeline_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = "pipeline_test_telemetry_write_failure"

    with monkeypatch.context() as patch:
        patch.setattr(
            pipeline_service.telemetry_service,
            "record_pipeline_step",
            lambda **_kwargs: None,
        )
        baseline = pipeline_service.run_pipeline_for_lead(
            _DEMO_LEAD_ID, run_id=run_id
        )

    def raise_on_record(_entry: object) -> None:
        raise RuntimeError("telemetry store unavailable")

    telemetry_service.clear_telemetry()
    monkeypatch.setattr(
        telemetry_service.telemetry_service,
        "record",
        raise_on_record,
    )
    observed = pipeline_service.run_pipeline_for_lead(_DEMO_LEAD_ID, run_id=run_id)

    assert observed.model_dump() == baseline.model_dump()
    assert telemetry_service.get_run_detail(run_id) is None
