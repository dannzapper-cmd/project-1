"""Demo data loader — Fase 4.2.

Reads, validates, and returns the static demo files shipped in `data/demo/`:

- `data/demo/leads.csv`               -> list[LeadIn]
- `data/demo/company_research.json`   -> list[DemoCompanyResearch]

The loaders use only the Python standard library (`csv`, `json`, `pathlib`).
No pandas, no network calls, no LLM, no DB writes.

Each loader is intentionally focused on ONE file and validates only that
file's internal structure (presence, parseability, required fields, no
duplicate `lead_id`s). Cross-file consistency between leads.csv and
company_research.json is handled by `validate_demo_dataset()`.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.demo import DemoCompanyResearch, DemoSummary
from app.schemas.lead import LeadIn

logger = get_logger(__name__)

# Required CSV columns (header-level). These columns MUST exist in the
# header row. Per-row value enforcement is narrower: the existing `LeadIn`
# schema in app/schemas/lead.py treats `industry` as nullable, and the
# bundled demo dataset intentionally ships a row with missing `industry`
# to exercise the future Intake Agent's incomplete-data path. We therefore
# require `industry` AS A COLUMN but accept empty cells per row (graceful
# handling of optional empties). Per-row non-empty values are enforced
# only for `lead_id` and `company_name`.
_REQUIRED_CSV_COLUMNS: tuple[str, ...] = ("lead_id", "company_name", "industry")

_REQUIRED_RESEARCH_FIELDS: tuple[str, ...] = ("lead_id", "company_name", "research_status")


class DemoDataError(Exception):
    """Raised for any demo data file failure: missing, unreadable,
    malformed, or violating required structure."""


# --------------------------------------------------------------------------- #
# Path helpers                                                                #
# --------------------------------------------------------------------------- #
def _resolve_leads_path(path: Path | None, settings: Settings | None) -> Path:
    if path is not None:
        return path
    return (settings or get_settings()).demo_leads_csv_path


def _resolve_research_path(path: Path | None, settings: Settings | None) -> Path:
    if path is not None:
        return path
    return (settings or get_settings()).demo_company_research_path


def _ensure_file_exists(path: Path, kind: str) -> None:
    if not path.exists():
        raise DemoDataError(f"Demo {kind} file not found: {path}")
    if not path.is_file():
        raise DemoDataError(f"Demo {kind} path is not a regular file: {path}")


# --------------------------------------------------------------------------- #
# Leads CSV                                                                   #
# --------------------------------------------------------------------------- #
def _coerce_employee_count(raw: str | None, *, context: str = "") -> int | None:
    """Parse an optional integer cell. Returns None for missing/empty values.

    For non-integer values in this OPTIONAL field, we log a warning and
    return None rather than raise — this matches the prompt's rule
    "Optional fields should not break loading" / "Empty optional values
    should be handled gracefully" while still surfacing the issue in logs
    (not silent failure). Required fields are validated separately and
    still raise.
    """
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Non-integer employee_count value %s%s; treating as missing.",
            repr(raw),
            f" ({context})" if context else "",
        )
        return None


def _normalize_optional(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip()
    return value if value else None


def load_demo_leads(
    path: Path | None = None,
    *,
    settings: Settings | None = None,
) -> list[LeadIn]:
    """Load and validate `data/demo/leads.csv`.

    Validates that the file exists, has a header row, contains the required
    columns, has no duplicate `lead_id`s, and that each row passes the
    `LeadIn` Pydantic schema.

    Raises `DemoDataError` on any failure.
    """
    resolved = _resolve_leads_path(path, settings)
    _ensure_file_exists(resolved, "leads CSV")

    try:
        with resolved.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                raise DemoDataError(f"Demo leads CSV has no header row: {resolved}")

            header = [name.strip() for name in reader.fieldnames]
            missing = [col for col in _REQUIRED_CSV_COLUMNS if col not in header]
            if missing:
                raise DemoDataError(
                    "Demo leads CSV is missing required columns "
                    f"{missing}; found header={header}"
                )

            leads: list[LeadIn] = []
            seen_ids: set[str] = set()
            for line_no, row in enumerate(reader, start=2):  # line 1 = header
                lead_id = _normalize_optional(row.get("lead_id"))
                company_name = _normalize_optional(row.get("company_name"))
                industry = _normalize_optional(row.get("industry"))

                if not lead_id:
                    raise DemoDataError(
                        f"Demo leads CSV row {line_no} is missing lead_id"
                    )
                if not company_name:
                    raise DemoDataError(
                        f"Demo leads CSV row {line_no} ({lead_id}) is missing company_name"
                    )
                if lead_id in seen_ids:
                    raise DemoDataError(
                        f"Demo leads CSV contains duplicate lead_id: {lead_id!r} (row {line_no})"
                    )
                seen_ids.add(lead_id)

                payload: dict[str, Any] = {
                    "lead_id": lead_id,
                    "company_name": company_name,
                    "website": _normalize_optional(row.get("website")),
                    "industry": industry,
                    "country": _normalize_optional(row.get("country")),
                    "employee_count": _coerce_employee_count(
                        row.get("employee_count"), context=f"row {line_no} lead_id={lead_id}"
                    ),
                    "contact_name": _normalize_optional(row.get("contact_name")),
                    "contact_role": _normalize_optional(row.get("contact_role")),
                    "notes": _normalize_optional(row.get("notes")),
                }

                try:
                    leads.append(LeadIn(**payload))
                except ValidationError as exc:
                    raise DemoDataError(
                        f"Demo leads CSV row {line_no} ({lead_id}) failed validation: {exc}"
                    ) from exc
    except OSError as exc:
        raise DemoDataError(f"Could not read demo leads CSV {resolved}: {exc}") from exc

    if not leads:
        raise DemoDataError(f"Demo leads CSV contains no data rows: {resolved}")

    logger.info("Loaded %d demo lead(s) from %s", len(leads), resolved)
    return leads


# --------------------------------------------------------------------------- #
# Company research JSON                                                       #
# --------------------------------------------------------------------------- #
def load_demo_company_research(
    path: Path | None = None,
    *,
    settings: Settings | None = None,
) -> list[DemoCompanyResearch]:
    """Load and validate `data/demo/company_research.json`.

    The file MUST be a top-level JSON array. Each record MUST have at
    minimum `lead_id`, `company_name`, and `research_status`.

    Raises `DemoDataError` on any failure.
    """
    resolved = _resolve_research_path(path, settings)
    _ensure_file_exists(resolved, "company research JSON")

    try:
        with resolved.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise DemoDataError(
            f"Demo company research JSON is not valid JSON ({resolved}): {exc}"
        ) from exc
    except OSError as exc:
        raise DemoDataError(
            f"Could not read demo company research JSON {resolved}: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise DemoDataError(
            "Demo company research JSON must be a top-level array of records, "
            f"got {type(data).__name__} ({resolved})"
        )

    records: list[DemoCompanyResearch] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(data):
        if not isinstance(raw, dict):
            raise DemoDataError(
                f"Demo company research record at index {index} is not an object: "
                f"{type(raw).__name__}"
            )

        missing = [field for field in _REQUIRED_RESEARCH_FIELDS if not raw.get(field)]
        if missing:
            raise DemoDataError(
                f"Demo company research record at index {index} is missing required "
                f"fields {missing}"
            )

        lead_id = str(raw["lead_id"])
        if lead_id in seen_ids:
            raise DemoDataError(
                f"Demo company research JSON contains duplicate lead_id: {lead_id!r}"
            )
        seen_ids.add(lead_id)

        try:
            records.append(DemoCompanyResearch.model_validate(raw))
        except ValidationError as exc:
            raise DemoDataError(
                f"Demo company research record {lead_id} failed validation: {exc}"
            ) from exc

    if not records:
        raise DemoDataError(
            f"Demo company research JSON contains no records: {resolved}"
        )

    logger.info(
        "Loaded %d company research record(s) from %s", len(records), resolved
    )
    return records


# --------------------------------------------------------------------------- #
# Cross-file consistency + summary                                            #
# --------------------------------------------------------------------------- #
def _lead_ids(items: Iterable[Any]) -> list[str]:
    return [item.lead_id for item in items]


def validate_demo_dataset(
    leads: list[LeadIn],
    research: list[DemoCompanyResearch],
) -> None:
    """Cross-validate that leads.csv and company_research.json describe the
    same set of `lead_id` values.

    Raises `DemoDataError` if the two ID sets diverge.
    """
    csv_ids = set(_lead_ids(leads))
    json_ids = set(_lead_ids(research))

    only_in_csv = sorted(csv_ids - json_ids)
    only_in_json = sorted(json_ids - csv_ids)

    if only_in_csv or only_in_json:
        details: list[str] = []
        if only_in_csv:
            details.append(f"only in leads.csv: {only_in_csv}")
        if only_in_json:
            details.append(f"only in company_research.json: {only_in_json}")
        raise DemoDataError(
            "Demo dataset lead_id mismatch between leads.csv and "
            "company_research.json (" + "; ".join(details) + ")"
        )


def build_demo_summary(
    leads: list[LeadIn] | None = None,
    research: list[DemoCompanyResearch] | None = None,
    *,
    settings: Settings | None = None,
) -> DemoSummary:
    """Return a small summary of the demo dataset.

    Reuses the two loaders + `validate_demo_dataset`; introduces no new
    abstraction.
    """
    leads = leads if leads is not None else load_demo_leads(settings=settings)
    research = (
        research if research is not None else load_demo_company_research(settings=settings)
    )
    validate_demo_dataset(leads, research)

    return DemoSummary(
        total_leads=len(leads),
        total_research_records=len(research),
        data_source="synthetic_demo",
        status="ready",
    )
