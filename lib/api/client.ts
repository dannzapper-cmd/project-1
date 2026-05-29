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
import { getDemoAccessHeaders } from "./demo-access.ts";
import type {
  AssistantRequest,
  AssistantResponse,
  EmailRegenerateRequest,
  EmailRegenerateResponse,
  EnrichedBatch,
  EnrichedLeadResult,
  IntakePreviewRequest,
  IntakePreviewResponse,
  LeadIn,
  LeadPipelineContractOutput,
  LiveResearchRequest,
  LiveResearchResponse,
  PipelineRunContractOutput,
  SystemStatusResponse,
} from "./types.ts";

export interface ApiClientOptions {
  /** Override the base URL (used in tests). Defaults to `API_BASE_URL`. */
  baseUrl?: string;
  /** Override the `fetch` implementation (used in tests). */
  fetchImpl?: typeof fetch;
  /** AbortSignal forwarded to every request. */
  signal?: AbortSignal;
  /** Optional request headers. Demo access header is added automatically in browsers. */
  headers?: Record<string, string>;
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
    headers: {
      Accept: "application/json",
      ...getDemoAccessHeaders(),
      ...(opts.headers ?? {}),
    },
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

async function postJson<T>(
  path: string,
  body: unknown,
  opts: ApiClientOptions = {},
): Promise<T> {
  const baseUrl = opts.baseUrl ?? API_BASE_URL;
  const fetchImpl = opts.fetchImpl ?? fetch;
  const url = joinUrl(baseUrl, path);

  const response = await fetchImpl(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...getDemoAccessHeaders(),
      ...(opts.headers ?? {}),
    },
    body: JSON.stringify(body),
    signal: opts.signal,
    credentials: "omit",
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ApiError(
      `POST ${path} failed with HTTP ${response.status}`,
      { status: response.status, url, body: text.slice(0, 500) },
    );
  }

  return (await response.json()) as T;
}

async function postForm<T>(
  path: string,
  body: FormData,
  opts: ApiClientOptions = {},
): Promise<T> {
  const baseUrl = opts.baseUrl ?? API_BASE_URL;
  const fetchImpl = opts.fetchImpl ?? fetch;
  const url = joinUrl(baseUrl, path);

  const response = await fetchImpl(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      ...getDemoAccessHeaders(),
      ...(opts.headers ?? {}),
    },
    body,
    signal: opts.signal,
    credentials: "omit",
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ApiError(
      `POST ${path} failed with HTTP ${response.status}`,
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

export function getSystemStatus(
  opts: ApiClientOptions = {},
): Promise<SystemStatusResponse> {
  return getJson<SystemStatusResponse>("/api/system/status", opts);
}

export function postIntakePreview(
  request: IntakePreviewRequest,
  opts: ApiClientOptions = {},
): Promise<IntakePreviewResponse> {
  return postJson<IntakePreviewResponse>("/api/intake/preview", request, opts);
}

export function postCsvIntakePreview(
  file: File,
  opts: ApiClientOptions = {},
): Promise<IntakePreviewResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("generate_missing_lead_ids", "true");
  return postForm<IntakePreviewResponse>("/api/intake/preview-file/csv", form, opts);
}

export function postIntakeFilePreview(
  file: File,
  opts: ApiClientOptions = {},
): Promise<IntakePreviewResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("generate_missing_lead_ids", "true");
  return postForm<IntakePreviewResponse>("/api/intake/extract-file", form, opts);
}

export function postPipelineBatch(
  leads: LeadIn[],
  opts: ApiClientOptions = {},
): Promise<PipelineRunContractOutput> {
  return postJson<PipelineRunContractOutput>("/api/demo/pipeline/batch", { leads }, opts);
}

/**
 * Block 10E — manual single-lead live web research.
 *
 * The endpoint always returns HTTP 200 with a structured
 * {@link LiveResearchResponse}. Callers must render the matching
 * UI from `status` and `user_message` rather than treating any
 * non-`ok` status as a hard error.
 */
export function postLiveCompanyResearch(
  request: LiveResearchRequest,
  opts: ApiClientOptions = {},
): Promise<LiveResearchResponse> {
  return postJson<LiveResearchResponse>(
    "/api/research/live-company",
    request,
    opts,
  );
}

/**
 * Block 10G — manual single-lead contextual assistant.
 *
 * The endpoint always returns HTTP 200 with a structured
 * {@link AssistantResponse}. Callers must render the matching UI
 * from `status` and `user_message` rather than treating any non-`ok`
 * status as a hard error.
 */
export function postAssistantLeadQuestion(
  request: AssistantRequest,
  opts: ApiClientOptions = {},
): Promise<AssistantResponse> {
  return postJson<AssistantResponse>(
    "/api/assistant/lead-question",
    request,
    opts,
  );
}

/**
 * Block 11C.4 — controlled single-lead live email draft regeneration.
 *
 * Backend-only Groq path. No API keys are accepted from the browser and the
 * backend route returns draft text only; it never sends email or writes CRM.
 */
export function postRegenerateEmailDraft(
  leadId: string,
  request: EmailRegenerateRequest,
  opts: ApiClientOptions = {},
): Promise<EmailRegenerateResponse> {
  return postJson<EmailRegenerateResponse>(
    `/api/demo/email/regenerate-draft/${encodeURIComponent(leadId)}`,
    request,
    opts,
  );
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
