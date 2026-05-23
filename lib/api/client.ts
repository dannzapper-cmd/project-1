/**
 * Phase 7.0 — minimal typed fetch client for the LeadForge backend.
 *
 * This module is **plumbing only**. It does not consume or render
 * any UI; the dashboard continues to read `lib/mock-data.ts` until
 * Phase 7.1 flips the `DATA_SOURCE` flag. The client deliberately
 * has no React/Next dependency so it can be unit-tested against
 * the captured fixtures with the Node test runner.
 */

import { API_BASE_URL } from "./config.ts";
import type {
  EnrichedBatch,
  EnrichedLeadResult,
  LeadIn,
  LeadPipelineContractOutput,
  PipelineRunContractOutput,
} from "./types.ts";

export interface ApiClientOptions {
  /** Override the base URL (used in tests). Defaults to `API_BASE_URL`. */
  baseUrl?: string;
  /** Override the `fetch` implementation (used in tests). */
  fetchImpl?: typeof fetch;
  /** AbortSignal forwarded to every request. */
  signal?: AbortSignal;
}

export class ApiError extends Error {
  readonly status: number;
  readonly url: string;
  readonly body: string;

  constructor(message: string, opts: { status: number; url: string; body: string }) {
    super(message);
    this.name = "ApiError";
    this.status = opts.status;
    this.url = opts.url;
    this.body = opts.body;
  }
}

function joinUrl(base: string, path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const trimmedBase = base.replace(/\/+$/, "");
  const trimmedPath = path.startsWith("/") ? path : `/${path}`;
  return `${trimmedBase}${trimmedPath}`;
}

async function getJson<T>(path: string, opts: ApiClientOptions = {}): Promise<T> {
  const baseUrl = opts.baseUrl ?? API_BASE_URL;
  const fetchImpl = opts.fetchImpl ?? fetch;
  const url = joinUrl(baseUrl, path);

  const response = await fetchImpl(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal: opts.signal,
    // The demo backend is fully read-only and never sets cookies.
    credentials: "omit",
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ApiError(
      `GET ${path} failed with HTTP ${response.status}`,
      { status: response.status, url, body: text.slice(0, 500) },
    );
  }

  return (await response.json()) as T;
}

// --------------------------------------------------------------------------- //
// Low-level endpoint wrappers                                                 //
// --------------------------------------------------------------------------- //

export function getPipelineBatch(
  opts: ApiClientOptions = {},
): Promise<PipelineRunContractOutput> {
  return getJson<PipelineRunContractOutput>("/api/demo/pipeline/batch", opts);
}

export function getPipelineForLead(
  leadId: string,
  opts: ApiClientOptions = {},
): Promise<LeadPipelineContractOutput> {
  return getJson<LeadPipelineContractOutput>(
    `/api/demo/pipeline/${encodeURIComponent(leadId)}`,
    opts,
  );
}

export function getDemoLeads(opts: ApiClientOptions = {}): Promise<LeadIn[]> {
  return getJson<LeadIn[]>("/api/demo/leads", opts);
}

// --------------------------------------------------------------------------- //
// Joined endpoint — pipeline/batch enriched with LeadIn rows                  //
// --------------------------------------------------------------------------- //

/**
 * Combine `GET /api/demo/pipeline/batch` with `GET /api/demo/leads`,
 * joining client-side on `lead_id`. Each per-lead pipeline result is
 * paired with its source `LeadIn`. Components downstream consume the
 * enriched shape so they don't have to issue two requests + join.
 *
 * The two endpoints are fetched in parallel. A missing lead_id on
 * either side resolves to `lead_in = null` rather than throwing — a
 * partial dataset still renders.
 */
export async function getPipelineBatchEnriched(
  opts: ApiClientOptions = {},
): Promise<EnrichedBatch> {
  const [batch, leads] = await Promise.all([
    getPipelineBatch(opts),
    getDemoLeads(opts),
  ]);

  return joinBatchWithLeads(batch, leads);
}

/**
 * Pure join helper exported for tests. Stable, order-preserving:
 * the output `results` list mirrors the order of `batch.results`.
 */
export function joinBatchWithLeads(
  batch: PipelineRunContractOutput,
  leads: LeadIn[],
): EnrichedBatch {
  const leadsById = new Map<string, LeadIn>();
  for (const lead of leads) {
    leadsById.set(lead.lead_id, lead);
  }

  const enrichedResults: EnrichedLeadResult[] = batch.results.map((result) => ({
    result,
    lead_in: leadsById.get(result.lead_id) ?? null,
  }));

  return {
    run_id: batch.run_id,
    run_mode: batch.run_mode,
    model_mode: batch.model_mode,
    lead_count: batch.lead_count,
    summary: batch.summary,
    results: enrichedResults,
  };
}
