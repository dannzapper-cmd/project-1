"""Block 8.3 — Minimal Live Groq single-lead pipeline service.

Runs the existing five agent services sequentially against a single
demo lead, swapping the model service backing for ``GroqModelService``
where each agent already supports ``use_model_synthesis=True``. The
deterministic baseline is computed in the same request (via the
existing :func:`run_pipeline_for_lead`) so the response always includes
a comparison context — even when the live path fails.

Hard rules baked into this module:

* **One lead per request.** No batch path, no all-leads helper, no
  loops over the demo dataset.
* **Explicit opt-in.** The caller is responsible for confirming that
  ``ENABLE_LIVE_MODEL_PIPELINE`` is enabled and ``GROQ_API_KEY`` is
  set; this service raises a ``LivePipelineDisabledError`` otherwise.
* **No silent fallback.** When any live agent step fails, the
  response is built with ``live_success=False``, the deterministic
  baseline is preserved as comparison context, and the failure stage
  / failed agent / error code are surfaced explicitly.
* **No retry, no exponential backoff.** Block 8.3 never retries a
  Groq call. Rate-limit errors are surfaced verbatim with
  ``error_code="rate_limited"``.
* **Token budget.** A hard total-tokens budget per single-lead run is
  enforced via ``MAX_LIVE_TOKENS_PER_RUN``. When the running total
  crosses the cap mid-pipeline, the next agent step is skipped and
  the run is marked as a token-budget failure.
* **Telemetry safety.** Only summary-level data is recorded
  (``run_id``, ``lead_id``, ``agent_name``, status, latency, token
  estimates, fallback flags, QA score, hallucination risk). No
  prompts, no full lead payloads, no email bodies, no raw provider
  responses are stored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.agents.email_drafter_agent import EmailDrafterAgentService
from app.agents.qa_evaluator_agent import QAEvaluatorAgentService
from app.agents.qualifier_agent import QualifierAgentService
from app.agents.research_agent import ResearchAgentService
from app.agents.strategist_agent import StrategistAgentService
from app.core.config import get_settings
from app.schemas.agents import (
    EmailDrafterAgentInput,
    EmailDrafterAgentOutput,
    LeadPipelineContractOutput,
    QAEvaluatorAgentInput,
    QAEvaluatorAgentOutput,
    QualifierAgentInput,
    QualifierAgentOutput,
    ResearchAgentInput,
    ResearchAgentOutput,
    StrategistAgentInput,
    StrategistAgentOutput,
)
from app.schemas.common import AgentRunStatus, Priority
from app.schemas.demo import DemoCompanyResearch
from app.schemas.lead import LeadIn
from app.schemas.live_pipeline import (
    LivePipelineComparison,
    LivePipelineResponse,
)
from app.schemas.run import TraceEntry
from app.services import telemetry_service
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
)
from app.services.pipeline_service import run_pipeline_for_lead


# --------------------------------------------------------------------------- #
# Block 8.3 constants                                                          #
# --------------------------------------------------------------------------- #

# Hard total-token budget for one single-lead live run, summed across
# every agent step. Picked low enough to stop accidental runaway
# spend; the deterministic baseline does NOT consume this budget.
MAX_LIVE_TOKENS_PER_RUN: int = 8_000

# Fallback default Groq model name for the live pipeline. The runtime
# value is resolved at request time from ``get_settings().groq_default_model``
# (see :func:`_resolve_live_groq_model`). This constant is only used
# when the setting is empty / unavailable, so cluster-level overrides
# via the ``GROQ_DEFAULT_MODEL`` env var continue to drive the live
# pipeline without changes here.
LIVE_GROQ_MODEL: str = "llama-3.1-8b-instant"


def _resolve_live_groq_model() -> str:
    """Return the Groq model name the live pipeline should use.

    Resolves ``get_settings().groq_default_model`` first so the
    existing ``GROQ_DEFAULT_MODEL`` env var / Settings field drives
    the live pipeline without a parallel knob. Falls back to
    :data:`LIVE_GROQ_MODEL` when the setting is missing or blank
    (defensive — Pydantic Settings always returns the declared
    default, but a future Settings refactor must not silently
    surface an empty model name).
    """

    try:
        candidate = get_settings().groq_default_model
    except Exception:  # noqa: BLE001 — settings access must not break live runs
        candidate = None
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    return LIVE_GROQ_MODEL

# Live-mode telemetry constants.
_LIVE_RUN_MODE: str = "live_groq_pipeline"
_LIVE_MODEL_MODE: str = "groq"

# Pipeline stage labels. Order matches execution order.
_STAGE_RESEARCH: str = "research"
_STAGE_QUALIFIER: str = "qualifier"
_STAGE_STRATEGIST: str = "strategist"
_STAGE_EMAIL: str = "email_drafter"
_STAGE_QA: str = "qa_evaluator"

_STAGES_IN_ORDER: tuple[str, ...] = (
    _STAGE_RESEARCH,
    _STAGE_QUALIFIER,
    _STAGE_STRATEGIST,
    _STAGE_EMAIL,
    _STAGE_QA,
)

_AGENT_NAMES_BY_STAGE: dict[str, str] = {
    _STAGE_RESEARCH: "research_agent",
    _STAGE_QUALIFIER: "qualifier_agent",
    _STAGE_STRATEGIST: "strategist_agent",
    _STAGE_EMAIL: "email_drafter_agent",
    _STAGE_QA: "qa_evaluator_agent",
}


# --------------------------------------------------------------------------- #
# Errors                                                                      #
# --------------------------------------------------------------------------- #


class LivePipelineDisabledError(Exception):
    """Raised when the live pipeline is requested but not enabled."""


class LivePipelineKeyMissingError(Exception):
    """Raised when ``GROQ_API_KEY`` is missing at request time."""


class LivePipelineLeadNotFoundError(Exception):
    """Raised when ``lead_id`` does not exist in the demo dataset."""


# --------------------------------------------------------------------------- #
# Internal helpers                                                            #
# --------------------------------------------------------------------------- #


@dataclass
class _LiveFailure:
    failed_agent: str
    failure_stage: str
    error_code: str
    fallback_reason: str


class _ErrorCapturingModelService:
    """Wrap a model service so the live runner can observe provider errors.

    Each agent service catches its own exceptions internally and
    converts them into a deterministic-fallback or success=False
    output, which loses the original exception type. Wrapping the
    model service lets the live runner inspect ``last_error`` after
    the agent returns and classify the failure correctly (e.g.
    distinguish ``rate_limited`` from a generic ``provider_error``).
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.last_error: BaseException | None = None
        self.call_count: int = 0

    def reset(self) -> None:
        self.last_error = None

    def complete(self, request):  # noqa: ANN001 — mirror BaseModelService
        self.call_count += 1
        try:
            return self._inner.complete(request)
        except BaseException as exc:  # noqa: BLE001 — captured for inspection
            self.last_error = exc
            raise


def _classify_error(exc: BaseException) -> str:
    """Map a provider exception to a stable Block 8.3 error code.

    The classification is duck-typed: we never import provider error
    classes here so the module remains importable without the Groq
    SDK. Block 8.3 never retries — this function exists only to label
    the failure for the response, not to drive control flow.
    """

    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return "rate_limited"

    text = str(exc).lower()
    if "rate limit" in text or "429" in text or "too many requests" in text:
        return "rate_limited"
    if "timeout" in text or "timed out" in text:
        return "provider_timeout"
    if "unauthorized" in text or "invalid api key" in text or status_code == 401:
        return "provider_unauthorized"
    return "provider_error"


def _short_text(value: str | None, max_length: int = 160) -> str | None:
    """Sanitize a candidate summary value to a short single-line string.

    Used for ``live_summary`` / ``deterministic_summary`` /
    ``comparison_notes``. Strips whitespace, collapses internal
    whitespace, and truncates with an ellipsis. Returns ``None`` when
    the input is empty.
    """

    if value is None:
        return None
    snippet = " ".join(str(value).strip().split())
    if not snippet:
        return None
    if len(snippet) <= max_length:
        return snippet
    return snippet[: max_length - 3] + "..."


def _agent_total_tokens(agent_output: Any) -> int:
    """Read ``tokens`` off an agent output's metadata, defaulting to 0."""

    try:
        return int(agent_output.result.metadata.tokens or 0)
    except Exception:  # noqa: BLE001 — defensive; telemetry must not crash
        return 0


def _agent_succeeded(agent_output: Any) -> bool:
    try:
        return bool(agent_output.result.success)
    except Exception:  # noqa: BLE001
        return False


def _classify_failure_code(
    *,
    captured_error: BaseException | None,
    agent_output: Any,
) -> str:
    """Pick a stable error code for a failed agent step.

    Priority order:

    1. If the model-service wrapper captured a provider exception,
       classify that exception (so HTTP 429s become ``rate_limited``).
    2. If the agent itself reported an error code via
       ``AgentContractResult.error``, use that code's textual content
       to classify (the agent stores the original ``str(exc)``).
    3. If the agent used a deterministic fallback path (``..._fallback``
       prompt version), surface ``agent_fallback``.
    4. Otherwise default to ``agent_failure``.
    """

    if captured_error is not None:
        return _classify_error(captured_error)

    try:
        agent_error = agent_output.result.error
    except Exception:  # noqa: BLE001
        agent_error = None
    if agent_error is not None:
        message = (agent_error.message or "").lower()
        if "rate" in message or "429" in message or "too many requests" in message:
            return "rate_limited"
        if "timeout" in message or "timed out" in message:
            return "provider_timeout"
        if "unauthorized" in message or "invalid api key" in message:
            return "provider_unauthorized"
        return "provider_error"

    if _agent_used_fallback(agent_output):
        return "agent_fallback"
    return "agent_failure"


def _agent_used_fallback(agent_output: Any) -> bool:
    """Return True when an agent output's prompt_version flags a fallback.

    The Block 5.5C / 5.6B / 5.7 / 5.8 / 5.9 agents tag their
    deterministic-fallback metadata with a ``..._fallback`` prompt
    version. The live path treats that as a failure for the live
    pipeline (Block 8.3 must not silently complete the run with a
    deterministic-fallback agent output).
    """

    try:
        prompt_version = (agent_output.result.metadata.prompt_version or "").lower()
    except Exception:  # noqa: BLE001
        return False
    return "fallback" in prompt_version


def _find_lead_or_raise(lead_id: str) -> LeadIn:
    leads = load_demo_leads()
    for lead in leads:
        if lead.lead_id == lead_id:
            return lead
    raise LivePipelineLeadNotFoundError(
        f"Lead '{lead_id}' not found in the demo dataset."
    )


def _find_research_record(lead_id: str) -> DemoCompanyResearch | None:
    research_records = load_demo_company_research()
    for record in research_records:
        if record.lead_id == lead_id:
            return record
    return None


def _available_context(
    research: DemoCompanyResearch | None,
) -> dict | None:
    if research is None:
        return None
    return research.model_dump()


def _qualifier_seed_signals(
    research_output: ResearchAgentOutput,
    research_record: DemoCompanyResearch | None,
) -> tuple[list[str], list[str]]:
    signals: list[str] = list(research_output.opportunity_signals)
    risks: list[str] = list(research_output.information_risks)

    if research_record is not None:
        for signal in research_record.opportunity_signals:
            if (
                isinstance(signal.signal, str)
                and signal.signal.strip()
                and signal.signal not in signals
            ):
                signals.append(signal.signal)
        for risk in research_record.information_risks:
            if isinstance(risk, str) and risk.strip() and risk not in risks:
                risks.append(risk)

    return signals, risks


def _research_summary_for_qualifier(
    research_output: ResearchAgentOutput,
    research_record: DemoCompanyResearch | None,
) -> str | None:
    if research_output.company_summary:
        return research_output.company_summary
    if research_record is None:
        return None
    return (
        research_record.recommended_research_summary
        or research_record.company_summary
        or None
    )


def _trace_entry(
    agent_label: str,
    agent_output: Any,
    *,
    input_summary: str,
    output_summary: str,
) -> TraceEntry:
    metadata = agent_output.result.metadata
    status = (
        AgentRunStatus.SUCCESS
        if agent_output.result.success
        else AgentRunStatus.FAILED
    )
    return TraceEntry(
        agent=agent_label,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
        latency=metadata.latency,
        tokens=metadata.tokens,
        prompt_version=metadata.prompt_version or "live_groq_pipeline_v1",
        model=metadata.model,
        simulated=False,
    )


# --------------------------------------------------------------------------- #
# Comparison construction                                                     #
# --------------------------------------------------------------------------- #


def _priority_rank(priority: Priority | None) -> int | None:
    if priority is None:
        return None
    return {Priority.LOW: 1, Priority.MEDIUM: 2, Priority.HIGH: 3}.get(priority)


def _hallucination_risk_rank(risk_value: str | None) -> int | None:
    if risk_value is None:
        return None
    return {"Low": 1, "Medium": 2, "High": 3}.get(risk_value)


def _safe_summary(pipeline_output: LeadPipelineContractOutput | None) -> str | None:
    """Build a short, sanitized summary for one pipeline output.

    Block 8.3 telemetry rule: the summary must not contain email
    body content or raw lead PII. We project only safe numeric /
    enum fields — fit_score, priority, qa_score, hallucination_risk
    — into a short string.
    """

    if pipeline_output is None:
        return None

    parts: list[str] = []
    if pipeline_output.qualification is not None:
        parts.append(f"fit={pipeline_output.qualification.fit_score}")
        parts.append(f"priority={pipeline_output.qualification.priority.value}")
    if pipeline_output.qa is not None:
        parts.append(f"qa={pipeline_output.qa.qa_score}")
        parts.append(
            f"risk={pipeline_output.qa.hallucination_risk.value}"
        )
    if not parts:
        return None
    return _short_text(" ".join(parts))


def _build_comparison(
    *,
    deterministic: LeadPipelineContractOutput | None,
    live: LeadPipelineContractOutput | None,
    notes: str,
) -> LivePipelineComparison:
    """Construct the comparison view between deterministic and live outputs.

    When ``live`` is ``None`` (the live run failed), every delta field
    is left as ``None`` and the schema's defaults take over.
    """

    if live is None or deterministic is None:
        return LivePipelineComparison(
            fit_score_delta=None,
            priority_changed=None,
            qa_score_delta=None,
            email_subject_changed=None,
            risk_level_changed=None,
            live_summary=_safe_summary(live),
            deterministic_summary=_safe_summary(deterministic),
            comparison_notes=_short_text(notes) or "",
        )

    fit_score_delta: int | None = None
    if deterministic.qualification is not None and live.qualification is not None:
        fit_score_delta = (
            int(live.qualification.fit_score)
            - int(deterministic.qualification.fit_score)
        )

    priority_changed: bool | None = None
    if deterministic.qualification is not None and live.qualification is not None:
        priority_changed = (
            deterministic.qualification.priority != live.qualification.priority
        )

    qa_score_delta: int | None = None
    if deterministic.qa is not None and live.qa is not None:
        qa_score_delta = int(live.qa.qa_score) - int(deterministic.qa.qa_score)

    email_subject_changed: bool | None = None
    if deterministic.email is not None and live.email is not None:
        email_subject_changed = (
            deterministic.email.email_subject != live.email.email_subject
        )

    risk_level_changed: bool | None = None
    if deterministic.qa is not None and live.qa is not None:
        det_rank = _hallucination_risk_rank(
            deterministic.qa.hallucination_risk.value
        )
        live_rank = _hallucination_risk_rank(live.qa.hallucination_risk.value)
        if det_rank is not None and live_rank is not None:
            risk_level_changed = det_rank != live_rank

    return LivePipelineComparison(
        fit_score_delta=fit_score_delta,
        priority_changed=priority_changed,
        qa_score_delta=qa_score_delta,
        email_subject_changed=email_subject_changed,
        risk_level_changed=risk_level_changed,
        live_summary=_safe_summary(live),
        deterministic_summary=_safe_summary(deterministic),
        comparison_notes=_short_text(notes) or "",
    )


# --------------------------------------------------------------------------- #
# Telemetry recording                                                         #
# --------------------------------------------------------------------------- #


def _record_live_step(
    *,
    run_id: str,
    lead_id: str,
    agent_name: str,
    agent_output: Any,
) -> None:
    """Record one telemetry step for the live pipeline.

    Best-effort: telemetry must never break the request. Only safe
    summary-level fields are forwarded; the in-memory telemetry store
    refuses unknown fields via ``ConfigDict(extra="ignore")``.
    """

    try:
        entry = telemetry_service.build_pipeline_step_entry(
            run_id=run_id,
            lead_id=lead_id,
            agent_name=agent_name,
            agent_output=agent_output,
            run_mode=_LIVE_RUN_MODE,
            model_mode=_LIVE_MODEL_MODE,
        )
    except Exception:  # noqa: BLE001 — telemetry must not crash live path
        return

    try:
        telemetry_service.telemetry_service.record(entry)
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------------- #
# Public entry point                                                          #
# --------------------------------------------------------------------------- #


def run_live_groq_pipeline_for_lead(
    lead_id: str,
    *,
    groq_service_factory: Any | None = None,
) -> LivePipelineResponse:
    """Run the live Groq pipeline for exactly one demo lead.

    Parameters
    ----------
    lead_id:
        Demo lead identifier. Raises :class:`LivePipelineLeadNotFoundError`
        when the lead is not in the demo dataset.
    groq_service_factory:
        Optional callable returning a ``BaseModelService`` instance.
        Tests inject a stub here so unit tests never touch the network.
        When ``None``, the factory builds a real
        :class:`GroqModelService` bound to the model name returned by
        :func:`_resolve_live_groq_model` (which reads
        ``Settings.groq_default_model`` first and falls back to
        :data:`LIVE_GROQ_MODEL` only when the setting is empty).

    Raises
    ------
    LivePipelineDisabledError
        When ``ENABLE_LIVE_MODEL_PIPELINE`` is not enabled.
    LivePipelineKeyMissingError
        When ``GROQ_API_KEY`` is not set at request time.
    LivePipelineLeadNotFoundError
        When ``lead_id`` is unknown.
    """

    # Read both gating signals at request time. ``get_settings()`` is
    # ``lru_cache``-wrapped, so we additionally consult the live
    # process environment so monkeypatched changes are honoured by
    # tests and short-lived processes.
    settings = get_settings()
    env_flag_raw = os.environ.get("ENABLE_LIVE_MODEL_PIPELINE")
    env_flag = (
        env_flag_raw.strip().lower() in ("1", "true", "yes", "on")
        if env_flag_raw is not None
        else settings.enable_live_model_pipeline
    )
    if not env_flag:
        raise LivePipelineDisabledError(
            "Live model pipeline is disabled. Set "
            "ENABLE_LIVE_MODEL_PIPELINE=true to opt in."
        )

    api_key = os.environ.get("GROQ_API_KEY") or settings.groq_api_key
    if not api_key:
        raise LivePipelineKeyMissingError(
            "GROQ_API_KEY is required to run the live Groq pipeline."
        )

    lead = _find_lead_or_raise(lead_id)
    research_record = _find_research_record(lead_id)

    run_id = f"live_groq_pipeline_{lead.lead_id}_{uuid4().hex[:8]}"

    # Resolve the actual Groq model for this request once so every
    # subsequent response field (success or failure) reports the same
    # value as the one passed to the provider.
    live_model_used = _resolve_live_groq_model()

    # Build the deterministic baseline first; it never consumes Groq
    # tokens and is always available as comparison context, even when
    # the live path fails.
    deterministic_result: LeadPipelineContractOutput | None
    try:
        deterministic_result = run_pipeline_for_lead(lead.lead_id, run_id=run_id)
    except Exception:  # noqa: BLE001 — defensive; baseline is best-effort
        deterministic_result = None

    if groq_service_factory is None:
        def _default_factory() -> Any:
            from app.services.model_service import GroqModelService

            return GroqModelService(default_model=live_model_used)

        groq_service_factory = _default_factory

    try:
        groq_service = groq_service_factory()
    except Exception as exc:  # noqa: BLE001
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent="(none)",
                failure_stage="provider_init",
                error_code=_classify_error(exc),
                fallback_reason=(
                    "Groq client could not be constructed; live run not "
                    "started."
                ),
            ),
        )

    return _execute_live_pipeline(
        run_id=run_id,
        lead=lead,
        research_record=research_record,
        deterministic_result=deterministic_result,
        groq_service=groq_service,
        live_model_used=live_model_used,
    )


def _build_failed_response(
    *,
    run_id: str,
    lead_id: str,
    deterministic_result: LeadPipelineContractOutput | None,
    failure: _LiveFailure,
    live_model_used: str,
) -> LivePipelineResponse:
    notes = (
        f"live run failed at {failure.failure_stage} "
        f"({failure.error_code}); no comparison available"
    )
    comparison = _build_comparison(
        deterministic=deterministic_result,
        live=None,
        notes=notes,
    )
    return LivePipelineResponse(
        run_id=run_id,
        lead_id=lead_id,
        run_mode="live_failed",
        live_success=False,
        live_model_used=live_model_used,
        fallback_used=True,
        fallback_reason=failure.fallback_reason,
        deterministic_baseline_available=deterministic_result is not None,
        failed_agent=failure.failed_agent,
        failure_stage=failure.failure_stage,
        error_code=failure.error_code,
        deterministic_result=deterministic_result,
        live_result=None,
        comparison=comparison,
    )


def _execute_live_pipeline(
    *,
    run_id: str,
    lead: LeadIn,
    research_record: DemoCompanyResearch | None,
    deterministic_result: LeadPipelineContractOutput | None,
    groq_service: Any,
    live_model_used: str,
) -> LivePipelineResponse:
    """Run the five-agent chain end-to-end with Groq-backed synthesis.

    Each step is wrapped in a narrow try/except so a provider
    exception at any stage is captured as a structured live failure
    without polluting the overall response shape.
    """

    tokens_so_far: int = 0
    trace: list[TraceEntry] = []

    capturing_wrapper = _ErrorCapturingModelService(groq_service)

    # ---- 1) Research --------------------------------------------------- #
    capturing_wrapper.reset()
    try:
        research_service = ResearchAgentService(
            model_service=capturing_wrapper, use_model_synthesis=True
        )
        research_input = ResearchAgentInput(
            lead=lead,
            run_id=run_id,
            available_context=_available_context(research_record),
        )
        research_output: ResearchAgentOutput = research_service.run(research_input)
    except Exception as exc:  # noqa: BLE001
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_RESEARCH],
                failure_stage=_STAGE_RESEARCH,
                error_code=_classify_error(exc),
                fallback_reason=(
                    "Research agent failed in live mode; deterministic "
                    "baseline preserved as comparison context."
                ),
            ),
        )

    _record_live_step(
        run_id=run_id,
        lead_id=lead.lead_id,
        agent_name=_AGENT_NAMES_BY_STAGE[_STAGE_RESEARCH],
        agent_output=research_output,
    )

    if not _agent_succeeded(research_output) or _agent_used_fallback(research_output):
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_RESEARCH],
                failure_stage=_STAGE_RESEARCH,
                error_code=_classify_failure_code(
                    captured_error=capturing_wrapper.last_error,
                    agent_output=research_output,
                ),
                fallback_reason=(
                    "Research agent failed or fell back to deterministic "
                    "output; live run not considered successful."
                ),
            ),
        )

    tokens_so_far += _agent_total_tokens(research_output)
    if tokens_so_far > MAX_LIVE_TOKENS_PER_RUN:
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_RESEARCH],
                failure_stage=_STAGE_RESEARCH,
                error_code="token_budget_exceeded",
                fallback_reason=(
                    "Token budget exceeded after research stage; live "
                    "run halted."
                ),
            ),
        )

    trace.append(
        _trace_entry(
            "research_agent",
            research_output,
            input_summary=f"lead={lead.lead_id}",
            output_summary=(
                f"signals={len(research_output.opportunity_signals)}"
            ),
        )
    )

    # ---- 2) Qualifier -------------------------------------------------- #
    qualifier_signals, qualifier_risks = _qualifier_seed_signals(
        research_output, research_record
    )
    capturing_wrapper.reset()
    try:
        qualifier_service = QualifierAgentService(
            model_service=capturing_wrapper, use_model_synthesis=True
        )
        qualifier_input = QualifierAgentInput(
            lead=lead,
            research_summary=_research_summary_for_qualifier(
                research_output, research_record
            ),
            opportunity_signals=qualifier_signals,
            information_risks=qualifier_risks,
            run_id=run_id,
        )
        qualifier_output: QualifierAgentOutput = qualifier_service.run(
            qualifier_input
        )
    except Exception as exc:  # noqa: BLE001
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_QUALIFIER],
                failure_stage=_STAGE_QUALIFIER,
                error_code=_classify_error(exc),
                fallback_reason=(
                    "Qualifier agent failed in live mode; deterministic "
                    "baseline preserved as comparison context."
                ),
            ),
        )

    _record_live_step(
        run_id=run_id,
        lead_id=lead.lead_id,
        agent_name=_AGENT_NAMES_BY_STAGE[_STAGE_QUALIFIER],
        agent_output=qualifier_output,
    )

    if not _agent_succeeded(qualifier_output) or _agent_used_fallback(
        qualifier_output
    ):
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_QUALIFIER],
                failure_stage=_STAGE_QUALIFIER,
                error_code=_classify_failure_code(
                    captured_error=capturing_wrapper.last_error,
                    agent_output=qualifier_output,
                ),
                fallback_reason=(
                    "Qualifier agent failed or fell back to deterministic "
                    "output; live run not considered successful."
                ),
            ),
        )

    tokens_so_far += _agent_total_tokens(qualifier_output)
    if tokens_so_far > MAX_LIVE_TOKENS_PER_RUN:
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_QUALIFIER],
                failure_stage=_STAGE_QUALIFIER,
                error_code="token_budget_exceeded",
                fallback_reason=(
                    "Token budget exceeded after qualifier stage; live "
                    "run halted."
                ),
            ),
        )

    trace.append(
        _trace_entry(
            "qualifier_agent",
            qualifier_output,
            input_summary=f"lead={lead.lead_id}",
            output_summary=(
                f"fit={qualifier_output.fit_score}; "
                f"priority={qualifier_output.priority.value}"
            ),
        )
    )

    # ---- 3) Strategist ------------------------------------------------- #
    capturing_wrapper.reset()
    try:
        strategist_service = StrategistAgentService(
            model_service=capturing_wrapper, use_model_synthesis=True
        )
        strategist_input = StrategistAgentInput(
            lead=lead,
            company_summary=research_output.company_summary or "",
            opportunity_signals=list(research_output.opportunity_signals),
            pain_hypotheses=list(research_output.pain_hypotheses),
            fit_score=qualifier_output.fit_score,
            priority=qualifier_output.priority,
            run_id=run_id,
        )
        strategist_output: StrategistAgentOutput = strategist_service.run(
            strategist_input
        )
    except Exception as exc:  # noqa: BLE001
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_STRATEGIST],
                failure_stage=_STAGE_STRATEGIST,
                error_code=_classify_error(exc),
                fallback_reason=(
                    "Strategist agent failed in live mode; deterministic "
                    "baseline preserved as comparison context."
                ),
            ),
        )

    _record_live_step(
        run_id=run_id,
        lead_id=lead.lead_id,
        agent_name=_AGENT_NAMES_BY_STAGE[_STAGE_STRATEGIST],
        agent_output=strategist_output,
    )

    if not _agent_succeeded(strategist_output) or _agent_used_fallback(
        strategist_output
    ):
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_STRATEGIST],
                failure_stage=_STAGE_STRATEGIST,
                error_code=_classify_failure_code(
                    captured_error=capturing_wrapper.last_error,
                    agent_output=strategist_output,
                ),
                fallback_reason=(
                    "Strategist agent failed or fell back to deterministic "
                    "output; live run not considered successful."
                ),
            ),
        )

    tokens_so_far += _agent_total_tokens(strategist_output)
    if tokens_so_far > MAX_LIVE_TOKENS_PER_RUN:
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_STRATEGIST],
                failure_stage=_STAGE_STRATEGIST,
                error_code="token_budget_exceeded",
                fallback_reason=(
                    "Token budget exceeded after strategist stage; live "
                    "run halted."
                ),
            ),
        )

    trace.append(
        _trace_entry(
            "strategist_agent",
            strategist_output,
            input_summary=f"lead={lead.lead_id}",
            output_summary=(
                f"sales_angle_len={len(strategist_output.sales_angle)}"
            ),
        )
    )

    # ---- 4) Email Drafter --------------------------------------------- #
    capturing_wrapper.reset()
    try:
        email_service = EmailDrafterAgentService(
            model_service=capturing_wrapper, use_model_synthesis=True
        )
        email_input = EmailDrafterAgentInput(
            lead=lead,
            company_summary=research_output.company_summary or "",
            pain_hypothesis=strategist_output.pain_hypothesis,
            sales_angle=strategist_output.sales_angle,
            core_message=strategist_output.core_message,
            personalization_notes=list(strategist_output.personalization_notes),
            run_id=run_id,
        )
        email_output: EmailDrafterAgentOutput = email_service.run(email_input)
    except Exception as exc:  # noqa: BLE001
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_EMAIL],
                failure_stage=_STAGE_EMAIL,
                error_code=_classify_error(exc),
                fallback_reason=(
                    "Email drafter failed in live mode; deterministic "
                    "baseline preserved as comparison context."
                ),
            ),
        )

    _record_live_step(
        run_id=run_id,
        lead_id=lead.lead_id,
        agent_name=_AGENT_NAMES_BY_STAGE[_STAGE_EMAIL],
        agent_output=email_output,
    )

    if not _agent_succeeded(email_output) or _agent_used_fallback(email_output):
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_EMAIL],
                failure_stage=_STAGE_EMAIL,
                error_code=_classify_failure_code(
                    captured_error=capturing_wrapper.last_error,
                    agent_output=email_output,
                ),
                fallback_reason=(
                    "Email drafter failed or fell back to deterministic "
                    "output; live run not considered successful."
                ),
            ),
        )

    tokens_so_far += _agent_total_tokens(email_output)
    if tokens_so_far > MAX_LIVE_TOKENS_PER_RUN:
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_EMAIL],
                failure_stage=_STAGE_EMAIL,
                error_code="token_budget_exceeded",
                fallback_reason=(
                    "Token budget exceeded after email drafter stage; "
                    "live run halted."
                ),
            ),
        )

    trace.append(
        _trace_entry(
            "email_drafter_agent",
            email_output,
            input_summary=f"lead={lead.lead_id}",
            output_summary=f"subject_len={len(email_output.email_subject)}",
        )
    )

    # ---- 5) QA Evaluator ---------------------------------------------- #
    capturing_wrapper.reset()
    try:
        qa_service = QAEvaluatorAgentService(
            model_service=capturing_wrapper, use_model_synthesis=True
        )
        qa_input = QAEvaluatorAgentInput(
            lead=lead,
            email_subject=email_output.email_subject,
            email_body=email_output.email_body,
            evidence_cards=list(research_output.evidence_cards),
            personalization_notes=list(email_output.personalization_notes),
            run_id=run_id,
        )
        qa_output: QAEvaluatorAgentOutput = qa_service.run(qa_input)
    except Exception as exc:  # noqa: BLE001
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_QA],
                failure_stage=_STAGE_QA,
                error_code=_classify_error(exc),
                fallback_reason=(
                    "QA evaluator failed in live mode; deterministic "
                    "baseline preserved as comparison context."
                ),
            ),
        )

    _record_live_step(
        run_id=run_id,
        lead_id=lead.lead_id,
        agent_name=_AGENT_NAMES_BY_STAGE[_STAGE_QA],
        agent_output=qa_output,
    )

    if not _agent_succeeded(qa_output) or _agent_used_fallback(qa_output):
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_QA],
                failure_stage=_STAGE_QA,
                error_code=_classify_failure_code(
                    captured_error=capturing_wrapper.last_error,
                    agent_output=qa_output,
                ),
                fallback_reason=(
                    "QA evaluator failed or fell back to deterministic "
                    "output; live run not considered successful."
                ),
            ),
        )

    tokens_so_far += _agent_total_tokens(qa_output)
    if tokens_so_far > MAX_LIVE_TOKENS_PER_RUN:
        return _build_failed_response(
            run_id=run_id,
            lead_id=lead.lead_id,
            deterministic_result=deterministic_result,
            live_model_used=live_model_used,
            failure=_LiveFailure(
                failed_agent=_AGENT_NAMES_BY_STAGE[_STAGE_QA],
                failure_stage=_STAGE_QA,
                error_code="token_budget_exceeded",
                fallback_reason=(
                    "Token budget exceeded after QA evaluator stage; "
                    "live run halted."
                ),
            ),
        )

    trace.append(
        _trace_entry(
            "qa_evaluator_agent",
            qa_output,
            input_summary=f"lead={lead.lead_id}",
            output_summary=(
                f"qa_score={qa_output.qa_score}; "
                f"recommendation={qa_output.recommendation.value}"
            ),
        )
    )

    live_result = LeadPipelineContractOutput(
        run_id=run_id,
        lead_id=lead.lead_id,
        intake=None,
        research=research_output,
        qualification=qualifier_output,
        strategy=strategist_output,
        email=email_output,
        qa=qa_output,
        trace=trace,
    )

    notes = (
        "live and deterministic outputs are both available; "
        f"tokens_used={tokens_so_far}/{MAX_LIVE_TOKENS_PER_RUN}"
    )
    comparison = _build_comparison(
        deterministic=deterministic_result,
        live=live_result,
        notes=notes,
    )

    return LivePipelineResponse(
        run_id=run_id,
        lead_id=lead.lead_id,
        run_mode="live",
        live_success=True,
        live_model_used=live_model_used,
        fallback_used=False,
        fallback_reason=None,
        deterministic_baseline_available=deterministic_result is not None,
        failed_agent=None,
        failure_stage=None,
        error_code=None,
        deterministic_result=deterministic_result,
        live_result=live_result,
        comparison=comparison,
    )


__all__ = [
    "MAX_LIVE_TOKENS_PER_RUN",
    "LIVE_GROQ_MODEL",
    "LivePipelineDisabledError",
    "LivePipelineKeyMissingError",
    "LivePipelineLeadNotFoundError",
    "_resolve_live_groq_model",
    "run_live_groq_pipeline_for_lead",
]
