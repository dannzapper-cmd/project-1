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

import json
from typing import Any

from pydantic import ValidationError

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
from app.schemas.research_synthesis import (
    ResearchSynthesisEvidence,
    ResearchSynthesisPayload,
)
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "research_agent"
_PROMPT_VERSION: str = "research_agent_mock_v1"
_PROMPT_VERSION_GROQ_JSON: str = "research_agent_groq_json_v1"
_PROMPT_VERSION_GROQ_JSON_FALLBACK: str = "research_agent_groq_json_v1_fallback"
_MOCK_MODEL_NAME: str = "mock-research-agent"
_SYSTEM_PROMPT: str = (
    "You are LeadForge Research Agent running in Phase 5.5A mock mode. "
    "Do not invent sources."
)
_INSUFFICIENT_SUMMARY: str = (
    "Insufficient context available; no synthesised research is "
    "produced for this lead."
)

# Phase 5.5C structured-synthesis system prompt (FIX 5). The JSON schema
# is included verbatim so the model has the exact field shape and
# Pydantic v2 validation does not reject responses for missing/renamed
# fields.
_SYNTHESIS_SYSTEM_PROMPT: str = (
    "You are LeadForge Research Agent running in Phase 5.5C structured "
    "synthesis mode.\n"
    "\n"
    "Hard rules:\n"
    "- Do not use live web research.\n"
    "- Do not invent facts, sources, public claims, or live research.\n"
    "- Use only the provided lead fields and available_context.\n"
    "- Summarise and structure the provided context; do not extend it.\n"
    "\n"
    "Return ONLY a valid JSON object with this exact schema, no markdown:\n"
    "{\n"
    '  "company_summary": "string (required)",\n'
    '  "opportunity_signals": ["string", ...],\n'
    '  "pain_hypotheses": ["string", ...],\n'
    '  "evidence_cards": [{"headline": "string",\n'
    '                       "description": "string",\n'
    '                       "confidence": "low|medium|high"}],\n'
    '  "information_risks": ["string", ...],\n'
    '  "confidence": "low|medium|high"\n'
    "}"
)
_EVIDENCE_PROVENANCE_NOTE: str = (
    "[LLM structured synthesis from provided demo context only]"
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
# Phase 5.5C — JSON parsing / validation helpers                              #
# --------------------------------------------------------------------------- #
def extract_json_object(text: str) -> dict:
    """Best-effort JSON-object extraction from an LLM response (FIX 2).

    Three explicit attempts, in order, with stdlib ``json`` only — no
    regex, no ``eval``, no ``ast.literal_eval``, no YAML, no third-party
    parsers:

    1. ``json.loads(text)`` on the stripped string.
    2. If the string contains markdown code fences, strip them (and an
       optional ``json`` language tag) and try again.
    3. Take the substring from the first ``{`` to the last ``}`` and
       try ``json.loads`` on that.

    Raises
    ------
    ValueError
        If none of the three attempts produces a JSON object.
    """

    text = text.strip()

    # Attempt 1: parse the whole response.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: strip markdown code fences (with optional `json` tag).
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start < end:
            inner = text[start + 3 : end].strip()
            if inner.startswith("json"):
                inner = inner[4:].strip()
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                pass

    # Attempt 3: first { to last }.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON object found in model response.")


def validate_research_synthesis_payload(text: str) -> ResearchSynthesisPayload:
    """Extract + validate a structured-research payload from a model response.

    Returns the validated :class:`ResearchSynthesisPayload`. Raises
    ``ValueError`` if extraction or validation fails (the agent layer
    converts that into the safe deterministic fallback path).
    """

    payload_dict = extract_json_object(text)
    try:
        return ResearchSynthesisPayload.model_validate(payload_dict)
    except ValidationError as exc:
        # Keep the raised message generic — the original model response
        # is never included here, only the validator diagnostics, which
        # are derived from the parsed structure (not from raw text).
        raise ValueError(
            f"Model response failed ResearchSynthesisPayload validation: {exc}"
        ) from exc


# --------------------------------------------------------------------------- #
# Service                                                                     #
# --------------------------------------------------------------------------- #
class ResearchAgentService:
    """Executable Research Agent backed by the model service abstraction.

    Phase 5.5C adds the optional ``use_model_synthesis`` flag. Behaviour:

    * ``use_model_synthesis=False`` (default) — Phase 5.5A behaviour is
      preserved exactly. The mock model service is called only to fill
      in metadata; output is synthesised deterministically from the
      lead and ``available_context``.
    * ``use_model_synthesis=True`` — the model service is called, and:
        * If its response carries ``simulated=True`` (e.g. the mock
          service), the mock content is **not** consumed as evidence;
          the deterministic path runs instead.
        * If the response carries ``simulated=False`` (e.g. a real
          ``GroqModelService`` call), the response content is parsed
          as a strict ``ResearchSynthesisPayload``; on success the
          payload becomes the agent output, on failure a deterministic
          fallback is returned with a clear information risk note.
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
    # Phase 5.5C — Structured-synthesis helpers                             #
    # --------------------------------------------------------------------- #
    def _build_synthesis_request(
        self, agent_input: ResearchAgentInput
    ) -> ModelRequest:
        """Build the strict-JSON ModelRequest used by the Groq path."""

        lead = agent_input.lead
        context_payload: dict[str, Any] = {
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
            "available_context": agent_input.available_context or {},
        }
        user_content = (
            "Synthesise a research summary for the following lead, "
            "using ONLY the provided context. Respond with valid JSON "
            "matching the schema described in the system message.\n\n"
            f"{json.dumps(context_payload, ensure_ascii=False, indent=2)}"
        )

        config = ModelConfig(
            provider=ModelProvider.GROQ,
            model_name="llama-3.1-8b-instant",
        )
        return ModelRequest(
            messages=[
                ModelMessage(role=ModelRole.SYSTEM, content=_SYNTHESIS_SYSTEM_PROMPT),
                ModelMessage(role=ModelRole.USER, content=user_content),
            ],
            config=config,
            request_id=(
                f"research_agent_synthesis::{agent_input.run_id}::{lead.lead_id}"
                if agent_input.run_id
                else f"research_agent_synthesis::{lead.lead_id}"
            ),
        )

    def _synthesis_metadata(
        self,
        response: ModelResponse,
        *,
        prompt_version: str,
        simulated: bool,
    ) -> AgentExecutionMetadata:
        """Build the metadata block for the structured-synthesis path.

        Phase 5.5C FIX 6: ``run_mode`` is always ``RunMode.SIMULATION``;
        ``RunMode.LIVE`` is reserved for a future orchestration phase.
        Phase 5.5C FIX 1: ``simulated`` reflects the data's origin (was
        the validated payload actually used?), not whether a network
        call occurred.
        """

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

    def _payload_to_output(
        self,
        lead: LeadIn,
        payload: ResearchSynthesisPayload,
        response: ModelResponse,
    ) -> ResearchAgentOutput:
        """Project a validated synthesis payload onto ``ResearchAgentOutput``."""

        evidence_cards: list[EvidenceCard] = []
        for idx, entry in enumerate(payload.evidence_cards, start=1):
            description = (
                f"{entry.description} {_EVIDENCE_PROVENANCE_NOTE}".strip()
            )
            evidence_cards.append(
                EvidenceCard(
                    id=f"{lead.lead_id}_synthesis_evidence_{idx:02d}",
                    headline=entry.headline,
                    # Phase 5.5C honesty rule: source is always
                    # DEMO_CONTEXT; the LLM only summarises context the
                    # agent already had.
                    source_type=EvidenceSource.DEMO_CONTEXT,
                    description=description,
                    confidence=entry.confidence,
                )
            )

        return ResearchAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=self._synthesis_metadata(
                    response,
                    prompt_version=_PROMPT_VERSION_GROQ_JSON,
                    # FIX 1: simulated=False ONLY when the validated
                    # payload is actually used as the output source.
                    simulated=False,
                ),
                error=None,
            ),
            lead_id=lead.lead_id,
            company_summary=payload.company_summary,
            opportunity_signals=list(payload.opportunity_signals),
            pain_hypotheses=list(payload.pain_hypotheses),
            evidence_cards=evidence_cards,
            information_risks=list(payload.information_risks),
            confidence=payload.confidence,
        )

    def _deterministic_output_with_response(
        self,
        agent_input: ResearchAgentInput,
        response: ModelResponse,
        *,
        prompt_version: str,
        extra_risk: str | None = None,
    ) -> ResearchAgentOutput:
        """Deterministic synthesis re-using the metadata of an existing model call.

        Used by the Groq path when JSON validation fails. The metadata's
        ``simulated`` is set to ``True`` (per FIX 1: the output's data
        origin is deterministic regardless of whether a network call
        was made). When supplied, ``extra_risk`` is appended to
        ``information_risks``.
        """

        deterministic = self._synthesize_output(
            lead=agent_input.lead,
            available_context=agent_input.available_context,
            response=response,
        )
        deterministic.result.metadata = self._synthesis_metadata(
            response,
            prompt_version=prompt_version,
            simulated=True,
        )
        if extra_risk and extra_risk not in deterministic.information_risks:
            deterministic.information_risks = list(deterministic.information_risks) + [
                extra_risk
            ]
        return deterministic

    # --------------------------------------------------------------------- #
    # Phase 5.5C — Structured-synthesis entry path                          #
    # --------------------------------------------------------------------- #
    def _run_with_model_synthesis(
        self, agent_input: ResearchAgentInput
    ) -> ResearchAgentOutput:
        """Optional path: call the model service for structured synthesis.

        Honesty rule (FIX 3): if the response is marked ``simulated``
        (e.g. ``MockModelService``), the mock content is NOT consumed;
        the deterministic Phase 5.5A path runs instead. This works for
        every future provider that sets ``simulated=True`` without the
        agent needing to know the concrete class.
        """

        request = self._build_synthesis_request(agent_input)
        response = self.model_service.complete(request)

        if response.simulated:
            # Simulated response → do not consume content as evidence.
            # Re-run the deterministic Phase 5.5A path so the agent
            # still produces a useful output.
            return self._synthesize_output(
                lead=agent_input.lead,
                available_context=agent_input.available_context,
                response=response,
            )

        try:
            payload = validate_research_synthesis_payload(response.content)
        except ValueError:
            # Raw model content is intentionally NOT included in the
            # fallback risk note (it might contain unverified claims).
            return self._deterministic_output_with_response(
                agent_input,
                response,
                prompt_version=_PROMPT_VERSION_GROQ_JSON_FALLBACK,
                extra_risk=(
                    "LLM synthesis failed validation; deterministic "
                    "fallback used."
                ),
            )

        return self._payload_to_output(agent_input.lead, payload, response)

    # --------------------------------------------------------------------- #
    # Public entry point                                                    #
    # --------------------------------------------------------------------- #
    def run(self, agent_input: ResearchAgentInput) -> ResearchAgentOutput:
        try:
            if self.use_model_synthesis:
                return self._run_with_model_synthesis(agent_input)
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
            # Deliberately use a generic error message — no raw model
            # response or prompt text is ever leaked here.
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


__all__ = [
    "ResearchAgentService",
    "extract_json_object",
    "validate_research_synthesis_payload",
]
