"use client";

import type { Lead } from "@/lib/types";

interface DemoNextStepsProps {
  leads: Lead[];
}

export function DemoNextSteps({ leads }: DemoNextStepsProps) {
  if (leads.length === 0) return null;

  const highFit = leads.filter((l) => l.fit_score >= 70).length;
  const pending = leads.filter((l) => l.status === "Pending Review").length;

  return (
    <section
      aria-labelledby="next-steps-heading"
      className="bg-[--bg-elevated] border border-[--border-subtle] rounded-lg px-4 py-3"
    >
      <h2
        id="next-steps-heading"
        className="text-xs font-semibold text-[--text-primary] uppercase tracking-wide"
      >
        What to look at next
      </h2>
      <ol className="mt-2 space-y-1.5 text-xs text-[--text-secondary] list-decimal list-inside">
        <li>
          Sort or filter the lead table — start with{" "}
          {highFit > 0 ? `${highFit} high-fit` : "top"} leads by fit score.
        </li>
        <li>Open a row to inspect agent trace, evidence, and QA before approving.</li>
        <li>
          Use Approve / Reject / Needs edit locally ({pending} pending) — then export
          reviewed leads as CSV.
        </li>
        <li>
          Add Leads (above) when your backend is available; replay demo below needs no API.
        </li>
      </ol>
    </section>
  );
}
