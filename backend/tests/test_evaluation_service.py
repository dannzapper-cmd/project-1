"""Unit tests for the Phase 5.3 trace & evaluation service.

Test IDs map 1:1 to the Phase 5.3 spec (S-01 .. S-14).
"""

from __future__ import annotations

import pytest

from app.schemas.common import Priority, RunMode
from app.schemas.evaluation import (
    LeadEvaluationReport,
    LeadTraceReport,
    RunEvaluationSummary,
    RunTraceReport,
)
from app.services.evaluation_service import (
    build_lead_evaluation_report,
    build_lead_trace_report,
    build_run_evaluation_summary,
    build_run_trace_report,
)
from app.services.simulation_service import build_simulation_run


# --------------------------------------------------------------------------- #
# Trace report                                                                #
# --------------------------------------------------------------------------- #


def test_s01_build_run_trace_report_returns_response_without_error() -> None:
    """S-01: build_run_trace_report() returns RunTraceReport."""

    report = build_run_trace_report()
    assert isinstance(report, RunTraceReport)


def test_s02_run_trace_report_mode_is_simulation() -> None:
    """S-02: run trace report run_mode == RunMode.SIMULATION."""

    report = build_run_trace_report()
    assert report.run_mode == RunMode.SIMULATION
    assert report.run_mode.value == "simulation"


def test_s03_run_trace_total_leads_matches_simulation_results() -> None:
    """S-03: run trace report total_leads matches simulation results length."""

    report = build_run_trace_report()
    simulation = build_simulation_run()
    assert report.total_leads == len(simulation.results)
    assert len(report.leads) == len(simulation.results)


def test_s04_every_lead_trace_has_exactly_six_steps() -> None:
    """S-04: every lead trace has exactly 6 steps."""

    report = build_run_trace_report()
    assert report.leads, "trace report has no leads"
    for lead in report.leads:
        assert len(lead.trace) == 6, (
            f"lead {lead.lead_id} has {len(lead.trace)} steps, expected 6"
        )
        assert lead.total_steps == 6


def test_s05_every_trace_step_is_simulation_shaped() -> None:
    """S-05: every trace step has model == "none", simulated == True, tokens == 0."""

    report = build_run_trace_report()
    for lead in report.leads:
        for step in lead.trace:
            assert step.model == "none", (
                f"{lead.lead_id}/{step.agent}: model={step.model!r}"
            )
            assert step.simulated is True, (
                f"{lead.lead_id}/{step.agent}: simulated={step.simulated}"
            )
            assert step.tokens == 0, (
                f"{lead.lead_id}/{step.agent}: tokens={step.tokens}"
            )


def test_s06_build_lead_trace_report_returns_matching_lead() -> None:
    """S-06: build_lead_trace_report("lead_001") returns lead_001."""

    report = build_lead_trace_report("lead_001")
    assert isinstance(report, LeadTraceReport)
    assert report.lead_id == "lead_001"
    assert report.run_mode == RunMode.SIMULATION
    assert len(report.trace) == 6


def test_s07_build_lead_trace_report_raises_value_error_for_missing_lead() -> None:
    """S-07: build_lead_trace_report("missing_lead") raises ValueError."""

    with pytest.raises(ValueError):
        build_lead_trace_report("missing_lead")


# --------------------------------------------------------------------------- #
# Evaluation report                                                           #
# --------------------------------------------------------------------------- #


def test_s08_build_run_evaluation_summary_returns_response_without_error() -> None:
    """S-08: build_run_evaluation_summary() returns RunEvaluationSummary."""

    summary = build_run_evaluation_summary()
    assert isinstance(summary, RunEvaluationSummary)


def test_s09_avg_scores_within_zero_to_one_hundred() -> None:
    """S-09: avg_fit_score and avg_qa_score are within 0..100."""

    summary = build_run_evaluation_summary()
    assert 0.0 <= summary.avg_fit_score <= 100.0
    assert 0.0 <= summary.avg_qa_score <= 100.0


def test_s10_priority_counts_add_up_to_total_leads() -> None:
    """S-10: priority counts add up to total_leads."""

    summary = build_run_evaluation_summary()
    total_counted = (
        summary.high_priority_leads
        + summary.medium_priority_leads
        + summary.low_priority_leads
    )
    assert total_counted == summary.total_leads
    assert summary.total_leads == len(summary.leads)


def test_s11_every_lead_dimensions_scored_within_bounds() -> None:
    """S-11: every LeadEvaluationReport has dimensions with scores within 0..100."""

    summary = build_run_evaluation_summary()
    for lead in summary.leads:
        assert lead.dimensions, f"lead {lead.lead_id} has no dimensions"
        for dim in lead.dimensions:
            assert 0 <= dim.score <= 100, (
                f"{lead.lead_id}/{dim.name}: score={dim.score}"
            )
            assert 0.0 <= dim.weight <= 1.0


def test_s12_lead_010_has_risks_and_lower_quality_than_lead_001() -> None:
    """S-12: lead_010 has risks and lower quality than lead_001."""

    summary = build_run_evaluation_summary()
    by_id = {lead.lead_id: lead for lead in summary.leads}
    lead_001 = by_id["lead_001"]
    lead_010 = by_id["lead_010"]

    assert len(lead_010.risks) >= 1
    assert lead_010.fit_score < lead_001.fit_score
    assert lead_010.qa_score < lead_001.qa_score
    assert lead_010.priority == Priority.LOW


def test_s13_build_lead_evaluation_report_returns_matching_lead() -> None:
    """S-13: build_lead_evaluation_report("lead_001") returns lead_001."""

    report = build_lead_evaluation_report("lead_001")
    assert isinstance(report, LeadEvaluationReport)
    assert report.lead_id == "lead_001"


def test_s14_build_lead_evaluation_report_raises_value_error_for_missing_lead() -> None:
    """S-14: build_lead_evaluation_report("missing_lead") raises ValueError."""

    with pytest.raises(ValueError):
        build_lead_evaluation_report("missing_lead")
