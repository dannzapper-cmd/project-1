/**
 * Controlled Groq Live Demo Mode client tests.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  ApiError,
  getLiveDemoStatus,
  postLiveDemoRun,
  postLiveDemoUnlock,
} from "../client.ts";
import {
  clearStoredLiveSessionToken,
  getStoredLiveSessionToken,
  LIVE_SESSION_HEADER,
  setStoredLiveSessionToken,
} from "../live-demo-access.ts";
import type {
  LiveDemoRunResponse,
  LiveDemoStatusResponse,
  LiveDemoUnlockResponse,
} from "../types.ts";

function statusBody(overrides: Partial<LiveDemoStatusResponse> = {}): LiveDemoStatusResponse {
  return {
    available: false,
    groq_configured: false,
    live_mode_enabled: false,
    live_mode_unlocked: false,
    unlock_required: true,
    model_name: null,
    limits: {
      max_live_leads_per_run: 3,
      max_live_runs_per_session_per_day: 3,
      max_live_runs_per_ip_per_day: 10,
      max_live_agent_steps_per_lead: 6,
      max_live_tokens_per_lead: 6000,
      daily_live_demo_budget_usd: 1,
      live_model_timeout_seconds: 30,
      live_concurrency_limit: 1,
    },
    unavailable_reasons: ["live_mode_disabled", "groq_api_key_missing"],
    session_runs_remaining_today: null,
    ip_runs_remaining_today: null,
    daily_budget_remaining_usd: null,
    ...overrides,
  };
}

function unlockBody(): LiveDemoUnlockResponse {
  return {
    unlocked: true,
    session_token: "session-token",
    message: "Groq Live Demo Mode unlocked for this browser session.",
  };
}

function runBody(): LiveDemoRunResponse {
  return {
    results: [
      {
        lead_id: "lead_001",
        pipeline: null,
        metadata: {
          run_mode: "groq_live",
          model_provider: "groq",
          model_name: "llama-3.1-8b-instant",
          estimated_tokens: 120,
          estimated_cost_usd: 0.001,
          latency_ms: 250,
          parse_success: true,
          fallback_used: false,
          warnings: [],
          limits_applied: [],
          live_mode_unlocked: true,
        },
        error: null,
      },
    ],
    rejected_lead_ids: [],
    message: "Groq Live Demo Mode completed for 1 lead.",
  };
}

describe("controlled Groq Live Demo client", () => {
  it("reads /api/demo/live/status without secrets", async () => {
    const fakeFetch = (async (url: string) => {
      assert.equal(url, "https://api.test/api/demo/live/status");
      return new Response(JSON.stringify(statusBody()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const response = await getLiveDemoStatus({
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(response.live_mode_enabled, false);
    assert.equal(response.groq_configured, false);
    assert.equal(response.available, false);
    assert.deepEqual(response.unavailable_reasons, [
      "live_mode_disabled",
      "groq_api_key_missing",
    ]);
  });

  it("posts unlock code and lets callers store the returned session token", async () => {
    let capturedBody = "";
    const fakeFetch = (async (url: string, init?: RequestInit) => {
      assert.equal(url, "https://api.test/api/demo/live/unlock");
      capturedBody = String(init?.body ?? "");
      return new Response(JSON.stringify(unlockBody()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    clearStoredLiveSessionToken();
    const response = await postLiveDemoUnlock("reviewer-code", {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });
    if (response.session_token) {
      setStoredLiveSessionToken(response.session_token);
    }

    assert.equal(JSON.parse(capturedBody).unlock_code, "reviewer-code");
    assert.equal(response.unlocked, true);
    assert.equal(getStoredLiveSessionToken(), "session-token");
    clearStoredLiveSessionToken();
  });

  it("throws ApiError when unlock code is rejected", async () => {
    const fakeFetch = (async () =>
      new Response(JSON.stringify({ detail: "Incorrect unlock code." }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      })) as unknown as typeof fetch;

    await assert.rejects(
      () =>
        postLiveDemoUnlock("wrong-code", {
          baseUrl: "https://api.test",
          fetchImpl: fakeFetch,
        }),
      (err: unknown) => err instanceof ApiError && err.status === 403,
    );
  });

  it("sends X-LeadForge-Live-Session on live run requests", async () => {
    let capturedHeaders: HeadersInit | undefined;
    const fakeFetch = (async (url: string, init?: RequestInit) => {
      assert.equal(url, "https://api.test/api/demo/live/run");
      capturedHeaders = init?.headers;
      return new Response(JSON.stringify(runBody()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    setStoredLiveSessionToken("session-token");
    try {
      const response = await postLiveDemoRun(
        { lead_ids: ["lead_001"] },
        { baseUrl: "https://api.test", fetchImpl: fakeFetch },
      );

      assert.equal(response.results[0].metadata.run_mode, "groq_live");
    } finally {
      clearStoredLiveSessionToken();
    }

    assert.equal(
      (capturedHeaders as Record<string, string>)[LIVE_SESSION_HEADER],
      "session-token",
    );
  });
});
