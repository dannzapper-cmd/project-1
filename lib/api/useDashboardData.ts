"use client";

/**
 * Phase 7.1 — single read point for the `DATA_SOURCE` feature flag.
 *
 * Block 10I: the dashboard starts empty. Leads and metrics appear only
 * after the reviewer processes a batch via the intake panel. No demo
 * leads are preloaded on mount.
 */

import { useCallback } from "react";

import { DATA_SOURCE } from "./config";
import {
  normalizeLeadId,
  toAgentStatuses,
  toLeads,
  toLeadDetail,
  toRunMetrics,
} from "./adapters";
import type { EnrichedBatch } from "./types";
import { mockLeadDetail } from "@/lib/mock-data";
import type {
  AgentStatus,
  Lead,
  LeadDetail,
  RunMetrics,
} from "@/lib/types";

export interface DashboardData {
  metrics: RunMetrics | null;
  leads: Lead[];
  agentStatuses: AgentStatus[];
  getLeadDetail: (leadId: string) => LeadDetail | null;
  loading: boolean;
  error: string | null;
  dataSource: "mock" | "api";
  refresh: () => void;
}

const EMPTY_DASHBOARD: Pick<
  DashboardData,
  "metrics" | "leads" | "agentStatuses" | "getLeadDetail"
> = {
  metrics: null,
  leads: [],
  agentStatuses: [],
  getLeadDetail: () => null,
};

function buildApiDashboardData(batch: EnrichedBatch): Pick<
  DashboardData,
  "metrics" | "leads" | "agentStatuses" | "getLeadDetail"
> {
  const leads = toLeads(batch);
  const detailById = new Map<string, LeadDetail>();
  for (const enriched of batch.results) {
    const detail = toLeadDetail(enriched);
    detailById.set(detail.id, detail);
  }

  return {
    metrics: toRunMetrics(batch),
    leads,
    agentStatuses: toAgentStatuses(batch),
    getLeadDetail: (leadId: string): LeadDetail | null => {
      return (
        detailById.get(leadId) ??
        detailById.get(normalizeLeadId(leadId)) ??
        null
      );
    },
  };
}

export function buildDashboardFromBatch(
  batch: EnrichedBatch,
): Pick<DashboardData, "metrics" | "leads" | "agentStatuses" | "getLeadDetail"> {
  return buildApiDashboardData(batch);
}

/** Mock detail fallback when drawer opens without resolved detail. */
export function getMockLeadDetailFallback(lead: Lead): LeadDetail {
  return { ...mockLeadDetail, ...lead };
}

/**
 * React hook returning a normalized view model for the dashboard.
 * Starts empty; intake processing populates data via parent state.
 */
export function useDashboardData(): DashboardData {
  const dataSource = DATA_SOURCE;

  const refresh = useCallback(() => {
    // Reserved for a future manual backend refresh control.
  }, []);

  return {
    ...EMPTY_DASHBOARD,
    loading: false,
    error: null,
    dataSource,
    refresh,
  };
}
