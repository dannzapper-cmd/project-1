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

import { useEffect, useMemo, useState } from "react";

import {
  B2BProfilePackPanel,
  DEFAULT_PROFILE_PACK_ID,
} from "./B2BProfilePackPanel";
import { AgentStatusRow } from "./AgentStatusRow";
import { BusinessValueSection } from "./BusinessValueSection";
import { DemoNextSteps } from "./DemoNextSteps";
import { LeadIntakePanel } from "./LeadIntakePanel";
import { RunControls } from "./RunControls";
import { LeadTable } from "./LeadTable";
import { MetricsRow } from "./MetricsRow";
import { RunQualityPanel } from "./RunQualityPanel";
import { DashboardEmptyState } from "./DashboardEmptyState";
import { getSystemStatus, joinBatchWithLeads } from "@/lib/api/client";
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
  SystemStatusResponse,
} from "@/lib/api/types";
import type { LeadDetail } from "@/lib/types";
import { getProfilePack, type B2BProfilePackId } from "@/lib/b2b-profile-packs";
import { useDashboardData } from "@/lib/api/useDashboardData";

interface DemoDashboardClientProps {
  /** Contents of `data/demo/leads.csv` for the empty-state onboarding. */
  sampleCsvContent: string;
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

export function DemoDashboardClient({ sampleCsvContent }: DemoDashboardClientProps) {
  const [userBatch, setUserBatch] = useState<EnrichedBatch | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [systemStatusError, setSystemStatusError] = useState<string | null>(null);
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
    error,
    refresh,
    dataSource,
  } = useDashboardData();

  useEffect(() => {
    let cancelled = false;
    getSystemStatus()
      .then((status) => {
        if (cancelled) return;
        setSystemStatus(status);
        setSystemStatusError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setSystemStatus(null);
        setSystemStatusError(
          err instanceof Error ? err.message : "Backend status unavailable",
        );
      });
    return () => {
      cancelled = true;
    };
  }, []);

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

  const hasLoadedResults = displayLeads.length > 0;

  if (error) {
    return (
      <>
        <RunControls
          hasLoadedResults={false}
          systemStatus={systemStatus}
          systemStatusError={systemStatusError}
        />
        <LeadIntakePanel onBatchProcessed={handleBatchProcessed} />
        <DashboardError message={error} onRetry={refresh} />
      </>
    );
  }

  if (displayLeads.length === 0) {
    return (
      <>
        <RunControls
          hasLoadedResults={false}
          systemStatus={systemStatus}
          systemStatusError={systemStatusError}
        />
        <LeadIntakePanel onBatchProcessed={handleBatchProcessed} />
        <DashboardEmptyState sampleCsvContent={sampleCsvContent} />
      </>
    );
  }

  return (
    <>
      <RunControls
        hasLoadedResults={hasLoadedResults}
        leadsCount={displayLeads.length}
        systemStatus={systemStatus}
        systemStatusError={systemStatusError}
      />
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
      <AgentStatusRow
        agents={displayAgentStatuses}
        replayMode={displayMetrics?.run_mode === "Replay" || dataSource === "mock"}
      />
      <LeadTable
        leads={displayLeads}
        getLeadDetail={displayGetLeadDetail}
        profilePack={profilePack}
        systemStatus={systemStatus}
      />
    </>
  );
}
