"""Unit tests for the Phase 5.4 model service foundation.

Test IDs map 1:1 to the Phase 5.4 spec (S-01 .. S-15).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.model import (
    ModelConfig,
    ModelCostEstimate,
    ModelMessage,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelRole,
    ModelUsage,
)
from app.services.model_service import (
    BaseModelService,
    MockModelService,
    build_mock_response_content,
    estimate_model_cost,
    estimate_token_count,
    get_model_service,
)

_MOCK_MARKER = "[MOCK MODEL RESPONSE — no external model was called]"


def _user_message(content: str = "Hello LeadForge") -> ModelMessage:
    return ModelMessage(role=ModelRole.USER, content=content)


# --------------------------------------------------------------------------- #
# Schema validation                                                            #
# --------------------------------------------------------------------------- #


def test_s01_model_message_rejects_empty_content() -> None:
    """S-01: ModelMessage rejects empty content (FIX 2)."""

    with pytest.raises(ValidationError):
        ModelMessage(role=ModelRole.USER, content="")


def test_s02_model_request_rejects_empty_messages() -> None:
    """S-02: ModelRequest rejects an empty messages list (FIX 2)."""

    with pytest.raises(ValidationError):
        ModelRequest(messages=[])


def test_s03_model_config_defaults() -> None:
    """S-03: ModelConfig defaults to provider=mock and the mock model name."""

    cfg = ModelConfig()
    assert cfg.provider == ModelProvider.MOCK
    assert cfg.provider.value == "mock"
    assert cfg.model_name == "mock-leadforge-model"
    assert cfg.temperature == 0.0
    assert cfg.max_tokens == 512
    assert cfg.timeout_seconds == 30
    assert cfg.cost_per_1k_input_tokens == 0.0
    assert cfg.cost_per_1k_output_tokens == 0.0


def test_s04_temperature_bounded_zero_to_two() -> None:
    """S-04: ModelConfig.temperature rejects values < 0 or > 2."""

    with pytest.raises(ValidationError):
        ModelConfig(temperature=-0.1)
    with pytest.raises(ValidationError):
        ModelConfig(temperature=2.1)
    # Boundary values must be accepted.
    ModelConfig(temperature=0.0)
    ModelConfig(temperature=2.0)


def test_s05_max_tokens_minimum_one() -> None:
    """S-05: ModelConfig.max_tokens rejects values < 1."""

    with pytest.raises(ValidationError):
        ModelConfig(max_tokens=0)
    with pytest.raises(ValidationError):
        ModelConfig(max_tokens=-5)
    ModelConfig(max_tokens=1)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def test_s06_estimate_token_count_deterministic_and_zero_for_empty() -> None:
    """S-06: estimate_token_count is deterministic and returns 0 for empty text."""

    assert estimate_token_count("") == 0
    assert estimate_token_count("   ") == 0
    assert estimate_token_count("\n\t  \n") == 0
    # Determinism: same input → same output across calls.
    sample = "LeadForge model service foundation phase test"
    first = estimate_token_count(sample)
    second = estimate_token_count(sample)
    assert first == second
    # Non-empty input must produce at least 1 token.
    assert estimate_token_count("a") >= 1


def test_s07_estimate_cost_returns_zero_when_rates_zero() -> None:
    """S-07: estimate_model_cost returns zero cost when rates are zero."""

    cost = estimate_model_cost(input_tokens=1000, output_tokens=500, config=ModelConfig())
    assert cost.input_cost == 0.0
    assert cost.output_cost == 0.0
    assert cost.total_cost == 0.0
    assert cost.display_cost == "$0.0000"
    assert cost.currency == "USD"


def test_s08_estimate_cost_returns_expected_nonzero_cost() -> None:
    """S-08: estimate_model_cost returns the expected non-zero cost.

    1000 input tokens at $0.50/1K  → $0.50
    500  output tokens at $1.50/1K → $0.75
    total                          → $1.25, display "$1.2500".
    """

    cfg = ModelConfig(
        cost_per_1k_input_tokens=0.5,
        cost_per_1k_output_tokens=1.5,
    )
    cost = estimate_model_cost(1000, 500, cfg)
    assert cost.input_cost == pytest.approx(0.5)
    assert cost.output_cost == pytest.approx(0.75)
    assert cost.total_cost == pytest.approx(1.25)
    assert cost.display_cost == "$1.2500"


# --------------------------------------------------------------------------- #
# MockModelService                                                            #
# --------------------------------------------------------------------------- #


def test_s09_mock_complete_returns_model_response() -> None:
    """S-09: MockModelService.complete returns a ModelResponse."""

    svc = MockModelService()
    resp = svc.complete(ModelRequest(messages=[_user_message()]))
    assert isinstance(resp, ModelResponse)
    assert resp.provider == ModelProvider.MOCK
    assert resp.model_name == "mock-leadforge-model"


def test_s10_mock_response_is_simulated() -> None:
    """S-10: MockModelService response has simulated=True."""

    svc = MockModelService()
    resp = svc.complete(ModelRequest(messages=[_user_message()]))
    assert resp.simulated is True
    assert resp.finish_reason == "mock_stop"
    assert resp.latency == "0ms"


def test_s11_mock_response_content_contains_marker() -> None:
    """S-11: MockModelService response content contains the mock marker."""

    svc = MockModelService()
    resp = svc.complete(
        ModelRequest(messages=[_user_message("Test prompt for the marker.")])
    )
    assert _MOCK_MARKER in resp.content
    # The mock body must not pretend to be an LLM or include sales text.
    assert "I am an AI" not in resp.content.lower()
    assert "subject:" not in resp.content.lower()


def test_s12_mock_usage_total_equals_input_plus_output() -> None:
    """S-12: MockModelService usage.total_tokens == input_tokens + output_tokens."""

    svc = MockModelService()
    resp = svc.complete(
        ModelRequest(messages=[_user_message("Total token reconciliation check.")])
    )
    assert resp.usage.total_tokens == resp.usage.input_tokens + resp.usage.output_tokens
    assert resp.usage.input_tokens >= 1
    assert resp.usage.output_tokens >= 1


# --------------------------------------------------------------------------- #
# Factory                                                                     #
# --------------------------------------------------------------------------- #


def test_s13_factory_returns_mock_service_for_mock_provider() -> None:
    """S-13: get_model_service(ModelProvider.MOCK) returns a MockModelService."""

    svc = get_model_service(ModelProvider.MOCK)
    assert isinstance(svc, MockModelService)
    assert isinstance(svc, BaseModelService)


def test_s14_factory_raises_not_implemented_for_groq() -> None:
    """S-14: get_model_service(ModelProvider.GROQ) raises NotImplementedError
    with a clear, provider-aware message (FIX 1).

    Also asserts the same for OLLAMA and OPENAI so it is structurally
    impossible to accidentally fall back to the mock for a real provider.
    """

    for provider in (ModelProvider.GROQ, ModelProvider.OLLAMA, ModelProvider.OPENAI):
        with pytest.raises(NotImplementedError) as excinfo:
            get_model_service(provider)
        message = str(excinfo.value)
        assert provider.value in message
        assert "Phase 5.4" in message


# --------------------------------------------------------------------------- #
# ModelResponse composition                                                   #
# --------------------------------------------------------------------------- #


def test_s15_model_response_validates_required_fields() -> None:
    """S-15: ModelResponse validates provider, usage, cost and content."""

    usage = ModelUsage(input_tokens=10, output_tokens=20, total_tokens=30)
    cost = ModelCostEstimate(
        input_cost=0.0,
        output_cost=0.0,
        total_cost=0.0,
        display_cost="$0.0000",
    )
    response = ModelResponse(
        provider=ModelProvider.MOCK,
        model_name="mock-leadforge-model",
        content="hello",
        usage=usage,
        cost=cost,
    )
    assert response.provider == ModelProvider.MOCK
    assert response.simulated is True  # default

    # Missing required fields must raise ValidationError.
    with pytest.raises(ValidationError):
        ModelResponse(  # type: ignore[call-arg]
            provider=ModelProvider.MOCK,
            model_name="mock-leadforge-model",
            content="hello",
        )

    # raw_response is optional and defaults to None.
    assert response.raw_response is None


def test_extra_mock_response_via_build_mock_response_content_is_deterministic() -> None:
    """Auxiliary determinism check: building the mock content twice for
    the same request yields byte-identical output."""

    request = ModelRequest(
        messages=[_user_message("Determinism probe.")],
        request_id="probe-001",
    )
    first = build_mock_response_content(request)
    second = build_mock_response_content(request)
    assert first == second
    assert _MOCK_MARKER in first
