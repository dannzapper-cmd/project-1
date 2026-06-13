"""Tests for controlled Groq Live Demo Mode endpoints."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.live_pipeline import LivePipelineComparison, LivePipelineResponse
from app.services import demo_live_mode_service as live_demo_module
from app.services import live_pipeline_service as live_module

_STATUS_URL = "/api/demo/live/status"
_UNLOCK_URL = "/api/demo/live/unlock"
_RUN_URL = "/api/demo/live/run"
_DEMO_LEAD_ID = "lead_001"
_UNLOCK_CODE = "555588"


@pytest.fixture(autouse=True)
def _reset_live_demo_store() -> None:
    live_demo_module.demo_live_mode_store.clear()
    yield
    live_demo_module.demo_live_mode_store.clear()


def _enable_live_demo(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("LIVE_MODE_ENABLED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-only-not-a-real-key")
    get_settings.cache_clear()
    return "test-only-not-a-real-key"


def _unlock_session(client: TestClient) -> str:
    response = client.post(_UNLOCK_URL, json={"unlock_code": _UNLOCK_CODE})
    assert response.status_code == 200
    body = response.json()
    assert body["unlocked"] is True
    token = body["session_token"]
    assert isinstance(token, str) and token
    return token


def test_app_starts_without_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_live_status_unavailable_when_groq_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LIVE_MODE_ENABLED", "true")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get(_STATUS_URL)
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["groq_api_key_configured"] is False
    assert "groq_api_key_missing" in body["unavailable_reasons"]


def test_correct_demo_code_unlocks_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)
    try:
        with TestClient(app) as client:
            response = client.post(_UNLOCK_URL, json={"unlock_code": _UNLOCK_CODE})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["unlocked"] is True
    assert body["session_token"]


def test_wrong_code_does_not_unlock_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)
    try:
        with TestClient(app) as client:
            response = client.post(_UNLOCK_URL, json={"unlock_code": "000000"})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["unlocked"] is False
    assert body["session_token"] is None


def test_live_run_rejects_without_unlock(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_live_demo(monkeypatch)
    try:
        with TestClient(app) as client:
            response = client.post(
                _RUN_URL,
                json={"lead_ids": [_DEMO_LEAD_ID]},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["results"] == []
    assert "unlock" in (body["message"] or "").lower()


def test_max_leads_per_live_run_is_enforced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)
    try:
        with TestClient(app) as client:
            token = _unlock_session(client)
            response = client.post(
                _RUN_URL,
                json={"lead_ids": ["lead_001", "lead_002", "lead_003", "lead_004"]},
                headers={live_demo_module.LIVE_SESSION_HEADER: token},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert "Too many leads" in response.json()["detail"]


def test_rate_limit_blocks_excessive_live_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)
    monkeypatch.setenv("MAX_LIVE_RUNS_PER_SESSION_PER_DAY", "1")
    get_settings.cache_clear()

    def _fake_runner(lead_id: str, **kwargs) -> LivePipelineResponse:
        comparison = LivePipelineComparison(comparison_notes="ok")
        return LivePipelineResponse(
            run_id=f"live_{lead_id}",
            lead_id=lead_id,
            run_mode="live",
            live_success=True,
            live_model_used=live_module.LIVE_GROQ_MODEL,
            fallback_used=False,
            deterministic_baseline_available=True,
            comparison=comparison,
        )

    monkeypatch.setattr(live_demo_module, "run_live_groq_pipeline_for_lead", _fake_runner)

    try:
        with TestClient(app) as client:
            token = _unlock_session(client)
            headers = {live_demo_module.LIVE_SESSION_HEADER: token}
            first = client.post(
                _RUN_URL,
                json={"lead_ids": [_DEMO_LEAD_ID]},
                headers=headers,
            )
            second = client.post(
                _RUN_URL,
                json={"lead_ids": [_DEMO_LEAD_ID]},
                headers=headers,
            )
    finally:
        get_settings.cache_clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert "limit" in (second.json()["message"] or "").lower()


def test_missing_input_rejected_before_model_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)
    try:
        with TestClient(app) as client:
            token = _unlock_session(client)
            response = client.post(
                _RUN_URL,
                json={"lead_ids": []},
                headers={live_demo_module.LIVE_SESSION_HEADER: token},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code in {400, 422}


def test_invalid_pipeline_triggers_explicit_fallback_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)

    def _fake_runner(lead_id: str, **kwargs) -> LivePipelineResponse:
        comparison = LivePipelineComparison(
            comparison_notes="live run failed — no comparison available"
        )
        return LivePipelineResponse(
            run_id=f"live_{lead_id}",
            lead_id=lead_id,
            run_mode="live_failed",
            live_success=False,
            live_model_used=live_module.LIVE_GROQ_MODEL,
            fallback_used=True,
            fallback_reason="stubbed validation failure",
            deterministic_baseline_available=True,
            failed_agent="research_agent",
            failure_stage="research",
            error_code="agent_fallback",
            comparison=comparison,
        )

    monkeypatch.setattr(live_demo_module, "run_live_groq_pipeline_for_lead", _fake_runner)

    try:
        with TestClient(app) as client:
            token = _unlock_session(client)
            response = client.post(
                _RUN_URL,
                json={"lead_ids": [_DEMO_LEAD_ID]},
                headers={live_demo_module.LIVE_SESSION_HEADER: token},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["metadata"]["run_mode"] == "fallback"
    assert result["metadata"]["fallback_used"] is True


def test_deterministic_pipeline_still_works() -> None:
    with TestClient(app) as client:
        response = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")
    assert response.status_code == 200
    assert response.json()["lead_id"] == _DEMO_LEAD_ID


def test_status_response_contains_no_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live_demo(monkeypatch)
    try:
        with TestClient(app) as client:
            response = client.get(_STATUS_URL)
    finally:
        get_settings.cache_clear()

    text = json.dumps(response.json())
    assert "test-only-not-a-real-key" not in text
    assert "GROQ_API_KEY" not in text


def test_no_email_sending_introduced(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_live_demo(monkeypatch)

    def _fake_runner(lead_id: str, **kwargs) -> LivePipelineResponse:
        comparison = LivePipelineComparison(comparison_notes="ok")
        return LivePipelineResponse(
            run_id=f"live_{lead_id}",
            lead_id=lead_id,
            run_mode="live",
            live_success=True,
            live_model_used=live_module.LIVE_GROQ_MODEL,
            fallback_used=False,
            deterministic_baseline_available=True,
            comparison=comparison,
        )

    monkeypatch.setattr(live_demo_module, "run_live_groq_pipeline_for_lead", _fake_runner)

    try:
        with TestClient(app) as client:
            token = _unlock_session(client)
            response = client.post(
                _RUN_URL,
                json={"lead_ids": [_DEMO_LEAD_ID]},
                headers={live_demo_module.LIVE_SESSION_HEADER: token},
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    # Live demo run path must not import or invoke SMTP/email send helpers.
    import app.services.demo_live_mode_service as service_module

    source = open(service_module.__file__, encoding="utf-8").read().lower()
    assert "smtplib" not in source
    assert "send_email" not in source
    assert "sendmail" not in source
