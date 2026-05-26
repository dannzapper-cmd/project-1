"use client";

import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  postCsvIntakePreview,
  postIntakePreview,
  postPipelineBatch,
} from "@/lib/api/client";
import type {
  IntakePreviewResponse,
  LeadIn,
  PipelineRunContractOutput,
} from "@/lib/api/types";
import {
  isProcessEnabled,
  processableLeads,
  processLimitMessage,
  rowMessage,
} from "@/lib/intake/preview-state";

const MAX_CSV_UPLOAD_BYTES = 1 * 1024 * 1024;

type InputMode = "paste" | "csv";

interface LeadIntakePanelProps {
  onBatchProcessed: (batch: PipelineRunContractOutput, leads: LeadIn[]) => void;
}

function describeError(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Unknown intake error.";
}

function statusClass(status: string): string {
  if (status === "invalid") return "text-[--color-error]";
  if (status === "warning") return "text-[--color-warning]";
  return "text-[--color-success]";
}

export function LeadIntakePanel({ onBatchProcessed }: LeadIntakePanelProps) {
  const [mode, setMode] = useState<InputMode>("paste");
  const [pasteValue, setPasteValue] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<IntakePreviewResponse | null>(null);
  const [mappingConfirmed, setMappingConfirmed] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const validLeads = useMemo(() => processableLeads(preview), [preview]);
  const limitMessage = processLimitMessage(preview);
  const canProcess = isProcessEnabled({
    preview,
    mappingConfirmed,
    processing,
  });

  const resetPreview = () => {
    setPreview(null);
    setMappingConfirmed(false);
    setSuccessMessage(null);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setFile(event.target.files?.[0] ?? null);
    resetPreview();
  };

  const handlePreview = async () => {
    setError(null);
    setSuccessMessage(null);
    setLoadingPreview(true);
    setMappingConfirmed(false);

    try {
      const nextPreview =
        mode === "csv"
          ? await previewCsvFile(file)
          : await postIntakePreview({
              input_type: "pasted_table",
              source_name: "dashboard_paste",
              content: pasteValue,
              options: {
                has_header: true,
                delimiter: "auto",
                generate_missing_lead_ids: true,
              },
            });
      setPreview(nextPreview);
    } catch (err) {
      setPreview(null);
      setError(describeError(err));
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleProcess = async () => {
    if (!preview || !canProcess) return;
    setError(null);
    setSuccessMessage(null);
    setProcessing(true);

    try {
      const selectedLeads = validLeads.slice(0, preview.max_leads_per_run);
      const batch = await postPipelineBatch(selectedLeads);
      onBatchProcessed(batch, selectedLeads);
      setSuccessMessage(
        `Processed ${batch.lead_count} lead${batch.lead_count === 1 ? "" : "s"} through the deterministic pipeline.`,
      );
    } catch (err) {
      setError(describeError(err));
    } finally {
      setProcessing(false);
    }
  };

  const previewDisabledReason =
    mode === "paste" && pasteValue.trim() === ""
      ? "Paste CSV or spreadsheet rows with headers before previewing."
      : mode === "csv" && file === null
        ? "Choose a .csv file before previewing."
        : null;

  const processDisabledReason = !preview
    ? "Preview lead data first."
    : !mappingConfirmed
      ? "Confirm the detected column mapping before processing."
      : validLeads.length === 0
        ? "No valid rows are available to process."
        : null;

  return (
    <section id="lead-intake" className="bg-[--bg-surface] border border-[--border-default] rounded-lg p-5 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-[--text-primary]">
            Add Leads
          </h2>
          <p className="text-sm text-[--text-muted] mt-1">
            Use the sample demo below, paste spreadsheet rows, or upload a CSV.
            LeadForge previews and validates B2B lead data before processing.
          </p>
        </div>
        <div className="text-xs text-[--text-muted] border border-[--border-subtle] rounded-full px-3 py-1">
          Max {preview?.max_leads_per_run ?? 10} leads per run
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => {
            setMode("paste");
            resetPreview();
          }}
          className={`px-3 py-1.5 rounded-md text-sm font-medium ${
            mode === "paste"
              ? "bg-[--accent-primary] text-white"
              : "border border-[--border-default] text-[--text-secondary]"
          }`}
        >
          Paste table
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("csv");
            resetPreview();
          }}
          className={`px-3 py-1.5 rounded-md text-sm font-medium ${
            mode === "csv"
              ? "bg-[--accent-primary] text-white"
              : "border border-[--border-default] text-[--text-secondary]"
          }`}
        >
          Upload CSV
        </button>
        <span className="text-xs text-[--text-muted] self-center">
          Required columns: company_name and industry. Recommended: website,
          country, contact_role.
        </span>
      </div>

      {mode === "paste" ? (
        <Textarea
          value={pasteValue}
          onChange={(event) => {
            setPasteValue(event.target.value);
            resetPreview();
          }}
          placeholder={"company_name\tindustry\twebsite\tcountry\tcontact_role\nAcme SaaS\tB2B SaaS\tacme.example\tUS\tVP Sales"}
          className="min-h-32 bg-[--bg-elevated] border-[--border-default] text-sm"
        />
      ) : (
        <div className="border border-dashed border-[--border-default] rounded-lg p-4">
          <label className="flex items-center gap-3 text-sm text-[--text-secondary] cursor-pointer">
            <Upload className="h-4 w-4" />
            <span>{file ? file.name : "Choose a UTF-8 .csv file (max 1 MB)"}</span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={handleFileChange}
              className="sr-only"
            />
          </label>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          onClick={handlePreview}
          disabled={loadingPreview || previewDisabledReason !== null}
          className="bg-[--accent-primary] hover:bg-[--accent-primary]/90 text-white disabled:opacity-50"
        >
          {loadingPreview ? "Previewing..." : "Preview and validate"}
        </Button>
        {previewDisabledReason && (
          <p className="text-xs text-[--text-muted]">{previewDisabledReason}</p>
        )}
      </div>

      {error && (
        <div role="alert" className="text-sm text-[--color-error] bg-[--color-error-bg] border border-[--color-error]/30 rounded-lg p-3">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="text-sm text-[--color-success] bg-[--color-success-bg] border border-[--color-success]/30 rounded-lg p-3">
          {successMessage}
        </div>
      )}

      {preview && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-[--bg-elevated] rounded-lg p-3">
              <p className="text-xs text-[--text-muted]">Rows</p>
              <p className="font-semibold text-[--text-primary]">{preview.total_rows}</p>
            </div>
            <div className="bg-[--bg-elevated] rounded-lg p-3">
              <p className="text-xs text-[--text-muted]">Processable</p>
              <p className="font-semibold text-[--color-success]">{preview.valid_rows}</p>
            </div>
            <div className="bg-[--bg-elevated] rounded-lg p-3">
              <p className="text-xs text-[--text-muted]">Warnings</p>
              <p className="font-semibold text-[--color-warning]">{preview.rows_with_warnings}</p>
            </div>
            <div className="bg-[--bg-elevated] rounded-lg p-3">
              <p className="text-xs text-[--text-muted]">Invalid</p>
              <p className="font-semibold text-[--color-error]">{preview.failed_rows}</p>
            </div>
          </div>

          <div className="border border-[--border-default] rounded-lg overflow-hidden">
            <div className="bg-[--bg-elevated] px-4 py-3 border-b border-[--border-default]">
              <h3 className="text-sm font-medium text-[--text-primary]">
                Detected column mapping
              </h3>
              <p className="text-xs text-[--text-muted] mt-1">
                Confirm this mapping before processing. Unmapped columns are
                skipped and remain visible here.
              </p>
            </div>
            <div className="p-4 flex flex-wrap gap-2">
              {Object.entries(preview.mapped_columns).map(([source, target]) => (
                <span key={source} className="text-xs border border-[--border-subtle] rounded-full px-3 py-1 text-[--text-secondary]">
                  {source} -&gt; {target}
                </span>
              ))}
              {preview.unmapped_columns.map((column) => (
                <span key={column} className="text-xs border border-[--color-warning]/40 rounded-full px-3 py-1 text-[--color-warning]">
                  skipped: {column}
                </span>
              ))}
            </div>
            <div className="px-4 pb-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setMappingConfirmed(true)}
                disabled={mappingConfirmed}
                className="border-[--border-default] text-[--text-secondary]"
              >
                {mappingConfirmed ? "Mapping confirmed" : "Confirm mapping"}
              </Button>
            </div>
          </div>

          {limitMessage && (
            <p className="text-xs text-[--color-warning]">{limitMessage}</p>
          )}

          <div className="border border-[--border-default] rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[--bg-elevated] text-[--text-muted]">
                <tr>
                  <th className="text-left px-3 py-2">Row</th>
                  <th className="text-left px-3 py-2">Status</th>
                  <th className="text-left px-3 py-2">Company</th>
                  <th className="text-left px-3 py-2">Industry</th>
                  <th className="text-left px-3 py-2">Website</th>
                  <th className="text-left px-3 py-2">Message</th>
                </tr>
              </thead>
              <tbody>
                {preview.normalized_leads.map((row) => (
                  <tr key={row.row_number} className="border-t border-[--border-subtle]">
                    <td className="px-3 py-2 text-[--text-muted]">{row.row_number}</td>
                    <td className={`px-3 py-2 font-medium ${statusClass(row.status)}`}>
                      {row.status}
                    </td>
                    <td className="px-3 py-2 text-[--text-primary]">
                      {String(row.normalized_fields.company_name ?? "")}
                    </td>
                    <td className="px-3 py-2 text-[--text-secondary]">
                      {String(row.normalized_fields.industry ?? "")}
                    </td>
                    <td className="px-3 py-2 text-[--text-secondary]">
                      {String(row.normalized_fields.website ?? "")}
                    </td>
                    <td className="px-3 py-2 text-[--text-muted] max-w-md">
                      {rowMessage(row)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              onClick={handleProcess}
              disabled={!canProcess}
              className="bg-[--accent-primary] hover:bg-[--accent-primary]/90 text-white disabled:opacity-50"
            >
              {processing ? "Processing..." : "Process valid leads"}
            </Button>
            {processDisabledReason && (
              <p className="text-xs text-[--text-muted]">{processDisabledReason}</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

async function previewCsvFile(file: File | null): Promise<IntakePreviewResponse> {
  if (!file) {
    throw new Error("Choose a .csv file before previewing.");
  }
  if (!file.name.toLowerCase().endsWith(".csv")) {
    throw new Error("Only .csv files are supported in this block.");
  }
  if (file.size > MAX_CSV_UPLOAD_BYTES) {
    throw new Error("CSV file is larger than the 1 MB safety limit.");
  }
  return postCsvIntakePreview(file);
}
