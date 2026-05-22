"""Model service layer (Phase 5.4).

A clean, testable abstraction over future model providers. Only the
mock provider is implemented in Phase 5.4; every real-provider path
raises ``NotImplementedError`` so it is impossible to accidentally call
an LLM during this phase.

Hard guarantees:

* No network I/O. The module does not import ``requests``, ``httpx``,
  ``urllib``, ``aiohttp``, or any other HTTP/network client.
* No API keys read or required.
* No new pip dependencies (stdlib + already-installed Pydantic).
* :class:`MockModelService` is deterministic, in-memory, and clearly
  labelled: every response carries ``simulated=True``,
  ``finish_reason="mock_stop"``, and a content body that begins with
  ``[MOCK MODEL RESPONSE — no external model was called]``.
* Phase 5.4 FIX 4: :class:`BaseModelService` and :class:`MockModelService`
  are **plain Python classes**, not Pydantic models. Only the schemas
  in ``app.schemas.model`` are Pydantic.

Public surface:

* :func:`estimate_token_count`        -- deterministic token approximation.
* :func:`estimate_model_cost`         -- deterministic cost calculator.
* :func:`build_mock_response_content` -- deterministic mock body builder.
* :class:`BaseModelService`           -- abstract interface.
* :class:`MockModelService`           -- the only Phase 5.4 implementation.
* :func:`get_model_service`           -- factory; raises
  ``NotImplementedError`` for non-mock providers (FIX 1).
"""

from __future__ import annotations

import math
import os
import time

from app.schemas.model import (
    ModelConfig,
    ModelCostEstimate,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelUsage,
)

_MOCK_MARKER: str = "[MOCK MODEL RESPONSE — no external model was called]"
_MOCK_FINISH_REASON: str = "mock_stop"
_MOCK_LATENCY: str = "0ms"

# --------------------------------------------------------------------------- #
# Phase 5.5B — Groq provider rate table (USD per 1M tokens, public pricing). #
# Stored once here so GroqModelService can derive the per-1K rates that      #
# ModelConfig already accepts. Models not in this table fall back to        #
# whatever rates the caller passed on ModelConfig (default 0.0 / 0.0).      #
# --------------------------------------------------------------------------- #
_GROQ_DEFAULT_MODEL: str = "llama-3.1-8b-instant"
_GROQ_RATE_TABLE_PER_1M_USD: dict[str, tuple[float, float]] = {
    # model_name → (input_cost_per_1m, output_cost_per_1m)
    "llama-3.1-8b-instant": (0.05, 0.08),
    "openai/gpt-oss-20b": (0.075, 0.30),
}


# --------------------------------------------------------------------------- #
# Cost / token helpers                                                        #
# --------------------------------------------------------------------------- #


def estimate_token_count(text: str) -> int:
    """Deterministic word-based token approximation.

    Returns ``0`` for empty / whitespace-only text. Otherwise returns
    ``max(1, ceil(word_count * 1.3))``. The 1.3 factor is the same coarse
    rule-of-thumb used in many LLM cost calculators; it is intentionally
    a stdlib-only approximation, not a real tokenizer.
    """

    if not text or not text.strip():
        return 0
    word_count = len(text.split())
    return max(1, math.ceil(word_count * 1.3))


def estimate_model_cost(
    input_tokens: int,
    output_tokens: int,
    config: ModelConfig,
) -> ModelCostEstimate:
    """Deterministic cost calculation for one model call.

    The unit is per-1000-tokens (matching the convention every real
    provider uses). ``display_cost`` is computed here (Phase 5.4 FIX 3)
    and exposed on the returned ``ModelCostEstimate`` so callers do not
    have to format it themselves.
    """

    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("Token counts must be non-negative.")

    input_cost = (input_tokens / 1000.0) * config.cost_per_1k_input_tokens
    output_cost = (output_tokens / 1000.0) * config.cost_per_1k_output_tokens
    # Floating point can produce tiny negative values from a
    # mathematically-zero product (e.g. 0.0 * -0.0). Clamp to 0 so the
    # ge=0.0 field validator on ModelCostEstimate never fires
    # spuriously.
    input_cost = max(0.0, input_cost)
    output_cost = max(0.0, output_cost)
    total_cost = input_cost + output_cost
    display_cost = f"${total_cost:.4f}"

    return ModelCostEstimate(
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        display_cost=display_cost,
    )


# --------------------------------------------------------------------------- #
# Mock response body                                                          #
# --------------------------------------------------------------------------- #


def _last_user_message(request: ModelRequest) -> str | None:
    for message in reversed(request.messages):
        if message.role == ModelRole.USER:
            return message.content
    return None


def build_mock_response_content(request: ModelRequest) -> str:
    """Deterministic mock response body.

    Always starts with the ``[MOCK MODEL RESPONSE — no external model
    was called]`` marker. When present, the last user message is echoed
    as a short single-line snippet so the response is recognizably
    derived from the request — without pretending to be an LLM,
    generating sales emails, or producing any real agent output.
    """

    last_user = _last_user_message(request)
    lines: list[str] = [_MOCK_MARKER]

    if last_user is not None:
        snippet = " ".join(last_user.strip().split())
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        lines.append(f"Echoed user message: {snippet}")
    else:
        lines.append("No user message provided.")

    lines.append(
        "This response is generated deterministically by MockModelService "
        "for contract and routing verification. Replace with a real "
        "provider in a future phase."
    )

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Service classes (plain Python, per FIX 4)                                   #
# --------------------------------------------------------------------------- #


class BaseModelService:
    """Abstract interface for every model service implementation.

    Plain Python class — not a Pydantic model (FIX 4). Subclasses
    implement :meth:`complete` to turn a ``ModelRequest`` into a
    ``ModelResponse``.
    """

    def complete(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError(
            "BaseModelService.complete must be implemented by a subclass."
        )


class MockModelService(BaseModelService):
    """Deterministic, in-memory mock implementation.

    No network calls, no provider API, no real model invocation. The
    output is shaped exactly like a real ``ModelResponse`` so callers
    can integrate against the contract today and switch providers
    later without changing their code.
    """

    def complete(self, request: ModelRequest) -> ModelResponse:
        # Token accounting: join all message contents (separated by
        # newlines) and use the deterministic estimator. This mirrors the
        # behavior real chat-completion providers expose via their usage
        # objects: input tokens are the full prompt, output tokens are
        # the generated body.
        joined_input = "\n".join(message.content for message in request.messages)
        input_tokens = estimate_token_count(joined_input)

        content = build_mock_response_content(request)
        output_tokens = estimate_token_count(content)
        total_tokens = input_tokens + output_tokens

        usage = ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        cost = estimate_model_cost(input_tokens, output_tokens, request.config)

        return ModelResponse(
            request_id=request.request_id,
            provider=request.config.provider,
            model_name=request.config.model_name,
            content=content,
            usage=usage,
            cost=cost,
            latency=_MOCK_LATENCY,
            finish_reason=_MOCK_FINISH_REASON,
            simulated=True,
            raw_response=None,
        )


# --------------------------------------------------------------------------- #
# Factory                                                                     #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Phase 5.5B — Groq provider                                                  #
# --------------------------------------------------------------------------- #


def _groq_rates_per_1k(model_name: str) -> tuple[float, float] | None:
    """Return ``(input_per_1k, output_per_1k)`` for a known Groq model.

    ModelConfig accepts per-1K rates, so the per-1M pricing in the rate
    table is divided by 1000 here. Unknown models return ``None`` and
    the caller falls back to whatever rates were on ``ModelConfig``.
    """

    rates = _GROQ_RATE_TABLE_PER_1M_USD.get(model_name)
    if rates is None:
        return None
    input_per_1m, output_per_1m = rates
    return input_per_1m / 1000.0, output_per_1m / 1000.0


class GroqModelService(BaseModelService):
    """Real model service backed by the official Groq Python SDK.

    Safety guarantees:

    * The Groq SDK is imported lazily inside ``__init__`` so the rest of
      the application — and the rest of the model service module — can
      be imported on machines that do not have the ``groq`` package
      installed (e.g. when only the mock provider is needed).
    * ``GROQ_API_KEY`` is the only credential read; no key is logged or
      printed and no key is ever returned to a caller.
    * If no key is available, the constructor raises ``ValueError``
      before any client object is built. The factory never silently
      falls back to mock for Groq.
    * Network calls are confined to ``complete``; transport latency is
      measured with ``time.perf_counter`` per Phase 5.5B FIX 3.
    * Tests pass a fake / stub ``client`` via the FIX 1 dependency
      injection point so unit tests never make a real network call.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = _GROQ_DEFAULT_MODEL,
        timeout_seconds: int = 30,
        client: object | None = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError("GROQ_API_KEY is required for GroqModelService.")
        # The key is held on the instance only because the SDK client
        # needs it; it is never logged, printed, or returned in any
        # response or error message.
        self._api_key: str = resolved_key
        self.default_model: str = default_model
        self.timeout_seconds: int = timeout_seconds

        if client is None:
            # Lazy import so the broader codebase does not require the
            # groq package at import time. FIX 4: httpx is a transitive
            # dependency of the groq SDK; we never import it here.
            from groq import Groq

            self.client: object = Groq(
                api_key=self._api_key, timeout=float(timeout_seconds)
            )
        else:
            self.client = client

    def complete(self, request: ModelRequest) -> ModelResponse:
        # FIX 5: ModelRole values already match Groq's role strings.
        groq_messages = [
            {"role": m.role.value, "content": m.content}
            for m in request.messages
        ]
        model = request.config.model_name or self.default_model

        # FIX 3: latency measured with time.perf_counter.
        start = time.perf_counter()
        # Intentionally minimal kwargs — no logprobs, no logit_bias, no
        # top_logprobs, no message-level "name", no n != 1, no tools,
        # no live web search / browser / compound systems.
        completion = self.client.chat.completions.create(  # type: ignore[attr-defined]
            messages=groq_messages,
            model=model,
            temperature=request.config.temperature,
            max_tokens=request.config.max_tokens,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Defensive parsing — every field we touch on the SDK response
        # is wrapped in ``getattr(..., default)`` so a future SDK schema
        # tweak cannot crash the service.
        choices = getattr(completion, "choices", None) or []
        content: str = ""
        finish_reason: str = "stop"
        if choices:
            first = choices[0]
            message = getattr(first, "message", None)
            if message is not None:
                content = getattr(message, "content", "") or ""
            finish_reason = getattr(first, "finish_reason", None) or "stop"

        usage_obj = getattr(completion, "usage", None)
        prompt_tokens = getattr(usage_obj, "prompt_tokens", None)
        completion_tokens = getattr(usage_obj, "completion_tokens", None)
        total_tokens = getattr(usage_obj, "total_tokens", None)

        if prompt_tokens is None or completion_tokens is None:
            # Fallback to deterministic estimation when the provider did
            # not return a usage object.
            joined_input = "\n".join(m.content for m in request.messages)
            estimated_input = estimate_token_count(joined_input)
            estimated_output = estimate_token_count(content)
            prompt_tokens = (
                prompt_tokens if prompt_tokens is not None else estimated_input
            )
            completion_tokens = (
                completion_tokens
                if completion_tokens is not None
                else estimated_output
            )
            total_tokens = (
                total_tokens
                if total_tokens is not None
                else prompt_tokens + completion_tokens
            )
        elif total_tokens is None:
            total_tokens = prompt_tokens + completion_tokens

        usage = ModelUsage(
            input_tokens=int(prompt_tokens),
            output_tokens=int(completion_tokens),
            total_tokens=int(total_tokens),
        )

        # Compute cost using Groq's published rate for this model when
        # known, falling back to whatever rates were on ModelConfig
        # (default 0.0/0.0) when the model is not in the table.
        groq_rates = _groq_rates_per_1k(model)
        if groq_rates is not None:
            cost_config = ModelConfig(
                provider=ModelProvider.GROQ,
                model_name=model,
                temperature=request.config.temperature,
                max_tokens=request.config.max_tokens,
                timeout_seconds=request.config.timeout_seconds,
                cost_per_1k_input_tokens=groq_rates[0],
                cost_per_1k_output_tokens=groq_rates[1],
            )
        else:
            cost_config = request.config
        cost = estimate_model_cost(usage.input_tokens, usage.output_tokens, cost_config)

        return ModelResponse(
            request_id=request.request_id,
            provider=ModelProvider.GROQ,
            model_name=model,
            content=content,
            usage=usage,
            cost=cost,
            latency=f"{elapsed_ms}ms",
            finish_reason=str(finish_reason),
            simulated=False,
            raw_response=None,
        )


# --------------------------------------------------------------------------- #
# Factory                                                                     #
# --------------------------------------------------------------------------- #


def get_model_service(
    provider: ModelProvider = ModelProvider.MOCK,
) -> BaseModelService:
    """Return the model service implementation for ``provider``.

    * ``MOCK``  -> :class:`MockModelService` (always available).
    * ``GROQ``  -> :class:`GroqModelService` (Phase 5.5B). Requires
      ``GROQ_API_KEY``; if the key is missing the constructor raises
      ``ValueError``. The factory NEVER silently falls back to mock.
    * ``OLLAMA`` / ``OPENAI`` -> ``NotImplementedError`` (still
      declared on the enum so contracts and routes can reference them,
      but not implemented in Phase 5.5B).
    """

    if provider == ModelProvider.MOCK:
        return MockModelService()
    if provider == ModelProvider.GROQ:
        return GroqModelService()
    raise NotImplementedError(
        f"Provider '{provider.value}' is declared but not implemented "
        f"in Phase 5.5B."
    )
