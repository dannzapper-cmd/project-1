"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";

const POINTS = [
  {
    title: "Sample demo / replay",
    body: "Pre-computed results load instantly. No model calls, no API cost, safe for public previews.",
  },
  {
    title: "Add Leads",
    body: "Paste a table or upload CSV when the FastAPI backend is available. LeadForge previews rows, maps columns, and only processes valid entries (max 10 per run).",
  },
  {
    title: "Honest outputs",
    body: "Low-evidence or missing context is surfaced instead of invented research. Human review is required before any action.",
  },
  {
    title: "What LeadForge does not do",
    body: "No emails are sent. No CRM writes. Export and review state stay in your browser for this demo.",
  },
] as const;

export function DemoOnboarding() {
  const [expanded, setExpanded] = useState(true);

  return (
    <section
      aria-labelledby="demo-onboarding-heading"
      className="bg-[--bg-surface] border border-[--border-default] rounded-lg overflow-hidden"
    >
      <button
        type="button"
        id="demo-onboarding-heading"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left hover:bg-[--bg-elevated]/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-[--accent-primary]" aria-hidden />
          <span className="text-sm font-semibold text-[--text-primary]">
            How this demo works
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-[--text-muted]" aria-hidden />
        ) : (
          <ChevronDown className="h-4 w-4 text-[--text-muted]" aria-hidden />
        )}
      </button>

      {expanded && (
        <div className="px-5 pb-5 pt-0 border-t border-[--border-subtle]">
          <p className="text-sm text-[--text-secondary] mt-4 mb-4">
            LeadForge is a B2B sales intelligence workflow: research, qualify,
            strategize, draft outreach, and QA — with traces you can inspect before
            approving anything.
          </p>
          <ul className="grid gap-3 sm:grid-cols-2">
            {POINTS.map((point) => (
              <li
                key={point.title}
                className="bg-[--bg-elevated] rounded-lg p-3 border border-[--border-subtle]"
              >
                <p className="text-xs font-semibold text-[--text-primary] uppercase tracking-wide">
                  {point.title}
                </p>
                <p className="text-xs text-[--text-muted] mt-1 leading-relaxed">
                  {point.body}
                </p>
              </li>
            ))}
          </ul>
          <p className="text-xs text-[--text-muted] mt-4">
            On public Vercel previews without a configured backend, scroll to the
            sample results below. Add Leads needs{" "}
            <code className="font-mono text-[--text-secondary]">NEXT_PUBLIC_API_URL</code>{" "}
            — planned for the controlled deployment block.
          </p>
        </div>
      )}
    </section>
  );
}
