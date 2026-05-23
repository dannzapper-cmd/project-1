"""Block 8.3 — integration tests for POST /api/demo/pipeline/live-groq/{lead_id}.

No real Groq call is made. The endpoint is gated by
``ENABLE_LIVE_MODEL_PIPELINE`` and ``GROQ_API_KEY``; tests either delete
both env vars (to confirm the disabled-by-default behaviour) or set the
opt-in flag with a synthetic placeholder API key and stub the live
pipeline service so the actual provider is never reached.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.live_pipeline import (
    LivePipelineComparison,
    LivePipelineResponse,
)
from app.services import live_pipeline_service as live_module
from app.services import telemetry_service as telemetry_module

_LIVE_URL = "/api/demo/pipeline/live-groq/{lead_id}"
_DEMO_LEAD_ID = "lead_001"


# --------------------------------------------------------------------------- #
# Pre-state expectation check (Block 8.3 prompt requirement)                 #
# --------------------------------------------------------------------------- #


def test_repo_state_block_8_3_baseline_endpoints_present() -> None:
    """Sanity check: the Block 8.1 / 8.2 surfaces the new endpoint
    builds on must already be in place. Failing this test signals a
    dirty/unexpected ``main`` state."""

    with TestClient(app) as client:
        deterministic = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")
        telemetry_runs = client.get("/api/demo/telemetry/runs")

    assert deterministic.status_code == 200
    assert telemetry_runs.status_code == 200


# --------------------------------------------------------------------------- #
# Gating tests                                                                #
# --------------------------------------------------------------------------- #


def test_live_endpoint_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The live endpoint must be off until both env vars are set."""

    monkeypatch.delenv("ENABLE_LIVE_MODEL_PIPELINE", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.post(_LIVE_URL.format(lead_id=_DEMO_LEAD_ID))
    finally:
        get_settings.cache_clear()

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "ENABLE_LIVE_MODEL_PIPELINE" in detail


def test_live_endpoint_returns_503_when_groq_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.post(_LIVE_URL.format(lead_id=_DEMO_LEAD_ID))
    finally:
        get_settings.cache_clear()

    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_live_endpoint_returns_404_for_unknown_lead(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-only-not-a-real-key")
    get_settings.cache_clear()

    # Patch GroqModelService construction so the real Groq client is
    # never built. The endpoint should reject the unknown lead before
    # the model is even resolved or the provider touched.
    class _FakeService:
        def complete(self, request):  # noqa: ANN001
            raise RuntimeError("must not be called for unknown lead")

    monkeypatch.setattr(
        "app.services.model_service.GroqModelService",
        lambda *a, **kw: _FakeService(),
    )

    try:
        with TestClient(app) as client:
            response = client.post(_LIVE_URL.format(lead_id="lead_does_not_exist"))
    finally:
        get_settings.cache_clear()

    assert response.status_code == 404
    assert "lead_does_not_exist" in response.json()["detail"]


# --------------------------------------------------------------------------- #
# Live-failure shape tests                                                    #
# --------------------------------------------------------------------------- #


def _enable_live(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-only-not-a-real-key")
    get_settings.cache_clear()


def _patch_runner_to_failure(
    monkeypatch: pytest.MonkeyPatch, *, error_code: str
) -> None:
    """Replace the live runner with one that always reports a failure.

    Tests use this to assert HTTP-level shape without exercising any
    real provider network call.
    """

    def _fake_runner(lead_id: str, **kwargs) -> LivePipelineResponse:
        comparison = LivePipelineComparison(
            fit_score_delta=None,
            priority_changed=None,
            qa_score_delta=None,
            email_subject_changed=None,
            risk_level_changed=None,
            live_summary=None,
            deterministic_summary="fit=70 priority=Medium",
            comparison_notes="live run failed — no comparison available",
        )
        return LivePipelineResponse(
            run_id=f"live_groq_pipeline_{lead_id}_test0001",
            lead_id=lead_id,
            run_mode="live_failed",
            live_success=False,
            live_model_used=live_module.LIVE_GROQ_MODEL,
            fallback_used=True,
            fallback_reason="stubbed failure",
            deterministic_baseline_available=True,
            failed_agent="research_agent",
            failure_stage="research",
            error_code=error_code,
            deterministic_result=None,
            live_result=None,
            comparison=comparison,
        )

    monkeypatch.setattr(
        "app.api.routes.demo.run_live_groq_pipeline_for_lead",
        _fake_runner,
    )


def test_live_endpoint_returns_200_with_failed_shape_on_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live(monkeypatch)
    _patch_runner_to_failure(monkeypatch, error_code="provider_error")

    try:
        with TestClient(app) as client:
            response = client.post(_LIVE_URL.format(lead_id=_DEMO_LEAD_ID))
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["live_success"] is False
    assert body["run_mode"] == "live_failed"
    assert body["live_model_used"] == live_module.LIVE_GROQ_MODEL
    assert body["fallback_used"] is True
    assert body["fallback_reason"] == "stubbed failure"
    assert body["failed_agent"] == "research_agent"
    assert body["failure_stage"] == "research"
    assert body["error_code"] == "provider_error"

    comparison = body["comparison"]
    assert comparison["fit_score_delta"] is None
    assert comparison["priority_changed"] is None
    assert comparison["qa_score_delta"] is None
    assert comparison["email_subject_changed"] is None
    assert comparison["risk_level_changed"] is None
    assert comparison["live_summary"] is None
    assert "no comparison" in comparison["comparison_notes"]


def test_live_endpoint_surfaces_rate_limited_error_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_live(monkeypatch)
    _patch_runner_to_failure(monkeypatch, error_code="rate_limited")

    try:
        with TestClient(app) as client:
            response = client.post(_LIVE_URL.format(lead_id=_DEMO_LEAD_ID))
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["live_success"] is False
    assert body["error_code"] == "rate_limited"


# --------------------------------------------------------------------------- #
# Regression: existing surfaces still respond                                #
# --------------------------------------------------------------------------- #


def test_deterministic_pipeline_still_works() -> None:
    with TestClient(app) as client:
        response = client.get(f"/api/demo/pipeline/{_DEMO_LEAD_ID}")
    assert response.status_code == 200
    assert response.json()["lead_id"] == _DEMO_LEAD_ID


def test_telemetry_runs_endpoint_still_works() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/telemetry/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_telemetry_run_detail_endpoint_returns_404_for_unknown_run() -> None:
    telemetry_module.clear_telemetry()
    with TestClient(app) as client:
        response = client.get("/api/demo/telemetry/runs/nope-not-a-run")
    assert response.status_code == 404


def test_existing_groq_check_endpoint_still_returns_503_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/demo/model-service/groq-check")
    assert response.status_code == 503
