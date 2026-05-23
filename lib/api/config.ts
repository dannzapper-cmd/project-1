/**
 * Phase 7.0 — frontend data-source configuration.
 *
 * The dashboard reads `DATA_SOURCE` to decide whether to consume the
 * static `lib/mock-data.ts` (Phase 6.x default) or the real backend
 * via `lib/api/client.ts`. The Phase 7.0 default is intentionally
 * "mock" so this preparation PR does not change runtime behaviour;
 * Phase 7.1 flips the dashboard over to "api".
 */
export const DATA_SOURCE: "api" | "mock" =
  process.env.NEXT_PUBLIC_DATA_SOURCE === "api" ? "api" : "mock";

/**
 * Base URL of the LeadForge FastAPI backend. Defaults to the local
 * dev backend on port 8000 so a forgotten `.env.local` still yields
 * a working URL during development. Override via
 * `NEXT_PUBLIC_API_URL` for staging / production.
 */
export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
