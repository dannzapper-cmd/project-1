"""Deployment safety checks for public backend configuration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


def _preflight(client: TestClient, origin: str):
    return client.options(
        "/api/intake/preview",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )


def test_cors_allows_configured_vercel_origin_and_localhost(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://leadforge-demo.vercel.app,http://localhost:3000",
    )
    get_settings.cache_clear()

    try:
        test_app = create_app()
        with TestClient(test_app) as client:
            vercel_response = _preflight(
                client, "https://leadforge-demo.vercel.app"
            )
            localhost_response = _preflight(client, "http://localhost:3000")
            unknown_response = _preflight(client, "https://example.invalid")
    finally:
        get_settings.cache_clear()

    assert vercel_response.status_code == 200
    assert (
        vercel_response.headers["access-control-allow-origin"]
        == "https://leadforge-demo.vercel.app"
    )
    assert localhost_response.status_code == 200
    assert (
        localhost_response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )
    assert unknown_response.status_code == 400
    assert "access-control-allow-origin" not in unknown_response.headers


def test_production_cors_rejects_wildcard_origin() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        Settings(app_env="production", cors_origins="*")
