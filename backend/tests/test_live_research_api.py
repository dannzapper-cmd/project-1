"""Integration tests for ``POST /api/research/live-company``.

The endpoint always returns HTTP 200 with a structured response;
disabled / unavailable / rate-limited / timeout / no-evidence /
provider-error states are encoded in the response body, not in
HTTP status codes. These tests cover the happy path plus every
guard (A–E) end-to-end.

No real Exa request is made — the underlying service's
``http_caller`` is patched at the module level so the FastAPI route
exercises the full request/response flow without touching the
network.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import live_research_service as live_module


_URL = "/api/research/live-company"


def _good_results(score: float = 0.7) -> dict[str, Any]:
    return {
        "results": [
            {
                "title": "Acme Corp expands EMEA sales",
                "url": "https://news.example.com/acme-emea",
                "score": score,
                "highlights": [
                    "Acme Corp announced an EMEA expansion this quarter, "
                    "doubling its sales headcount across France and Germany."
                ],
            }
        ]
    }


def _enable(monkeypatch: pytest.MonkeyPatch, *, daily_limit: int = 20) -> None:
    monkeypatch.setenv("ENABLE_LIVE_RESEARCH", "true")
    monkeypatch.setenv("EXA_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("LIVE_RESEARCH_DAILY_LIMIT", str(daily_limit))
    monkeypatch.setenv("LIVE_RESEARCH_MAX_RESULTS", "3")
    monkeypatch.setenv("LIVE_RESEARCH_TIMEOUT_SECONDS", "8")
    get_settings.cache_clear()
    live_module._reset_daily_counter_for_tests()


def _disable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENABLE_LIVE_RESEARCH", raising=False)
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    get_settings.cache_clear()
    live_module._reset_daily_counter_for_tests()


def test_endpoint_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable(monkeypatch)

    with TestClient(app) as client:
        response = client.post(
            _URL,
            json={"company_name": "Acme Corp"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disabled"
    assert body["enabled"] is False
    assert body["run_mode"] == "live_research"
    assert body["evidence_cards"] == []
    assert body["provider"] == "none"


def test_endpoint_unavailable_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_LIVE_RESEARCH", "true")
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    get_settings.cache_clear()
    live_module._reset_daily_counter_for_tests()

    with TestClient(app) as client:
        response = client.post(_URL, json={"company_name": "Acme Corp"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["provider"] == "none"


def test_endpoint_rejects_missing_company_name() -> None:
    """The Pydantic validator rejects an empty company_name with 422."""

    with TestClient(app) as client:
        response = client.post(_URL, json={"company_name": ""})

    assert response.status_code == 422


def test_endpoint_returns_evidence_cards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        live_module,
        "_default_http_caller",
        lambda *a, **kw: _good_results(),
    )

    with TestClient(app) as client:
        response = client.post(
            _URL,
            json={
                "company_name": "Acme Corp",
                "industry": "SaaS",
                "country": "Sweden",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["enabled"] is True
    assert body["provider"] == "exa"
    assert len(body["evidence_cards"]) == 1
    card = body["evidence_cards"][0]
    assert card["url"].startswith("https://")
    assert card["source_domain"] == "news.example.com"
    assert card["source_type"] == "live_web"
    assert card["confidence"] == "High"


def test_endpoint_no_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        live_module,
        "_default_http_caller",
        lambda *a, **kw: {"results": []},
    )

    with TestClient(app) as client:
        response = client.post(_URL, json={"company_name": "Acme Corp"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_evidence"
    assert body["evidence_cards"] == []


def test_endpoint_timeout_is_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)
    import httpx

    def fake_http(*a, **kw):  # noqa: ANN001
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(live_module, "_default_http_caller", fake_http)

    with TestClient(app) as client:
        response = client.post(_URL, json={"company_name": "Acme Corp"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "timeout"
    assert "warming up" in body["user_message"].lower()


def test_endpoint_enforces_daily_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch, daily_limit=1)
    monkeypatch.setattr(
        live_module,
        "_default_http_caller",
        lambda *a, **kw: _good_results(),
    )

    with TestClient(app) as client:
        first = client.post(_URL, json={"company_name": "Acme Corp"})
        second = client.post(_URL, json={"company_name": "Acme Corp"})

    assert first.status_code == 200
    assert first.json()["status"] == "ok"
    assert second.status_code == 200
    assert second.json()["status"] == "rate_limited"


def test_endpoint_does_not_leak_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(
        live_module,
        "_default_http_caller",
        lambda *a, **kw: _good_results(),
    )

    with TestClient(app) as client:
        response = client.post(_URL, json={"company_name": "Acme Corp"})

    text = response.text
    assert "test-only-not-a-real-key" not in text
