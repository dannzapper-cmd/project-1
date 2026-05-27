"""Lightweight production-safety helpers for the public demo deployment."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
import hmac
import json
import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings

DEMO_ACCESS_HEADER = "X-LeadForge-Demo-Key"
DEMO_ACCESS_REQUIRED_MESSAGE = (
    "This demo action requires the private demo access code. If you're a recruiter "
    "or hiring manager, the code was included with the demo link."
)

_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/api/system/status",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)

_PROTECTED_EXACT_POST_PATHS: frozenset[str] = frozenset(
    {
        "/api/intake/preview",
        "/api/intake/preview-file/csv",
        "/api/intake/extract-file",
        "/api/demo/pipeline/batch",
        "/api/demo/pipeline/live-groq",
        "/api/research/live-company",
        "/api/assistant/lead-question",
    }
)

_LIVE_PATH_PREFIXES: tuple[str, ...] = (
    "/api/research/live-company",
    "/api/assistant/lead-question",
    "/api/demo/pipeline/live-groq/",
    "/api/demo/model-service/groq-check",
)

_GROQ_AGENT_MARKERS: tuple[str, ...] = (
    "-groq/",
    "/research-groq/",
    "/qualifier-groq/",
)


def apply_security_headers(response: Response) -> None:
    """Apply basic hardening headers without introducing CSP complexity."""

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")


def client_ip(request: Request) -> str:
    """Best-effort client IP for abuse throttling only."""

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def is_protected_demo_path(method: str, path: str) -> bool:
    """Return whether a route should be protected by demo safety controls."""

    normalized_method = method.upper()
    if normalized_method == "OPTIONS" or path in _PUBLIC_PATHS:
        return False

    if normalized_method == "POST":
        if path in _PROTECTED_EXACT_POST_PATHS:
            return True
        if path.startswith("/api/demo/pipeline/live-groq/"):
            return True

    if normalized_method == "GET":
        if path == "/api/demo/model-service/groq-check":
            return True
        if path.startswith("/api/demo/agents/") and any(
            marker in path for marker in _GROQ_AGENT_MARKERS
        ):
            return True

    return False


def rate_limit_scope_for_path(path: str) -> str:
    if any(path.startswith(prefix) for prefix in _LIVE_PATH_PREFIXES):
        return "live"
    if path.startswith("/api/demo/agents/") and any(
        marker in path for marker in _GROQ_AGENT_MARKERS
    ):
        return "live"
    return "default"


def _safe_error_category(status_code: int) -> str:
    if status_code == 429:
        return "rate_limited"
    if status_code in {401, 403}:
        return "demo_access_required"
    if status_code == 413:
        return "upload_too_large"
    if status_code == 415:
        return "unsupported_media_type"
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return "ok"


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    retry_after_seconds: int


class InMemoryRateLimiter:
    """Simple per-IP, per-minute limiter for single-instance demo deployments.

    # NOTE: In-memory only. Resets on Render spin-down/restart.
    # This is intentional for a portfolio demo. Not suitable for production SaaS.
    """

    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str, int], int] = defaultdict(int)

    def check(
        self,
        *,
        scope: str,
        ip_address: str,
        limit: int,
        now: float | None = None,
    ) -> RateLimitResult:
        current_time = time.time() if now is None else now
        minute_bucket = int(current_time // 60)
        self._cleanup(current_bucket=minute_bucket)

        key = (scope, ip_address, minute_bucket)
        current_count = self._buckets[key]
        retry_after = max(1, 60 - int(current_time % 60))
        if current_count >= limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                retry_after_seconds=retry_after,
            )

        self._buckets[key] = current_count + 1
        return RateLimitResult(allowed=True, limit=limit, retry_after_seconds=0)

    def _cleanup(self, *, current_bucket: int) -> None:
        expired_before = current_bucket - 1
        for key in list(self._buckets.keys()):
            if key[2] < expired_before:
                del self._buckets[key]


def check_demo_access(settings: Settings, request: Request) -> bool:
    access_code = (settings.demo_access_code or "").strip()
    if not access_code:
        return True

    # DEMO NOTE: This is a lightweight abuse deterrent for a portfolio demo.
    # The code is entered by the user and stored in sessionStorage (browser-only).
    # It is NOT cryptographically secure authentication.
    # A determined user with DevTools can see the code in the Network tab.
    # That is acceptable for this use case.
    provided_code = request.headers.get(DEMO_ACCESS_HEADER, "").strip()
    return bool(provided_code) and hmac.compare_digest(provided_code, access_code)


def demo_access_response(request_id: str) -> JSONResponse:
    response = JSONResponse(
        status_code=403,
        content={
            "error": "demo_access_required",
            "detail": DEMO_ACCESS_REQUIRED_MESSAGE,
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    apply_security_headers(response)
    return response


def rate_limit_response(*, request_id: str, result: RateLimitResult) -> JSONResponse:
    response = JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "detail": "Too many demo requests. Please wait a moment and try again.",
            "limit": result.limit,
            "retry_after_seconds": result.retry_after_seconds,
            "request_id": request_id,
        },
    )
    response.headers["Retry-After"] = str(result.retry_after_seconds)
    response.headers["X-Request-ID"] = request_id
    apply_security_headers(response)
    return response


def server_error_response(request_id: str) -> JSONResponse:
    response = JSONResponse(
        status_code=500,
        content={
            "error": "server_error",
            "detail": "Something went wrong while handling this demo request.",
            "request_id": request_id,
        },
    )
    response.headers["X-Request-ID"] = request_id
    apply_security_headers(response)
    return response


def make_request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id", "").strip()
    return incoming[:128] if incoming else uuid4().hex


def log_request(
    logger: logging.Logger,
    *,
    request: Request,
    request_id: str,
    status_code: int,
    latency_ms: float,
) -> None:
    """Emit a safe structured request log line.

    The event intentionally includes only high-level routing/debug fields and
    excludes request bodies, prompts, uploaded file content, API keys, and PII.
    """

    event = {
        "event": "http_request",
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
        "error_category": _safe_error_category(status_code),
    }
    logger.info(json.dumps(event, sort_keys=True))


def build_request_safety_middleware(
    *,
    settings: Settings,
    limiter: InMemoryRateLimiter,
    logger: logging.Logger,
) -> Callable:
    async def request_safety_middleware(request: Request, call_next: Callable) -> Response:
        request_id = make_request_id(request)
        request.state.request_id = request_id
        start = time.perf_counter()
        status_code = 500

        try:
            protected = is_protected_demo_path(request.method, request.url.path)
            if protected and not check_demo_access(settings, request):
                response = demo_access_response(request_id)
                status_code = response.status_code
                return response

            if protected and settings.rate_limit_enabled:
                scope = rate_limit_scope_for_path(request.url.path)
                limit = (
                    settings.rate_limit_live_requests_per_minute
                    if scope == "live"
                    else settings.rate_limit_requests_per_minute
                )
                result = limiter.check(
                    scope=scope,
                    ip_address=client_ip(request),
                    limit=limit,
                )
                if not result.allowed:
                    response = rate_limit_response(
                        request_id=request_id,
                        result=result,
                    )
                    status_code = response.status_code
                    return response

            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            apply_security_headers(response)
            return response
        except Exception:
            logger.exception("Unhandled request failure request_id=%s", request_id)
            response = server_error_response(request_id)
            status_code = response.status_code
            return response
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            log_request(
                logger,
                request=request,
                request_id=request_id,
                status_code=status_code,
                latency_ms=latency_ms,
            )

    return request_safety_middleware


def build_security_headers_middleware() -> Callable:
    async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        apply_security_headers(response)
        return response

    return security_headers_middleware

