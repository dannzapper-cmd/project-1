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


def get_model_service(
    provider: ModelProvider = ModelProvider.MOCK,
) -> BaseModelService:
    """Return the model service implementation for ``provider``.

    Phase 5.4 only ships the mock provider. ``OLLAMA``, ``GROQ`` and
    ``OPENAI`` are declared on the enum so contracts and routes can
    reference them, but invoking them raises ``NotImplementedError``
    (Phase 5.4 FIX 1) so a real provider call cannot happen
    accidentally — and the factory never silently falls back to mock.
    """

    if provider == ModelProvider.MOCK:
        return MockModelService()
    raise NotImplementedError(
        f"Provider '{provider.value}' is declared but not implemented "
        f"in Phase 5.4."
    )
