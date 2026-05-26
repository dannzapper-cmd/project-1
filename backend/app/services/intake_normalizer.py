"""Smart lead intake normalizer (Fase 4.3A).

Pure functions only. No database writes, no agents, no model calls, no
external API access, no file I/O.

The public entry point is :func:`build_preview`, which takes an
``IntakePreviewRequest`` and returns an ``IntakePreviewResponse``. The
pipeline is:

1. Parse the raw input into a list of dictionaries.
2. Map original column names to ``LeadIn`` field names via a static alias
   dictionary.
3. Normalize each value (strip whitespace, parse ``employee_count``, etc.).
4. Optionally generate ``lead_id`` placeholders for the preview.
5. Assign a coarse confidence label (``high`` / ``medium`` / ``low``) or
   mark the row as failed when ``company_name`` is missing.
6. Compute aggregate counts and the overall status.

# Future adapters (NOT implemented in this phase):
# - csv_file: read file bytes, decode to string, then use csv_text parser
# - excel_file: use openpyxl to extract sheet as list of dicts (no pandas)
# - pdf_file: use pdfplumber or pypdf to extract text, then apply raw_text parser
# - image_file / screenshot: use multimodal API (Gemini/GPT-4V) or OCR (Tesseract)
# - scanned_document: same as image_file
# All future adapters should normalize to list[dict] and then call the
# shared column_mapping + normalization pipeline already implemented here.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

from app.schemas.intake import (
    CapabilityMap,
    IntakeIssue,
    IntakeOptions,
    IntakePreviewRequest,
    IntakePreviewResponse,
    NormalizedLeadRow,
)
from app.schemas.lead import LeadIn

# ---------------------------------------------------------------------------
# Static configuration
# ---------------------------------------------------------------------------

MAX_LEADS_PER_RUN: int = 10
_REQUIRED_FIELDS: tuple[str, ...] = ("company_name", "industry")

_IMPLEMENTED_NOW: list[str] = [
    "csv_text",
    "csv_file",
    "pasted_table",
    "records_json",
    "raw_text",
    "excel_file",
    "pdf_file",
]
_FUTURE_ADAPTERS: list[str] = [
    "image_file",
    "screenshot",
]


def _build_alias_index() -> dict[str, str]:
    """Build the alias → LeadIn-field-name lookup table.

    Keys are normalized (stripped, lowercased, spaces/hyphens → underscores)
    so that header lookup is a single dict access.
    """

    aliases: dict[str, list[str]] = {
        "company_name": [
            "company",
            "company_name",
            "organization",
            "account",
            "account_name",
            "company name",
            "account name",
        ],
        "website": [
            "website",
            "url",
            "domain",
            "site",
            "website_url",
            "web",
        ],
        "industry": [
            "industry",
            "sector",
            "vertical",
            "category",
        ],
        "country": [
            "country",
            "location",
            "market",
            "geography",
        ],
        "employee_count": [
            "employee_count",
            "employees",
            "headcount",
            "company_size",
            "size",
            "num_employees",
            "number_of_employees",
        ],
        "contact_name": [
            "name",
            "contact",
            "contact_name",
            "full_name",
            "prospect",
            "lead_name",
            "contact name",
            "full name",
            "lead name",
        ],
        "contact_role": [
            "role",
            "title",
            "job_title",
            "contact_role",
            "contact role",
            "position",
            "job title",
        ],
        "notes": [
            "notes",
            "note",
            "context",
            "description",
            "comments",
        ],
        "lead_id": [
            "lead_id",
            "id",
            "lead id",
        ],
    }

    index: dict[str, str] = {}
    for field, names in aliases.items():
        for name in names:
            index[_normalize_header(name)] = field
    return index


def _normalize_header(raw: str) -> str:
    return raw.strip().lower().replace(" ", "_").replace("-", "_")


_ALIAS_INDEX: dict[str, str] = _build_alias_index()

_RAW_TEXT_PATTERNS: dict[str, re.Pattern[str]] = {
    "company_name": re.compile(r"(?i)^company\s*:\s*(.+)"),
    "website": re.compile(r"(?i)^website\s*:\s*(.+)"),
    "industry": re.compile(r"(?i)^industry\s*:\s*(.+)"),
    "country": re.compile(r"(?i)^country\s*:\s*(.+)"),
    "employee_count": re.compile(r"(?i)^employees?\s*:\s*(.+)"),
    "contact_name": re.compile(r"(?i)^contact\s*:\s*(.+)"),
    "contact_role": re.compile(r"(?i)^role\s*:\s*(.+)"),
    "notes": re.compile(r"(?i)^notes?\s*:\s*(.+)"),
    "lead_id": re.compile(r"(?i)^(?:lead_?id|id)\s*:\s*(.+)"),
}


# ---------------------------------------------------------------------------
# CSV / pasted-table parsing
# ---------------------------------------------------------------------------


def _parse_csv(content: str, delimiter: str) -> list[list[str]]:
    """Parse `content` as CSV using the built-in csv module."""

    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    return [row for row in reader if any(cell.strip() for cell in row)]


def _detect_delimiter(
    content: str,
    requested: str,
    *,
    prefer_tab_first: bool,
) -> str:
    """Return the effective delimiter for csv_text / pasted_table.

    ``requested`` is ``"auto"``, ``","`` or ``"\t"``. When ``"auto"``:

    * For csv_text, try comma first; if fewer than 2 columns are detected,
      try tab.
    * For pasted_table, try tab first; if fewer than 2 columns are
      detected, try comma.

    No ``csv.Sniffer`` is used and no further heuristics are applied.
    """

    if requested != "auto":
        return requested

    primary, secondary = ("\t", ",") if prefer_tab_first else (",", "\t")
    primary_rows = _parse_csv(content, primary)
    if primary_rows and len(primary_rows[0]) >= 2:
        return primary
    return secondary


def _csv_rows_to_dicts(
    content: str,
    delimiter: str,
) -> tuple[list[str], list[dict[str, str]]]:
    """Parse ``content`` and return ``(headers, list_of_row_dicts)``.

    Empty lines are dropped before splitting. If the header row has more
    columns than a data row, missing columns are treated as empty strings.
    Extra columns in data rows beyond the header length are dropped (the
    header set is authoritative).
    """

    rows = _parse_csv(content, delimiter)
    if not rows:
        return [], []

    headers = [cell.strip() for cell in rows[0]]
    records: list[dict[str, str]] = []
    for row in rows[1:]:
        record: dict[str, str] = {}
        for idx, header in enumerate(headers):
            value = row[idx] if idx < len(row) else ""
            record[header] = value
        records.append(record)
    return headers, records


# ---------------------------------------------------------------------------
# Raw-text parsing
# ---------------------------------------------------------------------------


def _split_raw_text_blocks(content: str) -> list[list[str]]:
    """Split ``content`` into blocks separated by one or more blank lines."""

    blocks: list[list[str]] = []
    current: list[str] = []
    for line in content.splitlines():
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _parse_raw_text_block(lines: list[str]) -> dict[str, str]:
    """Apply the labelled regex patterns to a block of lines."""

    record: dict[str, str] = {}
    for line in lines:
        for field, pattern in _RAW_TEXT_PATTERNS.items():
            if field in record:
                continue
            match = pattern.match(line)
            if match:
                record[field] = match.group(1)
                break
    return record


# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------


def _map_columns(
    headers: list[str],
) -> tuple[dict[str, str], list[str], list[IntakeIssue]]:
    """Map original headers to LeadIn field names.

    Returns ``(mapped_columns, unmapped_columns, global_issues)``.

    * ``mapped_columns``: ``original_header -> lead_in_field``.
    * ``unmapped_columns``: original headers that did not match an alias,
      *and* duplicate original headers that mapped to a field already
      claimed by an earlier header.
    * ``global_issues``: one ``unmapped_column`` info issue per entry in
      ``unmapped_columns``.
    """

    mapped: dict[str, str] = {}
    unmapped: list[str] = []
    issues: list[IntakeIssue] = []
    used_fields: set[str] = set()

    for header in headers:
        normalized = _normalize_header(header)
        field = _ALIAS_INDEX.get(normalized)
        if field is None or field in used_fields:
            unmapped.append(header)
            issues.append(
                IntakeIssue(
                    severity="info",
                    code="unmapped_column",
                    message=f"Column '{header}' could not be mapped to an internal Lead field.",
                    row_number=None,
                    field=header,
                )
            )
            continue
        mapped[header] = field
        used_fields.add(field)

    return mapped, unmapped, issues


# ---------------------------------------------------------------------------
# Per-record normalization
# ---------------------------------------------------------------------------


def _normalize_record(
    record: dict[str, Any],
    mapped_columns: dict[str, str],
) -> tuple[dict[str, Any], list[IntakeIssue]]:
    """Project ``record`` onto LeadIn fields and apply normalization.

    The returned dict only contains keys for LeadIn fields that were
    mapped. ``employee_count`` is returned as ``int | None``. All other
    string fields are stripped, with empty strings replaced by ``None``.
    """

    normalized: dict[str, Any] = {}
    issues: list[IntakeIssue] = []

    for original, field in mapped_columns.items():
        raw_value = record.get(original)
        if raw_value is None:
            normalized[field] = None
            continue

        if isinstance(raw_value, str):
            value: Any = raw_value.strip()
            if value == "":
                value = None
        else:
            value = raw_value

        if field == "employee_count" and value is not None:
            value = _parse_employee_count(value, issues)

        normalized[field] = value

    return normalized, issues


def _parse_employee_count(value: Any, issues: list[IntakeIssue]) -> int | None:
    """Parse ``value`` as an integer, removing commas first.

    On failure, returns ``None`` and appends an ``invalid_employee_count``
    warning to ``issues``.
    """

    if isinstance(value, int) and not isinstance(value, bool):
        return value if value >= 0 else None

    if isinstance(value, float):
        try:
            return int(value)
        except (ValueError, OverflowError):
            issues.append(
                IntakeIssue(
                    severity="warning",
                    code="invalid_employee_count",
                    message=f"employee_count value '{value}' could not be parsed as integer.",
                    field="employee_count",
                )
            )
            return None

    text = str(value).replace(",", "").strip()
    try:
        return int(text)
    except ValueError:
        issues.append(
            IntakeIssue(
                severity="warning",
                code="invalid_employee_count",
                message=f"employee_count value '{value}' could not be parsed as integer.",
                field="employee_count",
            )
        )
        return None


# ---------------------------------------------------------------------------
# Per-row pipeline
# ---------------------------------------------------------------------------


def _build_row(
    *,
    row_number: int,
    record: dict[str, Any],
    mapped_columns: dict[str, str],
    options: IntakeOptions,
    generated_index: int,
) -> tuple[NormalizedLeadRow, bool]:
    """Build a single ``NormalizedLeadRow``.

    Returns ``(row, lead_id_was_generated)`` so the caller can keep the
    generated-id counter monotonic.
    """

    normalized, issues = _normalize_record(record, mapped_columns)

    # Attach row_number to all per-record issues that did not set one.
    for issue in issues:
        if issue.row_number is None:
            issue.row_number = row_number

    missing_required: list[str] = [
        field for field in _REQUIRED_FIELDS if not normalized.get(field)
    ]
    for field in missing_required:
        issues.append(
            IntakeIssue(
                severity="error",
                code=f"missing_{field}",
                message=f"Row has no required field '{field}'.",
                row_number=row_number,
                field=field,
            )
        )

    low_confidence_fields: list[str] = []
    for field, message in (
        ("website", "Missing website; research confidence will be reduced."),
        ("country", "Missing country; geography scoring will be weaker."),
        (
            "employee_count",
            "Missing employee_count; company size confidence will be reduced.",
        ),
        (
            "contact_role",
            "Missing contact_role; personalization and contact fit will be weaker.",
        ),
        ("notes", "Missing notes; fewer user-provided sales signals are available."),
    ):
        if normalized.get(field) in (None, ""):
            low_confidence_fields.append(field)
            issues.append(
                IntakeIssue(
                    severity="warning",
                    code=f"missing_{field}",
                    message=message,
                    row_number=row_number,
                    field=field,
                )
            )

    if missing_required:
        return (
            NormalizedLeadRow(
                row_number=row_number,
                status="invalid",
                normalized_fields=normalized,
                lead=None,
                confidence=None,
                missing_required_fields=missing_required,
                low_confidence_fields=low_confidence_fields,
                issues=issues,
            ),
            False,
        )

    lead_id = normalized.get("lead_id")
    lead_id_generated = False
    if not lead_id:
        if options.generate_missing_lead_ids:
            lead_id = f"preview_{generated_index:03d}"
            lead_id_generated = True
            issues.append(
                IntakeIssue(
                    severity="info",
                    code="generated_lead_id",
                    message="lead_id was generated for preview only.",
                    row_number=row_number,
                    field="lead_id",
                )
            )
        else:
            lead_id = None

    # LeadIn.lead_id is a required `str`. When the caller disables
    # generate_missing_lead_ids and provided no id, we surface that as the
    # empty string so the row is still produced (per spec: "Do not error
    # on this alone"). The downstream UI can treat empty as "needs id".
    lead = LeadIn(
        lead_id=lead_id if lead_id is not None else "",
        company_name=normalized["company_name"],
        website=normalized.get("website"),
        industry=normalized.get("industry"),
        country=normalized.get("country"),
        employee_count=normalized.get("employee_count"),
        contact_name=normalized.get("contact_name"),
        contact_role=normalized.get("contact_role"),
        notes=normalized.get("notes"),
    )

    confidence = _assign_confidence(lead, issues)

    return (
        NormalizedLeadRow(
            row_number=row_number,
            status=(
                "warning"
                if any(issue.severity == "warning" for issue in issues)
                else "valid"
            ),
            normalized_fields=normalized,
            lead=lead,
            confidence=confidence,
            missing_required_fields=[],
            low_confidence_fields=low_confidence_fields,
            issues=issues,
        ),
        lead_id_generated,
    )

def _assign_confidence(
    lead: LeadIn,
    issues: list[IntakeIssue],
) -> str:
    """Apply the Fase 4.3A confidence rules.

    Precondition: ``lead.company_name`` is present (caller has already
    handled the failed-row case).
    """

    has_error = any(issue.severity == "error" for issue in issues)

    has_industry = bool(lead.industry)
    has_website = bool(lead.website)
    has_contact_role = bool(lead.contact_role)

    other_fields = [
        lead.website,
        lead.industry,
        lead.country,
        lead.employee_count,
        lead.contact_name,
        lead.contact_role,
        lead.notes,
    ]
    only_company = all(value in (None, "") for value in other_fields)

    if (
        has_industry
        and (has_website or has_contact_role)
        and not has_error
    ):
        return "high"
    if only_company:
        return "low"
    return "medium"


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def _parse_records(
    request: IntakePreviewRequest,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Dispatch parsing based on ``request.input_type``.

    Returns ``(headers, records)``. ``headers`` is the ordered list of
    original column names; for ``raw_text`` it is the empty list (the
    regex parser does not produce column headers).
    """

    options = request.options
    input_type = request.input_type

    if input_type == "records_json":
        records = request.records or []
        seen: list[str] = []
        for record in records:
            for key in record.keys():
                if key not in seen:
                    seen.append(key)
        return seen, list(records)

    if input_type == "raw_text":
        content = request.content or ""
        records_raw: list[dict[str, Any]] = []
        for block in _split_raw_text_blocks(content):
            records_raw.append(_parse_raw_text_block(block))
        headers = list(_RAW_TEXT_PATTERNS.keys())
        return headers, records_raw

    content = request.content or ""
    if input_type == "csv_text":
        delimiter = _detect_delimiter(content, options.delimiter, prefer_tab_first=False)
    else:  # pasted_table
        delimiter = _detect_delimiter(content, options.delimiter, prefer_tab_first=True)

    headers, records_csv = _csv_rows_to_dicts(content, delimiter)
    return headers, list(records_csv)


def build_preview(request: IntakePreviewRequest) -> IntakePreviewResponse:
    """Run the full intake preview pipeline."""

    capabilities = CapabilityMap(
        implemented_now=list(_IMPLEMENTED_NOW),
        future_adapters=list(_FUTURE_ADAPTERS),
    )

    headers, records = _parse_records(request)

    # For raw_text the "columns" are the regex-derived field names, which
    # are already LeadIn field names. Build a trivial mapping for them.
    if request.input_type == "raw_text":
        mapped_columns: dict[str, str] = {field: field for field in headers}
        unmapped_columns: list[str] = []
        global_issues: list[IntakeIssue] = []
    else:
        mapped_columns, unmapped_columns, global_issues = _map_columns(headers)

    rows: list[NormalizedLeadRow] = []
    generated_index = 1
    for idx, record in enumerate(records, start=1):
        row, was_generated = _build_row(
            row_number=idx,
            record=record,
            mapped_columns=mapped_columns,
            options=request.options,
            generated_index=generated_index,
        )
        rows.append(row)
        if was_generated:
            generated_index += 1

    total_rows = len(rows)
    valid_rows = sum(1 for row in rows if row.status != "invalid")
    failed_rows = sum(1 for row in rows if row.status == "invalid")
    rows_with_warnings = sum(
        1
        for row in rows
        if row.lead is not None
        and any(issue.severity == "warning" for issue in row.issues)
    )

    if valid_rows == 0:
        status: str = "preview_blocked"
    elif failed_rows == 0 and rows_with_warnings == 0:
        status = "preview_ready"
    else:
        status = "preview_with_warnings"

    return IntakePreviewResponse(
        status=status,  # type: ignore[arg-type]
        input_type=request.input_type,
        source_name=request.source_name,
        total_rows=total_rows,
        valid_rows=valid_rows,
        rows_with_warnings=rows_with_warnings,
        failed_rows=failed_rows,
        max_leads_per_run=MAX_LEADS_PER_RUN,
        mapped_columns=mapped_columns,
        unmapped_columns=unmapped_columns,
        normalized_leads=rows,
        global_issues=global_issues,
        capabilities=capabilities,
    )
