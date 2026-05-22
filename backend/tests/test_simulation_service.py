"""Unit tests for the Phase 5.1 Pipeline Simulation Layer service.

Test IDs map 1:1 to the Phase 5.1 spec (S-01 .. S-12).
"""

from __future__ import annotations

from app.schemas.simulation import SimulationRunResponse
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
)
from app.services.simulation_service import build_simulation_run


def _by_id(run: SimulationRunResponse, lead_id: str):
    for result in run.results:
        if result.id == lead_id:
            return result
    raise AssertionError(f"lead_id {lead_id!r} not found in simulation results")


def test_s01_build_simulation_run_returns_response_without_error() -> None:
    """S-01: build_simulation_run() returns SimulationRunResponse without error."""

    run = build_simulation_run()
    assert isinstance(run, SimulationRunResponse)


def test_s02_run_mode_is_simulation() -> None:
    """S-02: run_mode == "simulation"."""

    run = build_simulation_run()
    assert run.run_mode == "simulation"


def test_s03_run_id_is_fixed() -> None:
    """S-03: run_id == "simulation_demo_run_001"."""

    run = build_simulation_run()
    assert run.run_id == "simulation_demo_run_001"


def test_s04_model_calls_is_zero() -> None:
    """S-04: model_calls == 0."""

    run = build_simulation_run()
    assert run.model_calls == 0


def test_s05_estimated_cost_is_zero_dollars() -> None:
    """S-05: estimated_cost == "$0.00"."""

    run = build_simulation_run()
    assert run.estimated_cost == "$0.00"


def test_s06_results_length_matches_demo_leads() -> None:
    """S-06: len(results) == len(demo leads)."""

    run = build_simulation_run()
    demo_leads = load_demo_leads()
    assert len(run.results) == len(demo_leads)


def test_s07_research_summary_non_empty_when_research_present() -> None:
    """S-07: every result whose lead has a company_research.json entry has a
    non-empty research_summary (stored on LeadDetail.company_summary)."""

    run = build_simulation_run()
    research_ids = {r.lead_id for r in load_demo_company_research()}

    matched = [r for r in run.results if r.id in research_ids]
    assert matched, "expected at least one lead with a matching research record"

    for result in matched:
        assert result.company_summary.strip(), (
            f"lead {result.id} has matching research but empty company_summary"
        )


def test_s08_lead_010_is_low_or_needs_review_with_risks() -> None:
    """S-08: lead_010 (Orbis Solutions) produces a result with fit_tier in
    ["Low", "Needs Review"] (i.e. Priority.LOW) and at least one entry in
    information_risks."""

    run = build_simulation_run()
    lead_010 = _by_id(run, "lead_010")

    # Per Phase 5.1 schema correction, "Needs Review" maps to Priority.LOW
    # and LeadStatus.NEEDS_EDIT. A "Low" fit_tier also maps to Priority.LOW
    # (with status PENDING_REVIEW). Either is acceptable for this assertion.
    assert lead_010.priority.value == "Low"
    assert lead_010.status.value in {"Needs Edit", "Pending Review"}
    assert len(lead_010.fit_risks) >= 1


def test_s09_every_result_has_exactly_six_trace_steps() -> None:
    """S-09: every result's trace has exactly 6 steps."""

    run = build_simulation_run()
    assert run.results, "simulation produced no results"
    for result in run.results:
        assert len(result.trace) == 6, (
            f"lead {result.id} has {len(result.trace)} trace steps, expected 6"
        )


def test_s10_every_trace_step_has_zero_tokens_and_model_none() -> None:
    """S-10: every trace step has tokens == 0 and model == "none"."""

    run = build_simulation_run()
    for result in run.results:
        for step in result.trace:
            assert step.tokens == 0, (
                f"{result.id}/{step.agent}: tokens={step.tokens}"
            )
            assert step.model == "none", (
                f"{result.id}/{step.agent}: model={step.model!r}"
            )


def test_s11_every_trace_step_is_marked_simulated() -> None:
    """S-11: every trace step has simulated == True (and status "success")."""

    run = build_simulation_run()
    for result in run.results:
        for step in result.trace:
            assert step.simulated is True, (
                f"{result.id}/{step.agent}: simulated={step.simulated}"
            )
            assert step.status.value == "success", (
                f"{result.id}/{step.agent}: status={step.status.value!r}"
            )


def test_s12_lead_010_score_is_lower_than_lead_001_score() -> None:
    """S-12: qualification_score for lead_010 (degraded data) is strictly
    lower than the qualification_score for a lead with full data
    (lead_001 — Veltrix Systems, full ICP match)."""

    run = build_simulation_run()
    lead_001 = _by_id(run, "lead_001")
    lead_010 = _by_id(run, "lead_010")
    assert lead_010.fit_score < lead_001.fit_score, (
        f"expected lead_010 ({lead_010.fit_score}) < "
        f"lead_001 ({lead_001.fit_score})"
    )
