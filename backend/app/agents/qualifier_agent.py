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

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    QualifierAgentInput,
    QualifierAgentOutput,
)
from app.schemas.common import Confidence, Priority, RunMode
from app.schemas.lead import LeadIn
from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
)
from app.schemas.qualifier_synthesis import QualifierSynthesisPayload
from app.services.icp_scoring import (
    PRIORITY_CAP_NONE,
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
from app.services.json_utils import extract_json_object
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "qualifier_agent"
_PROMPT_VERSION: str = "qualifier_agent_deterministic_v1"
_PROMPT_VERSION_GROQ_JSON: str = "qualifier_agent_groq_json_v1"
_PROMPT_VERSION_GROQ_JSON_FALLBACK: str = "qualifier_agent_groq_json_v1_fallback"
_MODEL_NAME: str = "none"
_GROQ_QUALIFIER_MODEL_NAME: str = "llama-3.1-8b-instant"

# Phase 5.6B FIX 4 — JSON schema included verbatim in the system prompt.
_SYNTHESIS_SYSTEM_PROMPT: str = (
    "You are LeadForge Qualifier Agent running in Phase 5.6B structured "
    "synthesis mode.\n"
    "\n"
    "Hard rules:\n"
    "- Do not use live web research.\n"
    "- Do not invent facts.\n"
    "- Use only the provided lead, research_summary, opportunity_signals, "
    "and information_risks.\n"
    "- Respect the deterministic baseline score unless there is a clear "
    "reason in the provided context to revise it.\n"
    "- Never propose a fit_score more than 15 points above the baseline.\n"
    "- Never override a deterministic priority cap.\n"
    "\n"
    "Return ONLY a valid JSON object with this exact schema, no markdown:\n"
    '{"fit_score": integer 0-100,\n'
    ' "priority": "high|medium|low",\n'
    ' "fit_reasons": ["string"],\n'
    ' "fit_risks": ["string"],\n'
    ' "confidence": "high|medium|low"}'
)
_GUARDRAIL_FALLBACK_RISK: str = (
    "LLM qualification failed validation or guardrails; deterministic "
    "fallback used."
)

# Maximum upward score swing the LLM is allowed to introduce vs the
# deterministic baseline (Phase 5.6B FIX 3 — guardrail step 3).
_MAX_LLM_SCORE_UPGRADE: int = 15

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


# --------------------------------------------------------------------------- #
# Deterministic baseline (shared between the default path and the fallback   #
# path of the Phase 5.6B synthesis route).                                    #
# --------------------------------------------------------------------------- #


class _DeterministicBaseline:
    """Bundle of the deterministic scoring result and the inputs used.

    Carried internally between ``_run_inner`` and the synthesis path so
    the LLM guardrails can compare against the exact baseline a
    deterministic call would have produced for the same input.
    """

    __slots__ = (
        "fit_score",
        "priority",
        "confidence",
        "fit_reasons",
        "fit_risks",
        "deductions",
        "cap",
        "override_notes",
    )

    def __init__(
        self,
        *,
        fit_score: int,
        priority: Priority,
        confidence: Confidence,
        fit_reasons: list[str],
        fit_risks: list[str],
        deductions: int,
        cap: int,
        override_notes: list[str],
    ) -> None:
        self.fit_score = fit_score
        self.priority = priority
        self.confidence = confidence
        self.fit_reasons = fit_reasons
        self.fit_risks = fit_risks
        self.deductions = deductions
        self.cap = cap
        self.override_notes = override_notes


class QualifierAgentService:
    """Deterministic ICP qualifier backed by the shared icp_scoring rubric.

    Phase 5.6B adds the optional ``use_model_synthesis`` flag. Behaviour:

    * ``use_model_synthesis=False`` (default) — Phase 5.6A behaviour is
      preserved exactly. The model service is never invoked.
    * ``use_model_synthesis=True`` — the deterministic baseline is
      computed first (it is also the fallback for every failure mode);
      then the model service is called for a strict-JSON synthesis.
        * If the response carries ``simulated=True`` (mock or any
          future simulated provider), the response content is NOT
          consumed; the deterministic baseline is returned.
        * If the response carries ``simulated=False`` (real provider),
          the response content is parsed via
          :class:`QualifierSynthesisPayload` and then run through
          guardrails: ``fit_score`` clamped to ``0..100``; an override
          cap on the baseline forces the deterministic priority to win
          (Phase 5.6B FIX 3); ``fit_score`` may not exceed the baseline
          by more than 15 points. Failures route to the deterministic
          fallback path with a clear risk note and
          ``metadata.simulated=True``.
    """

    def __init__(
        self,
        model_service: BaseModelService | None = None,
        use_model_synthesis: bool = False,
    ) -> None:
        self.model_service: BaseModelService = (
            model_service if model_service is not None
            else get_model_service(ModelProvider.MOCK)
        )
        self.use_model_synthesis: bool = use_model_synthesis

    # ------------------------------------------------------------------- #
    # Public entry point                                                  #
    # ------------------------------------------------------------------- #
    def run(
        self, agent_input: QualifierAgentInput
    ) -> QualifierAgentOutput:
        try:
            baseline = self._compute_baseline(agent_input)
            if self.use_model_synthesis:
                return self._run_with_model_synthesis(agent_input, baseline)
            return self._output_from_baseline(
                agent_input.lead.lead_id, baseline, _metadata()
            )
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
    # Phase 5.6A — Inner scoring pipeline                                 #
    # ------------------------------------------------------------------- #
    def _run_inner(
        self, agent_input: QualifierAgentInput
    ) -> QualifierAgentOutput:
        """Original Phase 5.6A entry point — kept for test compatibility.

        Test ``S-12`` monkeypatches ``_run_inner`` to raise; preserving
        the method ensures that override still triggers the failure
        path in :meth:`run` exactly as before.
        """

        baseline = self._compute_baseline(agent_input)
        return self._output_from_baseline(
            agent_input.lead.lead_id, baseline, _metadata()
        )

    def _compute_baseline(
        self, agent_input: QualifierAgentInput
    ) -> _DeterministicBaseline:
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

        if (
            not _is_blank(lead.contact_role)
            and classify_contact_role(lead.contact_role) == "out_of_scope"
        ):
            fit_risks.append(
                "Contact role out of scope: Dimension 4 scored 0."
            )
        for note in override_notes:
            if note not in fit_risks:
                fit_risks.append(note)
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

        return _DeterministicBaseline(
            fit_score=fit_score,
            priority=priority,
            confidence=confidence,
            fit_reasons=fit_reasons,
            fit_risks=fit_risks,
            deductions=deductions,
            cap=cap,
            override_notes=override_notes,
        )

    def _output_from_baseline(
        self,
        lead_id: str,
        baseline: _DeterministicBaseline,
        metadata: AgentExecutionMetadata,
        *,
        extra_risk: str | None = None,
    ) -> QualifierAgentOutput:
        fit_risks = list(baseline.fit_risks)
        if extra_risk and extra_risk not in fit_risks:
            fit_risks.append(extra_risk)
        return QualifierAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=metadata,
                error=None,
            ),
            lead_id=lead_id,
            fit_score=baseline.fit_score,
            priority=baseline.priority,
            fit_reasons=list(baseline.fit_reasons),
            fit_risks=fit_risks,
            confidence=baseline.confidence,
        )

    # ------------------------------------------------------------------- #
    # Phase 5.6B — Structured-synthesis path                              #
    # ------------------------------------------------------------------- #
    def _build_synthesis_request(
        self,
        agent_input: QualifierAgentInput,
        baseline: _DeterministicBaseline,
    ) -> ModelRequest:
        lead = agent_input.lead
        payload = {
            "lead": {
                "lead_id": lead.lead_id,
                "company_name": lead.company_name or "(missing)",
                "industry": lead.industry or "(missing)",
                "country": lead.country or "(missing)",
                "website": lead.website or "(missing)",
                "contact_name": lead.contact_name or "(missing)",
                "contact_role": lead.contact_role or "(missing)",
                "employee_count": lead.employee_count,
                "notes": lead.notes,
            },
            "research_summary": agent_input.research_summary,
            "opportunity_signals": list(agent_input.opportunity_signals),
            "information_risks": list(agent_input.information_risks),
            "baseline": {
                "fit_score": baseline.fit_score,
                "priority": baseline.priority.value,
                "confidence": baseline.confidence.value,
                "fit_reasons": baseline.fit_reasons,
                "fit_risks": baseline.fit_risks,
                "override_cap_active": baseline.cap < PRIORITY_CAP_NONE,
            },
        }
        user_content = (
            "Refine the deterministic baseline for the following lead, "
            "using ONLY the provided context. Respond with valid JSON "
            "matching the schema described in the system message.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

        config = ModelConfig(
            provider=ModelProvider.GROQ,
            model_name=_GROQ_QUALIFIER_MODEL_NAME,
        )
        return ModelRequest(
            messages=[
                ModelMessage(role=ModelRole.SYSTEM, content=_SYNTHESIS_SYSTEM_PROMPT),
                ModelMessage(role=ModelRole.USER, content=user_content),
            ],
            config=config,
            request_id=(
                f"qualifier_agent_synthesis::{agent_input.run_id}::{lead.lead_id}"
                if agent_input.run_id
                else f"qualifier_agent_synthesis::{lead.lead_id}"
            ),
        )

    def _synthesis_metadata(
        self,
        response: ModelResponse,
        *,
        prompt_version: str,
        simulated: bool,
    ) -> AgentExecutionMetadata:
        return AgentExecutionMetadata(
            agent_name=_AGENT_NAME,
            run_mode=RunMode.SIMULATION,
            model=response.model_name,
            prompt_version=prompt_version,
            latency=response.latency,
            tokens=response.usage.total_tokens,
            cost=response.cost.display_cost,
            simulated=simulated,
        )

    def _validate_payload(self, content: str) -> QualifierSynthesisPayload:
        payload_dict = extract_json_object(content)
        try:
            return QualifierSynthesisPayload.model_validate(payload_dict)
        except ValidationError as exc:
            # The original LLM content is intentionally NOT included
            # here; only the validator diagnostics, which are derived
            # from the parsed dict.
            raise ValueError(
                f"Model response failed QualifierSynthesisPayload validation: {exc}"
            ) from exc

    def _apply_guardrails(
        self,
        payload: QualifierSynthesisPayload,
        baseline: _DeterministicBaseline,
    ) -> QualifierSynthesisPayload:
        """Enforce Phase 5.6B guardrails on a freshly-validated payload.

        Raises ``ValueError`` when a guardrail fires so the caller
        routes to the deterministic fallback.
        """

        # Step 1 — clamp to 0..100 (schema also enforces this; defensive).
        clamped_score = max(0, min(100, payload.fit_score))

        # Step 2 — score may not exceed the baseline by more than 15.
        if clamped_score - baseline.fit_score > _MAX_LLM_SCORE_UPGRADE:
            raise ValueError(
                "LLM fit_score exceeds deterministic baseline by more than "
                f"{_MAX_LLM_SCORE_UPGRADE} points."
            )

        # Step 3 — Phase 5.6B FIX 3: if an override cap was active on
        # the baseline, the LLM priority is REJECTED entirely. The
        # deterministic priority must be used regardless of what the
        # LLM proposed.
        if baseline.cap < PRIORITY_CAP_NONE:
            if payload.priority != baseline.priority:
                raise ValueError(
                    "Override cap is active on the baseline; LLM priority "
                    "is rejected per Phase 5.6B FIX 3."
                )

        return QualifierSynthesisPayload(
            fit_score=clamped_score,
            priority=payload.priority,
            fit_reasons=list(payload.fit_reasons),
            fit_risks=list(payload.fit_risks),
            confidence=payload.confidence,
        )

    def _payload_to_output(
        self,
        lead_id: str,
        payload: QualifierSynthesisPayload,
        response: ModelResponse,
    ) -> QualifierAgentOutput:
        return QualifierAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=self._synthesis_metadata(
                    response,
                    prompt_version=_PROMPT_VERSION_GROQ_JSON,
                    # simulated=False ONLY when a validated, guardrail-
                    # approved LLM payload is used as the output source.
                    simulated=False,
                ),
                error=None,
            ),
            lead_id=lead_id,
            fit_score=payload.fit_score,
            priority=payload.priority,
            fit_reasons=list(payload.fit_reasons),
            fit_risks=list(payload.fit_risks),
            confidence=payload.confidence,
        )

    def _fallback_with_response(
        self,
        lead_id: str,
        baseline: _DeterministicBaseline,
        response: ModelResponse,
    ) -> QualifierAgentOutput:
        """Build a deterministic-fallback output that records the model
        call's metadata but flags ``simulated=True`` (the OUTPUT origin
        is deterministic regardless of whether Groq was called)."""

        fallback_metadata = self._synthesis_metadata(
            response,
            prompt_version=_PROMPT_VERSION_GROQ_JSON_FALLBACK,
            simulated=True,
        )
        return self._output_from_baseline(
            lead_id,
            baseline,
            fallback_metadata,
            extra_risk=_GUARDRAIL_FALLBACK_RISK,
        )

    def _run_with_model_synthesis(
        self,
        agent_input: QualifierAgentInput,
        baseline: _DeterministicBaseline,
    ) -> QualifierAgentOutput:
        """Optional synthesis path: call the model service and route
        the result through validation + guardrails.

        Honesty rule: if the response is marked ``simulated`` (e.g. the
        mock service), the response content is NOT consumed — we
        return the deterministic baseline output instead.
        """

        request = self._build_synthesis_request(agent_input, baseline)
        response = self.model_service.complete(request)

        if response.simulated:
            return self._output_from_baseline(
                agent_input.lead.lead_id, baseline, _metadata()
            )

        try:
            payload = self._validate_payload(response.content)
            approved = self._apply_guardrails(payload, baseline)
        except ValueError:
            return self._fallback_with_response(
                agent_input.lead.lead_id, baseline, response
            )

        return self._payload_to_output(
            agent_input.lead.lead_id, approved, response
        )


__all__ = ["QualifierAgentService"]
