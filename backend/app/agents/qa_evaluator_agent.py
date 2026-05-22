"""QA Evaluator Agent service (Phase 5.9).

Fifth executable individual agent service for LeadForge. Evaluates the
quality, safety, reliability, and review-readiness of the generated
pipeline output for a single lead: the lead row, the evidence the
Research Agent gathered, and the email draft the Email Drafter
produced.

Phase 5.9 ships both:

* the deterministic foundation (always available; no model service
  call), and
* the optional Groq structured-synthesis path (only used when
  ``use_model_synthesis=True`` AND the model service is a real,
  non-simulated provider). The deterministic baseline runs first and
  is always the safe fallback; the LLM may only refine within explicit
  safety guardrails and a strict JSON schema.

Hard rules for this module:

* **Evaluate only — never rewrite, never send.** No SMTP, no email
  transport, no CRM delivery. No symbol named ``send`` / ``deliver`` /
  ``transport`` / ``smtp`` is exposed at the module level.
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

* :class:`QAEvaluatorAgentService`
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.schemas.agents import (
    AgentContractResult,
    AgentError,
    AgentExecutionMetadata,
    QAEvaluatorAgentInput,
    QAEvaluatorAgentOutput,
)
from app.schemas.common import HallucinationRisk, Recommendation, RunMode
from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
)
from app.schemas.qa import QAScores
from app.schemas.qa_synthesis import QAEvaluatorSynthesisPayload
from app.services.json_utils import extract_json_object
from app.services.model_service import BaseModelService, get_model_service

_AGENT_NAME: str = "qa_evaluator_agent"
_PROMPT_VERSION: str = "qa_evaluator_agent_deterministic_v1"
_PROMPT_VERSION_GROQ_JSON: str = "qa_evaluator_agent_groq_json_v1"
_PROMPT_VERSION_GROQ_JSON_FALLBACK: str = (
    "qa_evaluator_agent_groq_json_v1_fallback"
)
_MODEL_NAME: str = "none"
_GROQ_QA_MODEL_NAME: str = "llama-3.1-8b-instant"

# Phase 5.6B FIX 3 / 5.9 guardrails — LLM may not exceed deterministic
# baseline qa_score by more than this delta.
_MAX_LLM_SCORE_UPGRADE: int = 15

# --------------------------------------------------------------------------- #
# Hard-safety phrase tables                                                   #
#                                                                             #
# Matches are case-insensitive. The Email Drafter agent enforces the same    #
# phrases on its own output; the QA Evaluator's job is to catch anything    #
# that slips through.                                                        #
# --------------------------------------------------------------------------- #
_LIVE_RESEARCH_PHRASES: tuple[str, ...] = (
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

_GUARANTEED_OUTCOME_PHRASES: tuple[str, ...] = (
    "guaranteed",
    "will definitely",
    "100% certain",
    "we promise you",
    "you will see results",
    "proven to increase",
)

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

_RAW_MODEL_MARKERS: tuple[str, ...] = (
    "[mock model response",
    "[raw model output",
)

_SOFT_CTA_PHRASES: tuple[str, ...] = (
    "would it be worth",
    "open to seeing",
    "happy to share",
    "happy to walk through",
    "open to a quick chat",
    "any interest in",
)

_GUARDRAIL_FALLBACK_RISK_NOTE: str = (
    "LLM QA evaluation failed validation or guardrails; deterministic "
    "fallback used."
)

# Recommendation/risk permissiveness ranks for guardrail comparison.
_REC_RANK: dict[Recommendation, int] = {
    Recommendation.REGENERATE: 0,  # least permissive
    Recommendation.REVIEW: 1,
    Recommendation.APPROVE: 2,     # most permissive
}
_RISK_RANK: dict[HallucinationRisk, int] = {
    HallucinationRisk.LOW: 0,
    HallucinationRisk.MEDIUM: 1,
    HallucinationRisk.HIGH: 2,
}

_SYNTHESIS_SYSTEM_PROMPT: str = (
    "You are LeadForge QA Evaluator Agent running in Phase 5.9 "
    "structured synthesis mode.\n"
    "\n"
    "Return ONLY a valid JSON object with this exact schema, no markdown:\n"
    "{\n"
    '  "qa_score": integer 0-100,\n'
    '  "personalization": integer 0-100,\n'
    '  "evidence_coverage": integer 0-100,\n'
    '  "cta_quality": integer 0-100,\n'
    '  "tone_match": integer 0-100,\n'
    '  "hallucination_risk": "low|medium|high",\n'
    '  "recommendation": "approve|review|regenerate",\n'
    '  "strengths": ["string"],\n'
    '  "risks": ["string"],\n'
    '  "required_fixes": ["string"]\n'
    "}\n"
    "\n"
    "Rules:\n"
    "- Evaluate only the provided context and generated draft.\n"
    "- Do not use live web research.\n"
    "- Do not invent facts.\n"
    "- Do not claim public sources, funding, hiring, customers, tech "
    "stack or news.\n"
    "- Do not rewrite the email.\n"
    "- Do not send email.\n"
    "- Do not approve drafts that claim unsupported facts.\n"
    "- Do not approve drafts with manipulative urgency, guaranteed "
    "outcomes, or delivery metadata.\n"
    "- If context is limited, recommend review rather than approval.\n"
    "- Respect the deterministic baseline: never raise qa_score by "
    "more than 15 points, never make hallucination_risk less severe "
    "when hard violations exist, never make recommendation more "
    "permissive when hard violations exist."
)


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def _is_blank(value: str | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


# --------------------------------------------------------------------------- #
# Deterministic baseline                                                      #
# --------------------------------------------------------------------------- #
class _DeterministicBaseline:
    """Bundle of the deterministic QA result.

    Mirrors :class:`QAEvaluatorAgentOutput` (minus the contract envelope)
    so the synthesis path can convert it into the output type via a
    single helper. Also carries the per-violation booleans so the
    guardrail layer can compare LLM output against the same evidence
    the baseline saw.
    """

    __slots__ = (
        "qa_score",
        "qa_scores",
        "hallucination_risk",
        "recommendation",
        "qa_notes",
        "has_hard_violation",
        "strengths",
        "risks",
        "fixes",
    )

    def __init__(
        self,
        *,
        qa_score: int,
        qa_scores: QAScores,
        hallucination_risk: HallucinationRisk,
        recommendation: Recommendation,
        qa_notes: list[str],
        has_hard_violation: bool,
        strengths: list[str],
        risks: list[str],
        fixes: list[str],
    ) -> None:
        self.qa_score = qa_score
        self.qa_scores = qa_scores
        self.hallucination_risk = hallucination_risk
        self.recommendation = recommendation
        self.qa_notes = qa_notes
        self.has_hard_violation = has_hard_violation
        self.strengths = strengths
        self.risks = risks
        self.fixes = fixes


def _compute_baseline(
    agent_input: QAEvaluatorAgentInput,
) -> _DeterministicBaseline:
    """Deterministic QA scoring from the provided context only.

    Starts at ``qa_score=100`` and subtracts deductions for each
    detected issue. ``hallucination_risk`` and ``recommendation`` are
    derived from the most severe issue detected.
    """

    body = agent_input.email_body or ""
    subject = agent_input.email_subject or ""
    notes_blob = " ".join(
        n for n in agent_input.personalization_notes
        if isinstance(n, str)
    )
    combined_text = body + " " + subject + " " + notes_blob

    has_live_research = _contains_any(combined_text, _LIVE_RESEARCH_PHRASES)
    has_urgency = _contains_any(body, _MANIPULATIVE_URGENCY_PHRASES)
    has_guaranteed = _contains_any(body, _GUARANTEED_OUTCOME_PHRASES)
    has_delivery = _contains_any(body, _SENT_OR_DELIVERY_MARKERS)
    has_raw_marker = _contains_any(combined_text, _RAW_MODEL_MARKERS)
    body_too_short = len(body.strip()) < 50
    no_cta = not _contains_any(body, _SOFT_CTA_PHRASES)

    company = (agent_input.lead.company_name or "").strip()
    body_lower = body.lower()
    has_company_or_team = (
        bool(company and company.lower() in body_lower)
        or "your team" in body_lower
    )
    no_company_or_team = not has_company_or_team

    # Lead-context degradation (informational; does not drive qa_score
    # directly because the email itself is what's being evaluated).
    degraded_lead = (
        _is_blank(agent_input.lead.industry)
        or _is_blank(agent_input.lead.country)
        or agent_input.lead.employee_count is None
    )

    qa_score = 100
    risks: list[str] = []
    fixes: list[str] = []
    strengths: list[str] = []

    if has_live_research:
        qa_score -= 30
        risks.append(
            "Email claims live web research or external facts not present in provided context."
        )
        fixes.append(
            "Remove live-research and external-claim phrasing; rely on demo context only."
        )
    if has_raw_marker:
        qa_score -= 30
        risks.append("Email contains a raw model-response marker.")
        fixes.append("Strip any [MOCK MODEL RESPONSE] / raw model markers from the draft.")
    if body_too_short:
        qa_score -= 30
        risks.append("Email body is too short to review meaningfully.")
        fixes.append("Expand the body to 3–5 short paragraphs.")
    if has_delivery:
        qa_score -= 25
        risks.append("Email body contains delivery / SMTP metadata.")
        fixes.append("Remove transport metadata; the draft must remain reviewable text only.")
    if has_guaranteed:
        qa_score -= 25
        risks.append("Email body claims guaranteed outcomes.")
        fixes.append(
            "Replace guaranteed-outcome phrasing with conditional, evidence-based language."
        )
    if has_urgency:
        qa_score -= 20
        risks.append("Email body uses manipulative urgency phrasing.")
        fixes.append("Remove urgency phrasing; keep tone professional and low-pressure.")
    if no_company_or_team:
        qa_score -= 10
        risks.append(
            "Email body does not reference the company name or 'your team'."
        )
        fixes.append(
            "Anchor the opening to the company name or to 'your team'."
        )
    if no_cta:
        qa_score -= 10
        risks.append("Email lacks a soft CTA.")
        fixes.append(
            "Add a low-pressure CTA such as 'Would it be worth a quick look?'."
        )

    # Informational notes — do not affect qa_score directly because
    # this evaluator scores the email, not the lead. Surfaced as a
    # qa_note so the human reviewer sees the context warning.
    info_notes: list[str] = []
    if degraded_lead:
        info_notes.append(
            "Lead context is degraded (missing industry/country/employee_count); "
            "keep outreach exploratory."
        )

    has_hard_violation = (
        has_live_research
        or has_guaranteed
        or has_delivery
        or has_raw_marker
        or body_too_short
        or no_cta
    )

    # Strengths surfaced only when the corresponding signal looks clean.
    if has_company_or_team and not has_live_research:
        strengths.append("Body references the company or 'your team' clearly.")
    if not no_cta and not has_urgency:
        strengths.append("Body includes a soft, non-urgent CTA.")
    if agent_input.evidence_cards:
        strengths.append("Has supporting evidence cards from research.")
    if agent_input.personalization_notes and not has_live_research:
        strengths.append("Carries personalization notes from upstream agents.")

    qa_score = _clamp(qa_score)

    # Hallucination risk: scale with the worst violation.
    if has_live_research:
        hallucination_risk = HallucinationRisk.HIGH
    elif has_raw_marker or has_guaranteed:
        hallucination_risk = HallucinationRisk.MEDIUM
    else:
        hallucination_risk = HallucinationRisk.LOW

    # Recommendation: never auto-approve in the portfolio version.
    # REVIEW only when everything is clean; REGENERATE for any hard
    # violation or low qa_score.
    if has_hard_violation or qa_score < 50:
        recommendation = Recommendation.REGENERATE
    else:
        recommendation = Recommendation.REVIEW

    # Per-dimension scores.
    personalization = 80
    if no_company_or_team:
        personalization -= 30
    if not agent_input.personalization_notes:
        personalization -= 20
    personalization = _clamp(personalization)

    evidence_coverage = 80
    if has_live_research:
        evidence_coverage -= 50
    if not agent_input.evidence_cards:
        evidence_coverage -= 20
    evidence_coverage = _clamp(evidence_coverage)

    cta_quality = 80 if not no_cta else 30
    if has_urgency:
        cta_quality -= 25
    cta_quality = _clamp(cta_quality)

    tone_match = 80
    if has_urgency:
        tone_match -= 30
    if has_guaranteed:
        tone_match -= 30
    if has_delivery:
        tone_match -= 20
    if has_raw_marker:
        tone_match -= 30
    tone_match = _clamp(tone_match)

    qa_scores = QAScores(
        personalization=personalization,
        evidence_coverage=evidence_coverage,
        cta_quality=cta_quality,
        tone_match=tone_match,
        hallucination_risk=hallucination_risk,
        recommendation=recommendation,
    )

    # Project strengths/risks/fixes/info into qa_notes with prefixes
    # (matches the FIX 1 projection used by the synthesis path so the
    # output shape is identical regardless of which path produced it).
    qa_notes: list[str] = (
        [f"[STRENGTH] {s}" for s in strengths]
        + [f"[RISK] {r}" for r in risks]
        + [f"[FIX] {f}" for f in fixes]
        + [f"[INFO] {n}" for n in info_notes]
    )

    return _DeterministicBaseline(
        qa_score=qa_score,
        qa_scores=qa_scores,
        hallucination_risk=hallucination_risk,
        recommendation=recommendation,
        qa_notes=qa_notes,
        has_hard_violation=has_hard_violation,
        strengths=strengths,
        risks=risks,
        fixes=fixes,
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
class QAEvaluatorAgentService:
    """Deterministic-first QA evaluator with optional Groq synthesis."""

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
        self, agent_input: QAEvaluatorAgentInput
    ) -> QAEvaluatorAgentOutput:
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
    ) -> QAEvaluatorAgentOutput:
        qa_notes = list(baseline.qa_notes)
        if extra_note and extra_note not in qa_notes:
            qa_notes.append(extra_note)
        return QAEvaluatorAgentOutput(
            result=AgentContractResult(
                success=True,
                metadata=metadata,
                error=None,
            ),
            lead_id=lead_id,
            qa_score=baseline.qa_score,
            qa_scores=baseline.qa_scores,
            hallucination_risk=baseline.hallucination_risk,
            recommendation=baseline.recommendation,
            qa_notes=qa_notes,
        )

    def _payload_to_output(
        self,
        lead_id: str,
        payload: QAEvaluatorSynthesisPayload,
        response: ModelResponse,
    ) -> QAEvaluatorAgentOutput:
        qa_scores = QAScores(
            personalization=payload.personalization,
            evidence_coverage=payload.evidence_coverage,
            cta_quality=payload.cta_quality,
            tone_match=payload.tone_match,
            hallucination_risk=payload.hallucination_risk,
            recommendation=payload.recommendation,
        )
        # Phase 5.9 FIX 1 — project strengths/risks/required_fixes into
        # qa_notes (the QAEvaluatorAgentOutput contract has no such
        # fields; qa_notes is the only textual-findings carrier).
        qa_notes: list[str] = (
            [f"[STRENGTH] {s}" for s in payload.strengths]
            + [f"[RISK] {r}" for r in payload.risks]
            + [f"[FIX] {f}" for f in payload.required_fixes]
        )
        return QAEvaluatorAgentOutput(
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
            qa_score=payload.qa_score,
            qa_scores=qa_scores,
            hallucination_risk=payload.hallucination_risk,
            recommendation=payload.recommendation,
            qa_notes=qa_notes,
        )

    def _fallback_with_response(
        self,
        lead_id: str,
        baseline: _DeterministicBaseline,
        response: ModelResponse,
    ) -> QAEvaluatorAgentOutput:
        return self._output_from_baseline(
            lead_id,
            baseline,
            _synthesis_metadata(
                response,
                prompt_version=_PROMPT_VERSION_GROQ_JSON_FALLBACK,
                simulated=True,
            ),
            extra_note=f"[FIX] {_GUARDRAIL_FALLBACK_RISK_NOTE}",
        )

    def _safe_failure_output(
        self, lead_id: str, exc: Exception
    ) -> QAEvaluatorAgentOutput:
        """Phase 5.9 FIX 4: the error fallback builds the output
        directly, bypassing ``QAEvaluatorSynthesisPayload``. ``qa_notes``
        is a plain ``list[str]`` and ``QAEvaluatorAgentOutput`` has no
        ``min_length`` constraint on it.

        Returns a maximally-conservative output:
        ``qa_score=0``, ``hallucination_risk=HIGH``,
        ``recommendation=REGENERATE``.
        """

        fallback_scores = QAScores(
            personalization=0,
            evidence_coverage=0,
            cta_quality=0,
            tone_match=0,
            hallucination_risk=HallucinationRisk.HIGH,
            recommendation=Recommendation.REGENERATE,
        )
        return QAEvaluatorAgentOutput(
            result=AgentContractResult(
                success=False,
                metadata=_deterministic_metadata(),
                error=AgentError(
                    code="qa_evaluator_agent_error",
                    message=str(exc),
                    recoverable=True,
                ),
            ),
            lead_id=lead_id,
            qa_score=0,
            qa_scores=fallback_scores,
            hallucination_risk=HallucinationRisk.HIGH,
            recommendation=Recommendation.REGENERATE,
            qa_notes=[
                "[FIX] QA evaluator failed before producing a score; "
                "the draft must be manually reviewed before any action."
            ],
        )

    # ------------------------------------------------------------------- #
    # Synthesis path                                                      #
    # ------------------------------------------------------------------- #
    def _build_synthesis_request(
        self,
        agent_input: QAEvaluatorAgentInput,
        baseline: _DeterministicBaseline,
    ) -> ModelRequest:
        lead = agent_input.lead
        payload: dict[str, Any] = {
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
            "email_subject": agent_input.email_subject,
            "email_body": agent_input.email_body,
            "personalization_notes": list(agent_input.personalization_notes),
            "evidence_cards": [
                {
                    "id": card.id,
                    "headline": card.headline,
                    "description": card.description,
                    "confidence": card.confidence.value,
                    "source_type": card.source_type.value,
                }
                for card in agent_input.evidence_cards
            ],
            "baseline": {
                "qa_score": baseline.qa_score,
                "personalization": baseline.qa_scores.personalization,
                "evidence_coverage": baseline.qa_scores.evidence_coverage,
                "cta_quality": baseline.qa_scores.cta_quality,
                "tone_match": baseline.qa_scores.tone_match,
                "hallucination_risk": baseline.hallucination_risk.value,
                "recommendation": baseline.recommendation.value,
                "has_hard_violation": baseline.has_hard_violation,
                "strengths": baseline.strengths,
                "risks": baseline.risks,
                "required_fixes": baseline.fixes,
            },
        }
        user_content = (
            "Evaluate the deterministic baseline below using ONLY the "
            "provided lead, email and evidence context. Respond with "
            "valid JSON matching the schema in the system message.\n\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )

        config = ModelConfig(
            provider=ModelProvider.GROQ,
            model_name=_GROQ_QA_MODEL_NAME,
            max_tokens=1024,
        )
        return ModelRequest(
            messages=[
                ModelMessage(role=ModelRole.SYSTEM, content=_SYNTHESIS_SYSTEM_PROMPT),
                ModelMessage(role=ModelRole.USER, content=user_content),
            ],
            config=config,
            request_id=(
                f"qa_evaluator_agent_synthesis::{agent_input.run_id}::{lead.lead_id}"
                if agent_input.run_id
                else f"qa_evaluator_agent_synthesis::{lead.lead_id}"
            ),
        )

    def _validate_payload(
        self, content: str
    ) -> QAEvaluatorSynthesisPayload:
        payload_dict = extract_json_object(content)
        try:
            return QAEvaluatorSynthesisPayload.model_validate(payload_dict)
        except ValidationError as exc:
            raise ValueError(
                "Model response failed QAEvaluatorSynthesisPayload "
                f"validation: {exc}"
            ) from exc

    def _apply_guardrails(
        self,
        payload: QAEvaluatorSynthesisPayload,
        baseline: _DeterministicBaseline,
        agent_input: QAEvaluatorAgentInput,
    ) -> QAEvaluatorSynthesisPayload:
        """Reject LLM payloads that would undermine deterministic safety.

        Raises ``ValueError`` on any violation so the caller routes to
        the deterministic fallback. No raw model text is included in
        the exception message.
        """

        # Score-inflation cap (mirrors Phase 5.6B FIX 3).
        if payload.qa_score - baseline.qa_score > _MAX_LLM_SCORE_UPGRADE:
            raise ValueError(
                "LLM qa_score exceeds deterministic baseline by more "
                f"than {_MAX_LLM_SCORE_UPGRADE} points."
            )

        # If baseline detected a hard violation, the LLM may not:
        # (a) make the hallucination_risk less severe, or
        # (b) make the recommendation more permissive.
        if baseline.has_hard_violation:
            llm_risk_rank = _RISK_RANK[payload.hallucination_risk]
            baseline_risk_rank = _RISK_RANK[baseline.hallucination_risk]
            if llm_risk_rank < baseline_risk_rank:
                raise ValueError(
                    "Baseline detected a hard violation; LLM "
                    "hallucination_risk must not be less severe."
                )

            llm_rec_rank = _REC_RANK[payload.recommendation]
            baseline_rec_rank = _REC_RANK[baseline.recommendation]
            if llm_rec_rank > baseline_rec_rank:
                raise ValueError(
                    "Baseline detected a hard violation; LLM "
                    "recommendation must not be more permissive."
                )

        # Forbidden phrases inside any LLM-supplied text field.
        text_fields = (
            *payload.strengths,
            *payload.risks,
            *payload.required_fixes,
        )
        for field_text in text_fields:
            if _contains_any(field_text, _LIVE_RESEARCH_PHRASES):
                raise ValueError(
                    "LLM QA output contains a forbidden live-research phrase."
                )
            if _contains_any(field_text, _RAW_MODEL_MARKERS):
                raise ValueError(
                    "LLM QA output contains a raw model-response marker."
                )

        return payload

    def _run_with_model_synthesis(
        self,
        agent_input: QAEvaluatorAgentInput,
        baseline: _DeterministicBaseline,
    ) -> QAEvaluatorAgentOutput:
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
            approved = self._apply_guardrails(payload, baseline, agent_input)
        except ValueError:
            return self._fallback_with_response(
                agent_input.lead.lead_id, baseline, response
            )

        return self._payload_to_output(
            agent_input.lead.lead_id, approved, response
        )


__all__ = ["QAEvaluatorAgentService"]
