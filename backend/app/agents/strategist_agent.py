"""Strategist Agent service (Phase 5.7).

Third executable individual agent service for LeadForge. Transforms a
``StrategistAgentInput`` (lead + research context + qualification
outcome) into a ``StrategistAgentOutput`` carrying pain hypothesis,
sales angle, core message, likely objection, and personalization notes.

Phase 5.7 ships both:

* the deterministic foundation (always available; no model service
  call), and
* the optional Groq structured-synthesis path (only used when
  ``use_model_synthesis=True`` AND the model service is a real,
  non-simulated provider). The pattern matches Phase 5.5C (Research)
  and Phase 5.6B (Qualifier): the deterministic baseline is computed
  first and is always the safe fallback; the LLM may only refine
  within explicit guardrails and a strict JSON schema.

Hard rules for this module:

* No real LLM call by default. ``MockModelService`` is the constructor
  default and is treated as a simulated provider — its content is
  never consumed as evidence.
* No network I/O. No imports from ``requests`` / ``httpx`` /
  ``urllib`` / ``aiohttp``. No imports from other agent modules.
* No LangGraph, no Chroma/RAG, no scraping, no DB writes, no live web
  research, no email sending.
* No raw model response is ever embedded in error messages, fallback
  risk notes, or any text-bearing output field.

Public surface:

* :class:`StrategistAgentService`
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    StrategistAgentInput,
    StrategistAgentOutput,
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
from app.schemas.strategist_synthesis import StrategistSynthesisPayload
from app.services.json_utils import extract_json_object
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "strategist_agent"
_PROMPT_VERSION: str = "strategist_agent_deterministic_v1"
_PROMPT_VERSION_GROQ_JSON: str = "strategist_agent_groq_json_v1"
_PROMPT_VERSION_GROQ_JSON_FALLBACK: str = "strategist_agent_groq_json_v1_fallback"
_MODEL_NAME: str = "none"
_GROQ_STRATEGIST_MODEL_NAME: str = "llama-3.1-8b-instant"

# Phase 5.7 STEP 6 + FIX 3 — Guardrail phrases (multi-word only) that
# imply the model invented live-research, public-source, or news
# claims that the agent should never surface. Single words like
# "funding" or "hiring" are NOT included here because they appear in
# legitimate sales messaging ("help with hiring efficiency", "support
# funding your growth") and would trigger false fallbacks.
_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "i found online",
    "we found online",
    "we noticed online",
    "we saw online",
    "according to your website",
    "we found on your website",
    "we read that you",
    "according to news",
    "recent news about",
    "recent announcement about",
    "your recent funding",
    "we noticed you're hiring",
    "we noticed youre hiring",
)

# Phrases that indicate a sales angle is cautious / discovery-oriented.
# Required when ``priority == Priority.LOW`` — anything more aggressive
# from the LLM triggers a fallback.
_CAUTIOUS_PHRASES: tuple[str, ...] = (
    "cautious",
    "discovery",
    "validate",
    "explore",
    "exploratory",
    "soft",
    "verify",
    "confirm",
)

_GUARDRAIL_FALLBACK_RISK_NOTE: str = (
    "LLM strategy failed validation or guardrails; deterministic "
    "fallback used."
)

_SYNTHESIS_SYSTEM_PROMPT: str = (
    "You are LeadForge Strategist Agent running in Phase 5.7 structured "
    "synthesis mode.\n"
    "\n"
    "Return ONLY a valid JSON object with this exact schema, no markdown:\n"
    "{\n"
    '  "pain_hypothesis": "string",\n'
    '  "pain_confidence": "high|medium|low",\n'
    '  "sales_angle": "string",\n'
    '  "core_message": "string",\n'
    '  "likely_objection": "string",\n'
    '  "personalization_notes": ["string"]\n'
    "}\n"
    "\n"
    "Rules:\n"
    "- Use only the provided lead, research and qualification context.\n"
    "- Do not use live web research.\n"
    "- Do not invent facts.\n"
    "- Do not claim public sources, funding rounds, hiring news, "
    "customer lists, tech stack or external announcements.\n"
    "- Keep the message professional and non-aggressive.\n"
    "- If context is limited, say so conservatively rather than "
    "embellishing.\n"
    "- Do not overpromise outcomes."
)


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _is_blank(value: str | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _truncate(value: str, max_length: int = 120) -> str:
    snippet = " ".join(value.strip().split())
    if len(snippet) <= max_length:
        return snippet
    return snippet[: max_length - 3] + "..."


def _first_non_empty(values: list[str]) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


# --------------------------------------------------------------------------- #
# Deterministic baseline                                                      #
# --------------------------------------------------------------------------- #
class _DeterministicBaseline:
    """Bundle of the deterministic strategist baseline.

    Used both as the default output and as the safe fallback when the
    Groq path's payload fails validation or guardrails. The fields
    mirror :class:`StrategistAgentOutput` 1:1 (minus the contract
    envelope).
    """

    __slots__ = (
        "pain_hypothesis",
        "pain_confidence",
        "sales_angle",
        "core_message",
        "likely_objection",
        "personalization_notes",
    )

    def __init__(
        self,
        *,
        pain_hypothesis: str,
        pain_confidence: Confidence,
        sales_angle: str,
        core_message: str,
        likely_objection: str,
        personalization_notes: list[str],
    ) -> None:
        self.pain_hypothesis = pain_hypothesis
        self.pain_confidence = pain_confidence
        self.sales_angle = sales_angle
        self.core_message = core_message
        self.likely_objection = likely_objection
        self.personalization_notes = personalization_notes


_FALLBACK_PAIN: str = (
    "The team may be dealing with fragmented prospecting, "
    "prioritization, or outreach workflows."
)

_SALES_ANGLE_HIGH: str = (
    "Position LeadForge as a way to accelerate revenue operations and "
    "improve lead-to-outreach conversion."
)
_SALES_ANGLE_MEDIUM: str = (
    "Position LeadForge as a way to improve prioritization and reduce "
    "manual research before outreach."
)
_SALES_ANGLE_LOW: str = (
    "Use a cautious discovery angle to validate whether there is a "
    "real sales workflow pain before pitching."
)

_OBJECTION_LOW: str = "This may not be a current priority or fit."
_OBJECTION_ESTABLISHED: str = (
    "We already have a process for lead research and qualification."
)
_OBJECTION_BANDWIDTH: str = (
    "We do not have time to evaluate another sales tool right now."
)


def _baseline_pain(input_pains: list[str]) -> str:
    first = _first_non_empty(input_pains)
    if first is not None:
        return first
    return _FALLBACK_PAIN


def _baseline_pain_confidence(
    pains: list[str],
    signals: list[str],
    fit_score: int,
    priority: Priority,
) -> Confidence:
    has_pain = any(isinstance(p, str) and p.strip() for p in pains)
    has_signal = any(isinstance(s, str) and s.strip() for s in signals)

    if (not has_pain and not has_signal) or fit_score < 45:
        return Confidence.LOW
    if has_pain and has_signal and priority == Priority.HIGH:
        return Confidence.HIGH
    if has_pain or has_signal:
        return Confidence.MEDIUM
    return Confidence.LOW


def _baseline_sales_angle(priority: Priority) -> str:
    if priority == Priority.HIGH:
        return _SALES_ANGLE_HIGH
    if priority == Priority.MEDIUM:
        return _SALES_ANGLE_MEDIUM
    return _SALES_ANGLE_LOW


def _baseline_core_message(
    lead: LeadIn,
    company_summary: str,
    priority: Priority,
    fit_score: int,
) -> str:
    company = lead.company_name if not _is_blank(lead.company_name) else "your team"
    has_summary = bool(company_summary and company_summary.strip())

    if priority == Priority.HIGH and has_summary:
        return (
            f"For {company}, LeadForge can structure lead research, "
            f"qualification and outreach so revenue operations spend "
            f"less time on prospecting and more time on conversion."
        )
    if priority == Priority.MEDIUM:
        return (
            f"At {company}, LeadForge can help prioritize the leads that "
            f"deserve attention and reduce the manual research that "
            f"slows outreach down."
        )
    # LOW priority — exploratory, no overpromise, no live-research claims.
    return (
        f"It is not yet clear whether {company} has a sales workflow "
        f"that would benefit from a research and qualification layer; "
        f"a short discovery conversation would help decide."
    )


def _baseline_objection(priority: Priority, fit_score: int) -> str:
    if priority == Priority.LOW:
        return _OBJECTION_LOW
    if priority in (Priority.HIGH, Priority.MEDIUM) and fit_score >= 70:
        return _OBJECTION_ESTABLISHED
    return _OBJECTION_BANDWIDTH


def _baseline_personalization_notes(
    lead: LeadIn,
    opportunity_signals: list[str],
    fit_score: int,
    priority: Priority,
) -> list[str]:
    """Build 2–5 deterministic personalization notes.

    Uses only provided lead fields, opportunity signals, fit score and
    priority. Never invents external facts. Always produces at least 2
    notes so the schema's ``min_length=1`` constraint and the test
    expectation of "2 to 5 notes when enough context exists" are
    satisfied.
    """

    notes: list[str] = []

    if not _is_blank(lead.company_name):
        notes.append(f"Reference company name: {lead.company_name}.")
    else:
        notes.append("Use generic 'your team' since company name is unclear.")

    if not _is_blank(lead.industry):
        notes.append(f"Anchor to the {lead.industry} context.")
    elif fit_score < 45:
        notes.append(
            "Keep outreach exploratory because available context is limited."
        )
    else:
        notes.append("Avoid industry-specific claims; industry not provided.")

    first_signal = _first_non_empty(opportunity_signals)
    if first_signal is not None and len(notes) < 5:
        notes.append(
            f"Reference an internal opportunity signal: {_truncate(first_signal)}."
        )

    if len(notes) < 5:
        if priority == Priority.HIGH:
            notes.append(
                "Lead is high priority; lead with the strongest fit reasons."
            )
        elif priority == Priority.LOW:
            notes.append(
                "Lead is low priority; soft, exploratory CTA only."
            )
        else:
            notes.append(
                f"Tier-appropriate tone (fit_score={fit_score})."
            )

    if len(notes) < 2:
        notes.append("Keep outreach short and review before sending.")

    return notes[:5]


def _compute_baseline(input: StrategistAgentInput) -> _DeterministicBaseline:
    lead = input.lead
    pains = list(input.pain_hypotheses)
    signals = list(input.opportunity_signals)

    return _DeterministicBaseline(
        pain_hypothesis=_baseline_pain(pains),
        pain_confidence=_baseline_pain_confidence(
            pains, signals, input.fit_score, input.priority
        ),
        sales_angle=_baseline_sales_angle(input.priority),
        core_message=_baseline_core_message(
            lead, input.company_summary, input.priority, input.fit_score
        ),
        likely_objection=_baseline_objection(input.priority, input.fit_score),
        personalization_notes=_baseline_personalization_notes(
            lead, signals, input.fit_score, input.priority
        ),
    )


# --------------------------------------------------------------------------- #
# Metadata builders                                                           #
# --------------------------------------------------------------------------- #
def _deterministic_metadata() -> AgentExecutionMetadata:
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


def _synthesis_metadata(
    response: ModelResponse, *, prompt_version: str, simulated: bool
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


# --------------------------------------------------------------------------- #
# Service                                                                     #
# --------------------------------------------------------------------------- #
class StrategistAgentService:
    """Deterministic-first strategist with optional Groq synthesis."""

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
    def run(self, agent_input: StrategistAgentInput) -> StrategistAgentOutput:
        try:
            baseline = _compute_baseline(agent_input)
            if self.use_model_synthesis:
                return self._run_with_model_synthesis(agent_input, baseline)
            return self._output_from_baseline(
                agent_input.lead.lead_id, baseline, _deterministic_metadata()
            )
        except Exception as exc:  # noqa: BLE001 — agent must never raise
            return self._safe_failure_output(agent_input.lead.lead_id, exc)

    # ------------------------------------------------------------------- #
    # Output construction                                                 #
    # ------------------------------------------------------------------- #
    def _output_from_baseline(
        self,
        lead_id: str,
        baseline: _DeterministicBaseline,
        metadata: AgentExecutionMetadata,
        *,
        extra_note: str | None = None,
    ) -> StrategistAgentOutput:
        notes = list(baseline.personalization_notes)
        if extra_note and extra_note not in notes:
            notes.append(extra_note)
            # Schema enforces max_length=5, but personalization_notes on
            # StrategistAgentOutput itself is unbounded. We keep the
            # fallback note even if it pushes past 5; it's the most
            # important context for a human reviewer.
        return StrategistAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=metadata,
                error=None,
            ),
            # Phase 5.7 FIX 2 — explicit lead_id wiring.
            lead_id=lead_id,
            pain_hypothesis=baseline.pain_hypothesis,
            pain_confidence=baseline.pain_confidence,
            sales_angle=baseline.sales_angle,
            core_message=baseline.core_message,
            likely_objection=baseline.likely_objection,
            personalization_notes=notes,
        )

    def _payload_to_output(
        self,
        lead_id: str,
        payload: StrategistSynthesisPayload,
        response: ModelResponse,
    ) -> StrategistAgentOutput:
        return StrategistAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=_synthesis_metadata(
                    response,
                    prompt_version=_PROMPT_VERSION_GROQ_JSON,
                    simulated=False,
                ),
                error=None,
            ),
            # Phase 5.7 FIX 2 — explicit lead_id wiring.
            lead_id=lead_id,
            pain_hypothesis=payload.pain_hypothesis,
            pain_confidence=payload.pain_confidence,
            sales_angle=payload.sales_angle,
            core_message=payload.core_message,
            likely_objection=payload.likely_objection,
            personalization_notes=list(payload.personalization_notes),
        )

    def _fallback_with_response(
        self,
        lead_id: str,
        baseline: _DeterministicBaseline,
        response: ModelResponse,
    ) -> StrategistAgentOutput:
        return self._output_from_baseline(
            lead_id,
            baseline,
            _synthesis_metadata(
                response,
                prompt_version=_PROMPT_VERSION_GROQ_JSON_FALLBACK,
                # Phase 5.7 FIX 1 / Phase 5.5C FIX 1: fallback output's
                # data origin is deterministic, so ``simulated=True``
                # even though Groq was actually called.
                simulated=True,
            ),
            extra_note=_GUARDRAIL_FALLBACK_RISK_NOTE,
        )

    def _safe_failure_output(
        self, lead_id: str, exc: Exception
    ) -> StrategistAgentOutput:
        return StrategistAgentOutput(
            result=AgentContractResult(
                success=False,
                metadata=_deterministic_metadata(),
                error=AgentError(
                    code="strategist_agent_error",
                    message=str(exc),
                    recoverable=True,
                ),
            ),
            lead_id=lead_id,
            pain_hypothesis=(
                "Strategy agent failed before producing a pain hypothesis."
            ),
            pain_confidence=Confidence.LOW,
            sales_angle="Manual review required before outreach.",
            core_message="Insufficient safe context to generate a strategy.",
            likely_objection="Insufficient context.",
            personalization_notes=[],
        )

    # ------------------------------------------------------------------- #
    # Synthesis path                                                      #
    # ------------------------------------------------------------------- #
    def _build_synthesis_request(
        self,
        agent_input: StrategistAgentInput,
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
            "company_summary": agent_input.company_summary,
            "opportunity_signals": list(agent_input.opportunity_signals),
            "pain_hypotheses": list(agent_input.pain_hypotheses),
            "fit_score": agent_input.fit_score,
            "priority": agent_input.priority.value,
            "baseline": {
                "pain_hypothesis": baseline.pain_hypothesis,
                "pain_confidence": baseline.pain_confidence.value,
                "sales_angle": baseline.sales_angle,
                "core_message": baseline.core_message,
                "likely_objection": baseline.likely_objection,
                "personalization_notes": baseline.personalization_notes,
            },
        }
        user_content = (
            "Refine the deterministic baseline strategy for the "
            "following lead, using ONLY the provided context. Respond "
            "with valid JSON matching the schema in the system message.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

        config = ModelConfig(
            provider=ModelProvider.GROQ,
            model_name=_GROQ_STRATEGIST_MODEL_NAME,
        )
        return ModelRequest(
            messages=[
                ModelMessage(role=ModelRole.SYSTEM, content=_SYNTHESIS_SYSTEM_PROMPT),
                ModelMessage(role=ModelRole.USER, content=user_content),
            ],
            config=config,
            request_id=(
                f"strategist_agent_synthesis::{agent_input.run_id}::{lead.lead_id}"
                if agent_input.run_id
                else f"strategist_agent_synthesis::{lead.lead_id}"
            ),
        )

    def _validate_payload(self, content: str) -> StrategistSynthesisPayload:
        payload_dict = extract_json_object(content)
        try:
            return StrategistSynthesisPayload.model_validate(payload_dict)
        except ValidationError as exc:
            raise ValueError(
                f"Model response failed StrategistSynthesisPayload validation: {exc}"
            ) from exc

    def _apply_guardrails(
        self,
        payload: StrategistSynthesisPayload,
        priority: Priority,
    ) -> StrategistSynthesisPayload:
        """Enforce the Phase 5.7 / FIX 3 guardrails.

        Raises ``ValueError`` on any guardrail violation so the caller
        routes to the deterministic fallback. No raw model text is
        included in the exception message — only a short, generic
        guardrail label.
        """

        text_fields = (
            payload.pain_hypothesis,
            payload.sales_angle,
            payload.core_message,
            payload.likely_objection,
            *payload.personalization_notes,
        )
        for field_text in text_fields:
            if _contains_any(field_text, _FORBIDDEN_PHRASES):
                raise ValueError(
                    "LLM strategy includes a forbidden live-research / "
                    "external-claim phrase."
                )

        if priority == Priority.LOW:
            if not _contains_any(payload.sales_angle, _CAUTIOUS_PHRASES):
                raise ValueError(
                    "LLM sales_angle for a LOW priority lead is not "
                    "cautious / discovery-oriented."
                )

        # max_length=5 on personalization_notes is enforced by Pydantic,
        # but assert defensively as well to keep the contract visible.
        if len(payload.personalization_notes) > 5:
            raise ValueError(
                "LLM personalization_notes exceeds the 5-item limit."
            )

        return payload

    def _run_with_model_synthesis(
        self,
        agent_input: StrategistAgentInput,
        baseline: _DeterministicBaseline,
    ) -> StrategistAgentOutput:
        request = self._build_synthesis_request(agent_input, baseline)
        response = self.model_service.complete(request)

        # Simulated response (mock or any future simulated provider):
        # content is not consumed; return the deterministic baseline.
        if response.simulated:
            return self._output_from_baseline(
                agent_input.lead.lead_id, baseline, _deterministic_metadata()
            )

        try:
            payload = self._validate_payload(response.content)
            approved = self._apply_guardrails(payload, agent_input.priority)
        except ValueError:
            return self._fallback_with_response(
                agent_input.lead.lead_id, baseline, response
            )

        return self._payload_to_output(
            agent_input.lead.lead_id, approved, response
        )


__all__ = ["StrategistAgentService"]
