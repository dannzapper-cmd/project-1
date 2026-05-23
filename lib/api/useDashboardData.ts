"use client";

/**
 * Phase 7.1 — single read point for the `DATA_SOURCE` feature flag.
 *
 * This hook is the *only* module in the dashboard that consults
 * `lib/api/config.ts`. Components consume the normalized view model
 * returned here and therefore do not care whether the data came
 * from `lib/mock-data.ts` or from the live FastAPI backend. Future
 * phases (Groq, live mode, websockets) only touch this hook.
 *
 * Return contract (`DashboardData`):
 *
 * * `metrics` / `leads` / `agentStatuses` — the existing dashboard
 *   view-model shapes from `lib/types.ts`. In mock mode these are
 *   the same `mockRunMetrics` / `mockLeads` / `mockAgentStatus`
 *   constants the dashboard has always used. In API mode they are
 *   produced by the pure adapters in `lib/api/adapters.ts`.
 * * `getLeadDetail(leadId)` — synchronous lookup of a single
 *   `LeadDetail`. In API mode this reads from the already-loaded
 *   `EnrichedBatch` held in memory; **no second fetch is issued
 *   from the detail drawer**. In mock mode it returns the existing
 *   `mockLeadDetail` shape merged with the selected lead.
 * * `loading` / `error` / `dataSource` — UI hooks. `loading` is
 *   always `false` in mock mode; `error` is always `null` in mock
 *   mode.
 * * `refresh()` — optional re-fetch in API mode (no-op in mock).
 *   Not currently wired to any UI control; reserved for a future
 *   phase that introduces a refresh button. The "Process Leads"
 *   button stays disabled in Phase 7.1 per the Phase 7.1 prompt.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DATA_SOURCE } from "./config";
import { ApiError, getPipelineBatchEnriched } from "./client";
import {
  normalizeLeadId,
  toAgentStatuses,
  toLeads,
  toLeadDetail,
  toRunMetrics,
} from "./adapters";
import type { EnrichedBatch } from "./types";
import {
  mockAgentStatus,
  mockLeadDetail,
  mockLeads,
  mockRunMetrics,
} from "@/lib/mock-data";
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

/** Mock-mode adapter: re-creates the existing dashboard behavior. */
function buildMockDashboardData(): Pick<
  DashboardData,
  "metrics" | "leads" | "agentStatuses" | "getLeadDetail"
> {
  const leadById = new Map<string, Lead>();
  for (const lead of mockLeads) leadById.set(lead.id, lead);

  return {
    metrics: mockRunMetrics,
    leads: mockLeads,
    agentStatuses: mockAgentStatus,
    // Phase 7.0 decision: normalize `lead-001` → `lead_001` on the way
    // in so a future state migration to the backend's underscore form
    // does not break this lookup. In mock mode, ids stay as they are.
    getLeadDetail: (leadId: string): LeadDetail | null => {
      const lead =
        leadById.get(leadId) ?? leadById.get(normalizeLeadId(leadId)) ?? null;
      if (!lead) return null;
      return { ...mockLeadDetail, ...lead };
    },
  };
}

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

function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    return `Backend returned HTTP ${err.status} (${err.url}).`;
  }
  if (err instanceof TypeError) {
    // Browser / Node 22 `fetch` throws a `TypeError` ("fetch failed",
    // "Failed to fetch", "NetworkError when attempting to fetch
    // resource", etc.) when the host is unreachable, DNS fails, or
    // CORS blocks the request. Surface a clearer message.
    return "Could not reach the backend. The request failed before a response was received.";
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Unknown error while loading dashboard data.";
}

/**
 * React hook returning a normalized view model for the dashboard.
 * Safe to call from a client component; in mock mode it does no
 * network work.
 */
export function useDashboardData(): DashboardData {
  const dataSource = DATA_SOURCE;

  // Mock branch: synchronous and stable across renders.
  const mockData = useMemo(buildMockDashboardData, []);

  // API branch state. Held even in mock mode so the hook keeps the
  // same return shape regardless of mode.
  const [batch, setBatch] = useState<EnrichedBatch | null>(null);
  const [loading, setLoading] = useState<boolean>(dataSource === "api");
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState<number>(0);

  // Track whether the component is still mounted so an in-flight
  // fetch never calls setState after unmount.
  const mountedRef = useRef<boolean>(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (dataSource !== "api") return;

    const controller = new AbortController();
    let cancelled = false;

    setLoading(true);
    setError(null);

    getPipelineBatchEnriched({ signal: controller.signal })
      .then((result) => {
        if (cancelled || !mountedRef.current) return;
        setBatch(result);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled || !mountedRef.current) return;
        // Ignore aborts triggered by component unmount / refresh.
        if (err?.name === "AbortError") return;
        setBatch(null);
        setError(describeError(err));
        setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [dataSource, refreshTick]);

  const refresh = useCallback(() => {
    setRefreshTick((t) => t + 1);
  }, []);

  if (dataSource === "mock") {
    return {
      ...mockData,
      loading: false,
      error: null,
      dataSource: "mock",
      refresh,
    };
  }

  if (batch === null) {
    // Either still loading or load failed. Components handle these
    // states explicitly; we still return well-typed empty values so
    // a partial render (e.g. layout skeleton) does not crash.
    return {
      metrics: null,
      leads: [],
      agentStatuses: [],
      getLeadDetail: () => null,
      loading,
      error,
      dataSource: "api",
      refresh,
    };
  }

  const apiData = buildApiDashboardData(batch);
  return {
    ...apiData,
    loading: false,
    error: null,
    dataSource: "api",
    refresh,
  };
}
