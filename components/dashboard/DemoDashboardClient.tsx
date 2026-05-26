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

import { useMemo, useState } from "react";

import {
  B2BProfilePackPanel,
  DEFAULT_PROFILE_PACK_ID,
} from "./B2BProfilePackPanel";
import { AgentStatusRow } from "./AgentStatusRow";
import { BusinessValueSection } from "./BusinessValueSection";
import { DemoNextSteps } from "./DemoNextSteps";
import { LeadIntakePanel } from "./LeadIntakePanel";
import { LeadTable } from "./LeadTable";
import { MetricsRow } from "./MetricsRow";
import { RunQualityPanel } from "./RunQualityPanel";
import { joinBatchWithLeads } from "@/lib/api/client";
import {
  toAgentStatuses,
  toLeadDetail,
  toLeads,
  toRunMetrics,
} from "@/lib/api/adapters";
import type {
  EnrichedBatch,
  LeadIn,
  PipelineRunContractOutput,
} from "@/lib/api/types";
import type { LeadDetail } from "@/lib/types";
import { getProfilePack, type B2BProfilePackId } from "@/lib/b2b-profile-packs";
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
  const [userBatch, setUserBatch] = useState<EnrichedBatch | null>(null);
  const [profilePackId, setProfilePackId] =
    useState<B2BProfilePackId>(DEFAULT_PROFILE_PACK_ID);
  const profilePack = useMemo(
    () => getProfilePack(profilePackId),
    [profilePackId],
  );
  const {
    metrics,
    leads,
    agentStatuses,
    getLeadDetail,
    loading,
    error,
    refresh,
    dataSource,
  } = useDashboardData();

  const processedDashboard = useMemo(() => {
    if (!userBatch) return null;
    const detailById = new Map<string, LeadDetail>();
    for (const enriched of userBatch.results) {
      const detail = toLeadDetail(enriched);
      detailById.set(detail.id, detail);
    }
    return {
      metrics: toRunMetrics(userBatch),
      leads: toLeads(userBatch),
      agentStatuses: toAgentStatuses(userBatch),
      getLeadDetail: (leadId: string): LeadDetail | null =>
        detailById.get(leadId) ?? null,
    };
  }, [userBatch]);

  const handleBatchProcessed = (
    batch: PipelineRunContractOutput,
    sourceLeads: LeadIn[],
  ) => {
    setUserBatch(joinBatchWithLeads(batch, sourceLeads));
  };

  const displayMetrics = processedDashboard?.metrics ?? metrics;
  const displayLeads = processedDashboard?.leads ?? leads;
  const displayAgentStatuses = processedDashboard?.agentStatuses ?? agentStatuses;
  const displayGetLeadDetail = processedDashboard?.getLeadDetail ?? getLeadDetail;
  const userBatchActive = userBatch !== null;

  const lowEvidenceCount = useMemo(() => {
    if (!displayMetrics || displayLeads.length === 0) return 0;
    return displayLeads.filter(
      (lead) => displayGetLeadDetail(lead.id)?.low_evidence === true,
    ).length;
  }, [displayLeads, displayGetLeadDetail, displayMetrics]);

  const batchIndustries = useMemo(
    () => displayLeads.map((lead) => lead.industry),
    [displayLeads],
  );

  if (loading) {
    return (
      <>
        <LeadIntakePanel onBatchProcessed={handleBatchProcessed} />
        <DashboardSkeleton />
      </>
    );
  }

  if (error) {
    return (
      <>
        <LeadIntakePanel onBatchProcessed={handleBatchProcessed} />
        <DashboardError message={error} onRetry={refresh} />
      </>
    );
  }

  if (displayLeads.length === 0) {
    return (
      <>
        <LeadIntakePanel onBatchProcessed={handleBatchProcessed} />
        <DashboardEmpty />
      </>
    );
  }

  return (
    <>
      <LeadIntakePanel onBatchProcessed={handleBatchProcessed} />
      <B2BProfilePackPanel
        selectedId={profilePackId}
        onSelect={setProfilePackId}
        batchIndustries={batchIndustries}
      />
      {displayMetrics && (
        <>
          <MetricsRow
            metrics={displayMetrics}
            metricCopyOverride={profilePack.metricCopyOverride}
          />
          <RunQualityPanel
            metrics={displayMetrics}
            dataSource={dataSource}
            leads={displayLeads}
            lowEvidenceCount={lowEvidenceCount}
            userBatchActive={userBatchActive}
            lowEvidenceWarning={profilePack.lowEvidenceWarning}
          />
          <BusinessValueSection metrics={displayMetrics} leads={displayLeads} />
          <DemoNextSteps leads={displayLeads} />
        </>
      )}
      <AgentStatusRow agents={displayAgentStatuses} />
      <LeadTable
        leads={displayLeads}
        getLeadDetail={displayGetLeadDetail}
        profilePack={profilePack}
      />
    </>
  );
}
