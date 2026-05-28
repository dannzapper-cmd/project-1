/**
 * Block 11C.4 — controlled regenerate draft client tests.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { ApiError, getSystemStatus, postRegenerateEmailDraft } from "../client.ts";
import type {
  EmailRegenerateRequest,
  EmailRegenerateResponse,
  SystemStatusResponse,
} from "../types.ts";

function statusBody(): SystemStatusResponse {
  return {
    backend_alive: true,
    demo_mode_available: true,
    demo_access_required: true,
    live_research_configured: false,
    live_model_pipeline_configured: true,
    live_email_regenerate_configured: true,
    assistant_configured: false,
    rate_limit_enabled: true,
    max_leads_per_run: 10,
    max_upload_size_mb: 5,
    live_single_lead_only: true,
    public_live_batch_enabled: false,
    storage_mode: "ephemeral",
    build_sha: "abc123",
  };
}

function requestBody(): EmailRegenerateRequest {
  return {
    lead: {
      company_name: "Acme Corp",
      industry: "B2B SaaS",
      contact_role: "VP Sales",
      company_summary: "Acme sells sales ops software.",
      pain_hypothesis: "Manual qualification slows outreach.",
      sales_angle: "Lead scoring transparency",
      core_message: "Reviewable drafts with traceability",
      personalization_notes: ["Use the RevOps angle."],
    },
  };
}

function regenerateBody(): EmailRegenerateResponse {
  return {
    status: "ok",
    mode: "live_groq",
    lead_id: "lead_001",
    draft_only: true,
    email_subject: "Idea for Acme",
    email_body: "Hi there,\n\nDraft only.",
    personalization_notes: ["Used provided lead context."],
    provider: "groq",
    model: "llama-3.1-8b-instant",
    latency: "1.2s",
    tokens: 420,
    estimated_cost: "$0.001",
    user_message: "Live Groq draft regenerated for this lead only. Draft not sent.",
    warnings: [],
  };
}

describe("controlled live status and regenerate draft client", () => {
  it("reads /api/system/status capability flags", async () => {
    const fakeFetch = (async (url: string) => {
      assert.equal(url, "https://api.test/api/system/status");
      return new Response(JSON.stringify(statusBody()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const response = await getSystemStatus({
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(response.live_email_regenerate_configured, true);
    assert.equal(response.public_live_batch_enabled, false);
  });

  it("posts selected lead context to the single-lead regenerate endpoint", async () => {
    let capturedUrl = "";
    let capturedBody = "";
    const fakeFetch = (async (url: string, init?: RequestInit) => {
      capturedUrl = url;
      capturedBody = String(init?.body ?? "");
      return new Response(JSON.stringify(regenerateBody()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const response = await postRegenerateEmailDraft("lead_001", requestBody(), {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(capturedUrl, "https://api.test/api/demo/email/regenerate-draft/lead_001");
    assert.equal(JSON.parse(capturedBody).lead.company_name, "Acme Corp");
    assert.equal(response.status, "ok");
    assert.equal(response.draft_only, true);
  });

  it("throws ApiError on protected-route HTTP failures", async () => {
    const fakeFetch = (async () =>
      new Response("rate limited", {
        status: 429,
        headers: { "Content-Type": "text/plain" },
      })) as unknown as typeof fetch;

    await assert.rejects(
      () =>
        postRegenerateEmailDraft("lead_001", requestBody(), {
          baseUrl: "https://api.test",
          fetchImpl: fakeFetch,
        }),
      (err: unknown) =>
        err instanceof ApiError &&
        err.status === 429 &&
        err.url.includes("/api/demo/email/regenerate-draft/lead_001"),
    );
  });
});
