"""Basic /health endpoint test."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["db"] == "ok"
    assert payload["app"] == "leadforge-backend"
    assert "version" in payload
    assert "env" in payload
