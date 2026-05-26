import type {
  IntakePreviewResponse,
  LeadIn,
  NormalizedLeadRow,
} from "../api/types";

export function processableRows(
  preview: IntakePreviewResponse | null,
): NormalizedLeadRow[] {
  if (!preview) return [];
  return preview.normalized_leads.filter(
    (row) => row.status !== "invalid" && row.lead !== null,
  );
}

export function processableLeads(preview: IntakePreviewResponse | null): LeadIn[] {
  return processableRows(preview)
    .map((row) => row.lead)
    .filter((lead): lead is LeadIn => lead !== null);
}

export function isProcessEnabled({
  preview,
  mappingConfirmed,
  processing,
}: {
  preview: IntakePreviewResponse | null;
  mappingConfirmed: boolean;
  processing: boolean;
}): boolean {
  return Boolean(
    preview &&
      mappingConfirmed &&
      !processing &&
      processableRows(preview).length > 0,
  );
}

export function processLimitMessage(preview: IntakePreviewResponse | null): string | null {
  if (!preview) return null;
  const processableCount = processableRows(preview).length;
  if (processableCount <= preview.max_leads_per_run) return null;
  return (
    `Only the first ${preview.max_leads_per_run} valid leads will be processed ` +
    `from this preview. Remove extra rows to process a different subset.`
  );
}

export function rowMessage(row: NormalizedLeadRow): string {
  if (row.status === "invalid") {
    return `Missing required: ${row.missing_required_fields.join(", ")}`;
  }
  const warningIssues = row.issues.filter((issue) => issue.severity === "warning");
  if (warningIssues.length > 0) {
    return warningIssues.map((issue) => issue.message).join(" ");
  }
  return "Ready to process.";
}
