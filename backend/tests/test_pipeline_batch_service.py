"""Unit tests for Phase 6.2 — run_pipeline_for_demo_leads."""

from __future__ import annotations

import os
from typing import Iterator

import pytest

from app.schemas.agents import (
    EmailDrafterAgentOutput,
    LeadPipelineContractOutput,
    PipelineRunContractOutput,
    PipelineRunSummary,
    QAEvaluatorAgentOutput,
    QualifierAgentOutput,
    ResearchAgentOutput,
    StrategistAgentOutput,
)
from app.services.demo_data_loader import load_demo_leads
from app.services.pipeline_service import (
    run_pipeline_for_demo_leads,
    run_pipeline_for_lead,
)


@pytest.fixture(scope="module")
def batch_output() -> PipelineRunContractOutput:
    """Run the batch pipeline once per module — it processes up to
    10 leads × 5 agents, so caching saves real time without masking
    determinism (the module is reloaded between test runs)."""

    return run_pipeline_for_demo_leads()


@pytest.fixture()
def _drop_groq_key() -> Iterator[None]:
    saved = os.environ.pop("GROQ_API_KEY", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["GROQ_API_KEY"] = saved


def test_batch_pipeline_returns_pipeline_run_contract_output(
    batch_output: PipelineRunContractOutput,
) -> None:
    assert isinstance(batch_output, PipelineRunContractOutput)
    assert isinstance(batch_output.summary, PipelineRunSummary)
    assert batch_output.run_mode == "deterministic_pipeline"
    assert batch_output.model_mode == "mock"


def test_batch_pipeline_has_shared_run_id_prefix(
    batch_output: PipelineRunContractOutput,
) -> None:
    assert batch_output.run_id.startswith("pipeline_batch_")
    # uuid4().hex[:8] suffix.
    suffix = batch_output.run_id[len("pipeline_batch_") :]
    assert len(suffix) == 8
    assert all(c in "0123456789abcdef" for c in suffix)
    # Every per-lead container shares the batch-level run_id.
    assert batch_output.results, "batch must produce at least one result"
    for result in batch_output.results:
        assert result.run_id == batch_output.run_id


def test_batch_pipeline_processes_up_to_ten_leads(
    batch_output: PipelineRunContractOutput,
) -> None:
    total_leads = len(load_demo_leads())
    expected_processed = min(total_leads, 10)
    assert batch_output.lead_count == expected_processed
    assert len(batch_output.results) == expected_processed
    assert batch_output.summary.total_leads == total_leads
    assert batch_output.summary.processed_leads == expected_processed


def test_batch_pipeline_results_have_all_five_agent_slots(
    batch_output: PipelineRunContractOutput,
) -> None:
    assert batch_output.results, "batch must produce at least one result"
    for result in batch_output.results:
        assert isinstance(result, LeadPipelineContractOutput)
        assert isinstance(result.research, ResearchAgentOutput)
        assert isinstance(result.qualification, QualifierAgentOutput)
        assert isinstance(result.strategy, StrategistAgentOutput)
        assert isinstance(result.email, EmailDrafterAgentOutput)
        assert isinstance(result.qa, QAEvaluatorAgentOutput)
        assert result.intake is None
        assert len(result.trace) == 5


def test_batch_pipeline_summary_counts_match_results(
    batch_output: PipelineRunContractOutput,
) -> None:
    high = sum(
        1
        for r in batch_output.results
        if r.qualification is not None
        and r.qualification.priority.value == "High"
    )
    medium = sum(
        1
        for r in batch_output.results
        if r.qualification is not None
        and r.qualification.priority.value == "Medium"
    )
    low = sum(
        1
        for r in batch_output.results
        if r.qualification is not None
        and r.qualification.priority.value == "Low"
    )

    summary = batch_output.summary
    assert summary.high_priority_leads == high
    assert summary.medium_priority_leads == medium
    assert summary.low_priority_leads == low
    # All priorities sum to processed_leads when every result has a
    # qualifier output (the deterministic baseline always does).
    assert (
        summary.high_priority_leads
        + summary.medium_priority_leads
        + summary.low_priority_leads
        == summary.processed_leads
    )


def test_batch_pipeline_average_qa_score_is_float_or_none(
    batch_output: PipelineRunContractOutput,
) -> None:
    average = batch_output.summary.average_qa_score
    if average is None:
        assert batch_output.summary.processed_leads == 0
        return
    assert isinstance(average, float)
    assert 0.0 <= average <= 100.0
    # Average matches the mean of qa_score across results that
    # produced a QA output.
    scores = [
        r.qa.qa_score for r in batch_output.results if r.qa is not None
    ]
    expected = sum(scores) / len(scores)
    assert average == pytest.approx(expected)


def test_batch_pipeline_no_groq_key_required(_drop_groq_key: None) -> None:
    assert "GROQ_API_KEY" not in os.environ
    output = run_pipeline_for_demo_leads()
    assert isinstance(output, PipelineRunContractOutput)
    assert output.lead_count >= 1


def test_single_lead_pipeline_still_works_after_refactor() -> None:
    # Phase 6.1 default behaviour: run_id is auto-generated when not provided.
    auto = run_pipeline_for_lead("lead_001")
    assert auto.lead_id == "lead_001"
    assert auto.run_id.startswith("pipeline_lead_001_")
    assert len(auto.trace) == 5

    # Phase 6.2: when a run_id is provided, the pipeline uses it as-is.
    forced = run_pipeline_for_lead("lead_001", run_id="pipeline_batch_deadbeef")
    assert forced.lead_id == "lead_001"
    assert forced.run_id == "pipeline_batch_deadbeef"
    assert len(forced.trace) == 5


def test_batch_max_leads_clamp() -> None:
    total_leads = len(load_demo_leads())

    # 0 → clamps up to 1.
    one = run_pipeline_for_demo_leads(max_leads=0)
    assert one.lead_count == min(1, total_leads)

    # negative → clamps up to 1.
    neg = run_pipeline_for_demo_leads(max_leads=-5)
    assert neg.lead_count == min(1, total_leads)

    # 1000 → clamps down to 10 (then bounded by available leads).
    big = run_pipeline_for_demo_leads(max_leads=1000)
    assert big.lead_count == min(10, total_leads)

    # An intermediate value passes through unchanged.
    three = run_pipeline_for_demo_leads(max_leads=3)
    assert three.lead_count == min(3, total_leads)
