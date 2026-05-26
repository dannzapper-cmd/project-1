"""Smart lead intake endpoints.

Fase 4.3A exposes ``POST /api/intake/preview`` for text/structured input
(csv_text, pasted_table, records_json, raw_text). Fase 4.3B.1 adds a
minimal multipart adapter, ``POST /api/intake/preview-file/csv``, that
accepts a single uploaded ``.csv`` file, decodes it safely, and routes it
through the existing Fase 4.3A pipeline as ``csv_text``.

Both endpoints are preview-only: no DB writes, no agent invocation, no
LLM calls, no external I/O, no file persistence to disk.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.intake import (
    IntakeIssue,
    IntakeOptions,
    IntakePreviewRequest,
    IntakePreviewResponse,
)
from app.services.intake_file_extractor import (
    IntakeFileExtractionError,
    extract_csv_text,
    extract_pdf_records,
    extract_xlsx_records,
)
from app.services.intake_normalizer import build_preview

router = APIRouter(prefix="/api/intake", tags=["intake"])
logger = get_logger(__name__)

# Hard cap for CSV uploads in Fase 4.3B.1. Files are read fully into memory
# before being passed to the existing csv_text pipeline.
_MAX_CSV_UPLOAD_BYTES: int = 1 * 1024 * 1024

# Content types that are commonly emitted by browsers / OSes for .csv files.
# Used only when the client actually sends a non-empty Content-Type; when
# Content-Type is absent we rely on the filename extension alone.
_ACCEPTED_CSV_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    }
)

_ACCEPTED_XLSX_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    }
)
_ACCEPTED_PDF_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/octet-stream",
    }
)
_FORMAT_INPUT_TYPES: dict[str, str] = {
    ".csv": "csv_file",
    ".xlsx": "excel_file",
    ".pdf": "pdf_file",
}


async def _read_and_decode_csv_upload(file: UploadFile) -> str:
    """Validate, read and UTF-8-decode an uploaded ``.csv`` file.

    Returns the decoded text content ready for the ``csv_text`` pipeline.
    Raises ``HTTPException`` with the appropriate status code on any
    validation failure. The validation order is:

    1. Filename must end with ``.csv`` (case-insensitive) → 415.
    2. ``Content-Type``, if present and non-empty, must be in the
       accepted list → 415.
    3. Read at most ``_MAX_CSV_UPLOAD_BYTES + 1`` bytes (so an oversize
       upload is rejected without loading the full payload into memory);
       empty payload → 422.
    4. Reject payloads larger than ``_MAX_CSV_UPLOAD_BYTES`` → 413.
    5. Decode as ``utf-8-sig`` (handles optional BOM). Any failure → 422.
       No further encodings are tried.
    """

    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .csv files are accepted by this endpoint.",
        )

    content_type = (file.content_type or "").strip().lower()
    if content_type and content_type not in _ACCEPTED_CSV_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content-Type '{file.content_type}' is not accepted for CSV upload.",
        )

    # Read one byte past the limit so we can distinguish "exactly at limit"
    # from "over limit" without loading an arbitrarily large file into RAM.
    file_bytes = await file.read(_MAX_CSV_UPLOAD_BYTES + 1)

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > _MAX_CSV_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Uploaded file is larger than the {_MAX_CSV_UPLOAD_BYTES} "
                f"byte limit for CSV uploads."
            ),
        )

    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File could not be decoded as UTF-8.",
        )


def _file_extension(file: UploadFile) -> str:
    filename = file.filename or ""
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        return ".xlsx"
    if lower.endswith(".xls"):
        return ".xls"
    if lower.endswith(".csv"):
        return ".csv"
    if lower.endswith(".pdf"):
        return ".pdf"
    return ""


def _validate_multiformat_upload(file: UploadFile) -> str:
    extension = _file_extension(file)
    if extension == ".xls":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Legacy .xls files are not supported in this block. "
                "Save the workbook as .xlsx and upload again."
            ),
        )
    if extension not in {".csv", ".xlsx", ".pdf"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .csv, .xlsx, and text-based .pdf files are accepted.",
        )

    content_type = (file.content_type or "").strip().lower()
    accepted_types = {
        ".csv": _ACCEPTED_CSV_CONTENT_TYPES,
        ".xlsx": _ACCEPTED_XLSX_CONTENT_TYPES,
        ".pdf": _ACCEPTED_PDF_CONTENT_TYPES,
    }[extension]
    if content_type and content_type not in accepted_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Content-Type '{file.content_type}' is not accepted for "
                f"{extension} upload."
            ),
        )
    return extension


async def _read_upload_bytes(file: UploadFile) -> tuple[str, bytes]:
    extension = _validate_multiformat_upload(file)
    settings = get_settings()
    max_bytes = settings.intake_max_upload_mb * 1024 * 1024
    file_bytes = await file.read(max_bytes + 1)

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Uploaded file is larger than the "
                f"{settings.intake_max_upload_mb} MB safety limit."
            ),
        )

    return extension, file_bytes


def _build_preview_from_file_payload(
    *,
    extension: str,
    file_bytes: bytes,
    source_name: str | None,
    filename: str | None,
    generate_missing_lead_ids: bool,
) -> IntakePreviewResponse:
    try:
        if extension == ".csv":
            payload = extract_csv_text(file_bytes)
        elif extension == ".xlsx":
            payload = extract_xlsx_records(file_bytes)
        elif extension == ".pdf":
            payload = extract_pdf_records(file_bytes)
        else:
            raise IntakeFileExtractionError("Unsupported file type.", status_code=415)
    except IntakeFileExtractionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    resolved_source_name = (
        source_name
        if source_name is not None and source_name.strip() != ""
        else filename
    )

    request = IntakePreviewRequest(
        input_type=payload.input_type,
        source_name=resolved_source_name,
        content=payload.content,
        records=payload.records,
        options=IntakeOptions(generate_missing_lead_ids=generate_missing_lead_ids),
    )
    preview = build_preview(request)

    global_issues = list(preview.global_issues)
    for warning in payload.warnings:
        global_issues.append(
            IntakeIssue(
                severity="warning",
                code="file_extraction_warning",
                message=warning,
                row_number=None,
                field=None,
            )
        )

    response_status = preview.status
    if payload.warnings and preview.valid_rows > 0:
        response_status = "preview_with_warnings"

    return preview.model_copy(
        update={
            "input_type": _FORMAT_INPUT_TYPES.get(extension, preview.input_type),
            "global_issues": global_issues,
            "status": response_status,
        }
    )


@router.post("/preview", response_model=IntakePreviewResponse)
def preview_intake(request: IntakePreviewRequest) -> IntakePreviewResponse:
    """Return a normalized preview for the submitted intake payload."""

    if request.input_type in {"csv_text", "pasted_table", "raw_text"}:
        if request.content is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"'content' is required when input_type is '{request.input_type}'."
                ),
            )
        if request.records is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"'records' must not be provided when input_type is "
                    f"'{request.input_type}'. It is only accepted for "
                    f"input_type='records_json'."
                ),
            )

    if request.input_type == "records_json":
        if request.records is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="'records' is required when input_type is 'records_json'.",
            )

    return build_preview(request)


@router.post("/preview-file/csv", response_model=IntakePreviewResponse)
async def preview_intake_csv_file(
    file: Annotated[UploadFile, File(description="CSV file to preview.")],
    source_name: Annotated[str | None, Form()] = None,
    delimiter: Annotated[str, Form()] = "auto",
    # FastAPI Form parameters do not reliably convert strings to ``bool``;
    # accept the value as a string and convert manually. Any value other
    # than "true"/"false" (case-insensitive) is treated as True.
    generate_missing_lead_ids_str: Annotated[
        str, Form(alias="generate_missing_lead_ids")
    ] = "true",
) -> IntakePreviewResponse:
    """Accept a CSV file upload and return a normalized intake preview.

    The endpoint is a thin adapter over the Fase 4.3A ``csv_text``
    pipeline: it validates and decodes the file, then calls
    ``build_preview`` directly with ``input_type="csv_text"``.
    """

    if delimiter not in {"auto", ",", "\t"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Invalid delimiter. Accepted values are 'auto', ',' or '\\t'."
            ),
        )

    content = await _read_and_decode_csv_upload(file)

    # The .csv filename validation inside _read_and_decode_csv_upload already
    # rejects missing/empty filenames with HTTP 415, so at this point
    # file.filename is guaranteed to be a non-empty string ending in .csv.
    if source_name is not None and source_name.strip() != "":
        resolved_source_name = source_name
    else:
        resolved_source_name = file.filename  # type: ignore[assignment]

    generate_missing_lead_ids = generate_missing_lead_ids_str.lower() != "false"

    request = IntakePreviewRequest(
        input_type="csv_text",
        source_name=resolved_source_name,
        content=content,
        options=IntakeOptions(
            has_header=True,
            delimiter=delimiter,  # type: ignore[arg-type]
            generate_missing_lead_ids=generate_missing_lead_ids,
        ),
    )

    return build_preview(request)


@router.post("/extract-file", response_model=IntakePreviewResponse)
async def extract_intake_file(
    file: Annotated[
        UploadFile,
        File(description="CSV, XLSX, or text-based PDF table to preview."),
    ],
    source_name: Annotated[str | None, Form()] = None,
    generate_missing_lead_ids_str: Annotated[
        str, Form(alias="generate_missing_lead_ids")
    ] = "true",
) -> IntakePreviewResponse:
    """Extract an uploaded intake file and return the standard preview.

    This is a focused Block 10F-A adapter over the existing preview pipeline.
    The upload is read from ``UploadFile`` in memory with the
    ``INTAKE_MAX_UPLOAD_MB`` cap, never written to disk, and never sent to
    live research, Groq, email, CRM, storage, or any background job.
    """

    extension, file_bytes = await _read_upload_bytes(file)
    generate_missing_lead_ids = generate_missing_lead_ids_str.lower() != "false"

    return _build_preview_from_file_payload(
        extension=extension,
        file_bytes=file_bytes,
        source_name=source_name,
        filename=file.filename,
        generate_missing_lead_ids=generate_missing_lead_ids,
    )
