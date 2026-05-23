/**
 * Block 7.4 — Reviewed-lead CSV export.
 *
 * Pure helpers + a browser-side download trigger for the single
 * lead the user has just reviewed in the dashboard drawer. There
 * is no backend export endpoint, no batch export, no JSON output,
 * no persistence, and no email send. The file is built entirely
 * in memory and handed to the browser via a Blob + Object URL.
 *
 * CSV encoding follows RFC 4180:
 *   - LF / CR / comma / double-quote in a value ⇒ wrap value in
 *     double quotes.
 *   - Internal double quotes are escaped by doubling them
 *     ("        →    "").
 *   - Cells whose first character could be interpreted as a
 *     spreadsheet formula (=, +, -, @, TAB, CR) are prefixed with
 *     a single apostrophe BEFORE the RFC 4180 wrap so Excel /
 *     Google Sheets / LibreOffice cannot trigger formula
 *     evaluation when a CSV is opened in a spreadsheet app. This
 *     is the OWASP-recommended mitigation.
 */

import type { Lead, LeadDetail } from "@/lib/types";

// --------------------------------------------------------------------------- //
// CSV primitives (pure, no DOM access)                                        //
// --------------------------------------------------------------------------- //

/** Characters whose presence triggers spreadsheet formula evaluation. */
const FORMULA_LEAD_CHARS = new Set(["=", "+", "-", "@", "\t", "\r"]);

/**
 * Prefix a single apostrophe to values whose first character could
 * be interpreted as a spreadsheet formula. Strings that do not
 * lead with a dangerous character are returned unchanged.
 *
 * Numbers are coerced to strings for caller convenience. ``null``
 * and ``undefined`` are treated as empty strings.
 */
export function protectCsvFormula(value: unknown): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (str.length === 0) return str;
  return FORMULA_LEAD_CHARS.has(str[0]) ? `'${str}` : str;
}

/**
 * RFC 4180 escape a single CSV field. Values containing a comma,
 * double quote, LF, or CR are wrapped in double quotes and any
 * internal double quote is doubled. All other values are returned
 * unchanged so a "Veltrix Systems" cell remains six characters.
 *
 * Apply ``protectCsvFormula`` BEFORE this function so the leading
 * apostrophe survives wrapping intact.
 */
export function csvEscape(value: string): string {
  const needsQuoting =
    value.includes(",") ||
    value.includes('"') ||
    value.includes("\n") ||
    value.includes("\r");
  if (!needsQuoting) return value;
  return `"${value.replace(/"/g, '""')}"`;
}

/** Compose ``protectCsvFormula`` then ``csvEscape`` for a single cell. */
export function toCsvCell(value: unknown): string {
  return csvEscape(protectCsvFormula(value));
}

// --------------------------------------------------------------------------- //
// Lead → CSV                                                                  //
// --------------------------------------------------------------------------- //

/**
 * Header order for the reviewed-lead CSV. The order is the source
 * of truth for the export columns; never reorder this without
 * intent because exported files may be diffed downstream.
 */
export const REVIEWED_LEAD_CSV_HEADERS: readonly string[] = [
  "lead_id",
  "company",
  "website",
  "industry",
  "country",
  "contact_name",
  "contact_role",
  "fit_score",
  "priority",
  "review_status",
  "email_subject",
  "email_body",
  "run_mode",
  "model_used",
] as const;

/**
 * Render the reviewed-lead CSV for a single `LeadDetail`. The
 * `status` argument is the locally-tracked human-review status
 * (``"Approved" | "Rejected" | "Needs Edit"`` after Block 7.4 — the
 * caller MUST NOT invoke this with ``"Pending Review"`` because the
 * UI gates the export on a reviewed status, but the helper does
 * not enforce that gate so it stays unit-testable).
 *
 * The resulting CSV ends with a single trailing newline (Excel and
 * most viewers ignore it; some Unix tools care). Line ending is LF.
 */
export function leadToCsv(detail: LeadDetail, status: Lead["status"]): string {
  const headerRow = REVIEWED_LEAD_CSV_HEADERS.map(toCsvCell).join(",");
  const valueRow = [
    detail.id,
    detail.company,
    detail.website,
    detail.industry,
    detail.country,
    detail.contact_name,
    detail.contact_role,
    detail.fit_score,
    detail.priority,
    status,
    detail.email_subject,
    detail.email_body,
    detail.run_mode,
    detail.model_used,
  ]
    .map(toCsvCell)
    .join(",");
  return `${headerRow}\n${valueRow}\n`;
}

// --------------------------------------------------------------------------- //
// Browser-side download trigger                                               //
// --------------------------------------------------------------------------- //

/**
 * Build a filesystem-safe filename for the CSV download. The
 * `lead_id` is sanitised so a malformed id ("../../etc/passwd" or
 * a Windows reserved name) cannot escape the suggested filename.
 */
export function leadCsvFilename(leadId: string): string {
  const safeId = leadId.replace(/[^A-Za-z0-9._-]/g, "_") || "lead";
  return `leadforge-${safeId}-reviewed.csv`;
}

/**
 * Trigger a browser download of the reviewed-lead CSV. No backend
 * call, no fetch, no persistence — the file is built in memory,
 * piped through a Blob + Object URL, and the URL is revoked after
 * the click is dispatched so the browser can garbage-collect.
 *
 * The function is a no-op in non-browser environments (server-side
 * render, Node test runner) so it can be imported safely from
 * shared modules without guarding the call site with `typeof
 * window`.
 */
export function downloadLeadCsv(
  detail: LeadDetail,
  status: Lead["status"],
): void {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }

  const csv = leadToCsv(detail, status);
  // Include a UTF-8 BOM so Excel on Windows opens the file with the
  // correct encoding (it otherwise auto-detects to CP1252).
  const bom = "\uFEFF";
  const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = leadCsvFilename(detail.id);
  // Some browsers require the anchor to be in the DOM for the
  // programmatic click to register; Safari historically did.
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Defer the revoke by one tick so older browsers still have a
  // chance to start the download before the URL is invalidated.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
