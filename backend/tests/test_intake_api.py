"""Integration tests for the Fase 4.3A intake endpoint, the Fase 4.3B.1
CSV file upload adapter, and stability of the pre-existing
Fase 4.1 / 4.2 endpoints.

CSV upload tests numbered ``csv_NN`` map 1:1 to the Fase 4.3B.1 spec
test list (NN = 1..15).
"""

from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app

_CSV_UPLOAD_URL = "/api/intake/preview-file/csv"
_EXTRACT_FILE_URL = "/api/intake/extract-file"


def _xlsx_bytes(rows: list[list[str]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _pdf_bytes(text: str) -> bytes:
    stream = "BT /F1 12 Tf 72 720 Td 14 TL "
    for idx, line in enumerate(text.split("\n")):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if idx == 0:
            stream += f"({escaped}) Tj "
        else:
            stream += f"T* ({escaped}) Tj "
    stream += "ET"
    stream_bytes = stream.encode("latin-1")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        (
            b"5 0 obj << /Length "
            + str(len(stream_bytes)).encode("ascii")
            + b" >> stream\n"
            + stream_bytes
            + b"\nendstream endobj\n"
        ),
    ]
    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets: list[int] = []
    for obj in objects:
        offsets.append(output.tell())
        output.write(obj)
    xref_offset = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.write(
        (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return output.getvalue()


def test_13_post_intake_preview_records_json_returns_200_and_expected_keys() -> None:
    payload = {
        "input_type": "records_json",
        "source_name": "manual_paste",
        "records": [
            {
                "company_name": "Acme Corp",
                "industry": "SaaS",
                "website": "acme.com",
                "contact_role": "CTO",
            }
        ],
    }
    with TestClient(app) as client:
        response = client.post("/api/intake/preview", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "normalized_leads" in body
    assert "capabilities" in body


def test_14_get_demo_summary_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/summary")

    assert response.status_code == 200


def test_15_get_demo_leads_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/api/demo/leads")

    assert response.status_code == 200


def test_16_get_health_still_returns_200() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_17_records_field_rejected_for_non_records_json_input_types() -> None:
    """`records` must only be accepted for `input_type='records_json'`.

    For csv_text / pasted_table / raw_text, providing `records` (even
    alongside valid `content`) must return HTTP 422.
    """

    payloads = [
        {
            "input_type": "csv_text",
            "content": "company_name\nAcme Corp\n",
            "records": [{"company_name": "Other"}],
        },
        {
            "input_type": "pasted_table",
            "content": "company_name\tindustry\nAcme\tSaaS\n",
            "records": [{"company_name": "Other"}],
        },
        {
            "input_type": "raw_text",
            "content": "Company: Acme Corp\n",
            "records": [{"company_name": "Other"}],
        },
    ]
    with TestClient(app) as client:
        for payload in payloads:
            response = client.post("/api/intake/preview", json=payload)
            assert response.status_code == 422, (
                f"Expected 422 for input_type={payload['input_type']} "
                f"with records provided, got {response.status_code}: {response.text}"
            )


# ---------------------------------------------------------------------------
# Fase 4.3B.1 — CSV file upload adapter tests
# ---------------------------------------------------------------------------


def test_csv_01_valid_csv_with_standard_headers_returns_200_and_expected_keys() -> None:
    """csv_01: valid CSV + standard headers → 200 with expected response keys."""

    csv_bytes = (
        b"company_name,industry,website,contact_role\n"
        b"Acme Corp,SaaS,acme.com,CTO\n"
        b"Globex,Finance,globex.com,CFO\n"
    )
    files = {"file": ("leads.csv", csv_bytes, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "normalized_leads" in body
    assert "capabilities" in body


def test_csv_02_response_shape_matches_preview_endpoint_shape() -> None:
    """csv_02: response keys/types identical to POST /api/intake/preview."""

    csv_bytes = (
        b"company_name,industry,website,contact_role\n"
        b"Acme Corp,SaaS,acme.com,CTO\n"
    )
    files = {"file": ("leads.csv", csv_bytes, "text/csv")}

    json_payload = {
        "input_type": "csv_text",
        "source_name": "leads.csv",
        "content": csv_bytes.decode("utf-8"),
    }

    with TestClient(app) as client:
        upload_response = client.post(_CSV_UPLOAD_URL, files=files)
        preview_response = client.post("/api/intake/preview", json=json_payload)

    assert upload_response.status_code == 200
    assert preview_response.status_code == 200

    upload_body = upload_response.json()
    preview_body = preview_response.json()

    assert set(upload_body.keys()) == set(preview_body.keys())

    for key in upload_body.keys():
        assert type(upload_body[key]) is type(preview_body[key]), (
            f"Type mismatch for key '{key}': "
            f"upload={type(upload_body[key]).__name__} "
            f"preview={type(preview_body[key]).__name__}"
        )


def test_csv_03_source_name_defaults_to_uploaded_filename() -> None:
    """csv_03: absent source_name → response.source_name == filename."""

    csv_bytes = b"company_name,industry\nAcme Corp,SaaS\n"
    files = {"file": ("custom_leads.csv", csv_bytes, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 200
    assert response.json()["source_name"] == "custom_leads.csv"


def test_csv_04_provided_source_name_overrides_filename() -> None:
    """csv_04: provided source_name overrides the uploaded filename."""

    csv_bytes = b"company_name,industry\nAcme Corp,SaaS\n"
    files = {"file": ("custom_leads.csv", csv_bytes, "text/csv")}
    data = {"source_name": "Q2 import"}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files, data=data)

    assert response.status_code == 200
    assert response.json()["source_name"] == "Q2 import"


def test_csv_05_alias_headers_are_mapped_to_lead_in_fields() -> None:
    """csv_05: CSV with alias headers maps to canonical LeadIn fields."""

    csv_bytes = (
        b"Company Name,Sector,URL,Title\n"
        b"Acme Corp,SaaS,acme.com,CTO\n"
    )
    files = {"file": ("leads.csv", csv_bytes, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["mapped_columns"] == {
        "Company Name": "company_name",
        "Sector": "industry",
        "URL": "website",
        "Title": "contact_role",
    }
    lead = body["normalized_leads"][0]["lead"]
    assert lead["company_name"] == "Acme Corp"
    assert lead["industry"] == "SaaS"
    assert lead["website"] == "acme.com"
    assert lead["contact_role"] == "CTO"


def test_csv_06_row_missing_company_name_yields_failed_row() -> None:
    """csv_06: one row missing company_name → that row has
    code=missing_company_name and confidence=None."""

    csv_bytes = (
        b"company_name,industry,website,contact_role\n"
        b"Acme Corp,SaaS,acme.com,CTO\n"
        b",Finance,globex.com,CFO\n"
    )
    files = {"file": ("leads.csv", csv_bytes, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    rows = body["normalized_leads"]
    assert len(rows) == 2

    failed_row = rows[1]
    assert failed_row["lead"] is None
    assert failed_row["confidence"] is None
    assert any(issue["code"] == "missing_company_name" for issue in failed_row["issues"])


def test_csv_07_all_rows_missing_company_name_is_preview_blocked() -> None:
    """csv_07: every row missing company_name → status=preview_blocked."""

    csv_bytes = (
        b"company_name,industry\n"
        b",SaaS\n"
        b",Finance\n"
    )
    files = {"file": ("leads.csv", csv_bytes, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "preview_blocked"
    assert body["valid_rows"] == 0
    assert body["failed_rows"] == 2


def test_csv_08_non_csv_extension_returns_415() -> None:
    """csv_08: .txt extension rejected with 415."""

    files = {"file": ("leads.txt", b"company_name\nAcme\n", "text/plain")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 415


def test_csv_09_empty_file_returns_422() -> None:
    """csv_09: empty file (0 bytes) → 422."""

    files = {"file": ("empty.csv", b"", "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 422


def test_csv_10_header_only_file_returns_200_with_zero_rows() -> None:
    """csv_10: header-only file → 200, total_rows=0, valid_rows=0."""

    csv_bytes = b"company_name,industry,website,contact_role\n"
    files = {"file": ("leads.csv", csv_bytes, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 0
    assert body["valid_rows"] == 0


def test_csv_11_invalid_utf8_bytes_return_422() -> None:
    """csv_11: invalid UTF-8 bytes → 422."""

    files = {
        "file": ("leads.csv", b"\xff\xfe\x00 invalid bytes", "text/csv"),
    }

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 422


def test_csv_12_file_over_configured_limit_returns_413() -> None:
    """csv_12: file > configured upload limit → 413.

    The endpoint reads only one byte past the configured cap from the
    upload before rejecting, so a much larger payload (e.g. 8 MiB) must
    still be refused with 413 without being fully loaded into memory.
    """

    # ``5 MiB + 1`` byte — minimal overflow for the default demo cap.
    minimal_overflow = b"a" * (5 * 1024 * 1024 + 1)
    files = {"file": ("big.csv", minimal_overflow, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 413

    # Larger payload also rejected; documents the bounded-read behavior.
    large_overflow = b"b" * (8 * 1024 * 1024)
    files = {"file": ("huge.csv", large_overflow, "text/csv")}

    with TestClient(app) as client:
        response = client.post(_CSV_UPLOAD_URL, files=files)

    assert response.status_code == 413


def test_csv_13_existing_preview_endpoint_records_json_still_returns_200() -> None:
    """csv_13: existing POST /api/intake/preview (records_json) still 200."""

    payload = {
        "input_type": "records_json",
        "records": [
            {
                "company_name": "Acme Corp",
                "industry": "SaaS",
                "website": "acme.com",
                "contact_role": "CTO",
            }
        ],
    }
    with TestClient(app) as client:
        response = client.post("/api/intake/preview", json=payload)

    assert response.status_code == 200


def test_csv_14_existing_demo_summary_still_returns_200() -> None:
    """csv_14: existing GET /api/demo/summary still 200."""

    with TestClient(app) as client:
        response = client.get("/api/demo/summary")

    assert response.status_code == 200


def test_csv_15_existing_health_still_returns_200() -> None:
    """csv_15: existing GET /health still 200."""

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Block 10F-A — multi-format file extraction tests
# ---------------------------------------------------------------------------


def test_extract_xlsx_valid_first_sheet_uses_existing_preview_shape() -> None:
    xlsx_bytes = _xlsx_bytes(
        [
            ["company_name", "industry", "website", "contact_role"],
            ["Acme Corp", "SaaS", "acme.example", "CTO"],
            ["Globex", "Finance", "globex.example", "CFO"],
        ]
    )
    files = {
        "file": (
            "leads.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["input_type"] == "excel_file"
    assert body["total_rows"] == 2
    assert body["mapped_columns"]["company_name"] == "company_name"
    assert body["mapped_columns"]["industry"] == "industry"
    assert body["normalized_leads"][0]["lead"]["company_name"] == "Acme Corp"


def test_extract_xlsx_empty_first_sheet_returns_clear_422() -> None:
    xlsx_bytes = _xlsx_bytes([["company_name", "industry"]])
    files = {
        "file": (
            "empty.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The first sheet appears empty. Check that your lead table is on the first sheet."
    )


def test_extract_xlsx_over_limit_previews_first_max_rows_with_warning() -> None:
    rows = [["company_name", "industry"]]
    rows.extend([f"Company {idx}", "SaaS"] for idx in range(12))
    xlsx_bytes = _xlsx_bytes(rows)
    files = {
        "file": (
            "many.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 10
    assert body["max_leads_per_run"] == 10
    assert any(
        "found 12 rows; previewing the first 10 rows" in issue["message"]
        for issue in body["global_issues"]
    )


def test_extract_pdf_text_table_returns_preview_rows() -> None:
    pdf_bytes = _pdf_bytes(
        "company_name,industry,website\n"
        "Acme Corp,SaaS,acme.example\n"
        "Globex,Finance,globex.example"
    )
    files = {"file": ("leads.pdf", pdf_bytes, "application/pdf")}

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["input_type"] == "pdf_file"
    assert body["total_rows"] == 2
    assert body["normalized_leads"][0]["lead"]["company_name"] == "Acme Corp"


def test_extract_pdf_image_only_returns_ocr_needed_message() -> None:
    files = {"file": ("scan.pdf", _pdf_bytes(""), "application/pdf")}

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "This PDF appears to require OCR. Image/OCR intake is planned for the next block."
    )


def test_extract_file_rejects_unsupported_extension() -> None:
    files = {"file": ("leads.txt", b"company_name,industry\nAcme,SaaS\n", "text/plain")}

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 415


def test_extract_file_rejects_legacy_xls_extension() -> None:
    files = {"file": ("leads.xls", b"not really excel", "application/vnd.ms-excel")}

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 415
    assert "Legacy .xls files are not supported" in response.json()["detail"]


def test_extract_file_rejects_empty_upload() -> None:
    files = {"file": ("empty.csv", b"", "text/csv")}

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 422


def test_extract_file_rejects_upload_over_default_limit() -> None:
    files = {"file": ("big.csv", b"a" * (5 * 1024 * 1024 + 1), "text/csv")}

    with TestClient(app) as client:
        response = client.post(_EXTRACT_FILE_URL, files=files)

    assert response.status_code == 413
