"""Unit tests for the Phase 5.5B GroqModelService.

No real Groq network call is made anywhere in this file. The
:class:`GroqModelService` is constructed with a fake / stub client
injected via the FIX 1 ``client`` parameter, so the entire SDK call
path is exercised in-process and deterministically.

Tests assume ``GROQ_API_KEY`` is NOT set in the environment for the
"no-key" cases; ``monkeypatch.delenv`` is used to guarantee that.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.model import (
    ModelConfig,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
)
from app.services.model_service import (
    GroqModelService,
    MockModelService,
    _groq_rates_per_1k,
    get_model_service,
)


# --------------------------------------------------------------------------- #
# Fake Groq client                                                            #
# --------------------------------------------------------------------------- #


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str, finish_reason: str = "stop") -> None:
        self.message = _FakeMessage(content)
        self.finish_reason = finish_reason


class _FakeUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens


class _FakeCompletion:
    def __init__(
        self,
        content: str,
        prompt_tokens: int = 50,
        completion_tokens: int = 25,
        finish_reason: str = "stop",
    ) -> None:
        self.choices = [_FakeChoice(content, finish_reason)]
        self.usage = _FakeUsage(prompt_tokens, completion_tokens)


class _FakeCompletions:
    def __init__(
        self,
        content: str = "LeadForge Groq check OK",
        prompt_tokens: int = 50,
        completion_tokens: int = 25,
    ) -> None:
        self._content = content
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self.last_call_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _FakeCompletion:
        self.last_call_kwargs = kwargs
        return _FakeCompletion(
            content=self._content,
            prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
        )


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeGroqClient:
    """Minimal stand-in for ``groq.Groq`` covering the exact surface
    ``GroqModelService.complete`` uses."""

    def __init__(
        self,
        content: str = "LeadForge Groq check OK",
        prompt_tokens: int = 50,
        completion_tokens: int = 25,
    ) -> None:
        self.completions = _FakeCompletions(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.chat = _FakeChat(self.completions)


def _request(model_name: str = "llama-3.1-8b-instant") -> ModelRequest:
    return ModelRequest(
        messages=[ModelMessage(role=ModelRole.USER, content="hi")],
        config=ModelConfig(provider=ModelProvider.GROQ, model_name=model_name),
        request_id="unit-test",
    )


# --------------------------------------------------------------------------- #
# 1. Missing API key                                                          #
# --------------------------------------------------------------------------- #


def test_01_groq_service_without_api_key_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """1: GroqModelService without an api key raises ValueError."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        GroqModelService()
    assert "GROQ_API_KEY" in str(excinfo.value)


def test_02_factory_raises_value_error_when_env_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """2: get_model_service(ModelProvider.GROQ) raises ValueError if env key missing."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        get_model_service(ModelProvider.GROQ)
    assert "GROQ_API_KEY" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# 3-4. Rate conversion                                                        #
# --------------------------------------------------------------------------- #


def test_03_llama_instant_rates_converted_to_per_1k() -> None:
    """3: llama-3.1-8b-instant rates converted correctly to per-1K.

    Published Groq rates: $0.05 / $0.08 per 1M tokens. Per 1K: $0.00005 / $0.00008.
    """

    rates = _groq_rates_per_1k("llama-3.1-8b-instant")
    assert rates is not None
    input_per_1k, output_per_1k = rates
    assert input_per_1k == pytest.approx(0.00005)
    assert output_per_1k == pytest.approx(0.00008)


def test_04_gpt_oss_20b_rates_converted_to_per_1k() -> None:
    """4: openai/gpt-oss-20b rates converted correctly.

    Published Groq rates: $0.075 / $0.30 per 1M. Per 1K: $0.000075 / $0.0003.
    """

    rates = _groq_rates_per_1k("openai/gpt-oss-20b")
    assert rates is not None
    input_per_1k, output_per_1k = rates
    assert input_per_1k == pytest.approx(0.000075)
    assert output_per_1k == pytest.approx(0.0003)


# --------------------------------------------------------------------------- #
# 5-8. Fake-client completion path                                            #
# --------------------------------------------------------------------------- #


def test_05_complete_uses_injected_fake_client_no_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """5: complete() can be tested with a fake client; no network call occurs.

    The injected fake client also captures the kwargs ``create`` was
    called with, so we can assert the SDK is invoked with the exact
    fields the contract specifies and no banned ones (no logprobs,
    logit_bias, top_logprobs, message-level "name", n != 1).
    """

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    fake = _FakeGroqClient()
    service = GroqModelService(api_key="test-key", client=fake)
    response = service.complete(_request())

    assert isinstance(response, ModelResponse)
    assert fake.completions.last_call_kwargs is not None
    kwargs = fake.completions.last_call_kwargs
    assert kwargs["model"] == "llama-3.1-8b-instant"
    assert kwargs["messages"] == [{"role": "user", "content": "hi"}]
    for banned in ("logprobs", "logit_bias", "top_logprobs", "n", "tools", "tool_choice"):
        assert banned not in kwargs, f"banned kwarg {banned!r} was sent to Groq"


def test_06_response_provider_is_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    """6: mocked Groq completion returns ModelResponse with provider="groq"."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service = GroqModelService(api_key="test-key", client=_FakeGroqClient())
    response = service.complete(_request())
    assert response.provider == ModelProvider.GROQ
    assert response.provider.value == "groq"


def test_07_response_simulated_is_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """7: mocked Groq completion returns simulated=False."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service = GroqModelService(api_key="test-key", client=_FakeGroqClient())
    response = service.complete(_request())
    assert response.simulated is False


def test_08_response_usage_and_cost_are_computed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """8: mocked Groq completion computes usage and cost.

    With 100k input + 100k output on llama-3.1-8b-instant, expected
    cost is:
        input:  100_000 / 1000 * 0.00005 = $0.005
        output: 100_000 / 1000 * 0.00008 = $0.008
        total:  $0.013  ->  display "$0.0130"
    """

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    fake = _FakeGroqClient(prompt_tokens=100_000, completion_tokens=100_000)
    service = GroqModelService(api_key="test-key", client=fake)
    response = service.complete(_request())

    assert response.usage.input_tokens == 100_000
    assert response.usage.output_tokens == 100_000
    assert response.usage.total_tokens == 200_000
    assert response.cost.input_cost == pytest.approx(0.005)
    assert response.cost.output_cost == pytest.approx(0.008)
    assert response.cost.total_cost == pytest.approx(0.013)
    assert response.cost.display_cost == "$0.0130"
    # Latency is measured per FIX 3 — non-negative ms suffix.
    assert response.latency.endswith("ms")
    assert int(response.latency.removesuffix("ms")) >= 0


# --------------------------------------------------------------------------- #
# 9. Other providers still NotImplementedError                                #
# --------------------------------------------------------------------------- #


def test_09_other_providers_still_raise_not_implemented(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """9: OLLAMA and OPENAI still raise NotImplementedError."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    for provider in (ModelProvider.OLLAMA, ModelProvider.OPENAI):
        with pytest.raises(NotImplementedError) as excinfo:
            get_model_service(provider)
        assert provider.value in str(excinfo.value)
        assert "Phase 5.5B" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# 10. MockModelService still works                                            #
# --------------------------------------------------------------------------- #


def test_10_mock_model_service_still_works() -> None:
    """10: MockModelService tests still pass (regression smoke check)."""

    service = MockModelService()
    response = service.complete(_request(model_name="mock-leadforge-model"))
    # Provider is taken from the request config — here MOCK is not the
    # default because the request was crafted for Groq tests. We just
    # confirm the mock path still produces a valid response with the
    # mock-stop finish reason.
    assert response.finish_reason == "mock_stop"
    assert response.simulated is True


# --------------------------------------------------------------------------- #
# Extra: explicit-key path bypasses the env var entirely                       #
# --------------------------------------------------------------------------- #


def test_extra_explicit_key_bypasses_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicitly-passed api_key must work even when GROQ_API_KEY is unset."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service = GroqModelService(api_key="explicit-key", client=_FakeGroqClient())
    response = service.complete(_request())
    assert response.simulated is False
    assert response.provider == ModelProvider.GROQ


def test_extra_unknown_model_falls_back_to_request_config_rates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """For a model not in the Groq rate table, cost falls back to the
    rates carried on the request's ModelConfig (default 0.0/0.0)."""

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    service = GroqModelService(api_key="test-key", client=_FakeGroqClient())
    req = ModelRequest(
        messages=[ModelMessage(role=ModelRole.USER, content="hi")],
        config=ModelConfig(
            provider=ModelProvider.GROQ,
            model_name="some-future-model-not-in-table",
        ),
    )
    response = service.complete(req)
    assert response.cost.total_cost == 0.0
    assert response.cost.display_cost == "$0.0000"
