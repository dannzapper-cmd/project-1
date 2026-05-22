"""Research Agent service (Phase 5.5A).

First executable agent service for LeadForge. Wires the Phase 5.2
``ResearchAgentInput`` / ``ResearchAgentOutput`` contracts through the
Phase 5.4 ``MockModelService`` and produces a structured, honestly
labelled research output.

Architecture rules:

* No real model provider is called. The default :class:`MockModelService`
  is used; the model-service call is performed only to exercise the
  pathway and to populate the agent metadata (model name, tokens,
  cost, latency). Its content is intentionally **not** used as
  evidence.
* No network I/O. No ``requests`` / ``httpx`` / ``urllib`` /
  ``aiohttp`` imported here or transitively from the modules this
  service uses.
* No LangGraph, no Chroma, no RAG, no scraping, no DB writes, no
  knowledge-file parsing.
* The service is pure and deterministic: given the same
  ``ResearchAgentInput``, it returns the same ``ResearchAgentOutput``
  (modulo the metadata fields filled in by the mock model service,
  which are themselves deterministic).
* Honesty: every output carries ``simulated=True`` on its metadata,
  evidence cards are always sourced as
  ``EvidenceSource.DEMO_CONTEXT``, and the agent never claims live
  web research, public sources, or LLM-generated reasoning.

This module deliberately does not modify any Phase 5.1 / 5.2 / 5.3 /
5.4 file. It composes them.
"""

from __future__ import annotations

from typing import Any

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    ResearchAgentInput,
    ResearchAgentOutput,
)
from app.schemas.common import Confidence, EvidenceSource, RunMode
from app.schemas.lead import LeadIn
from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
)
from app.schemas.qa import EvidenceCard
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "research_agent"
_PROMPT_VERSION: str = "research_agent_mock_v1"
_MOCK_MODEL_NAME: str = "mock-research-agent"
_SYSTEM_PROMPT: str = (
    "You are LeadForge Research Agent running in Phase 5.5A mock mode. "
    "Do not invent sources."
)
_INSUFFICIENT_SUMMARY: str = (
    "Insufficient context available; no synthesised research is "
    "produced for this lead."
)


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _is_blank(value: str | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _truncate(value: str, max_length: int = 200) -> str:
    snippet = " ".join(value.strip().split())
    if len(snippet) <= max_length:
        return snippet
    return snippet[: max_length - 3] + "..."


def _stringify_signal(signal: Any) -> str:
    """Best-effort projection of an opportunity-signal entry to a string.

    Accepts the plain-dict form that ``available_context`` carries
    (because the demo wiring passes ``DemoCompanyResearch.model_dump()``)
    as well as the rare case where a raw string is supplied directly.
    """

    if isinstance(signal, str):
        return signal
    if isinstance(signal, dict):
        for key in ("signal", "title", "description"):
            value = signal.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return str(signal)


def _stringify_pain(pain: Any) -> str:
    if isinstance(pain, str):
        return pain
    if isinstance(pain, dict):
        for key in ("pain", "description", "reasoning"):
            value = pain.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return str(pain)


def _confidence_from_str(raw: Any) -> Confidence:
    if isinstance(raw, str):
        lookup = {
            "high": Confidence.HIGH,
            "medium": Confidence.MEDIUM,
            "low": Confidence.LOW,
        }
        return lookup.get(raw.strip().lower(), Confidence.LOW)
    return Confidence.LOW


def _evidence_card_from_demo(
    lead_id: str, index: int, card: Any
) -> EvidenceCard:
    """Explicit DemoEvidenceCard-shaped → EvidenceCard projection (FIX 3).

    ``available_context`` is a plain ``dict`` (the demo wiring uses
    ``model_dump()``), so card entries arrive as ``dict`` here. We map
    the fields explicitly rather than assuming shape equality, and we
    *always* set ``source_type=EvidenceSource.DEMO_CONTEXT`` regardless
    of whatever ``source_type`` the demo data carried — matching the
    Phase 5.1 simulation behaviour and the Phase 5.5A honesty rule.
    """

    if isinstance(card, dict):
        headline = (
            card.get("title")
            or card.get("headline")
            or "Demo evidence (no title)"
        )
        description_parts: list[str] = []
        raw_desc = card.get("description")
        if isinstance(raw_desc, str) and raw_desc.strip():
            description_parts.append(raw_desc)
        description_parts.append("[Source: synthetic_demo_context]")
        confidence = _confidence_from_str(card.get("confidence"))
        description = " ".join(description_parts)
    else:
        headline = "Demo evidence (no title)"
        description = "[Source: synthetic_demo_context]"
        confidence = Confidence.LOW

    return EvidenceCard(
        id=f"{lead_id}_research_agent_evidence_{index:02d}",
        headline=str(headline),
        source_type=EvidenceSource.DEMO_CONTEXT,
        description=description,
        confidence=confidence,
    )


def _confidence_from_evidence_counts(
    signal_count: int, evidence_count: int
) -> Confidence:
    """Deterministic confidence rule based on evidence volume."""

    combined = signal_count + evidence_count
    if combined >= 4:
        return Confidence.HIGH
    if combined >= 1:
        return Confidence.MEDIUM
    return Confidence.LOW


# --------------------------------------------------------------------------- #
# Service                                                                     #
# --------------------------------------------------------------------------- #
class ResearchAgentService:
    """Executable Research Agent backed by the model service abstraction."""

    def __init__(self, model_service: BaseModelService | None = None) -> None:
        self.model_service: BaseModelService = (
            model_service if model_service is not None
            else get_model_service(ModelProvider.MOCK)
        )

    # --------------------------------------------------------------------- #
    # Prompt construction                                                   #
    # --------------------------------------------------------------------- #
    def _build_model_request(
        self, agent_input: ResearchAgentInput
    ) -> ModelRequest:
        lead = agent_input.lead

        lead_fields = [
            f"company_name: {lead.company_name or '(missing)'}",
            f"industry: {lead.industry or '(missing)'}",
            f"country: {lead.country or '(missing)'}",
            f"website: {lead.website or '(missing)'}",
            f"contact_role: {lead.contact_role or '(missing)'}",
        ]

        context_keys: list[str] = []
        if isinstance(agent_input.available_context, dict):
            context_keys = sorted(
                str(key)
                for key in agent_input.available_context.keys()
            )

        user_lines = [
            "Lead under research:",
            *(f"- {entry}" for entry in lead_fields),
        ]
        if context_keys:
            user_lines.append("")
            user_lines.append(
                "available_context keys: " + ", ".join(context_keys)
            )
        else:
            user_lines.append("")
            user_lines.append("available_context: none")

        config = ModelConfig(
            provider=ModelProvider.MOCK,
            model_name=_MOCK_MODEL_NAME,
        )
        return ModelRequest(
            messages=[
                ModelMessage(role=ModelRole.SYSTEM, content=_SYSTEM_PROMPT),
                ModelMessage(role=ModelRole.USER, content="\n".join(user_lines)),
            ],
            config=config,
            request_id=(
                f"research_agent::{agent_input.run_id}::{lead.lead_id}"
                if agent_input.run_id
                else f"research_agent::{lead.lead_id}"
            ),
        )

    # --------------------------------------------------------------------- #
    # Output construction                                                   #
    # --------------------------------------------------------------------- #
    def _metadata_from_response(
        self, response: ModelResponse
    ) -> AgentExecutionMetadata:
        return AgentExecutionMetadata(
            agent_name=_AGENT_NAME,
            run_mode=RunMode.SIMULATION,
            model=response.model_name,
            prompt_version=_PROMPT_VERSION,
            latency=response.latency,
            tokens=response.usage.total_tokens,
            cost=response.cost.display_cost,
            simulated=True,
        )

    def _synthesize_output(
        self,
        lead: LeadIn,
        available_context: dict | None,
        response: ModelResponse,
    ) -> ResearchAgentOutput:
        """Produce the structured research output deterministically.

        The model response is **not** read here as evidence — it is only
        used to populate the metadata block on the result.
        """

        context: dict[str, Any] = available_context or {}

        summary_candidate = (
            context.get("company_summary")
            or context.get("recommended_research_summary")
        )
        raw_signals = context.get("opportunity_signals") or []
        raw_pains = context.get("pain_hypotheses") or []
        raw_cards = context.get("evidence_cards") or []
        raw_context_risks = context.get("information_risks") or []

        # If nothing useful was supplied, return the insufficient-context
        # path with Confidence.LOW and a clear information risk note.
        if not (summary_candidate or raw_signals or raw_pains or raw_cards):
            risks: list[str] = [
                "No company research context was available; the research "
                "agent could not synthesise evidence for this lead."
            ]
            # Carry any context-supplied risks even when the rest of the
            # context was empty (defensive, but covers odd shapes).
            for entry in raw_context_risks:
                if isinstance(entry, str) and entry.strip():
                    risks.append(entry)

            return ResearchAgentOutput(
                result=AgentContractResult(
                    success=True,
                    metadata=self._metadata_from_response(response),
                    error=None,
                ),
                lead_id=lead.lead_id,
                company_summary=_INSUFFICIENT_SUMMARY,
                opportunity_signals=[],
                pain_hypotheses=[],
                evidence_cards=[],
                information_risks=risks,
                confidence=Confidence.LOW,
            )

        summary = (
            summary_candidate
            if isinstance(summary_candidate, str) and summary_candidate.strip()
            else _INSUFFICIENT_SUMMARY
        )

        opportunity_signals: list[str] = []
        for entry in raw_signals:
            text = _stringify_signal(entry)
            if text and text.strip():
                opportunity_signals.append(text)

        pain_hypotheses: list[str] = []
        for entry in raw_pains:
            text = _stringify_pain(entry)
            if text and text.strip():
                pain_hypotheses.append(text)

        evidence_cards: list[EvidenceCard] = []
        for idx, entry in enumerate(raw_cards, start=1):
            evidence_cards.append(_evidence_card_from_demo(lead.lead_id, idx, entry))

        information_risks: list[str] = []
        for entry in raw_context_risks:
            if isinstance(entry, str) and entry.strip():
                information_risks.append(entry)
        for field_name, value in (
            ("industry", lead.industry),
            ("country", lead.country),
            ("website", lead.website),
        ):
            if _is_blank(value):
                note = (
                    f"Lead is missing '{field_name}'; downstream "
                    f"qualification confidence will be reduced."
                )
                if note not in information_risks:
                    information_risks.append(note)

        confidence = _confidence_from_evidence_counts(
            signal_count=len(opportunity_signals),
            evidence_count=len(evidence_cards),
        )

        return ResearchAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=self._metadata_from_response(response),
                error=None,
            ),
            lead_id=lead.lead_id,
            company_summary=summary,
            opportunity_signals=opportunity_signals,
            pain_hypotheses=pain_hypotheses,
            evidence_cards=evidence_cards,
            information_risks=information_risks,
            confidence=confidence,
        )

    # --------------------------------------------------------------------- #
    # Public entry point                                                    #
    # --------------------------------------------------------------------- #
    def run(self, agent_input: ResearchAgentInput) -> ResearchAgentOutput:
        try:
            request = self._build_model_request(agent_input)
            # MockModelService output is intentionally not used as evidence in 5.5A.
            # In 5.5B, when a real provider is wired in, this output will become
            # the primary source of research synthesis.
            response = self.model_service.complete(request)
            return self._synthesize_output(
                lead=agent_input.lead,
                available_context=agent_input.available_context,
                response=response,
            )
        except Exception as exc:  # noqa: BLE001 — agent must never raise
            fallback_metadata = AgentExecutionMetadata(
                agent_name=_AGENT_NAME,
                run_mode=RunMode.SIMULATION,
                model=_MOCK_MODEL_NAME,
                prompt_version=_PROMPT_VERSION,
                latency="0ms",
                tokens=0,
                cost="$0.0000",
                simulated=True,
            )
            return ResearchAgentOutput(
                result=AgentContractResult(
                    success=False,
                    metadata=fallback_metadata,
                    error=AgentError(
                        code="research_agent_error",
                        message=str(exc),
                        recoverable=True,
                    ),
                ),
                lead_id=agent_input.lead.lead_id,
                company_summary="Research agent failed safely.",
                opportunity_signals=[],
                pain_hypotheses=[],
                evidence_cards=[],
                information_risks=[
                    "Research agent failed before producing evidence."
                ],
                confidence=Confidence.LOW,
            )


__all__ = ["ResearchAgentService"]
