"use client";

/**
 * Phase 7.1 — client wrapper for the demo dashboard's data-driven
 * sections.
 *
 * `app/demo/page.tsx` stays a server component so it can keep its
 * `metadata` export and the surrounding banner/header chrome. This
 * file owns:
 *
 * * the single call to `useDashboardData()`;
 * * the loading / error / empty states; and
 * * passing the normalized view model down to the existing
 *   `MetricsRow`, `AgentStatusRow`, and `LeadTable` components.
 *
 * The `DATA_SOURCE` flag is read only inside `useDashboardData`,
 * not here.
 */

import { AgentStatusRow } from "./AgentStatusRow";
import { LeadTable } from "./LeadTable";
import { MetricsRow } from "./MetricsRow";
import { useDashboardData } from "@/lib/api/useDashboardData";

function DashboardSkeleton() {
  // Lightweight skeleton that mirrors the production layout (metrics
  // row + agent row + table) so the page does not visibly reflow
  // when data arrives. Uses the same surface tokens as the real
  // cards so the placeholder blends with the dashboard theme.
  return (
    <div className="space-y-6" aria-busy="true" aria-live="polite">
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-28 bg-[--bg-surface] border border-[--border-subtle] rounded-lg animate-pulse"
          />
        ))}
      </div>
      <div className="grid grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-24 bg-[--bg-surface] border border-[--border-subtle] rounded-lg animate-pulse"
          />
        ))}
      </div>
      <div className="h-64 bg-[--bg-surface] border border-[--border-default] rounded-lg animate-pulse" />
      <p className="sr-only">Loading dashboard data…</p>
    </div>
  );
}

function DashboardError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div
      role="alert"
      className="bg-[--color-error-bg] border border-[--color-error]/30 rounded-lg p-6 text-center space-y-3"
    >
      <p className="text-sm font-medium text-[--color-error]">
        Could not load dashboard data.
      </p>
      <p className="text-xs text-[--text-secondary]">{message}</p>
      <p className="text-xs text-[--text-muted]">
        Confirm the backend is running on{" "}
        <code className="font-mono">NEXT_PUBLIC_API_URL</code> and reachable from the browser.
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="text-sm text-[--accent-primary] hover:underline"
      >
        Try again
      </button>
    </div>
  );
}

function DashboardEmpty() {
  return (
    <div className="bg-[--bg-surface] border border-[--border-default] rounded-lg p-8 text-center">
      <p className="text-sm font-medium text-[--text-primary]">
        No leads in this run.
      </p>
      <p className="text-xs text-[--text-muted] mt-2">
        The backend returned an empty pipeline result. Try refreshing once new
        demo leads are seeded.
      </p>
    </div>
  );
}

export function DemoDashboardClient() {
  const {
    metrics,
    leads,
    agentStatuses,
    getLeadDetail,
    loading,
    error,
    refresh,
  } = useDashboardData();

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return <DashboardError message={error} onRetry={refresh} />;
  }

  if (leads.length === 0) {
    return <DashboardEmpty />;
  }

  return (
    <>
      <MetricsRow metrics={metrics} />
      <AgentStatusRow agents={agentStatuses} />
      <LeadTable leads={leads} getLeadDetail={getLeadDetail} />
    </>
  );
}
