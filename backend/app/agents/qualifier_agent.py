"""Qualifier Agent service (Phase 5.6A).

Second executable individual agent service in the LeadForge codebase
(after the Phase 5.5A Research Agent). Wires the Phase 5.2
``QualifierAgentInput`` / ``QualifierAgentOutput`` contracts through a
deterministic implementation of the icp_rules.md rubric.

Hard rules for this module:

* No real LLM call. No Groq call. No LangGraph, no Chroma/RAG, no
  scraping, no DB writes, no live web research.
* The agent does not call the model service at all in Phase 5.6A:
  scoring is fully deterministic, so spending mock-call latency on
  metadata would only add noise. ``self.model_service`` is kept on
  the instance so a future Phase 5.6B can flip on optional model
  synthesis the same way Phase 5.5C did for the Research Agent.
* Output is honest: every metadata block carries ``simulated=True``,
  ``model="none"`` and ``tokens=0``.

Scoring uses the pure helpers in :mod:`app.services.icp_scoring` —
the same rubric Phase 5.1's simulation service implements (which is
not modified in this PR; migrating it onto this shared module is a
separate cleanup task per Phase 5.6A FIX 3).
"""

from __future__ import annotations

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    QualifierAgentInput,
    QualifierAgentOutput,
)
from app.schemas.common import Confidence, Priority, RunMode
from app.schemas.lead import LeadIn
from app.schemas.model import ModelProvider
from app.services.icp_scoring import (
    apply_override_rules,
    classify_contact_role,
    compute_data_quality_deductions,
    score_contact_role,
    score_country,
    score_data_quality,
    score_industry,
    score_opportunity_signals,
    score_size,
)
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "qualifier_agent"
_PROMPT_VERSION: str = "qualifier_agent_deterministic_v1"
_MODEL_NAME: str = "none"

# Priority thresholds — Phase 5.6A FIX 1: Medium is ≥ 45 per icp_rules.md §11.
_PRIORITY_HIGH_THRESHOLD: int = 75
_PRIORITY_MEDIUM_THRESHOLD: int = 45


def _is_blank(value: str | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _priority_from_score(score: int) -> Priority:
    if score >= _PRIORITY_HIGH_THRESHOLD:
        return Priority.HIGH
    if score >= _PRIORITY_MEDIUM_THRESHOLD:
        return Priority.MEDIUM
    return Priority.LOW


def _confidence_for(
    lead: LeadIn,
    deductions: int,
    fit_score: int,
    information_risks: list[str],
) -> Confidence:
    """Deterministic confidence mapping.

    * ``LOW`` when the score is in the Low band, or when more than one
      key data field is missing.
    * ``HIGH`` when the data is clean (no deductions, no carried
      information risks) and the fit score is solidly Medium or above.
    * ``MEDIUM`` otherwise.
    """

    if fit_score < _PRIORITY_MEDIUM_THRESHOLD:
        return Confidence.LOW
    if deductions == 0 and not information_risks and fit_score >= _PRIORITY_MEDIUM_THRESHOLD:
        return Confidence.HIGH
    if deductions >= 8:
        return Confidence.LOW
    return Confidence.MEDIUM


def _metadata() -> AgentExecutionMetadata:
    return AgentExecutionMetadata(
        agent_name=_AGENT_NAME,
        run_mode=RunMode.SIMULATION,
        model=_MODEL_NAME,
        prompt_version=_PROMPT_VERSION,
        latency="0ms",
        tokens=0,
        cost="$0.00",
        simulated=True,
    )


class QualifierAgentService:
    """Deterministic ICP qualifier backed by the shared icp_scoring rubric."""

    def __init__(self, model_service: BaseModelService | None = None) -> None:
        # Stored for future phases (Phase 5.6B may add optional Groq
        # synthesis the same way the Research Agent does); the Phase
        # 5.6A run() path never calls it.
        self.model_service: BaseModelService = (
            model_service if model_service is not None
            else get_model_service(ModelProvider.MOCK)
        )

    # ------------------------------------------------------------------- #
    # Public entry point                                                  #
    # ------------------------------------------------------------------- #
    def run(
        self, agent_input: QualifierAgentInput
    ) -> QualifierAgentOutput:
        try:
            return self._run_inner(agent_input)
        except Exception as exc:  # noqa: BLE001 — agent must never raise
            return QualifierAgentOutput(
                result=AgentContractResult(
                    success=False,
                    metadata=_metadata(),
                    error=AgentError(
                        code="qualifier_agent_error",
                        message=str(exc),
                        recoverable=True,
                    ),
                ),
                lead_id=agent_input.lead.lead_id,
                fit_score=0,
                priority=Priority.LOW,
                fit_reasons=[],
                fit_risks=[
                    "Qualifier agent failed before producing a score."
                ],
                confidence=Confidence.LOW,
            )

    # ------------------------------------------------------------------- #
    # Inner scoring pipeline                                              #
    # ------------------------------------------------------------------- #
    def _run_inner(
        self, agent_input: QualifierAgentInput
    ) -> QualifierAgentOutput:
        lead = agent_input.lead

        industry_score, industry_reason = score_industry(lead.industry)
        size_score, size_reason = score_size(lead.employee_count)
        country_score, country_reason = score_country(lead.country)
        role_score, role_reason = score_contact_role(lead.contact_role)
        signals_score, signals_reason = score_opportunity_signals(
            list(agent_input.opportunity_signals)
        )
        quality_score, quality_reason = score_data_quality(lead)

        raw_score = (
            industry_score
            + size_score
            + country_score
            + role_score
            + signals_score
            + quality_score
        )
        # Defensive clamp — the dimension scores sum to ≤100 by
        # construction, but keep the contract guarantee explicit.
        raw_score = max(0, min(100, raw_score))

        deductions = compute_data_quality_deductions(lead)
        cap, override_notes = apply_override_rules(raw_score, lead, deductions)
        fit_score = min(raw_score, cap)

        fit_reasons: list[str] = [
            industry_reason,
            size_reason,
            country_reason,
            role_reason,
            signals_reason,
            quality_reason,
        ]
        if override_notes:
            fit_reasons.extend(override_notes)

        fit_risks: list[str] = []

        # Phase 5.6A FIX 2 d: surface out-of-scope contact role as a risk.
        if (
            not _is_blank(lead.contact_role)
            and classify_contact_role(lead.contact_role) == "out_of_scope"
        ):
            fit_risks.append(
                "Contact role out of scope: Dimension 4 scored 0."
            )

        # Reflect override notes as risks too (they are the most
        # decision-relevant signal for a human reviewer).
        for note in override_notes:
            if note not in fit_risks:
                fit_risks.append(note)

        # Lead-level missing-field risks (boring but useful to the UI).
        if _is_blank(lead.industry):
            fit_risks.append(
                "Industry missing; ICP fit cannot be evaluated reliably."
            )
        if _is_blank(lead.country):
            fit_risks.append(
                "Country missing; geographic fit cannot be evaluated."
            )
        if lead.employee_count is None:
            fit_risks.append(
                "Employee count missing; company size fit cannot be evaluated."
            )
        if _is_blank(lead.website):
            fit_risks.append(
                "Website missing; company identity cannot be verified."
            )
        if _is_blank(lead.contact_role):
            fit_risks.append(
                "Contact role missing; contact-role fit cannot be evaluated."
            )

        # Carry forward any externally-provided information risks
        # (e.g. ones the Research Agent surfaced) without duplication.
        for risk in agent_input.information_risks:
            if isinstance(risk, str) and risk.strip() and risk not in fit_risks:
                fit_risks.append(risk)

        priority = _priority_from_score(fit_score)
        confidence = _confidence_for(
            lead=lead,
            deductions=deductions,
            fit_score=fit_score,
            information_risks=fit_risks,
        )

        return QualifierAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=_metadata(),
                error=None,
            ),
            lead_id=lead.lead_id,
            fit_score=fit_score,
            priority=priority,
            fit_reasons=fit_reasons,
            fit_risks=fit_risks,
            confidence=confidence,
        )


__all__ = ["QualifierAgentService"]
