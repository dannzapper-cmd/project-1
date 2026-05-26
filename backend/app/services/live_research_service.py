"""Block 10E — Live Web Research MVP service.

Direct, backend-only Exa Search calls for one selected B2B lead at
a time. Designed to be safe by default:

- ``ENABLE_LIVE_RESEARCH`` and ``EXA_API_KEY`` are both read at
  request time. Either missing → structured ``disabled`` /
  ``unavailable`` response (never a generic 500).
- Hard timeout via ``LIVE_RESEARCH_TIMEOUT_SECONDS``. A timeout
  surfaces as ``status="timeout"`` with an honest user message
  (Guard D — Render free-tier cold start awareness).
- In-process daily counter (Guard B). Resets on restart by design.
- Query length capped at 120 characters (Guard C).
- Missing ``company_name`` → ``insufficient_input`` (Guard C).
- Snippets shorter than 40 chars or all-low-confidence results are
  filtered out (Guard E). Empty result sets surface ``no_evidence``.
- Snippets are NEVER routed through Groq or any LLM (Guard A).
  ``why_it_matters`` is a deterministic template built only from
  lead context.

This module never imports the Groq SDK or any LLM client. It uses
``httpx`` directly (already a backend dep via ``groq``'s transitive
graph and the dev pin in ``backend/requirements.txt``).
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.common import Confidence
from app.schemas.live_research import (
    LiveResearchEvidenceCard,
    LiveResearchRequest,
    LiveResearchResponse,
    LiveResearchSource,
    LiveResearchStatus,
)


_logger = get_logger(__name__)


# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #

EXA_SEARCH_URL: str = "https://api.exa.ai/search"
QUERY_MAX_LENGTH: int = 120
SNIPPET_MIN_LENGTH: int = 40
SNIPPET_MAX_LENGTH: int = 600


# --------------------------------------------------------------------------- #
# In-process daily counter (Guard B)                                          #
# --------------------------------------------------------------------------- #


@dataclass
class _DailyCounter:
    """Thread-safe in-process daily counter.

    Resets when the calendar day (UTC) changes. The counter is
    intentionally module-level (process-local). Restarting the
    backend resets it; that is acceptable for Block 10E and
    explicitly called out in the prompt.
    """

    count: int = 0
    day_key: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)

    def increment_and_check(self, limit: int) -> tuple[bool, int]:
        """Reserve one slot for the current request.

        Returns ``(allowed, current_count)``. When ``allowed`` is
        ``False`` the counter is NOT incremented — the caller has
        crossed the daily cap and should respond with
        ``status="rate_limited"``.
        """

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.lock:
            if today != self.day_key:
                self.day_key = today
                self.count = 0
            if self.count >= max(int(limit), 0):
                return False, self.count
            self.count += 1
            return True, self.count

    def snapshot(self) -> int:
        with self.lock:
            return self.count

    def reset(self) -> None:
        """Test-only helper to reset the counter."""

        with self.lock:
            self.count = 0
            self.day_key = ""


_daily_counter = _DailyCounter()


def _reset_daily_counter_for_tests() -> None:
    """Test hook — reset the in-process daily counter."""

    _daily_counter.reset()


def _current_daily_count() -> int:
    """Test hook — read the in-process daily counter."""

    return _daily_counter.snapshot()


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:  # noqa: BLE001 — defensive
        return ""


def _build_query(request: LiveResearchRequest) -> str | None:
    """Build a conservative query from safe lead fields.

    Returns ``None`` when ``company_name`` is missing or blank
    (Guard C). The composed query never exceeds ``QUERY_MAX_LENGTH``
    characters.
    """

    company = (request.company_name or "").strip()
    if not company:
        return None

    parts: list[str] = [company]
    industry = (request.industry or "").strip()
    country = (request.country or "").strip()
    if industry:
        parts.append(industry)
    if country:
        parts.append(country)
    parts.extend(["company", "sales", "revenue", "operations"])

    query = " ".join(parts).strip()
    if len(query) > QUERY_MAX_LENGTH:
        # Truncate gracefully on a word boundary, then hard-truncate
        # if there is no whitespace to break on.
        truncated = query[:QUERY_MAX_LENGTH]
        last_space = truncated.rfind(" ")
        if last_space > 40:
            truncated = truncated[:last_space]
        query = truncated.strip()
    return query or None


def _normalize_snippet(value: str | None) -> str:
    if not value:
        return ""
    snippet = " ".join(str(value).split())
    if len(snippet) > SNIPPET_MAX_LENGTH:
        snippet = snippet[: SNIPPET_MAX_LENGTH - 3].rstrip() + "..."
    return snippet


def _classify_confidence(score: Any) -> Confidence:
    """Map an Exa relevance score to a coarse confidence bucket.

    Exa returns floats in [0, 1] in its ``score`` field. We bucket
    deterministically and never expose the raw number — the UI only
    consumes the discrete ``high | medium | low`` enum.
    """

    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return Confidence.LOW
    if numeric >= 0.65:
        return Confidence.HIGH
    if numeric >= 0.45:
        return Confidence.MEDIUM
    return Confidence.LOW


def _build_why_it_matters(
    company_name: str, industry: str | None, country: str | None
) -> str:
    """Deterministic template-built rationale.

    Crucially this string is composed only from the lead-provided
    context — never from the Exa snippet. That keeps the line
    Block 10E draws between "what Exa returned" and "everything
    else" sharp.
    """

    pieces: list[str] = [f"Public web result for {company_name}"]
    if industry:
        pieces.append(f"in {industry}")
    if country:
        pieces.append(f"({country})")
    pieces.append("— review the source before relying on it.")
    return " ".join(pieces).replace("  ", " ")


def _build_response(
    *,
    enabled: bool,
    status: LiveResearchStatus,
    company_name: str,
    query_used: str | None,
    user_message: str,
    evidence_cards: list[LiveResearchEvidenceCard] | None = None,
    sources: list[LiveResearchSource] | None = None,
    information_risks: list[str] | None = None,
    confidence: Confidence | None = None,
    warnings: list[str] | None = None,
    estimated_request_count: int = 0,
    provider: str = "exa",
) -> LiveResearchResponse:
    return LiveResearchResponse(
        provider=provider,  # type: ignore[arg-type]
        run_mode="live_research",
        enabled=enabled,
        status=status,
        company_name=company_name,
        query_used=query_used,
        evidence_cards=evidence_cards or [],
        information_risks=information_risks or [],
        confidence=confidence,
        sources=sources or [],
        fetched_at=datetime.now(timezone.utc),
        warnings=warnings or [],
        estimated_request_count=estimated_request_count,
        user_message=user_message,
    )


# --------------------------------------------------------------------------- #
# Provider call                                                               #
# --------------------------------------------------------------------------- #


# Type for the optional HTTP-call hook used by tests. Tests inject
# a callable returning a parsed JSON dict so no real network call is
# ever made; production passes ``None`` and a real httpx client is
# created.
HttpCaller = Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]


class _LiveResearchTimeout(Exception):
    """Raised internally when the provider exceeds the configured timeout."""


class _LiveResearchProviderError(Exception):
    """Raised internally for non-timeout provider failures."""


def _default_http_caller(
    url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float
) -> dict[str, Any]:
    """Default httpx-backed POST; raises classified exceptions on failure."""

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as exc:
        raise _LiveResearchTimeout(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise _LiveResearchProviderError(str(exc)) from exc

    if response.status_code == 408 or response.status_code == 504:
        raise _LiveResearchTimeout(f"upstream HTTP {response.status_code}")
    if response.status_code >= 400:
        raise _LiveResearchProviderError(
            f"Exa returned HTTP {response.status_code}"
        )

    try:
        return response.json()
    except Exception as exc:  # noqa: BLE001 — non-JSON body
        raise _LiveResearchProviderError(
            f"Exa returned non-JSON body: {exc}"
        ) from exc


def _call_exa(
    *,
    api_key: str,
    query: str,
    max_results: int,
    timeout_seconds: float,
    http_caller: HttpCaller | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query": query,
        "numResults": max_results,
        "type": "auto",
        "contents": {
            "highlights": {
                "numSentences": 2,
                "highlightsPerUrl": 1,
            }
        },
    }
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    caller = http_caller or _default_http_caller
    return caller(EXA_SEARCH_URL, payload, headers, timeout_seconds)


# --------------------------------------------------------------------------- #
# Result normalization                                                        #
# --------------------------------------------------------------------------- #


def _coerce_results(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, dict):
        return []
    results = raw.get("results")
    if not isinstance(results, list):
        return []
    return [item for item in results if isinstance(item, dict)]


def _build_card(
    item: dict[str, Any],
    *,
    company_name: str,
    industry: str | None,
    country: str | None,
) -> LiveResearchEvidenceCard | None:
    url = item.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return None
    title = item.get("title") or item.get("text") or company_name
    if not isinstance(title, str):
        title = company_name
    title = title.strip()[:200] or company_name

    # Prefer Exa highlights (already extractive) over the full text.
    snippet_source: str | None = None
    highlights = item.get("highlights")
    if isinstance(highlights, list) and highlights:
        first = highlights[0]
        if isinstance(first, str):
            snippet_source = first
        elif isinstance(first, dict):
            snippet_source = first.get("text") or first.get("highlight")
    if not snippet_source:
        text = item.get("text")
        if isinstance(text, str):
            snippet_source = text

    snippet = _normalize_snippet(snippet_source)

    domain = _extract_domain(url)
    if not domain:
        return None

    return LiveResearchEvidenceCard(
        title=title,
        url=url,
        source_domain=domain,
        snippet=snippet,
        source_type="live_web",
        confidence=_classify_confidence(item.get("score")),
        why_it_matters=_build_why_it_matters(company_name, industry, country),
    )


def _filter_cards(
    cards: list[LiveResearchEvidenceCard],
) -> tuple[list[LiveResearchEvidenceCard], list[str]]:
    """Apply Guard E — drop near-empty / all-low-confidence cards.

    Returns ``(kept, dropped_reasons)`` where ``dropped_reasons`` is
    a small set of human-readable strings the caller surfaces in
    ``warnings`` when the kept list ends up empty.
    """

    kept: list[LiveResearchEvidenceCard] = []
    dropped: list[str] = []
    for card in cards:
        if len(card.snippet) < SNIPPET_MIN_LENGTH:
            dropped.append("snippet too short")
            continue
        kept.append(card)

    if kept and all(card.confidence == Confidence.LOW for card in kept):
        dropped.append("all candidate sources resolved to low confidence")
        return [], dropped
    return kept, dropped


def _summarize_confidence(
    cards: list[LiveResearchEvidenceCard],
) -> Confidence | None:
    if not cards:
        return None
    if any(card.confidence == Confidence.HIGH for card in cards):
        return Confidence.HIGH
    if any(card.confidence == Confidence.MEDIUM for card in cards):
        return Confidence.MEDIUM
    return Confidence.LOW


# --------------------------------------------------------------------------- #
# Public entry point                                                          #
# --------------------------------------------------------------------------- #


def run_live_research(
    request: LiveResearchRequest,
    *,
    http_caller: HttpCaller | None = None,
) -> LiveResearchResponse:
    """Run one manual live-research request.

    Parameters
    ----------
    request:
        Validated :class:`LiveResearchRequest` (only safe lead fields).
    http_caller:
        Optional injection point used by tests. Production callers
        always pass ``None`` and the default httpx-backed caller is
        used. Tests inject a stub so no real Exa request is ever
        issued.
    """

    settings = get_settings()

    # Read both gating signals at request time. ``get_settings()`` is
    # cached, so we additionally consult the live process environment
    # so monkeypatched env vars are honoured by tests and short-lived
    # processes.
    env_flag_raw = os.environ.get("ENABLE_LIVE_RESEARCH")
    if env_flag_raw is not None:
        enabled = env_flag_raw.strip().lower() in ("1", "true", "yes", "on")
    else:
        enabled = bool(settings.enable_live_research)

    company_name = (request.company_name or "").strip()

    if not enabled:
        return _build_response(
            enabled=False,
            status="disabled",
            company_name=company_name,
            query_used=None,
            user_message=(
                "Live research is currently disabled for the public demo."
            ),
            warnings=[
                "ENABLE_LIVE_RESEARCH is not enabled on this backend."
            ],
            estimated_request_count=_current_daily_count(),
            provider="none",
        )

    api_key = (
        os.environ.get("EXA_API_KEY")
        or (settings.exa_api_key or "")
    ).strip()
    if not api_key:
        return _build_response(
            enabled=True,
            status="unavailable",
            company_name=company_name,
            query_used=None,
            user_message=(
                "Live research is unavailable: no provider API key is "
                "configured on the backend."
            ),
            warnings=["EXA_API_KEY is not set on the backend."],
            estimated_request_count=_current_daily_count(),
            provider="none",
        )

    # Guard C — refuse to even build a query when company_name is empty.
    query = _build_query(request)
    if not query:
        return _build_response(
            enabled=True,
            status="insufficient_input",
            company_name=company_name,
            query_used=None,
            user_message=(
                "Live research needs a company name to build a safe "
                "query."
            ),
            warnings=["Insufficient lead data to construct a query."],
            estimated_request_count=_current_daily_count(),
            provider="none",
        )

    # Guard B — daily limit enforcement.
    daily_limit = int(settings.live_research_daily_limit)
    allowed, current_count = _daily_counter.increment_and_check(daily_limit)
    if not allowed:
        return _build_response(
            enabled=True,
            status="rate_limited",
            company_name=company_name,
            query_used=query,
            user_message=(
                "The daily live-research limit for this demo backend has "
                "been reached. Try again later."
            ),
            warnings=[
                f"Daily limit of {daily_limit} live-research requests reached."
            ],
            estimated_request_count=current_count,
            provider="none",
        )

    max_results = max(1, int(settings.live_research_max_results))
    timeout_seconds = float(settings.live_research_timeout_seconds)

    try:
        raw = _call_exa(
            api_key=api_key,
            query=query,
            max_results=max_results,
            timeout_seconds=timeout_seconds,
            http_caller=http_caller,
        )
    except (httpx.TimeoutException, _LiveResearchTimeout):
        # Guard D — Render cold-start friendly timeout message.
        _logger.warning(
            "Live research timed out for company=%s", company_name
        )
        return _build_response(
            enabled=True,
            status="timeout",
            company_name=company_name,
            query_used=query,
            user_message=(
                "Research timed out. The backend may be warming up. Try "
                "again in a moment."
            ),
            warnings=["Provider call exceeded the configured timeout."],
            estimated_request_count=current_count,
            provider="exa",
        )
    except (httpx.HTTPError, _LiveResearchProviderError) as exc:
        _logger.warning(
            "Live research provider error for company=%s: %s",
            company_name,
            exc,
        )
        return _build_response(
            enabled=True,
            status="provider_error",
            company_name=company_name,
            query_used=query,
            user_message=(
                "Research could not complete. Please try again shortly."
            ),
            warnings=[f"Provider error: {exc}"],
            estimated_request_count=current_count,
            provider="exa",
        )
    except Exception as exc:  # noqa: BLE001 — defensive
        _logger.exception("Unexpected live research failure")
        return _build_response(
            enabled=True,
            status="provider_error",
            company_name=company_name,
            query_used=query,
            user_message=(
                "Research could not complete. Please try again shortly."
            ),
            warnings=[f"Unexpected error: {exc.__class__.__name__}"],
            estimated_request_count=current_count,
            provider="exa",
        )

    raw_results = _coerce_results(raw)
    candidate_cards: list[LiveResearchEvidenceCard] = []
    for item in raw_results[:max_results]:
        card = _build_card(
            item,
            company_name=company_name,
            industry=request.industry,
            country=request.country,
        )
        if card is not None:
            candidate_cards.append(card)

    kept_cards, drop_reasons = _filter_cards(candidate_cards)

    sources = [
        LiveResearchSource(url=card.url, domain=card.source_domain, title=card.title)
        for card in kept_cards
    ]

    if not kept_cards:
        warnings: list[str] = ["No usable evidence was found for this lead."]
        if drop_reasons:
            warnings.append("Filtered out: " + "; ".join(drop_reasons))
        return _build_response(
            enabled=True,
            status="no_evidence",
            company_name=company_name,
            query_used=query,
            user_message=(
                "Not enough public-web evidence was found for this "
                "company. Try a different lead or refine the lead "
                "details."
            ),
            warnings=warnings,
            estimated_request_count=current_count,
            information_risks=[
                "Live research returned no high-signal results.",
            ],
            confidence=Confidence.LOW,
            provider="exa",
        )

    confidence = _summarize_confidence(kept_cards)
    information_risks: list[str] = []
    if confidence == Confidence.LOW:
        information_risks.append(
            "All sources resolved to low confidence — verify before use."
        )
    if len(kept_cards) < max_results:
        information_risks.append(
            "Fewer sources than requested; coverage is limited."
        )

    return _build_response(
        enabled=True,
        status="ok",
        company_name=company_name,
        query_used=query,
        user_message=(
            f"Found {len(kept_cards)} public-web result(s). Review "
            "each source before relying on it."
        ),
        evidence_cards=kept_cards,
        sources=sources,
        information_risks=information_risks,
        confidence=confidence,
        warnings=[],
        estimated_request_count=current_count,
        provider="exa",
    )


__all__ = [
    "EXA_SEARCH_URL",
    "QUERY_MAX_LENGTH",
    "SNIPPET_MIN_LENGTH",
    "run_live_research",
    "_reset_daily_counter_for_tests",
    "_current_daily_count",
]
