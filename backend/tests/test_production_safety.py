"""Block 11B production-safety checks."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def _preview_payload() -> dict:
    return {
        "input_type": "records_json",
        "records": [
            {
                "company_name": "Acme Corp",
                "industry": "SaaS",
            }
        ],
    }


def test_request_id_and_security_headers_present() -> None:
    test_app = create_app()
    with TestClient(test_app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-xss-protection"] == "1; mode=block"


def test_system_status_exposes_safe_booleans(monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "secret-demo-code")
    monkeypatch.setenv("ENABLE_LIVE_RESEARCH", "true")
    monkeypatch.setenv("EXA_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_LLM_ASSISTANT", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("BUILD_SHA", "abc1234")
    get_settings.cache_clear()

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            response = client.get("/api/system/status")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["backend_alive"] is True
    assert body["demo_access_required"] is True
    assert body["live_research_configured"] is True
    assert body["assistant_configured"] is True
    assert body["rate_limit_enabled"] is True
    assert body["storage_mode"] == "ephemeral"
    assert body["build_sha"] == "abc1234"
    assert "test-key" not in response.text
    assert "secret-demo-code" not in response.text


def test_demo_access_code_required_only_for_protected_actions(monkeypatch) -> None:
    monkeypatch.setenv("DEMO_ACCESS_CODE", "private-code")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            health_response = client.get("/health")
            missing_response = client.post("/api/intake/preview", json=_preview_payload())
            invalid_response = client.post(
                "/api/intake/preview",
                json=_preview_payload(),
                headers={"X-LeadForge-Demo-Key": "wrong-code"},
            )
            allowed_response = client.post(
                "/api/intake/preview",
                json=_preview_payload(),
                headers={"X-LeadForge-Demo-Key": "private-code"},
            )
    finally:
        get_settings.cache_clear()

    assert health_response.status_code == 200
    assert missing_response.status_code == 403
    assert missing_response.json()["error"] == "demo_access_required"
    assert "private demo access code" in missing_response.json()["detail"]
    assert invalid_response.status_code == 403
    assert invalid_response.json()["error"] == "demo_access_required"
    assert allowed_response.status_code == 200


def test_rate_limit_returns_safe_429(monkeypatch) -> None:
    monkeypatch.delenv("DEMO_ACCESS_CODE", raising=False)
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "2")
    get_settings.cache_clear()

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            first = client.post("/api/intake/preview", json=_preview_payload())
            second = client.post("/api/intake/preview", json=_preview_payload())
            third = client.post("/api/intake/preview", json=_preview_payload())
            health_response = client.get("/health")
    finally:
        get_settings.cache_clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["error"] == "rate_limited"
    assert third.headers["retry-after"]
    assert health_response.status_code == 200


def test_configured_max_leads_per_run_limits_processing(monkeypatch) -> None:
    monkeypatch.setenv("MAX_LEADS_PER_RUN", "3")
    get_settings.cache_clear()
    payload = {
        "leads": [
            {
                "lead_id": f"lead_{idx}",
                "company_name": f"Company {idx}",
                "industry": "SaaS",
            }
            for idx in range(5)
        ],
    }

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            response = client.post("/api/demo/pipeline/batch", json=payload)
    finally:
        get_settings.cache_clear()

    assert response.status_code == 422
    assert "up to 3 leads per run" in response.json()["detail"]

