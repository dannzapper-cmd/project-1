"""Unit tests for Phase 6.1 — pipeline_service.run_pipeline_for_lead."""

from __future__ import annotations

import os
from typing import Iterator

import pytest

from app.schemas.agents import (
    EmailDrafterAgentOutput,
    LeadPipelineContractOutput,
    QAEvaluatorAgentOutput,
    QualifierAgentOutput,
    ResearchAgentOutput,
    StrategistAgentOutput,
)
from app.schemas.run import TraceEntry
from app.services.demo_data_loader import load_demo_leads
from app.services.pipeline_service import run_pipeline_for_lead


# A lead that is guaranteed to exist in the bundled demo dataset.
_DEMO_LEAD_ID = "lead_001"


@pytest.fixture()
def pipeline_output() -> LeadPipelineContractOutput:
    """Run the pipeline once per test (module-scope would mask
    non-determinism, so we stay function-scope on purpose)."""

    return run_pipeline_for_lead(_DEMO_LEAD_ID)


@pytest.fixture()
def _drop_groq_key() -> Iterator[None]:
    """Ensure ``GROQ_API_KEY`` is not visible to the pipeline."""

    saved = os.environ.pop("GROQ_API_KEY", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["GROQ_API_KEY"] = saved


def test_pipeline_returns_lead_pipeline_contract_output(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    assert isinstance(pipeline_output, LeadPipelineContractOutput)


def test_pipeline_all_five_agent_slots_populated(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    assert isinstance(pipeline_output.research, ResearchAgentOutput)
    assert isinstance(pipeline_output.qualification, QualifierAgentOutput)
    assert isinstance(pipeline_output.strategy, StrategistAgentOutput)
    assert isinstance(pipeline_output.email, EmailDrafterAgentOutput)
    assert isinstance(pipeline_output.qa, QAEvaluatorAgentOutput)


def test_pipeline_intake_is_none(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    # Phase 6.1 does not run an Intake Agent (no runtime exists yet).
    assert pipeline_output.intake is None


def test_pipeline_trace_has_five_entries(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    assert len(pipeline_output.trace) == 5
    assert all(isinstance(entry, TraceEntry) for entry in pipeline_output.trace)
    agents = [entry.agent for entry in pipeline_output.trace]
    assert agents == [
        "research_agent",
        "qualifier_agent",
        "strategist_agent",
        "email_drafter_agent",
        "qa_evaluator_agent",
    ]


def test_pipeline_trace_simulated_is_false_if_field_exists(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    # Phase 6.1 prompt requirement: trace entries opt out of the
    # ``simulated`` flag on the orchestration layer even though the
    # underlying agents are still mock-backed.
    for entry in pipeline_output.trace:
        assert hasattr(entry, "simulated")
        assert entry.simulated is False


def test_pipeline_run_id_is_not_empty(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    assert isinstance(pipeline_output.run_id, str)
    assert pipeline_output.run_id.startswith(f"pipeline_{_DEMO_LEAD_ID}_")
    # The Phase 6.1 contract uses uuid4().hex[:8] as the suffix.
    suffix = pipeline_output.run_id.split("_")[-1]
    assert len(suffix) == 8
    assert all(c in "0123456789abcdef" for c in suffix)


def test_pipeline_lead_id_matches(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    assert pipeline_output.lead_id == _DEMO_LEAD_ID
    # Every per-agent output that carries a lead_id should match.
    assert pipeline_output.research.lead_id == _DEMO_LEAD_ID
    assert pipeline_output.qualification.lead_id == _DEMO_LEAD_ID
    assert pipeline_output.strategy.lead_id == _DEMO_LEAD_ID
    assert pipeline_output.email.lead_id == _DEMO_LEAD_ID
    assert pipeline_output.qa.lead_id == _DEMO_LEAD_ID


def test_pipeline_unknown_lead_raises_value_error() -> None:
    # Sanity-check: the canary id is genuinely not in the demo dataset.
    known_ids = {lead.lead_id for lead in load_demo_leads()}
    assert "lead_does_not_exist" not in known_ids

    with pytest.raises(ValueError) as exc_info:
        run_pipeline_for_lead("lead_does_not_exist")
    assert "lead_does_not_exist" in str(exc_info.value)


def test_pipeline_no_groq_key_required(_drop_groq_key: None) -> None:
    # The pipeline must succeed end-to-end without GROQ_API_KEY.
    assert "GROQ_API_KEY" not in os.environ
    output = run_pipeline_for_lead(_DEMO_LEAD_ID)
    assert isinstance(output, LeadPipelineContractOutput)
    assert output.research is not None
    assert output.qa is not None


def test_pipeline_no_email_send_fields(
    pipeline_output: LeadPipelineContractOutput,
) -> None:
    # The EmailDrafter contract intentionally has no delivery fields.
    # We assert the structural absence so a future regression that
    # adds them would be caught here.
    email = pipeline_output.email
    assert email is not None
    email_fields = set(email.model_fields.keys())
    forbidden = {"sent", "delivered", "recipient", "to", "smtp", "send_at"}
    assert email_fields.isdisjoint(forbidden)
    # Round-trip dump should not carry any of those fields either.
    dumped = email.model_dump()
    assert set(dumped.keys()).isdisjoint(forbidden)
