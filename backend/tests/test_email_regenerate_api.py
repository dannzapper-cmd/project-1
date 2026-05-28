"""Block 11C.4 controlled single-lead regenerate draft API tests."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.schemas.model import (
    ModelCostEstimate,
    ModelProvider,
    ModelResponse,
    ModelUsage,
)

_URL = "/api/demo/email/regenerate-draft/lead_001"
_HEADERS = {"X-LeadForge-Demo-Key": "demo-code"}


def _payload() -> dict:
    return {
        "lead": {
            "company_name": "NovaBridge Solutions",
            "website": "novabridge.io",
            "industry": "B2B SaaS",
            "country": "USA",
            "employee_count": 200,
            "contact_name": "Jordan Kim",
            "contact_role": "VP of Sales",
            "company_summary": "NovaBridge serves mid-market revenue teams.",
            "pain_hypothesis": "Manual research slows outbound review.",
            "sales_angle": "Traceable sales intelligence",
            "core_message": "LeadForge drafts reviewable outreach with evidence.",
            "personalization_notes": ["Use the RevOps efficiency angle."],
        }
    }


def test_regenerate_draft_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_LIVE_MODEL_PIPELINE", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("DEMO_ACCESS_CODE", raising=False)
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            response = client.post(_URL, json=_payload())
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "disabled"
    assert body["draft_only"] is True
    assert "controlled backend live mode" in body["user_message"]


def test_regenerate_draft_requires_demo_access_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "demo-code")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            response = client.post(_URL, json=_payload())
    finally:
        get_settings.cache_clear()

    assert response.status_code == 403
    assert response.json()["error"] == "demo_access_required"


def test_regenerate_draft_returns_live_draft_with_safe_metadata(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_LIVE_MODEL_PIPELINE", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("DEMO_ACCESS_CODE", "demo-code")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()

    class _FakeGroqService:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def complete(self, request):  # noqa: ANN001
            content = json.dumps(
                {
                    "email_subject": "Idea for NovaBridge",
                    "email_body": "Hi Jordan,\n\nThis is a draft only for human review, based only on the selected lead context.\n\nBest,\nLeadForge",
                    "personalization_notes": ["Used selected lead context only."],
                    "confidence": "medium",
                }
            )
            return ModelResponse(
                request_id=request.request_id,
                provider=ModelProvider.GROQ,
                model_name="llama-3.1-8b-instant",
                content=content,
                usage=ModelUsage(input_tokens=100, output_tokens=80, total_tokens=180),
                cost=ModelCostEstimate(
                    input_cost=0.0,
                    output_cost=0.0,
                    total_cost=0.001,
                    display_cost="$0.001",
                ),
                latency="1.2s",
                simulated=False,
            )

    monkeypatch.setattr("app.api.routes.demo.GroqModelService", _FakeGroqService)

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            response = client.post(_URL, json=_payload(), headers=_HEADERS)
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "live_groq"
    assert body["draft_only"] is True
    assert body["provider"] == "groq"
    assert body["tokens"] == 180
    assert "Draft not sent" in body["user_message"]
