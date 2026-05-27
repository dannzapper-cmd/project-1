/**
 * Block 10B — classify intake preview/process fetch errors for Add Leads.
 *
 * Network-level failures get a clear backend-unavailable message.
 * Validation and HTTP 4xx responses keep their original detail.
 */

import { ApiError } from "../api/client.ts";

const BACKEND_UNAVAILABLE_MESSAGE =
  "Could not reach the LeadForge backend. The public Vercel preview can still show replay demo results, but Add Leads requires a running FastAPI backend and NEXT_PUBLIC_API_URL set to that backend base URL.";

const BACKEND_UNAVAILABLE_STATUSES = new Set([0, 502, 503, 504]);

export const DEMO_ACCESS_REQUIRED_MESSAGE =
  "This demo action requires the private demo access code. If you're a recruiter or hiring manager, the code was included with the demo link.";

function isFailedToFetchMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower.includes("failed to fetch") ||
    lower.includes("networkerror") ||
    lower.includes("network request failed") ||
    lower.includes("econnrefused") ||
    lower.includes("load failed")
  );
}

export function apiDetail(body: string): string {
  const trimmed = body.trim();
  if (!trimmed) return "";

  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (
      parsed &&
      typeof parsed === "object" &&
      "detail" in parsed
    ) {
      const detail = (parsed as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        return detail
          .map((item) => {
            if (
              item &&
              typeof item === "object" &&
              "msg" in item &&
              typeof (item as { msg: unknown }).msg === "string"
            ) {
              return (item as { msg: string }).msg;
            }
            return "";
          })
          .filter(Boolean)
          .join(" ");
      }
    }
  } catch {
    return trimmed;
  }

  return trimmed;
}

/** True when the error is a reachability / gateway failure, not validation. */
export function isBackendUnavailableError(err: unknown): boolean {
  if (err instanceof TypeError) {
    return true;
  }
  if (err instanceof ApiError) {
    if (BACKEND_UNAVAILABLE_STATUSES.has(err.status)) return true;
    if (err.status >= 500) return true;
    return false;
  }
  if (err instanceof Error && isFailedToFetchMessage(err.message)) {
    return true;
  }
  return false;
}

/**
 * User-facing message for Add Leads preview/process errors.
 * Validation errors (4xx) surface API detail when available.
 */
export function describeIntakePreviewError(err: unknown): string {
  if (isBackendUnavailableError(err)) {
    return BACKEND_UNAVAILABLE_MESSAGE;
  }

  if (err instanceof ApiError) {
    if (err.status === 401 || err.status === 403) {
      return DEMO_ACCESS_REQUIRED_MESSAGE;
    }
    if (err.status === 429) {
      return "This demo is receiving too many requests. Please wait a moment and try again.";
    }
    if (err.status === 413) {
      return "Upload failed: the file is larger than this public demo allows. Try a smaller CSV, Excel, or text-based PDF file.";
    }
    if (err.status === 415) {
      const detail = apiDetail(err.body);
      return detail || "Unsupported file type. Upload CSV, Excel (.xlsx), or a text-based PDF.";
    }
    const detail = apiDetail(err.body);
    if (detail) {
      return `Preview failed (HTTP ${err.status}): ${detail.slice(0, 280)}`;
    }
    return `Preview failed with HTTP ${err.status}. Check your column mapping and required fields.`;
  }

  if (err instanceof Error) {
    return err.message;
  }

  return "Unknown intake error.";
}
