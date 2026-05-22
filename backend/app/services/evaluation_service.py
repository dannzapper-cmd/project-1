"""Trace and evaluation report service (Phase 5.3).

Pure, deterministic, read-only projections of the existing Phase 5.1
simulation outputs into the Phase 5.3 trace/evaluation view models.

Hard guarantees (any change here would break the Phase 5.3 contract):

* No LLM, agent framework, LangGraph, model provider, Chroma, RAG,
  scraping, network I/O, database write, knowledge-file parsing, or
  external service call.
* No new pip dependencies.
* The Phase 5.1 simulation behavior is not changed; this module only
  *reads* the structures produced by
  :func:`app.services.simulation_service.build_simulation_run`.
* No randomness, no ``datetime`` use, no caching.

Public surface:

* :func:`build_run_trace_report`        → ``RunTraceReport``
* :func:`build_lead_trace_report`       → ``LeadTraceReport``
* :func:`build_run_evaluation_summary`  → ``RunEvaluationSummary``
* :func:`build_lead_evaluation_report`  → ``LeadEvaluationReport``

The two ``*_lead_*`` helpers raise ``ValueError`` when ``lead_id`` is not
present in the simulation run. Translating that into HTTP status codes
is the route layer's responsibility.
"""

from __future__ import annotations

from app.schemas.common import LeadStatus, Priority, RunMode
from app.schemas.evaluation import (
    AgentTraceSummary,
    EvaluationDimensionScore,
    LeadEvaluationReport,
    LeadTraceReport,
    RunEvaluationSummary,
    RunTraceReport,
)
from app.schemas.lead import LeadDetail
from app.schemas.run import TraceEntry
from app.schemas.simulation import SimulationRunResponse
from app.services.simulation_service import build_simulation_run

_ESTIMATED_COST: str = "$0.00"
_MODEL_NAME: str = "none"

# Dimension weights used for the evaluation report. They sum to 1.0 so
# downstream consumers can weight-average them without renormalization.
_DIM_FIT_QUALITY_WEIGHT: float = 0.30
_DIM_PERSONALIZATION_WEIGHT: float = 0.20
_DIM_EVIDENCE_COVERAGE_WEIGHT: float = 0.20
_DIM_CTA_QUALITY_WEIGHT: float = 0.15
_DIM_TONE_MATCH_WEIGHT: float = 0.15

# Thresholds for deterministic strengths/risks notes.
_STRENGTH_THRESHOLD: int = 70
_RISK_THRESHOLD: int = 50


# --------------------------------------------------------------------------- #
# Trace report                                                                #
# --------------------------------------------------------------------------- #
def _trace_entry_to_summary(entry: TraceEntry) -> AgentTraceSummary:
    """Project a canonical ``TraceEntry`` onto the frontend view model.

    ``status`` is a ``str, Enum`` on ``TraceEntry``; ``str(...)`` returns
    the enum's string value (e.g. ``"success"``) because the enum
    inherits from ``str``.
    """

    return AgentTraceSummary(
        agent=entry.agent,
        status=str(entry.status.value),
        model=entry.model,
        simulated=entry.simulated,
        latency=entry.latency,
        tokens=entry.tokens,
        prompt_version=entry.prompt_version,
        input_summary=entry.input_summary,
        output_summary=entry.output_summary,
    )


def _build_lead_trace(run_id: str, detail: LeadDetail) -> LeadTraceReport:
    summaries = [_trace_entry_to_summary(step) for step in detail.trace]
    total_tokens = sum(step.tokens for step in detail.trace)
    return LeadTraceReport(
        run_id=run_id,
        lead_id=detail.id,
        company_name=detail.company,
        run_mode=RunMode.SIMULATION,
        total_steps=len(summaries),
        total_tokens=total_tokens,
        total_estimated_cost=_ESTIMATED_COST,
        model_used=_MODEL_NAME,
        simulated=True,
        trace=summaries,
    )


def build_run_trace_report() -> RunTraceReport:
    """Build a run-level trace report from the current simulation run."""

    simulation: SimulationRunResponse = build_simulation_run()
    lead_reports = [
        _build_lead_trace(simulation.run_id, detail)
        for detail in simulation.results
    ]
    total_steps = sum(lead.total_steps for lead in lead_reports)
    total_tokens = sum(lead.total_tokens for lead in lead_reports)
    return RunTraceReport(
        run_id=simulation.run_id,
        run_mode=RunMode.SIMULATION,
        data_source=simulation.data_source,
        total_leads=len(lead_reports),
        total_steps=total_steps,
        total_tokens=total_tokens,
        total_estimated_cost=_ESTIMATED_COST,
        simulated=True,
        leads=lead_reports,
    )


def build_lead_trace_report(lead_id: str) -> LeadTraceReport:
    """Return the trace report for a single lead.

    Raises
    ------
    ValueError
        If ``lead_id`` is not present in the current simulation run. The
        route layer translates this into HTTP 404.
    """

    run_report = build_run_trace_report()
    for lead in run_report.leads:
        if lead.lead_id == lead_id:
            return lead
    raise ValueError(
        f"Lead '{lead_id}' not found in the simulation run."
    )


# --------------------------------------------------------------------------- #
# Evaluation report                                                           #
# --------------------------------------------------------------------------- #
def _classify(name: str, score: int) -> tuple[str | None, str | None]:
    """Return ``(strength_note, risk_note)`` for one dimension."""

    if score >= _STRENGTH_THRESHOLD:
        return f"{name}: strong (score={score}).", None
    if score < _RISK_THRESHOLD:
        return None, f"{name}: weak (score={score})."
    return None, None


def _build_dimensions(
    detail: LeadDetail,
) -> tuple[list[EvaluationDimensionScore], list[str], list[str]]:
    """Build the five evaluation dimensions plus the derived
    strengths/risks lists.
    """

    qa = detail.qa_scores

    raw: list[tuple[str, int, float]] = [
        ("Fit Quality", detail.fit_score, _DIM_FIT_QUALITY_WEIGHT),
        ("Personalization", qa.personalization, _DIM_PERSONALIZATION_WEIGHT),
        ("Evidence Coverage", qa.evidence_coverage, _DIM_EVIDENCE_COVERAGE_WEIGHT),
        ("CTA Quality", qa.cta_quality, _DIM_CTA_QUALITY_WEIGHT),
        ("Tone Match", qa.tone_match, _DIM_TONE_MATCH_WEIGHT),
    ]

    dimensions: list[EvaluationDimensionScore] = []
    strengths: list[str] = []
    risks: list[str] = []

    for name, score, weight in raw:
        strength_note, risk_note = _classify(name, score)
        notes: list[str] = []
        if strength_note:
            notes.append(strength_note)
            strengths.append(strength_note)
        if risk_note:
            notes.append(risk_note)
            risks.append(risk_note)
        dimensions.append(
            EvaluationDimensionScore(
                name=name,
                score=score,
                weight=weight,
                notes=notes,
            )
        )

    # Carry over per-lead information risks surfaced by the simulator so
    # the evaluation report stays consistent with the qualification
    # reasoning the dashboard already shows.
    for risk in detail.fit_risks:
        if risk and risk not in risks:
            risks.append(risk)

    return dimensions, strengths, risks


def _build_lead_evaluation(
    run_id: str, detail: LeadDetail
) -> LeadEvaluationReport:
    dimensions, strengths, risks = _build_dimensions(detail)
    return LeadEvaluationReport(
        run_id=run_id,
        lead_id=detail.id,
        company_name=detail.company,
        fit_score=detail.fit_score,
        qa_score=detail.qa_score,
        priority=detail.priority,
        status=detail.status,
        recommendation=detail.qa_scores.recommendation,
        hallucination_risk=detail.qa_scores.hallucination_risk,
        dimensions=dimensions,
        strengths=strengths,
        risks=risks,
        simulated=True,
    )


def build_run_evaluation_summary() -> RunEvaluationSummary:
    """Build a run-level evaluation summary from the current simulation run."""

    simulation: SimulationRunResponse = build_simulation_run()
    lead_reports = [
        _build_lead_evaluation(simulation.run_id, detail)
        for detail in simulation.results
    ]
    total_leads = len(lead_reports)

    high = sum(1 for lead in lead_reports if lead.priority == Priority.HIGH)
    medium = sum(1 for lead in lead_reports if lead.priority == Priority.MEDIUM)
    low = sum(1 for lead in lead_reports if lead.priority == Priority.LOW)

    needs_edit_or_review = sum(
        1
        for lead in lead_reports
        if lead.status in (LeadStatus.NEEDS_EDIT, LeadStatus.PENDING_REVIEW)
    )

    if total_leads > 0:
        avg_fit = sum(lead.fit_score for lead in lead_reports) / total_leads
        avg_qa = sum(lead.qa_score for lead in lead_reports) / total_leads
    else:
        avg_fit = 0.0
        avg_qa = 0.0

    total_tokens = sum(
        step.tokens for detail in simulation.results for step in detail.trace
    )

    return RunEvaluationSummary(
        run_id=simulation.run_id,
        run_mode=RunMode.SIMULATION,
        data_source=simulation.data_source,
        total_leads=total_leads,
        avg_fit_score=avg_fit,
        avg_qa_score=avg_qa,
        high_priority_leads=high,
        medium_priority_leads=medium,
        low_priority_leads=low,
        needs_edit_or_review=needs_edit_or_review,
        total_estimated_cost=_ESTIMATED_COST,
        total_tokens=total_tokens,
        simulated=True,
        leads=lead_reports,
    )


def build_lead_evaluation_report(lead_id: str) -> LeadEvaluationReport:
    """Return the evaluation report for a single lead.

    Raises
    ------
    ValueError
        If ``lead_id`` is not present in the current simulation run. The
        route layer translates this into HTTP 404.
    """

    run_summary = build_run_evaluation_summary()
    for lead in run_summary.leads:
        if lead.lead_id == lead_id:
            return lead
    raise ValueError(
        f"Lead '{lead_id}' not found in the simulation run."
    )
