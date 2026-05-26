"""Unit tests for ``app.services.live_research_service``.

No real Exa request is ever issued — the tests inject an
``http_caller`` stub and toggle ``ENABLE_LIVE_RESEARCH`` /
``EXA_API_KEY`` via ``monkeypatch``.

The tests cover:

- Disabled by default (no env vars).
- Missing API key.
- Insufficient input (Guard C).
- Query length cap (Guard C).
- Successful search → structured cards with citations.
- Empty / weak evidence (Guard E).
- Provider timeout (Guard D).
- Provider error mapping.
- Daily limit enforcement (Guard B).
- No LLM is reachable from the service (Guard A defended at the
  module-import level).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.core.config import get_settings
from app.schemas.common import Confidence
from app.schemas.live_research import LiveResearchRequest
from app.services import live_research_service as live_research_module
from app.services.live_research_service import (
    QUERY_MAX_LENGTH,
    _build_query,
    _reset_daily_counter_for_tests,
    run_live_research,
)


def _enable(monkeypatch: pytest.MonkeyPatch, *, daily_limit: int = 20) -> None:
    monkeypatch.setenv("ENABLE_LIVE_RESEARCH", "true")
    monkeypatch.setenv("EXA_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("LIVE_RESEARCH_DAILY_LIMIT", str(daily_limit))
    monkeypatch.setenv("LIVE_RESEARCH_MAX_RESULTS", "3")
    monkeypatch.setenv("LIVE_RESEARCH_TIMEOUT_SECONDS", "8")
    get_settings.cache_clear()
    _reset_daily_counter_for_tests()


def _disable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_LIVE_RESEARCH", raising=False)
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    get_settings.cache_clear()
    _reset_daily_counter_for_tests()


def _good_results(score: float = 0.7) -> dict[str, Any]:
    return {
        "results": [
            {
                "title": "Acme Corp expands EMEA sales",
                "url": "https://news.example.com/acme-emea",
                "score": score,
                "highlights": [
                    "Acme Corp announced an EMEA expansion this "
                    "quarter, doubling its sales headcount across "
                    "France and Germany."
                ],
            },
            {
                "title": "Acme Corp earnings update",
                "url": "https://www.example.org/acme/earnings",
                "score": score - 0.1,
                "highlights": [
                    "Quarterly revenue rose 12% as the company "
                    "invested in new go-to-market operations."
                ],
            },
        ]
    }


def test_service_does_not_import_groq_or_llm_paths() -> None:
    """Guard A — no LLM paths are reachable from this module."""

    src = live_research_module.__file__
    assert src is not None
    with open(src, encoding="utf-8") as handle:
        text = handle.read()

    forbidden = ["from groq", "import groq", "model_service", "GroqModelService"]
    for needle in forbidden:
        assert needle not in text, (
            f"Live research service must not reference {needle!r} (Guard A)."
        )


def test_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable(monkeypatch)
    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=lambda *a, **kw: pytest.fail("must not call provider"),
    )
    assert response.enabled is False
    assert response.status == "disabled"
    assert response.provider == "none"
    assert response.evidence_cards == []
    assert response.run_mode == "live_research"
    assert "disabled" in response.user_message.lower()


def test_missing_api_key_returns_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_LIVE_RESEARCH", "true")
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    get_settings.cache_clear()
    _reset_daily_counter_for_tests()

    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=lambda *a, **kw: pytest.fail("must not call provider"),
    )
    assert response.enabled is True
    assert response.status == "unavailable"
    assert response.provider == "none"
    assert response.evidence_cards == []
    assert "api key" in response.user_message.lower()


def test_insufficient_input_when_company_name_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guard C — must refuse to construct a query without a company."""

    _enable(monkeypatch)
    # The schema rejects an empty company name; mirror by passing
    # only whitespace through ``model_construct`` so we exercise the
    # service-level guard rather than the validator.
    request = LiveResearchRequest.model_construct(company_name="   ")
    response = run_live_research(
        request,
        http_caller=lambda *a, **kw: pytest.fail("must not call provider"),
    )
    assert response.status == "insufficient_input"
    assert response.query_used is None


def test_query_length_cap_truncates_to_120_chars() -> None:
    """Guard C — query never exceeds 120 chars."""

    long_industry = "x" * 119  # within Pydantic field cap, still triggers truncation
    request = LiveResearchRequest(
        company_name="Acme Corp",
        industry=long_industry,
        country="Sweden",
    )
    query = _build_query(request)
    assert query is not None
    assert len(query) <= QUERY_MAX_LENGTH
    assert query.startswith("Acme Corp ")


def test_successful_search_returns_cited_cards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)

    captured: dict[str, Any] = {}

    def fake_http(url, payload, headers, timeout):  # noqa: ANN001
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _good_results()

    response = run_live_research(
        LiveResearchRequest(
            company_name="Acme Corp",
            industry="SaaS",
            country="Sweden",
        ),
        http_caller=fake_http,
    )

    assert response.status == "ok"
    assert response.enabled is True
    assert response.provider == "exa"
    assert len(response.evidence_cards) == 2
    first = response.evidence_cards[0]
    assert first.url.startswith("https://")
    assert first.source_domain == "news.example.com"
    assert first.confidence == Confidence.HIGH
    assert first.source_type == "live_web"
    assert "Acme Corp" in first.why_it_matters
    # Ensure why_it_matters is NOT a paraphrase of the snippet (Guard A).
    assert first.snippet not in first.why_it_matters
    assert response.confidence == Confidence.HIGH
    assert len(response.sources) == 2
    assert response.sources[0].domain == "news.example.com"
    # Provider input safety: payload contains the truncated query and
    # the API key is sent in headers, never logged in the response.
    assert "Acme Corp" in captured["payload"]["query"]
    assert captured["headers"]["x-api-key"] == "test-only-not-a-real-key"
    assert captured["timeout"] == 8.0


def test_no_evidence_when_results_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)

    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=lambda *a, **kw: {"results": []},
    )

    assert response.status == "no_evidence"
    assert response.evidence_cards == []
    assert response.confidence == Confidence.LOW
    assert response.information_risks  # honesty surface


def test_filters_short_snippets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard E — snippets below 40 chars are dropped."""

    _enable(monkeypatch)
    payload = {
        "results": [
            {
                "title": "Acme",
                "url": "https://example.com/x",
                "score": 0.9,
                "highlights": ["too short"],
            }
        ]
    }
    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=lambda *a, **kw: payload,
    )
    assert response.status == "no_evidence"
    assert response.evidence_cards == []


def test_filters_all_low_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard E — if every kept card is low-confidence, surface no-evidence."""

    _enable(monkeypatch)
    payload = _good_results(score=0.1)  # all low confidence
    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=lambda *a, **kw: payload,
    )
    assert response.status == "no_evidence"


def test_provider_timeout_returns_structured_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guard D — Render cold-start friendly timeout response."""

    _enable(monkeypatch)
    import httpx

    def fake_http(*a, **kw):  # noqa: ANN001
        raise httpx.TimeoutException("timeout")

    # Reach the live caller via an intentional re-raise. We bypass the
    # injected hook and instead patch the default httpx caller so we
    # also exercise the timeout-classifying branch in production code.
    monkeypatch.setattr(
        "app.services.live_research_service._default_http_caller", fake_http
    )
    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
    )
    assert response.status == "timeout"
    assert "warming up" in response.user_message
    assert response.evidence_cards == []


def test_provider_error_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)

    def fake_http(*a, **kw):  # noqa: ANN001
        raise live_research_module._LiveResearchProviderError("boom")

    monkeypatch.setattr(
        "app.services.live_research_service._default_http_caller", fake_http
    )
    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
    )
    assert response.status == "provider_error"
    assert response.evidence_cards == []


def test_daily_limit_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard B — in-process counter rejects the (limit+1)th request."""

    _enable(monkeypatch, daily_limit=2)

    def fake_http(*a, **kw):  # noqa: ANN001
        return _good_results()

    first = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=fake_http,
    )
    second = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=fake_http,
    )
    third = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
        http_caller=fake_http,
    )

    assert first.status == "ok"
    assert second.status == "ok"
    assert third.status == "rate_limited"
    assert third.estimated_request_count == 2  # not incremented past cap
    assert "limit" in third.user_message.lower()


def test_unknown_status_code_maps_to_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider non-200 / non-timeout response surfaces provider_error."""

    _enable(monkeypatch)

    def fake_http(*a, **kw):  # noqa: ANN001
        raise live_research_module._LiveResearchProviderError(
            "Exa returned HTTP 502"
        )

    monkeypatch.setattr(
        "app.services.live_research_service._default_http_caller", fake_http
    )
    response = run_live_research(
        LiveResearchRequest(company_name="Acme Corp"),
    )
    assert response.status == "provider_error"
