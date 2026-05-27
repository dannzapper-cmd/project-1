"use client";

import { useCallback, useState } from "react";
import { Check, Copy, Download, FileSpreadsheet } from "lucide-react";

interface DashboardEmptyStateProps {
  /** Raw contents of `data/demo/leads.csv` (passed from the server). */
  sampleCsvContent: string;
}

export function DashboardEmptyState({ sampleCsvContent }: DashboardEmptyStateProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(sampleCsvContent);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [sampleCsvContent]);

  const handleDownload = useCallback(() => {
    const blob = new Blob([sampleCsvContent], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "leads.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }, [sampleCsvContent]);

  return (
    <section
      aria-labelledby="dashboard-empty-heading"
      className="surface-card rounded-lg p-8 md:p-10"
    >
      <div className="max-w-2xl mx-auto text-center space-y-4">
        <h2
          id="dashboard-empty-heading"
          className="text-lg font-semibold text-[--text-primary]"
        >
          Run your first lead batch
        </h2>
        <p className="text-sm text-[--text-secondary] leading-relaxed">
          LeadForge runs a controlled six-agent pipeline — Intake, Research,
          Qualifier, Strategist, Email Drafter, and QA Evaluator — to turn B2B
          leads into researched, scored, review-ready outreach. Add leads below
          to see agent activity, decision traces, and metrics for your run.
        </p>
      </div>

      <div className="mt-8 max-w-xl mx-auto rounded-lg border border-[--border-subtle] bg-[--surface] p-5 space-y-4">
        <div className="flex items-start gap-3">
          <FileSpreadsheet
            className="h-5 w-5 text-[--accent-primary] shrink-0 mt-0.5"
            aria-hidden
          />
          <div className="text-left space-y-2">
            <p className="text-sm font-medium text-[--text-primary]">
              Want to see LeadForge in action?
            </p>
            <p className="text-xs text-[--text-secondary] leading-relaxed">
              Use our sample file — fictional companies, fictional contacts.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-2">
          <button
            type="button"
            onClick={handleDownload}
            className="btn-secondary flex-1"
          >
            <Download className="h-4 w-4" aria-hidden />
            Download sample CSV
          </button>
          <button
            type="button"
            onClick={handleCopy}
            className="btn-secondary flex-1"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 text-[--color-success]" aria-hidden />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" aria-hidden />
                Copy to clipboard
              </>
            )}
          </button>
        </div>

        <p className="text-xs text-[--text-muted] text-center sm:text-left">
          Paste or upload it in Add Leads above, then preview and process.
        </p>
        <button
          type="button"
          onClick={() =>
            document.getElementById("lead-intake")?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            })
          }
          className="btn-primary w-full sm:w-auto mx-auto flex"
        >
          Go to Add Leads
        </button>
      </div>
    </section>
  );
}
