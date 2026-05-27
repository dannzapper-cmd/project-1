"use client";

import { useMemo } from "react";
import { Gauge } from "lucide-react";

import { computeRunQualitySummary } from "@/lib/metrics/run-quality";
import type { Lead, RunMetrics } from "@/lib/types";

interface RunQualityPanelProps {
  metrics: RunMetrics;
  dataSource: "mock" | "api";
  leads?: Lead[];
  lowEvidenceCount?: number;
  userBatchActive?: boolean;
  lowEvidenceWarning?: string;
}

export function RunQualityPanel({
  metrics,
  dataSource,
  leads,
  lowEvidenceCount,
  userBatchActive,
  lowEvidenceWarning,
}: RunQualityPanelProps) {
  const quality = useMemo(
    () =>
      computeRunQualitySummary({
        metrics,
        dataSource,
        leads,
        lowEvidenceCount,
        userBatchActive,
        lowEvidenceWarning,
      }),
    [metrics, dataSource, leads, lowEvidenceCount, userBatchActive, lowEvidenceWarning],
  );

  if (quality.leadsProcessed === 0) {
    return null;
  }

  return (
    <section
      aria-labelledby="run-quality-heading"
      className="surface-card rounded-lg p-5"
    >
      <div className="mb-4 space-y-1">
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-[--accent-primary]" aria-hidden />
          <h2
            id="run-quality-heading"
            className="text-sm font-semibold text-[--text-primary]"
          >
            Run quality &amp; mode
          </h2>
        </div>
        <p className="text-xs text-[--text-muted] pl-6">
          How this batch ran — replay/demo vs live, model, processing time, and
          estimated cost.
        </p>
      </div>

      <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <dt className="text-xs text-[--text-muted]">Run mode</dt>
          <dd className="font-medium text-[--text-primary] mt-0.5">
            {quality.runModeLabel}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[--text-muted]">Model</dt>
          <dd className="font-medium text-[--text-primary] mt-0.5">
            {quality.modelModeLabel}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[--text-muted]">Leads processed</dt>
          <dd className="font-medium text-[--text-primary] mt-0.5">
            {quality.leadsProcessed}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[--text-muted]">Avg QA score</dt>
          <dd className="font-medium text-[--accent-primary] mt-0.5">
            {quality.avgQaScoreLabel}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[--text-muted]">Data source</dt>
          <dd className="font-medium text-[--text-secondary] mt-0.5">
            {quality.dataSourceLabel}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[--text-muted]">Run cost</dt>
          <dd className="font-mono font-medium text-[--text-primary] mt-0.5">
            {quality.totalCostLabel}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-[--text-muted]">Cost per lead</dt>
          <dd className="font-mono font-medium text-[--text-primary] mt-0.5">
            {quality.costPerLeadLabel}
          </dd>
        </div>
      </dl>

      {quality.lowEvidenceNote && (
        <p className="text-xs text-[--color-warning] bg-[--color-warning-bg] border border-[--color-warning]/30 rounded-lg px-3 py-2 mt-4">
          {quality.lowEvidenceNote}
        </p>
      )}

      <p className="text-xs text-[--text-muted] mt-4">{quality.replayNote}</p>
    </section>
  );
}
