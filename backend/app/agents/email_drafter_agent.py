"""Email Drafter Agent service (Phase 5.8).

Fourth executable individual agent service for LeadForge. Transforms an
``EmailDrafterAgentInput`` (lead + research + strategy context) into a
reviewable outbound email **draft** carrying subject, body,
personalization notes, and a confidence label.

Phase 5.8 ships both:

* the deterministic foundation (always available; no model service
  call), and
* the optional Groq structured-synthesis path (only used when
  ``use_model_synthesis=True`` AND the model service is a real,
  non-simulated provider). The pattern matches Phase 5.5C / 5.6B /
  5.7: the deterministic baseline runs first and is always the safe
  fallback; the LLM may only refine within explicit guardrails and a
  strict JSON schema.

Hard rules for this module:

* **Draft only — never send.** No SMTP, no email transport client, no
  CRM delivery. No symbol named ``send``, ``deliver``, ``transport``,
  ``smtp`` exists in this module.
* No real LLM call by default. ``MockModelService`` is the constructor
  default and is treated as a simulated provider — its content is
  never consumed as evidence.
* No network I/O. No imports from ``requests`` / ``httpx`` / ``urllib``
  / ``aiohttp`` / ``smtplib`` / ``email.mime`` / any provider client.
  No imports from other agent modules.
* No LangGraph, no Chroma/RAG, no scraping, no DB writes, no live web
  research.
* No raw model response is ever embedded in error messages, fallback
  notes, or any text-bearing output field.

Public surface:

* :class:`EmailDrafterAgentService`
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    EmailDrafterAgentInput,
    EmailDrafterAgentOutput,
)
from app.schemas.common import Confidence, RunMode
from app.schemas.email_synthesis import EmailDraftSynthesisPayload
from app.schemas.lead import LeadIn
from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
)
from app.services.json_utils import extract_json_object
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "email_drafter_agent"
_PROMPT_VERSION: str = "email_drafter_agent_deterministic_v1"
_PROMPT_VERSION_GROQ_JSON: str = "email_drafter_agent_groq_json_v1"
_PROMPT_VERSION_GROQ_JSON_FALLBACK: str = (
    "email_drafter_agent_groq_json_v1_fallback"
)
_MODEL_NAME: str = "none"
_GROQ_EMAIL_DRAFTER_MODEL_NAME: str = "llama-3.1-8b-instant"

# --------------------------------------------------------------------------- #
# Phase 5.8 STEP 6 — Guardrail keyword tables                                 #
#                                                                             #
# All matches are case-insensitive. Multi-word phrases are preferred so       #
# legitimate B2B language ("help your team scale hiring") does not trip       #
# false fallbacks. The few single-word entries (e.g. "guaranteed",            #
# "unsubscribe") are only present where the standalone word itself            #
# unambiguously signals a problem in a Phase 5.8 reviewable draft.            #
# --------------------------------------------------------------------------- #
_FORBIDDEN_LIVE_RESEARCH_PHRASES: tuple[str, ...] = (
    "we found on your website",
    "according to your website",
    "we saw online",
    "we noticed online",
    "according to news",
    "recent news about",
    "recent announcement about",
    "your recent funding",
    "we noticed you're hiring",
    "we noticed youre hiring",
    "we read that you",
    "we found online",
    "i found online",
)

# Per Phase 5.8 FIX 2 — concrete keyword list for "manipulative urgency".
# These have no legitimate place in a Phase 5.8 reviewable draft for any
# lead, so the guardrail is unconditional (the original FIX 2 spec
# qualified this by priority / fit_score, but the Phase 5.2 contract
# does not expose those fields to EmailDrafterAgentInput; tightening the
# rule to "always reject" is the safer, contract-compatible default).
_MANIPULATIVE_URGENCY_PHRASES: tuple[str, ...] = (
    "act now",
    "limited time",
    "last chance",
    "final notice",
    "why wait",
    "don't miss",
    "do not miss",
    "you need to act",
    "missing out",
    "don't let this pass",
    "do not let this pass",
)

# Per Phase 5.8 FIX 2 — concrete keyword list for "guaranteed outcomes".
_GUARANTEED_OUTCOME_PHRASES: tuple[str, ...] = (
    "guaranteed",
    "will definitely",
    "100% certain",
    "we promise you",
    "you will see results",
    "proven to increase",
)

# Phrases / markers that imply the draft was already sent or carries
# transport metadata.
_SENT_OR_DELIVERY_MARKERS: tuple[str, ...] = (
    "this email was sent",
    "sent on behalf of",
    "delivered via",
    "message-id:",
    "x-mailer",
    "envelope-from",
    "smtp",
    "unsubscribe",
)

# Raw model-response markers that must never appear in output text.
_RAW_MODEL_MARKERS: tuple[str, ...] = (
    "[mock model response",
    "[raw model output",
)

# Clickbait / spam keywords for subject-line guardrail.
_SPAMMY_SUBJECT_PHRASES: tuple[str, ...] = (
    "urgent",
    "final notice",
    "last chance",
    "guaranteed",
    "free money",
    "you won",
)

_GUARDRAIL_FALLBACK_RISK_NOTE: str = (
    "LLM email draft failed validation or guardrails; deterministic "
    "fallback used."
)

_SYNTHESIS_SYSTEM_PROMPT: str = (
    "You are LeadForge Email Drafter Agent running in Phase 5.8 "
    "structured synthesis mode.\n"
    "\n"
    "Return ONLY a valid JSON object with this exact schema, no markdown:\n"
    "{\n"
    '  "email_subject": "string",\n'
    '  "email_body": "string",\n'
    '  "personalization_notes": ["string"],\n'
    '  "confidence": "high|medium|low"\n'
    "}\n"
    "\n"
    "Rules:\n"
    "- Generate a reviewable outbound sales email draft only.\n"
    "- Do not send email.\n"
    "- Do not include delivery, SMTP, or unsubscribe metadata.\n"
    "- Use only the provided lead, research, qualifier and strategy "
    "context.\n"
    "- Do not use live web research.\n"
    "- Do not invent facts.\n"
    "- Do not claim public sources, funding rounds, hiring news, "
    "customer lists, tech stack, or external announcements.\n"
    "- Keep tone professional, human, concise and low-pressure.\n"
    "- No manipulative urgency (no 'act now', 'last chance', 'don't "
    "miss', etc.).\n"
    "- No exaggerated promises (no 'guaranteed', 'will definitely', "
    "'100% certain', etc.).\n"
    "- No spammy formatting.\n"
    "- No fake personalization.\n"
    "- If context is limited, keep the email exploratory.\n"
    "\n"
    "email_body should be 3 to 5 paragraphs, approximately 200 to 400 "
    "words. Keep it professional and concise."
)


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _is_blank(value: str | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _first_name(contact_name: str | None) -> str:
    if not contact_name or not contact_name.strip():
        return "there"
    return contact_name.strip().split()[0]


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


# --------------------------------------------------------------------------- #
# Deterministic baseline                                                      #
# --------------------------------------------------------------------------- #
class _DeterministicBaseline:
    """Bundle of the deterministic email-drafter baseline.

    Mirrors :class:`EmailDrafterAgentOutput` (minus the contract envelope)
    so the synthesis path can convert it into the output type via a
    single helper.
    """

    __slots__ = (
        "email_subject",
        "email_body",
        "personalization_notes",
        "confidence",
    )

    def __init__(
        self,
        *,
        email_subject: str,
        email_body: str,
        personalization_notes: list[str],
        confidence: Confidence,
    ) -> None:
        self.email_subject = email_subject
        self.email_body = email_body
        self.personalization_notes = personalization_notes
        self.confidence = confidence


_SOFT_CTA: str = "Would it be worth a quick look?"
_LIMITED_CONTEXT_NOTE: str = (
    "Keep this draft exploratory because available context is limited."
)
_GENERIC_PAIN_MARKER: str = "fragmented prospecting"  # from Strategist baseline
_INSUFFICIENT_MARKER: str = "insufficient"


def _baseline_subject(lead: LeadIn) -> str:
    if not _is_blank(lead.company_name):
        subject = f"Idea for {lead.company_name}"
    else:
        subject = "Idea for your team"
    return subject[:120]


def _baseline_body(
    lead: LeadIn,
    company_summary: str,
    pain_hypothesis: str,
    sales_angle: str,
    core_message: str,
) -> str:
    """Render a 3–5 paragraph deterministic email body."""

    first_name = _first_name(lead.contact_name)
    company = lead.company_name if not _is_blank(lead.company_name) else "your team"

    has_summary = bool(company_summary and company_summary.strip())
    summary_clause = (
        f"Reading the context we already have on {company}, "
        "the picture suggests an opportunity to streamline how the "
        "team handles prospecting and qualification."
    ) if has_summary else (
        f"We do not yet have a lot of public context on {company}, "
        "so I'm reaching out to learn more rather than to pitch."
    )

    paragraphs = [
        f"Hi {first_name},",
        (
            f"I'm reaching out because of how teams at companies "
            f"like {company} tend to spend disproportionate time on "
            "lead research and qualification before any outreach goes out."
        ),
        summary_clause,
        (
            f"{pain_hypothesis.strip()} {sales_angle.strip()} "
            f"{core_message.strip()}"
        ).strip(),
        (
            f"{_SOFT_CTA} Happy to share a short example tailored to "
            f"{company}, or skip it entirely if this isn't a fit."
        ),
        "— LeadForge (draft for review)",
    ]
    body = "\n\n".join(paragraphs)
    # Hard cap below the schema's 1800-char limit so the deterministic
    # path always validates if the synthesis schema is ever applied.
    if len(body) > 1700:
        body = body[:1697] + "..."
    return body


def _baseline_personalization_notes(
    agent_input: EmailDrafterAgentInput,
    context_limited: bool,
) -> list[str]:
    """Build 1–5 deterministic personalization notes.

    Starts from the strategist-supplied notes (deduped, truncated to 5)
    and appends a conservative exploratory note when the context is
    limited. Always returns at least 1 note so downstream callers
    never see an empty list.
    """

    notes: list[str] = []
    for note in agent_input.personalization_notes:
        if isinstance(note, str) and note.strip() and note not in notes:
            notes.append(note)
        if len(notes) >= 5:
            break

    if context_limited and _LIMITED_CONTEXT_NOTE not in notes and len(notes) < 5:
        notes.append(_LIMITED_CONTEXT_NOTE)

    if not notes:
        notes.append(_LIMITED_CONTEXT_NOTE)

    return notes


def _baseline_confidence(
    agent_input: EmailDrafterAgentInput, context_limited: bool
) -> Confidence:
    has_summary = bool(
        agent_input.company_summary and agent_input.company_summary.strip()
    )
    has_pain = bool(agent_input.pain_hypothesis and agent_input.pain_hypothesis.strip())
    has_angle = bool(agent_input.sales_angle and agent_input.sales_angle.strip())
    has_message = bool(agent_input.core_message and agent_input.core_message.strip())
    notes_count = sum(
        1 for n in agent_input.personalization_notes
        if isinstance(n, str) and n.strip()
    )

    if context_limited:
        return Confidence.LOW
    if has_summary and has_pain and has_angle and has_message and notes_count >= 2:
        return Confidence.HIGH
    if has_pain or has_angle or has_message:
        return Confidence.MEDIUM
    return Confidence.LOW


def _is_context_limited(agent_input: EmailDrafterAgentInput) -> bool:
    """Heuristic: the strategist's deterministic fallback path used
    generic phrases like 'fragmented prospecting' or 'Insufficient
    safe context', so detecting either marker tells us the upstream
    context was thin.
    """

    text_blob = " ".join(
        [
            (agent_input.pain_hypothesis or ""),
            (agent_input.sales_angle or ""),
            (agent_input.core_message or ""),
        ]
    ).lower()
    if not agent_input.company_summary or not agent_input.company_summary.strip():
        return True
    if _GENERIC_PAIN_MARKER in text_blob:
        return True
    if _INSUFFICIENT_MARKER in text_blob:
        return True
    return False


def _compute_baseline(
    agent_input: EmailDrafterAgentInput,
) -> _DeterministicBaseline:
    context_limited = _is_context_limited(agent_input)
    return _DeterministicBaseline(
        email_subject=_baseline_subject(agent_input.lead),
        email_body=_baseline_body(
            agent_input.lead,
            agent_input.company_summary,
            agent_input.pain_hypothesis,
            agent_input.sales_angle,
            agent_input.core_message,
        ),
        personalization_notes=_baseline_personalization_notes(
            agent_input, context_limited
        ),
        confidence=_baseline_confidence(agent_input, context_limited),
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
class EmailDrafterAgentService:
    """Deterministic-first email drafter with optional Groq synthesis."""

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
        self, agent_input: EmailDrafterAgentInput
    ) -> EmailDrafterAgentOutput:
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
    ) -> EmailDrafterAgentOutput:
        notes = list(baseline.personalization_notes)
        if extra_note and extra_note not in notes:
            notes.append(extra_note)
        return EmailDrafterAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=metadata,
                error=None,
            ),
            # Explicit lead_id wiring (mirrors Phase 5.7 FIX 2 discipline).
            lead_id=lead_id,
            email_subject=baseline.email_subject,
            email_body=baseline.email_body,
            personalization_notes=notes,
            confidence=baseline.confidence,
        )

    def _payload_to_output(
        self,
        lead_id: str,
        payload: EmailDraftSynthesisPayload,
        response: ModelResponse,
    ) -> EmailDrafterAgentOutput:
        return EmailDrafterAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=_synthesis_metadata(
                    response,
                    prompt_version=_PROMPT_VERSION_GROQ_JSON,
                    simulated=False,
                ),
                error=None,
            ),
            lead_id=lead_id,
            email_subject=payload.email_subject,
            email_body=payload.email_body,
            personalization_notes=list(payload.personalization_notes),
            confidence=payload.confidence,
        )

    def _fallback_with_response(
        self,
        lead_id: str,
        baseline: _DeterministicBaseline,
        response: ModelResponse,
    ) -> EmailDrafterAgentOutput:
        return self._output_from_baseline(
            lead_id,
            baseline,
            _synthesis_metadata(
                response,
                prompt_version=_PROMPT_VERSION_GROQ_JSON_FALLBACK,
                simulated=True,
            ),
            extra_note=_GUARDRAIL_FALLBACK_RISK_NOTE,
        )

    def _safe_failure_output(
        self, lead_id: str, exc: Exception
    ) -> EmailDrafterAgentOutput:
        """Phase 5.8 FIX 3: the error fallback returns
        ``personalization_notes=[]`` directly to the agent output. This
        bypasses ``EmailDraftSynthesisPayload`` (which requires
        ``min_length=1``) — the synthesis schema is only for validating
        LLM-produced payloads, not for shaping the agent's own safe
        failure output. ``EmailDrafterAgentOutput.personalization_notes``
        itself has no ``min_length`` constraint.
        """

        return EmailDrafterAgentOutput(
            result=AgentContractResult(
                success=False,
                metadata=_deterministic_metadata(),
                error=AgentError(
                    code="email_drafter_agent_error",
                    message=str(exc),
                    recoverable=True,
                ),
            ),
            lead_id=lead_id,
            email_subject="Manual review required",
            email_body=(
                "Insufficient safe context to generate a reviewable "
                "email draft."
            ),
            personalization_notes=[],
            confidence=Confidence.LOW,
        )

    # ------------------------------------------------------------------- #
    # Synthesis path                                                      #
    # ------------------------------------------------------------------- #
    def _build_synthesis_request(
        self,
        agent_input: EmailDrafterAgentInput,
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
            "pain_hypothesis": agent_input.pain_hypothesis,
            "sales_angle": agent_input.sales_angle,
            "core_message": agent_input.core_message,
            "personalization_notes": list(agent_input.personalization_notes),
            "baseline": {
                "email_subject": baseline.email_subject,
                "email_body": baseline.email_body,
                "personalization_notes": baseline.personalization_notes,
                "confidence": baseline.confidence.value,
            },
        }
        user_content = (
            "Refine the deterministic baseline email draft for the "
            "following lead, using ONLY the provided context. Respond "
            "with valid JSON matching the schema in the system message.\n\n"
            "email_body should be 3 to 5 paragraphs, approximately 200 "
            "to 400 words. Keep it professional and concise.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

        config = ModelConfig(
            provider=ModelProvider.GROQ,
            model_name=_GROQ_EMAIL_DRAFTER_MODEL_NAME,
            max_tokens=1024,
        )
        return ModelRequest(
            messages=[
                ModelMessage(role=ModelRole.SYSTEM, content=_SYNTHESIS_SYSTEM_PROMPT),
                ModelMessage(role=ModelRole.USER, content=user_content),
            ],
            config=config,
            request_id=(
                f"email_drafter_agent_synthesis::{agent_input.run_id}::{lead.lead_id}"
                if agent_input.run_id
                else f"email_drafter_agent_synthesis::{lead.lead_id}"
            ),
        )

    def _validate_payload(self, content: str) -> EmailDraftSynthesisPayload:
        payload_dict = extract_json_object(content)
        try:
            return EmailDraftSynthesisPayload.model_validate(payload_dict)
        except ValidationError as exc:
            raise ValueError(
                "Model response failed EmailDraftSynthesisPayload "
                f"validation: {exc}"
            ) from exc

    def _apply_guardrails(
        self, payload: EmailDraftSynthesisPayload
    ) -> EmailDraftSynthesisPayload:
        """Enforce the Phase 5.8 STEP 6 + FIX 2 guardrails.

        Raises ``ValueError`` on any violation so the caller routes to
        the deterministic fallback. No raw model text is included in
        the exception message — only a short, generic label.
        """

        text_fields = (
            payload.email_subject,
            payload.email_body,
            *payload.personalization_notes,
        )

        # Live-research / fake-external-claim phrases (any field).
        for field_text in text_fields:
            if _contains_any(field_text, _FORBIDDEN_LIVE_RESEARCH_PHRASES):
                raise ValueError(
                    "LLM email draft includes a forbidden live-research "
                    "phrase."
                )

        # Subject-line guardrails.
        if _contains_any(payload.email_subject, _SPAMMY_SUBJECT_PHRASES):
            raise ValueError(
                "LLM email subject contains a spammy / clickbait keyword."
            )

        # Body guardrails.
        body = payload.email_body
        if _contains_any(body, _SENT_OR_DELIVERY_MARKERS):
            raise ValueError(
                "LLM email body implies the email was sent or carries "
                "delivery metadata."
            )
        if _contains_any(body, _RAW_MODEL_MARKERS):
            raise ValueError(
                "LLM email body contains a raw model-response marker."
            )
        if _contains_any(body, _MANIPULATIVE_URGENCY_PHRASES):
            raise ValueError(
                "LLM email body uses manipulative urgency phrasing."
            )
        if _contains_any(body, _GUARANTEED_OUTCOME_PHRASES):
            raise ValueError(
                "LLM email body claims guaranteed outcomes."
            )

        return payload

    def _run_with_model_synthesis(
        self,
        agent_input: EmailDrafterAgentInput,
        baseline: _DeterministicBaseline,
    ) -> EmailDrafterAgentOutput:
        request = self._build_synthesis_request(agent_input, baseline)
        response = self.model_service.complete(request)

        # Simulated response: content is not consumed; return the
        # deterministic baseline (mock or any future simulated provider).
        if response.simulated:
            return self._output_from_baseline(
                agent_input.lead.lead_id, baseline, _deterministic_metadata()
            )

        try:
            payload = self._validate_payload(response.content)
            approved = self._apply_guardrails(payload)
        except ValueError:
            return self._fallback_with_response(
                agent_input.lead.lead_id, baseline, response
            )

        return self._payload_to_output(
            agent_input.lead.lead_id, approved, response
        )


__all__ = ["EmailDrafterAgentService"]
